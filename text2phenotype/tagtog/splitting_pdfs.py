import copy
from typing import Tuple, List
import os

from PyPDF2 import PdfFileReader, PdfFileWriter

from text2phenotype.common.common import read_json, write_json
from text2phenotype.common.log import operations_logger


# TODO if we ant to use this in prod add pyPDF2 to requirements
# altered to be slightly more generalizable from
# https://datascience.text2phenotype.com/notebook/ana-bargo/biomed-tagtog/notebooks/clinical_summary/00_meds_review_select_files_splice_tagtog_push.ipynb
def split_pdf(pdf_fp, pages_to_keep, out_fp):
    with open(pdf_fp, 'rb') as infile:
        reader = PdfFileReader(infile)
        page_count = reader.getNumPages()
        operations_logger.info(f'Selecting {len(pages_to_keep)} from a {page_count} pg pdf')
        writer = PdfFileWriter()
        for pg in pages_to_keep:
            if pg < page_count:
                writer.addPage(reader.getPage(pg))
        operations_logger.info(f'Writing output spliced pdf to {out_fp}')
        with open(out_fp, 'wb') as outfile:
            writer.write(outfile)


def split_annotation_json(ann_json: str, pages_to_keep: List[int], out_ann: str):
    """
    Select a subset of annotations from a tagtog annotation file.
    :param ann_json: The tagtog annotation file to process.
    :param pages_to_keep: The 0-based PDF page numbers to select annotation for.
    :param out_ann: The new annotation file to write.
    :return:
    """
    pages_to_keep = sorted(pages_to_keep)

    original_annotations = read_json(ann_json)
    original_parts = set(original_annotations['annotatable']['parts'])

    split_annotations = copy.deepcopy(original_annotations)

    parts_map = dict()
    new_parts = []
    new_part_no = 1
    for page_no in pages_to_keep:
        page_no += 1
        original_part = f's{page_no}v1'
        if original_part not in original_parts:
            continue

        new_part = f's{new_part_no}v1'
        parts_map[original_part] = new_part
        new_parts.append(new_part)
        new_part_no += 1

    new_entities = []
    for entity in original_annotations['entities']:
        part = entity['part']
        if part not in parts_map:
            continue

        new_entity = copy.deepcopy(entity)
        new_entity['part'] = parts_map[part]
        new_entities.append(new_entity)

    split_annotations['entities'] = new_entities
    split_annotations['annotatable']['parts'] = new_parts

    write_json(split_annotations, out_ann)


def split_annotated_pdf(source_pdf, ann_json, out_dir: str, target_page_count: int = 20):
    """
    Split an annotated PDF into smaller PDFs.
    :param source_pdf: The PDF file to process.
    :param ann_json: The raw TagTog annotation json file.
    :param out_dir: The directory to write output files to.
    :param target_page_count: The ideal numbers of pages in the new split PDFs.
    """
    os.makedirs(out_dir, exist_ok=True)

    with open(source_pdf, 'rb') as infile:
        reader = PdfFileReader(infile)

        page_count = reader.getNumPages()
        page_sets = get_page_numbers(page_count, target_page_count)
        for chunk_num, (first_page, last_page) in enumerate(page_sets, 1):
            pages_to_keep = list(range(first_page, last_page + 1))

            path, file_name = os.path.split(source_pdf)
            file_base, file_ext = os.path.splitext(file_name)
            out_pdf = os.path.join(out_dir, f'{file_base}_pp{first_page+1}_{last_page+1}{file_ext}')

            split_pdf(source_pdf, pages_to_keep, out_pdf)

            out_ann = f'{out_pdf}.ann.json'
            split_annotation_json(ann_json, pages_to_keep, out_ann)


def get_page_numbers(pdf_page_count: int, target_page_count: int) -> List[Tuple[int, int]]:
    """
    Generate the page divisions for the split PDFs.
    :param pdf_page_count: The total number of pages in the original PDF.
    :param target_page_count: The number of pages to try to put in each bin.
    :return: The list of (page start, page end) numbers.
    """
    number_of_sets = round(pdf_page_count / target_page_count)
    if not number_of_sets:
        number_of_sets += 1

    page_counts = [target_page_count] * number_of_sets

    # adjust the final bin counts in the case of not having a perfectly uniform division of pages
    extra_page_count = pdf_page_count - (number_of_sets * target_page_count)
    if extra_page_count < 0:
        for i in range(extra_page_count, 0):
            page_counts[i % number_of_sets] -= 1
    elif extra_page_count > 0:
        for i in range(extra_page_count):
            page_counts[i % number_of_sets] += 1

    page_start = 0
    page_numbers = []
    for page_count in page_counts:
        page_numbers.append((page_start, page_start + page_count - 1))
        page_start += page_count

    return page_numbers

