import concurrent.futures
import os
import pickle
import time

from typing import Iterable, List, Tuple, Any, Generator

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import (
    TextRecognitionResult,
    TextOperationStatusCodes,
    ComputerVisionErrorException
)
from cachetools import (
    cached,
    TTLCache,
)
from msrest.authentication import CognitiveServicesCredentials

from text2phenotype.common.decorators import retry
from text2phenotype.common.log import operations_logger
from text2phenotype.constants.common import OCR_PAGE_SPLITTING_KEY
from text2phenotype.constants.environment import Environment
from text2phenotype.ocr.data_structures import OCRPageInfo, OCRCoordinate

from text2phenotype.ocr.ocr_helpers import (
    make_pngs_from_pdf,
    calculate_doc_indices,
    mk_image_with_bboxes,
)


class SeparatorInterruptedException(Exception):
    pass


class Orientation(object):
    TABULAR = 1
    REGULAR = 2


class Row(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.top = min(l.top for l in self)
        self.right = max(l.right for l in self)
        self.left = min(l.left for l in self)
        self.bottom = max(l.bottom for l in self)
        self.len = len(self)
        self.order = None

    @property
    def height(self):
        return self.bottom - self.top

    def update_size(self):
        self.top = min(l.top for l in self)
        self.right = max(l.right for l in self)
        self.left = min(l.left for l in self)
        self.bottom = max(l.bottom for l in self)


class Box:
    def __init__(self, left, right, top, bottom):
        super(Box, self).__init__()
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def h_center(self):
        return (self.left + self.right) / 2

    def __repr__(self):
        return f'{self.left} {self.right} {self.top} {self.bottom}'


@cached(cache=TTLCache(maxsize=1, ttl=300))
def get_computer_vision_client():
    credentials = CognitiveServicesCredentials(Environment.AZURE_OCR_SUBSCRIPTION_KEY.value)
    return ComputerVisionClient(Environment.AZURE_OCR_ENDPOINT.value, credentials)


def ocr_pdf_file(pdf_file_path: str, working_dir: str,
                 tid: str = None, draw_boundaries: bool = False) -> List[OCRPageInfo]:
    """
    Function converts PDF file to PNGs (one per page) and sends to Microsoft Azure
    Cognitive Services Computer Vision API to extract text as a list of OCRPageInfo objects.
    :param tid: transaction id
    :param pdf_file_path: str
    :param working_dir: directory for storing PNGs
    :param draw_boundaries: instructs the function to create png's with the blocks' bounding boxes drawn.
           The generated images are intended to be used for research and not production purposes.
    :return: extracted text as a list of OCRPageInfo objects
    """

    inputs = make_pngs_from_pdf(pdf_file_path, working_dir, tid)

    client = get_computer_vision_client()
    inputs = [(client, i // 10 * 2, *elem) for i, elem in enumerate(inputs)]

    workers_cnt = min(Environment.AZURE_MAX_CONCURRENT_REQUESTS.value, len(inputs))

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers_cnt) as executor:
        operations_logger.info(f'Sending PNGs to Azure OCR using {workers_cnt} threads', tid=tid)
        send_png_results = executor.map(_send_data_to_azure, *zip(*inputs))
        operations_logger.info('Calling Azure OCR to retrieve results', tid=tid)
        results = executor.map(_get_azure_recognition_result, *zip(*send_png_results))

    operations_logger.info('Formatting Azure OCR response', tid=tid)

    if draw_boundaries:
        draw_bounding_boxes(results)

    processed_result = process_recognition_results(results, tid)
    document_full_text = OCR_PAGE_SPLITTING_KEY[0].join((p.text for p in processed_result))

    return document_full_text, processed_result


@retry(ComputerVisionErrorException, logger=operations_logger)
def _send_data_to_azure(client: ComputerVisionClient, sleep_time: int, pg: int, png_file: str, tid: str) -> Tuple[ComputerVisionClient, int, str, str, str]:
    # Run Azure recognizing process
    try:
        time.sleep(sleep_time)

        with open(png_file, 'rb') as file:
            response = client.batch_read_file_in_stream(image=file, raw=True)

        # Get operation ID from returned headers
        operation_location_url = response.headers["Operation-Location"]
        operation_id = operation_location_url.split('/')[-1]
        return client, pg, png_file, operation_id, tid
    except Exception as e:
        operations_logger.exception("An exception occurred in the "
                                    "_send_data_to_azure.", exc_info=True, tid=tid)
        raise e


def _get_azure_recognition_result(client: ComputerVisionClient,
                                  pg: int,
                                  png_file: str,
                                  operation_id: str,
                                  tid: str = None) -> Tuple[int, str, Any]:
    try:
        start = time.time()
        while time.time() - start < Environment.AZURE_RESULT_WAITING_TIMEOUT.value:
                result = client.get_read_operation_result(operation_id)
                if result.status == TextOperationStatusCodes.succeeded:

                    pickle_file = f'{png_file.rstrip(".png")}.pkl'
                    pickle.dump(result.recognition_results, open(pickle_file, 'wb'))

                    operations_logger.info("Pickled response from Azure OCR API "
                                           f"for {png_file} in {pickle_file}", tid=tid)

                    return pg, png_file, pickle_file
                elif result.status in [TextOperationStatusCodes.not_started, TextOperationStatusCodes.running]:
                    time.sleep(1)
                else:
                    raise Exception(f'Azure OCR processing failed for {png_file}, pg #{pg},'
                        f'operation id: {operation_id}')
        raise Exception(f'Azzure OCR proccessing timeout exceeded for {png_file}, page #{pg},'
            f'operation id: {operation_id}')

    except Exception as e:
        operations_logger.exception("An exception occurred in the "
                                    "_get_azure_recognition_result.", exc_info=True, tid=tid)
        raise e


def find_separator(row, separators):
    vertical_center = (row.top + row.bottom) / 2
    for sep in separators:
        if sep.top <= vertical_center <= sep.bottom:
            return sep
    return None


def iter_reordered_blocks(rows, separators):

    column_left = []
    column_right = []
    for row in rows:
        sep = find_separator(row, separators)
        if sep:
            for block in row:
                if block.right <= sep.left:
                    column_left.append(block)
                else:
                    column_right.append(block)
        else:
            for block in column_left + column_right + row:
                yield [word for word in block.words]
            column_left = []
            column_right = []

    for block in column_left + column_right:
        yield [word for word in block.words]


def enrich_block(block):
    block.left = block.bounding_box[0]
    block.top = block.bounding_box[1]
    block.right = block.bounding_box[4]
    block.bottom = block.bounding_box[5]
    block.width = block.right - block.left
    block.height = block.bottom - block.top
    block.center = (
        (block.left + block.right) / 2,
        (block.top + block.bottom) / 2
    )
    return block


def is_row_ended(a, b):
    s = 0
    low_coef = 0.15
    high_coef = 0.4

    h = a.bottom - a.top
    d = a.bottom - b.top
    if d > 0 and d / h < 0.32:
        return True

    if b.bottom <= a.top or 0 < (b.bottom - a.top) / h < 0.32:
        return True

    if b.top >= a.bottom:
        s += high_coef
    if b.top > a.top:
        s += low_coef
    if b.left <= a.left:
        s += high_coef
    if b.left < a.right:
        s += low_coef
    return s > 0.5


def get_rows(text_result: TextRecognitionResult) -> List[Row]:
    """
    Get row by row horizontal projections of Azure line blocks
    :param text_result: result of Azure text recognition
    :return: list of Row objects
    """

    lines = list(map(enrich_block, text_result.lines))
    if not lines:
        return []

    rows = []
    lines[0].order = 0
    row = Row([lines[0]])
    for i, line in enumerate(lines[1:], start=1):
        line.order = i
        if is_row_ended(lines[i - 1], line):
            rows.append(row)
            row = Row([line])
        else:
            row.append(line)
    rows.append(row)
    return rows


def get_separator(row):
    separator = Box(
        left=row[0].right,
        right=row[1].left,
        top=min(r.top for r in row),
        bottom=max(r.bottom for r in row)
    )
    separator.l_width = row[0].width
    separator.l_count = 1
    separator.r_width = row[1].width
    separator.r_count = 1
    return separator


def update_projection_separator(row, separator):
    updated_separator = separator
    if len(row) == 1:
        box = row[0]

        if box.left < separator.left:  # left column
            if box.right < separator.right:
                updated_separator.bottom = box.bottom
                if box.right > separator.left:
                    updated_separator.left = box.right
                    updated_separator.l_width += row[0].width
                    updated_separator.l_count += 1
            else:
                raise SeparatorInterruptedException()
        elif box.left < separator.right:  # right column
            if box.right > separator.right:
                updated_separator.right = box.left
                updated_separator.bottom = box.bottom

                updated_separator.r_width += row[0].width
                updated_separator.r_count += 1
            else:
                raise SeparatorInterruptedException()
    elif len(row) == 2:
        updated_separator.left = max(row[0].right, separator.left)
        updated_separator.right = min(row[1].left, separator.right)
        updated_separator.bottom = max(r.bottom for r in row)

        updated_separator.l_width += row[0].width
        updated_separator.l_count += 1
        updated_separator.r_width += row[1].width
        updated_separator.r_count += 1

    return updated_separator


def detect_orientation(rows: List) -> Tuple[Orientation, float]:
    """
    Detect page orientation: tabular or regular (regular/2-column)
    :param rows: list of page text line (as Row objects), given as horizontal projection of Azure line blocks.
    :return: Tuple of Orientation constant (TABULAR or REGULAR) and the ratio of tabular rows to overall rows count: (Oritntaion, float)
    """

    # calculate tabular row count (row is tabular when it contains more than two blocks)
    tabular_rows_count = sum([1 for row in rows if len(row) > 2])
    rows_count = len(rows)
    tabular_ratio = tabular_rows_count / rows_count if rows_count else 0
    return (Orientation.TABULAR if tabular_ratio > 0.3 else Orientation.REGULAR, tabular_ratio)


def is_key_val_separator(s):
    return False
    w1 = s.l_width / s.l_count
    w2 = s.r_width / s.r_count

    x = w2 / w1

    return x < 0.5


def get_rows_projection_separators(rows) -> List[Box]:
    separators = []
    separator = None

    for r in rows:
        blocks_count = len(r)
        try:
            if separator and blocks_count > 2:
                raise SeparatorInterruptedException()
            elif separator:
                separator = update_projection_separator(r, separator)
                if separator.width <= 0:
                    raise SeparatorInterruptedException()

            elif blocks_count == 2:
                separator = get_separator(r)
        except SeparatorInterruptedException:
            if not is_key_val_separator(separator):
                separators.append(separator)  # separator ended
            separator = None

    if separator and not is_key_val_separator(separator):
        separators.append(separator)

    return separators


def reorder_lines_tabular(rows: List) -> Generator[List, None, None]:
    """
    Reorder Azure line blocks and words inside the blocks, keeping the structure of a tabular page.
    Multiline cells are merging in a single text line.
    :param rows: list of page text line (as Row objects), given as horizontal projection of Azure line blocks.
    :return: generator of lists of Azure word blocks (simple representation of line blocks)
    """

    # get maximum line blocks counts in the row (assuming it's the count of table columns)
    column_count = max(map(len, rows))
    cell_bounds = []
    # go through all rows and collect left and right coordinate for cells in full rows (rows which len is equal to count fo columns)
    i = 0
    for r in rows:
        if len(r) == column_count:
            cell_bounds.append([])
            for c in r:
                cell_bounds[i].append(Box(c.left, c.right, 0, 0))
            i += 1

    # wides coordinates for each cell
    max_cell_bounds = []
    for i in range(column_count):
        max_cell_bounds.append(
            Box(
                min(c[i].left for c in cell_bounds),
                max(c[i].right for c in cell_bounds),
                0, 0)
            )
    cell_matrix = []
    table_row_number = -1
    table_started = False

    # iterate through rows and put its words to an appropriate cell, guessing it by bound coordinates
    for r in rows:
        if len(r) >= column_count:
            # full table row, no need to allocate words by cells, use the original order
            cell_matrix.append([list(map(enrich_block, line.words)) for line in r])

            table_row_number += 1
            table_started = True
        elif not table_started:
            # row is not full, but the table is not started (none full rows was encountered)
            cell_matrix.append([list(map(enrich_block, line.words)) for line in r] + [[]] * (column_count - len(r)))

            table_row_number += 1
        else:
            if len(r) > 2:
                # row is not full, but it has more than 2 filled cells. assuming it's a separate table row
                # if cells count is less than 2, the current row's words will be allocated at previous row's cells.
                table_row_number += 1
                cell_matrix.append([])
                for i in range(column_count):
                    cell_matrix[table_row_number].append([])

            # get list of word objects that have 'left' and 'right' propierties
            words = []
            for cell in r:
                for w in map(enrich_block, cell.words):
                    words.append(w)

            i = 0
            j = 0

            # iterate through words and cells and put words to appropriate cell by checking its coordiantes and bounds
            while j < len(words):
                w = words[j]
                cell_bound_left = 0 if i == 0 else max_cell_bounds[i - 1].right

                cell_bound_right = w.right if i + 1 == len(max_cell_bounds) else max_cell_bounds[i + 1].left

                if w.left >= cell_bound_left and w.right <= cell_bound_right + 10:
                    # cell found, go to the next word
                    cell_matrix[table_row_number][i].append(w)
                    j += 1
                elif w.left >= cell_bound_right or abs(w.left - cell_bound_right) < 10:
                    # word is out of current cell, skip to the next cell
                    i += 1
                    if i >= len(max_cell_bounds):
                        break
                else:
                    # word is out of cell bounds (break in table), add it as separate row
                    cell_matrix.append([[w]] + [[]] * (column_count - 1))
                    table_row_number += 1
                    break
    for row in cell_matrix:
        yield [word for cell in row for word in cell]


def process_recognition_results(recognition_results: List, tid: str) -> List[OCRPageInfo]:
    """
    Given result of Azure OCR service, convert in to list of OCRPageInfo objects
    :param recognition_results: An array of text recognition result of the read operation.
    :return: extracted text as a list of OCRPageInfo objects
    """

    result = list()
    last_index = 0
    for pg, png_file, pickled_response in recognition_results:

        operations_logger.info(f'Started processing {pickled_response}.', tid=tid)

        response = pickle.load(open(pickled_response, 'rb'))

        ocr_page = OCRPageInfo(text="",
                               page=pg,
                               png_path=png_file)

        full_text = ""
        index = order = 0

        for text_result in response:
            rows = get_rows(text_result)
            page_width = text_result.width
            orientation, ratio = detect_orientation(rows)
            if orientation == Orientation.REGULAR:
                lines = reorder_lines_by_separators(rows, page_width)
            else:
                lines = reorder_lines_tabular(rows)

            for line in lines:
                for i, word in enumerate(line):
                    full_text += word.text
                    coord = OCRCoordinate(text=word.text,
                                          page=pg,
                                          left=word.bounding_box[0],
                                          top=word.bounding_box[1],
                                          right=word.bounding_box[4],
                                          bottom=word.bounding_box[5],
                                          order=order,
                                          page_index_first=index,
                                          document_index_first=index + last_index)
                    order += 1
                    index += len(word.text)
                    coord.page_index_last = index - 1
                    coord.document_index_last = index + last_index - 1

                    if i < len(line) - 1:
                        coord.spaces = 1
                        full_text += ' '
                    else:
                        coord.new_line = True
                        full_text += '\n'
                    index += 1
                    ocr_page.coordinates.append(coord)

        last_index += index
        ocr_page.text = full_text
        result.append(ocr_page)

    calculate_doc_indices(result)
    return result


def is_separator_at_page_center(x, page_width):
    page_hor_center = page_width / 2
    d = abs(x.h_center - page_hor_center) / page_width
    return x.left < page_hor_center < x.right or d < 0.1


def reorder_lines_by_separators(rows, page_width):

    separators = get_rows_projection_separators(rows)

    if len(separators) > 3:
        filtered_separators = []
    else:
        filtered_separators = list(filter(lambda x: is_separator_at_page_center(x, page_width), separators))

    return iter_reordered_blocks(rows, filtered_separators)


def draw_bounding_boxes(results: Iterable[Tuple[int, str, Any]]) -> None:
    """
    Given an iterable of tuples from the calling ocr function, create images of the
    each document page that have rectangles drawn around the text word boundary coordinates.
    :param results: page number, png_file of document page, response object from Azure
    :return: None
    """
    for pg, png_file, response in results:
        preamble = os.path.splitext(png_file)[0][:-10]
        postamble = os.path.splitext(png_file)[0][len(preamble):]
        output_path = f'{preamble}_bounding_boxes{postamble}.png'
        block_bounds = []
        for text_result in response:
            for line in text_result.lines:
                    block_bounds.append([
                        line.bounding_box[0],  # left
                        line.bounding_box[1],  # top
                        line.bounding_box[4],  # right
                        line.bounding_box[5],  # bottom
                    ])

        operations_logger.debug(f'drawing block boundaries for {png_file} to {output_path}\n')
        mk_image_with_bboxes(png_file, block_bounds, 'blue', 0, output_path)
