#!/usr/bin/env python
from argparse import ArgumentParser
import os
import sys
from typing import Set, Tuple

from text2phenotype.common.common import get_file_list
from text2phenotype.tagtog.splitting_pdfs import split_annotated_pdf


def get_file_key(file_name: str) -> str:
    return os.path.splitext(os.path.split(file_name)[1])[0]


def get_matched_files(pdf_dir: str, ann_dir: str) -> Set[Tuple[str, str]]:
    pdfs = get_file_list(pdf_dir, '.pdf')
    anns = get_file_list(ann_dir, '.json')

    ann_map = {get_file_key(ann.replace('.ann.json', '')): ann for ann in anns}

    file_pairs = set()
    for pdf in pdfs:
        pdf_key = get_file_key(pdf)
        if pdf_key in ann_map:
            file_pairs.add((pdf, ann_map[pdf_key]))

    return file_pairs


def process_file_pairs(file_pairs: Set[Tuple[str, str]], target_size: int, out_dir: str):
    for pdf, ann in file_pairs:
        split_annotated_pdf(pdf, ann, out_dir, target_size)


def parse_args(argv):
    parser = ArgumentParser()
    parser.add_argument('--ann_dir', required=True, help='The directory containing the tagtog annotation files to split.')
    parser.add_argument('--pdf_dir', required=True, help='The directory containing the PDF files to split.')
    parser.add_argument('--target_size', type=int, default=50, help='The ideal number of pages in the split PDFs.')
    parser.add_argument('--out_dir', required=True, help='The output directory to write split files to.')

    return parser.parse_args(argv)


def main(argv):
    parsed_args = parse_args(argv)

    file_pairs = get_matched_files(parsed_args.pdf_dir, parsed_args.ann_dir)

    process_file_pairs(file_pairs, parsed_args.target_size, parsed_args.out_dir)


if __name__ == '__main__':
    main(sys.argv[1:])
