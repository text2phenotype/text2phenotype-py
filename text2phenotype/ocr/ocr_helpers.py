import glob
import os
import subprocess
from typing import List, Tuple

from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import Environment

from text2phenotype.ocr.data_structures import OCRPageInfo, OCRCoordinate, Row


TABULAR_THRESHOLD = 0.3


def make_pngs_from_pdf(pdf_file_path: str,
                       working_dir: str,
                       page_offset: int = None,
                       tid: str = None) -> List[Tuple[int, str]]:

    file_name, _ = os.path.splitext(os.path.basename(pdf_file_path))

    # make PNGs
    png_files = f"{working_dir}/{file_name}_page_%04d.png"
    png_files_star = f"{working_dir}/{file_name}_page_*.png"

    # get number of pages in PDF
    process = subprocess.Popen(["pdfinfo", pdf_file_path],
                               encoding='UTF-8',
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    pdf_info, stderr = process.communicate()
    if process.returncode != 0:
        operations_logger.exception(msg=stderr)
        raise Exception(stderr)
    pdf_info_lines = pdf_info.split('\n')
    for line in pdf_info_lines:
        if line.startswith('Pages:'):
            label, value = line.split(':')
            pdf_len = int(value.strip())
    page_nums = [str(x) for x in range(pdf_len)]

    # convert PDF to PNG (one per page)
    if pdf_len < Environment.OCR_PDF_PARALLEL_JOBS.value:
        parallel_jobs = pdf_len
    else:
        parallel_jobs = Environment.OCR_PDF_PARALLEL_JOBS.value

    operations_logger.info(f'Converting {pdf_len}-page PDF to PNG', tid=tid)

    parallel_cmd = ['parallel', '--jobs', f'{parallel_jobs}']
    convert_cmd = ['convert', '-background', 'White', '-density', '300',
                   '-define', 'png:format=png8', '-resize', '20000000@',
                   f'{pdf_file_path}[{{}}]', f'{png_files}']
    parallel_options = [':::'] + [str(pn) for pn in page_nums]
    commands = parallel_cmd + convert_cmd + parallel_options

    # Google OCR accepts images in PNG8 and PNG24 that have a maximum of 20M pixels.
    # The PNG format specified with:
    #   -define png:format=png8: ensures a compatible PNG format
    #   -resize 20000000@: specifies a resize to a maximum of 20M pixels

    subprocess.check_output(commands)

    operations_logger.debug(f"convert command: {' '.join(commands)}", tid=tid)
    png_paths = list()
    for pg, png_file in enumerate(sorted(glob.glob(png_files_star)), start=1):
        png_paths.append((pg + page_offset, png_file, tid))

    return png_paths


def calculate_doc_indices(results: List[OCRPageInfo]) -> None:
    # Calculate indexes
    order = 0
    doc_index = 0
    for p in results:
        page_index = 0
        for c in p.coordinates:
            c.order = order

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

            order += 1


def is_tabular_page(projections: List[int]) -> bool:
    """
    Takes a list of numbers and determines if the page should be formatted tabularly.
    :param projections: list of numbers from get_block_horizontal_projections.
    :return: bool indicating if the format_tabular_page func should be used
    """
    pixels_with_blocks = 0
    pixels_with_cols = 0
    pixels_with_tables = 0
    pixels_with_zero = 0
    for i in range(len(projections)):
        if projections[i] > 0:
            pixels_with_blocks += 1
            if projections[i] == 2:
                pixels_with_cols += 1
            if projections[i] > 2:
                pixels_with_tables += 1
        else:
            pixels_with_zero += 1
    table_ratio = pixels_with_tables / pixels_with_blocks if pixels_with_blocks > 0 else 0
    operations_logger.debug(
        f"{pixels_with_tables} table pixels, {pixels_with_blocks} block pixels, {table_ratio} ratio, "
        f"{pixels_with_cols} column pixels, {pixels_with_zero} zero pixels"
    )
    if table_ratio > TABULAR_THRESHOLD:
        return True
    else:
        return False


def format_tabular_page(page: OCRPageInfo) -> None:
    """
    Function converts PDF file to PNGs (one per page) and sends to Google
    Cloud Vision OCR service to extract text as a list of OCRPageInfo objects.
    Comparing to ocr_pdf_file method have extra logic to detect columns in the text.

    :param page: OCRPageInfo of OCR'd page
    :return: extracted text as a list of OCRPageInfo objects
    """

    def join_postponed(postponed_rws: List[Row], last_wrd: OCRCoordinate, space_gap_size: float) -> OCRCoordinate:
        """
        Function updates order for coordinates in provided rows and returns last coordinate to
        continue ordering starting with order of last_wrd.order.
        :param postponed_rws: list of rows that contains coordinates to be ordered
        :param last_wrd: last ordered coordinate
        :param space_gap_size: mean space size for the page
        :return: last ordered coordinate
        """
        new_last_word = last_wrd
        for r in sorted(postponed_rws, key=lambda x: x.words[0].bottom):
            wrds = enumerate(sorted(r.words, key=lambda x: x.left))
            for j, w in wrds:
                if word.spaces == 0 and j + 1 < row_len and word.have_gap_with(words[j + 1], space_gap_size):
                    w.spaces = 1
                w.order = new_last_word.order + 1
                w.new_line = False
                new_last_word = w
            new_last_word.new_line = True

        return new_last_word

    last_word = None
    rows = []
    bottom_delta = 6
    # Filter out words longer than 50 chars (exclude unrecognized table rows)
    page.coordinates = [c for c in page.coordinates if len(c.text) < 50]
    # Detect rows by bottom coordinate
    for c in page.coordinates:
        matched_existent_row = False
        for rw in rows:
            if rw.range[0] - bottom_delta <= c.bottom <= rw.range[1] + bottom_delta:
                rw.words.append(c)
                matched_existent_row = True
                if rw.range[0] > c.bottom:
                    rw.range = (c.bottom, rw.range[1])
                elif rw.range[1] < c.bottom:
                    rw.range = (rw.range[0], c.bottom)
                break
        if not matched_existent_row:
            rows.append(
                Row(
                    range=(c.bottom - 5, c.bottom + 5),
                    words=[c],
                )
            )

    postponed_rows = []
    is_column_block = False

    # Calculate mean space gap size for the whole page weighted by word height
    spaces = []
    for row in rows:
        words = sorted(row.words, key=lambda w: w.left)
        for i, word in enumerate(words):
            if word.spaces and i + 1 < len(words):
                # avoid divide by zero errors
                word_height = 1 if word.height == 0 else word.height
                spaces.append(word.get_gap_with(words[i + 1]) / word_height)

    # avoid divide by zero errors
    len_spaces = 1 if len(spaces) == 0 else len(spaces)
    space_gap_size = sum(spaces) / len_spaces

    # Loop through the rows and assign order from scratch corresponding to left coordinate of word
    for row in sorted(rows, key=lambda r: r.words[0].bottom):
        row_len = len(row.words)
        words = sorted(row.words, key=lambda w: w.left)

        # Check if inside a column block or it's ended
        if row.type == Row.Types.column:
            is_column_block = True
        elif is_column_block:
            # Not column-type row found during the column block means
            # that block is ended and postponed rows should be joined
            last_word.new_line = True
            last_word = join_postponed(postponed_rows, last_word, space_gap_size)
            postponed_rows = []
            is_column_block = False

        for i, word in enumerate(words):

            word.order = last_word.order + 1 if last_word else 0
            word.new_line = False
            last_word = word

            # Column layout detecting and separating detected columns
            if word.spaces == 0 and i + 1 < row_len and word.have_gap_with(words[i + 1], space_gap_size):
                word.spaces = 1
                if is_column_block:
                    postponed_rows.append(
                        Row(
                            range=row.range,
                            words=words[i + 1:]
                        )
                    )
                    break

        last_word.new_line = True

    # Join separated columns back (end of page)
    if postponed_rows:
        last_word.new_line = True
        last_word = join_postponed(postponed_rows, last_word, space_gap_size)

    # Sort coordinates by order
    page.coordinates = sorted(page.coordinates, key=lambda x: x.order)

    page.text = ""
    for c in page.coordinates:
        page.text += c.text + ' ' * c.spaces
        page.text += '-' if c.hyphen else ''
        page.text += '\n' if c.new_line else ''


def mk_image_with_bboxes(img_path: str, bounds: List[object], color: str= 'black',
                         offset: int=0, output_path: str=None) -> None:
    """
    Given an image, coordinates, and options, draw rectangles for each coordinate object.
    :param img_path:
    :param bounds: list of block boundary coordinates to draw the boxes at
    :param color: color used to draw
    :param offset: add space to the outside of the coordinates
    :param output_path:
    :return: None
    """
    if output_path is None:
        output_path = img_path
    cmd = ['convert', img_path, '-fill', 'none', '-strokewidth', '5', '-stroke', color]
    for bound in bounds:
        cmd_parts = ['-draw', f'rectangle {bound[0] - offset},{bound[1] - offset},'
                              f'{bound[2] + offset},{bound[3] + offset}']
        cmd.extend(cmd_parts)
    cmd.append(output_path)
    out3 = subprocess.run(cmd, check=True)
