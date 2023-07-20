import concurrent
import os
import pickle

from typing import Iterable, List, Tuple, Any

from cachetools import (
    cached,
    TTLCache,
)
from google.cloud import vision
from google.cloud.vision import types
from google.auth.exceptions import TransportError
from google.api_core.exceptions import ServiceUnavailable

from text2phenotype.common.decorators import retry
from text2phenotype.common.log import operations_logger
from text2phenotype.constants.common import OCR_PAGE_SPLITTING_KEY
from text2phenotype.constants.environment import Environment
from text2phenotype.ocr.data_structures import (
    OCRCoordinate,
    OCRPageInfo
)
from text2phenotype.ocr.ocr_helpers import (
    make_pngs_from_pdf,
    mk_image_with_bboxes,
    is_tabular_page,
    format_tabular_page
)

BreakType = vision.enums.TextAnnotation.DetectedBreak.BreakType


@cached(cache=TTLCache(maxsize=1, ttl=300))
def get_image_annotator_client() -> vision.ImageAnnotatorClient:
    return vision.ImageAnnotatorClient()


def google_ocr_pdf_file(pdf_file_path: str,
                        working_dir: str,
                        page_offset: int = None,
                        png_inputs: List[Tuple[int, str]] = None,
                        tid: str = None,
                        draw_boundaries: bool = False) -> Tuple[str, List[OCRPageInfo]]:
    """
    Function converts PDF file to PNGs (one per page) and sends to Google
    Cloud Vision OCR service to extract text as a list of OCRPageInfo objects.
    :param tid: transaction id
    :param pdf_file_path: str
    :param working_dir: directory for storing PNGs
    :param draw_boundaries: instructs the function to create png's with the blocks' bounding boxes drawn.
           The generated images are intended to be used for research and not production purposes.
    :return: extracted text as a list of OCRPageInfo objects
    """
    document_full_text = ''
    inputs = png_inputs if png_inputs else make_pngs_from_pdf(pdf_file_path, working_dir, page_offset, tid)
    operations_logger.info('Calling Google OCR for each page', tid=tid)

    # Add thread-safety google client to the `inputs`
    google_client = get_image_annotator_client()
    inputs = [(google_client, *elem) for elem in inputs]

    # parallel processing of png files, returns iterator of results
    with concurrent.futures.ThreadPoolExecutor(max_workers=Environment.GVC_MAX_CONCURRENT_REQUESTS.value) as executor:
        try:
            results = executor.map(_ocr_helper_func, *zip(*inputs),
                                   timeout=Environment.GVC_REQUEST_TIMEOUT.value)

        except Exception as err:
            operations_logger.exception("An exception occurred in the "
                                        "_ocr_helper_func ThreadPoolExecutor.",
                                        exc_info=True, tid=tid)
            raise err

    if draw_boundaries:
        draw_bounding_boxes(results)

    operations_logger.info('Formatting Google OCR response.', tid=tid)
    result = list()
    last_index = 0
    order = 0
    doc_order = 0
    doc_index = 0

    for pg, png_file, pickled_response in results:
        operations_logger.info(f'Started processing {pickled_response}.', tid=tid)

        response = pickle.load(open(pickled_response, 'rb'))

        full_text = response.full_text_annotation.text

        ocr_page = OCRPageInfo(text=full_text,
                               page=pg,
                               png_path=png_file)
        index = 0
        for page in response.full_text_annotation.pages:
            page_text = ''
            filtered_blocks = filter_overlapping_blocks(page.blocks)
            for block in filtered_blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        coord = OCRCoordinate(text='',
                                              page=pg,
                                              left=word.bounding_box.vertices[0].x,
                                              top=word.bounding_box.vertices[0].y,
                                              right=word.bounding_box.vertices[2].x,
                                              bottom=word.bounding_box.vertices[2].y,
                                              order=order,
                                              page_index_first=index,
                                              document_index_first=index + last_index)
                        ocr_page.coordinates.append(coord)
                        order += 1

                        for symbol in word.symbols:
                            coord.text += symbol.text
                            coord.page_index_last = index
                            coord.document_index_last = index + last_index
                            page_text += symbol.text

                            if symbol.property.detected_break.type in \
                                    {BreakType.SPACE, BreakType.SURE_SPACE}:
                                index += 1
                                coord.spaces += 1
                                page_text += ' '
                            elif symbol.property.detected_break.type == BreakType.HYPHEN:
                                index += 2  # +1 for hyphen and +1 for newline
                                coord.hyphen = True
                                coord.new_line = True
                                page_text += '-\n'
                            elif symbol.property.detected_break.type in \
                                    {BreakType.LINE_BREAK, BreakType.EOL_SURE_SPACE}:
                                index += 1
                                coord.new_line = True
                                page_text += '\n'

                            index += 1

            projections = get_block_horizontal_projections(page)
            ocr_page.text = page_text
            if is_tabular_page(projections):
                operations_logger.debug(f'Tabular Formatting for page {pg}', tid=tid)
                format_tabular_page(ocr_page)

            page_index = 0
            for c in ocr_page.coordinates:
                c.order = doc_order

                c.document_index_first = doc_index
                c.document_index_last = doc_index + len(c.text) - 1
                c.page_index_first = page_index
                c.page_index_last = page_index + len(c.text) - 1

                doc_index += len(c.text)
                page_index += len(c.text)

                if c.spaces:
                    doc_index += c.spaces
                    page_index += c.spaces

                if c.hyphen:
                    doc_index += 1
                    page_index += 1

                if c.new_line:
                    doc_index += 1
                    page_index += 1

                doc_order += 1

            result.append(ocr_page)

        document_full_text += ocr_page.text
        document_full_text += OCR_PAGE_SPLITTING_KEY[0]

        last_index += index

        operations_logger.info(f'Completed processing {pickled_response}.', tid=tid)

    operations_logger.info('Formatting Google OCR response complete.', tid=tid)
    return document_full_text, result


@retry((TransportError, ServiceUnavailable, ConnectionError), logger=operations_logger)
def _ocr_helper_func(client: vision.ImageAnnotatorClient,
                     pg: int,
                     png_file: str,
                     tid: str = None) -> Tuple[int, str, Any]:
    try:
        operations_logger.info(f"Sending {png_file} to Google Vision API.", tid=tid)
        # Read PNG contents
        with open(png_file, 'rb') as file:
            content = file.read()

        # Get text from GCV OCR
        image = types.Image(content=content)
        response = client.document_text_detection(image=image)

        if response.error.code:
            # error if non-zero
            raise Exception(f'Google OCR error for {png_file}! code: '
                            f'{response.error.code}, '
                            f'message: {response.error.message}', tid=tid)

        pickle_file = f'{png_file.rstrip(".png")}.pkl'
        pickle.dump(response, open(pickle_file, 'wb'))

        operations_logger.info("Pickled response from Google Vision API "
                               f"for {png_file} in {pickle_file}", tid=tid)

        return pg, png_file, pickle_file

    except Exception as err:
        operations_logger.exception("An exception occurred in the "
                                    "_ocr_helper_func.", exc_info=True, tid=tid)
        raise err


def filter_overlapping_blocks(blocks):
    excludes = []
    # Straightforward approach. If it will take too much time during tests may be switched to advanced e.g. Line Sweep

    for block in blocks:
        overlaps = []
        for b in blocks:
            if is_overlap(block, b) and b != block:
                overlaps.append(b)
        if overlaps:
            overlaps.append(block)
            longest = overlaps[0]

            for overlap in overlaps[1:]:
                # In theory overlapping blocks may contain completely different texts. This part can be improved by
                # calculating % of text similarity and comparing it to some threshold.
                if len(get_text(overlap)) > len(get_text(longest)):
                    excludes.append(longest)
                    longest = overlap
                else:
                    excludes.append(overlap)
    return [block for block in blocks if block not in excludes]


def is_overlap(block1, block2):

    # Check if blocks overlap each other. Simple version (consider blocks as rectangles)

    bbox1 = block1.bounding_box
    bbox2 = block2.bounding_box

    # check x axis projection intersection
    if (bbox1.vertices[0].x > bbox2.vertices[2].x) or (bbox1.vertices[2].x < bbox2.vertices[0].x):
        return False

    # check y axis projection intersection
    if (bbox1.vertices[0].y > bbox2.vertices[2].y) or (bbox1.vertices[2].y < bbox2.vertices[0].y):
        return False

    return True


def get_text(block):
    text = ""
    for paragraph in block.paragraphs:
        for word in paragraph.words:
            for symbol in word.symbols:
                text += symbol.text
                if symbol.property.detected_break.type in \
                        {BreakType.SPACE, BreakType.SURE_SPACE}:
                    text += ' '
                elif symbol.property.detected_break.type == BreakType.HYPHEN:
                    text += '-\n'
                elif symbol.property.detected_break.type in \
                        {BreakType.LINE_BREAK, BreakType.EOL_SURE_SPACE}:
                    text += '\n'
    return text


def draw_bounding_boxes(results: Iterable[Tuple[int, str, Any]]) -> None:
    """
    Given an iterable of tuples from the calling ocr function, create images of the
    each document page that have rectangles drawn around the text block boundary coordinates.
    :param results: page number, png_file of document page, response object from Google
    :return: None
    """
    for pg, png_file, response in results:
        preamble = os.path.splitext(png_file)[0][:-10]
        postamble = os.path.splitext(png_file)[0][len(preamble):]
        output_path = f'{preamble}_bounding_boxes{postamble}.png'
        block_bounds = []
        for b in response.full_text_annotation.pages[0].blocks:
            block_bounds.append([
                b.bounding_box.vertices[0].x,
                b.bounding_box.vertices[0].y,
                b.bounding_box.vertices[2].x,
                b.bounding_box.vertices[2].y
            ])

        operations_logger.debug(f'drawing block boundaries for {png_file} to {output_path}\n')
        mk_image_with_bboxes(png_file, block_bounds, 'blue', 0, output_path)


def get_block_horizontal_projections(google_response_page: object) -> List[int]:
    """
    Creates a list of numbers where each cell represents a vertical pixel row of the document and
    the numeric value of that cell contains the number of text blocks that exist on that row.
    :param google_response_page: Google specif response object, straight from the API call.
    :return: list as described above.
    """
    projections = [0]  # switch to 1-based counting
    for block in google_response_page.blocks:

        # first, get the highest top point and the lowest bottom point
        if block.bounding_box.vertices[0].y < block.bounding_box.vertices[1].y:
            block_top = block.bounding_box.vertices[0].y
        else:
            block_top = block.bounding_box.vertices[1].y

        if block.bounding_box.vertices[2].y > block.bounding_box.vertices[3].y:
            block_bottom = block.bounding_box.vertices[2].y
        else:
            block_bottom = block.bounding_box.vertices[3].y

        # ensure no negative numbers on top coordinate
        if block_top < 0:
            block_top = 0

        # determine if projections needs to grow
        # first condition is the whole block is the lowest on the page we've seen
        if len(projections) < block_top:
            projections += [0 for _ in range(len(projections), block_top)]
            projections += [1 for _ in range(block_top, block_bottom + 1)]
        # second condition is where the block is partially projected
        elif len(projections) in range(block_top, block_bottom + 1):
            for i in range(block_top, len(projections)):
                projections[i] += 1
            projections += [1 for _ in range(len(projections), block_bottom + 1)]
        # last condition is if block is entirely in a projection
        else:
            for i in range(block_top, block_bottom + 1):
                projections[i] += 1
    return projections
