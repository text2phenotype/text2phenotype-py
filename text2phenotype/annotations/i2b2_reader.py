from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
import re
import shutil
import string
from typing import List, Dict, Any, Optional

import numpy as np
from text2phenotype.common.log import operations_logger
from text2phenotype.annotations.file_helpers import AnnotationSet


# used to strip from ends of text
STOP_PUNCTUATION = ",.:;?!"


class UnmatchedDiscontinuousText(Exception):
    """Raised when find discontinuous text (separated by ellipses) but coordinates do not match"""

    pass


class DataContext:
    """
    Labels for how the data is to be split
    """

    pretrain = "pretrain"  # used for unsupervised model training; these files have no annotation
    train = "train"  # used for supervised model training, partitioned subset from i2b2 test
    dev = "dev"  # used for individual model testing; NOT USED HERE (feature service will do this split)
    test = "test"  # holdout dataset, only used for final validation
    na = "na"  # no context assigned


@dataclass
class I2B2Entry:
    """
    data object for parsed I2B2 text and document coordinates
    Coordinates are in I2B2 format:
        line indexing starts at 1
        token indexing starts at 0, split by whitespace
    """
    text: str
    start_line: int
    start_token: int
    end_line: int
    end_token: int
    label: Optional[str] = None


class I2B2Reader(ABC):
    """
    Abstract base class for reading I2B2 formatted annotation files
    """
    def __init__(self):
        pass

    def convert_label_annotation_to_brat(self, target_label: str, i2b2_label: str):
        """
        Main entry point for dataset specific i2b2 to cyan label matching and extraction
        Currently only pulls one label at a time. This method could also join multiple passes
        on the annotation files to concatenate multiple label types from a file

        Generally, this method will deal with the challenge-specific file and folder structure
        """
        raise NotImplementedError

    def parse_i2b2_label_annotation_text(
            self,
            ann_text: str,
            raw_text: str,
            target_label: str,
            i2b2_label: str,
            label_filter_type_marker: str = None,
            label_filter_type_target: str = None,
    ):
        """
        Main entry point to create AnnotationSet from i2b2 annotation file and text
        Creates document line/token coordinates used for character position matching
        """
        raw_text_concat = raw_text.replace("\n", " ")
        # get the line and token position conversion to char position
        doc_token_ranges = self.get_doc_token_ranges(raw_text)

        ann_lines = ann_text.split("\n")  # split i2b2 annotation lines to create line coordinates
        ann_set = self.get_label_annotation_set(
            ann_lines,
            doc_token_ranges,
            i2b2_label,
            target_label,
            raw_text=raw_text,
            label_filter_type_marker=label_filter_type_marker,
            label_filter_type_target=label_filter_type_target

        )
        return ann_set

    def get_doc_token_ranges(self, raw_text: str) -> List[List[Dict[str, Any]]]:
        """
        From a list of raw text lines, return the start and end char coordinates for each token in document frame
        This will allow indexing by line and token coordinates (i2b2 standard) into doc char coordinates
        NOTE: char coordinates are assuming that any newline '\n' character counts the same as a space
        NOTE: file lines in i2b2 start with line number 1

        :param: raw_text, str
            The full document text string
            It will be split into lines internally, if the doc contains \n
        :return: List[List[Dict[str, Any]]]
            Outer list is the document line
            Inner list is the token position in the line
            Token dicts with internal fields:
                'token': content field
                'range': list with the token char start and end; end position is exclusive
        """
        raw_text_lines = raw_text.split("\n")
        raw_char_line_len = [len(line) + 1 for line in raw_text_lines]  # incl \n char in len
        raw_char_line_start = [0] + np.cumsum(raw_char_line_len).tolist()
        # split tokens by whitespace. note that whitespace maybe more than one char
        doc_token_start_by_line = [self.get_token_line_char_coord(line) for line in raw_text_lines]

        # for each line, iterate through the tokens and add the doc char position to the line-based
        # token positions will yield a list of lists that can be indexed by line and token position
        # to get the char position of the token
        doc_token_ranges = [
            [
                {
                    "token": token_dict["token"],
                    "text_range": (
                        line_start + token_dict["text_range"][0],
                        line_start + token_dict["text_range"][1],
                    ),
                }
                for token_dict in line_tokens
            ]
            for line_start, line_tokens in zip(raw_char_line_start, doc_token_start_by_line)
        ]
        return doc_token_ranges

    def get_label_annotation_set(
            self,
            ann_lines: List[str],
            doc_token_ranges: List[List[Dict[str, Any]]],
            i2b2_label: str,
            target_label_name: str,
            raw_text: str = None,
            label_filter_type_marker: str = None,
            label_filter_type_target: str = None,
    ) -> AnnotationSet:
        """
        Get an AnnotationSet for the targeted i2b2 labels, mapping an i2b2 label to a target_label_name

        NOTE: This is an I2B2 parser, and can easily be generalized as an AnnotationType
        TODO: Create Annotation abstraction and have this method be an I2B2 parser

        :param ann_lines:
            List of string content from the annotation file by line
        :param doc_token_ranges:  List[List[Dict[str, Any]]]
            Coordinate map from line/token to doc char position, output from get_doc_token_ranges()
        :param i2b2_label:
            String for the target label type, maps from MedLabelMarkers
            eg, "m"
        :param target_label_name:
            The NLP label name we want to use, comes from LabelEnum.get_category_label().persistent_label
        :param raw_text: str
            The full document text; can have \n swapped for " " or not
            If not specified, skips sanity checking the token char coords with the original document
        :param label_filter_type_marker: str
            Look for this LabelMarker in the line split
        :param label_filter_type_target: str
            Keep the annotation if the type marker has a value that matches this string
        :returns: AnnotationSet
        """
        # split the raw text into lines so we have coordinates; used for sanity check on line with leading space
        if raw_text:
            raw_text_lines = raw_text.split("\n")
        else:
            raw_text_lines = None

        ann_set = AnnotationSet()
        for i, line in enumerate(ann_lines):
            if not line:
                # empty new line
                # operations_logger.debug(f"newline {i+1}/{len(ann_lines)}")
                continue
            label_strs = line.split("||")
            label_prefix = f"{i2b2_label}="
            target_ann = [label for label in label_strs if label.startswith(label_prefix)]
            if not target_ann:
                operations_logger.warning(f"Didnt find label prefix '{label_prefix}': line='{line}'")
                continue
            if len(target_ann) > 1:
                operations_logger.warning(f"Found more than one match for label '{label_prefix}': {target_ann}")
            label, label_text = target_ann[0].split("=", 1)  # only split on the first equals
            if label_text == '"nm"':
                # label not mentioned
                continue

            if label_filter_type_marker:
                if not label_filter_type_target:
                    raise ValueError(
                        "Found label_filter_type_marker={label_filter_type_marker}, "
                        "expected label_filter_type_target not found")
                target_filter = [label for label in label_strs if label.startswith(label_filter_type_marker)]
                if not target_filter:
                    operations_logger.warning(f"Didnt find label prefix '{label_prefix}': line='{line}'")
                    continue
                if len(target_filter) > 1:
                    operations_logger.warning(f"Found more than one match for label '{label_prefix}': {target_ann}")
                # get the text inside the quote following the marker: 't="problem"' -> "problem"
                filter_label_text = re.findall(r'(?:.+)="(.*)"', target_filter[0])[0]
                if filter_label_text != label_filter_type_target:
                    continue

            # read the annotation line, minus the i2b2 label text, parse to text and text char range dicts
            try:
                # a single annotation entry may return more than one text/coord set, so we parse the returned list
                i2b2_token_coords_list = self.extract_i2b2_text_coords(label_text)
            except UnmatchedDiscontinuousText as e:
                operations_logger.warning(f"Got unmatched discontinuous text, skipping for now: {label_text}")
                continue

            # do sanity checks on the labels:
            # known errors:
            # - pluralization mismatch in the annotation text
            # - case mismatch
            # - typos in the annotation; annotation text doesnt match spelling on raw text
            for i2b2_token_coords in i2b2_token_coords_list:
                # get the text character range in document coordinates from i2b2 line/token coordinates
                i2b2_ann_text = i2b2_token_coords.text
                start_line_idx = i2b2_token_coords.start_line - 1
                end_line_idx = i2b2_token_coords.end_line - 1

                if raw_text_lines and len(raw_text_lines) > 1 and raw_text_lines[start_line_idx][0] == " ":
                    # have a leading space on the line, this will throw the token position off by one
                    # catches line 43 in /I2B2/2010 Relation Challenge/test_data/0270.txt
                    i2b2_token_coords.start_token -= 1
                    if end_line_idx == start_line_idx:
                        # if on the same line, pull back the end token index
                        i2b2_token_coords.end_token -= 1
                label_char_start = doc_token_ranges[start_line_idx][i2b2_token_coords.start_token]["text_range"][0]
                if i2b2_token_coords.end_token >= len(doc_token_ranges[end_line_idx]):
                    # sometimes the i2b2 annotation token position isnt correct,
                    # and the additional tokens are actually on the next line.
                    # Move cursor forward to next line and associated token
                    i2b2_token_coords.end_line += 1
                    end_line_idx = i2b2_token_coords.end_line - 1
                    i2b2_token_coords.end_token = i2b2_token_coords.end_token - len(doc_token_ranges[end_line_idx]) - 1
                label_char_end = doc_token_ranges[end_line_idx][i2b2_token_coords.end_token]["text_range"][1]
                text_char_range = [label_char_start, label_char_end]

                # sanity check the label char coordinates against the full doc text
                # To clean, we remove trailing stop punctuation, which probably shouldn't be in the label
                # we keep parenthetic punctuation, cause that could be useful
                i2b2_ann_text = self.clean_text(i2b2_ann_text, punc_strip=STOP_PUNCTUATION)
                if raw_text:
                    orig_doc_text = raw_text[text_char_range[0]: text_char_range[1]]
                    # force lower case, remove punctuation from the right and left
                    # WARNING: this may remove useful punctuation!
                    doc_text_cleaned = self.clean_text(orig_doc_text, punc_strip=STOP_PUNCTUATION)
                    # sanity check that cleaned ann_text matches cleaned_doc_text
                    if not self._text_equal(doc_text_cleaned, i2b2_ann_text):
                        # test for pluralization mismatch (ann_text has an extra 's')
                        if self._text_equal(doc_text_cleaned, i2b2_ann_text[:-1]):
                            operations_logger.warning(
                                f"Found pluralization mismatch: doc='{doc_text_cleaned}' != ann='{i2b2_ann_text}',"
                                "using doc text instead"
                            )
                            i2b2_ann_text = doc_text_cleaned

                    # final check, we haven't caught some typo yet
                    if not self._text_equal(doc_text_cleaned, i2b2_ann_text):
                        operations_logger.error(
                            f"ERROR: Doc text doesnt match ann text: doc='{doc_text_cleaned}' != ann='{i2b2_ann_text}'"
                            f" Using original doc_text='{orig_doc_text}'"
                        )
                        i2b2_ann_text = doc_text_cleaned  # hopefully fixes all edge cases
                # add to AnnotationSet
                if ann_set.has_matching_annotation(target_label_name, text_range=text_char_range, text=i2b2_ann_text):
                    operations_logger.debug(
                        f"Found existing annotation in ann_set, skipping: label={target_label_name}, "
                        f"text_range={text_char_range}, text={i2b2_ann_text}"
                    )
                    continue
                ann_set.add_annotation_no_coord(target_label_name, text_range=text_char_range, text=i2b2_ann_text)
        return ann_set

    @staticmethod
    def clean_text(text: str, punc_strip=string.punctuation):
        """remove the whitespace and target punctuation from the right and left"""
        return text.lower().lstrip().lstrip(punc_strip).rstrip().rstrip(punc_strip)

    @staticmethod
    def _text_equal(t1: str, t2: str) -> bool:
        """Compare text strings with ignoring all whitespace and punctuation"""
        trans = str.maketrans("", "", string.whitespace + string.punctuation)
        return t1.translate(trans) == t2.translate(trans)

    @staticmethod
    def extract_i2b2_text_coords(label_text: str) -> List[I2B2Entry]:
        """
        Expecting text with literal string format
            r'"{text}" {start_line}:{start_token} {end_line}:{end_token}'
        Sometimes get a list of coordinate pairs for each disjoint portion of the text
            These sections are often separated by ellipses in the ann_text

        :param label_text: the text associated with a specific label, split by "||"

        :returns:
            List of I2B2Annotations
        """
        # find paired quotes \".*\" in string, greedy matching matches the LAST occurrence of quote
        matches = re.findall(r'"(.*)" (.*)', label_text)  # "text" line1:token1 line2:token2
        if not matches:
            raise ValueError(f"Something went wrong in text parsing: {label_text}")
        if len(matches) > 1:
            # should never get here, really
            ValueError(f"Found multiple matches and we shouldn't have! {label_text}")
        ann_text = matches[0][0]
        text_range_str = matches[0][1]

        # find i2b2 line/token coordinate pairs
        #     line1:token1 line2:token2,line1:token1 line2:token2,line1:token1 line2:token2
        range_matches = re.findall(r"(\d+):(\d+) (\d+):(\d+)", text_range_str)

        # if we have a discontinuous range, split the label
        if len(range_matches) > 1:
            # split the ann_text at the ellipses; throw an error if there arent enough ellipses
            ann_text_split = ann_text.split("...")
            if len(ann_text_split) != len(range_matches):
                raise UnmatchedDiscontinuousText(
                    f"Found discontinuous range but incorrectly matching ellipses: {label_text}"
                )
            operations_logger.warning(f"Found discontinuous range, splitting into multiple annotations: {label_text}")
        else:
            ann_text_split = [ann_text]

        # create list of text coordinates found. Using list to get around writing discontinuous coordinates
        # See https://brat.nlplab.org/standoff.html for more info on BRAT "text-bound annotations"
        i2b2_token_coords_list = []
        for text, text_range in zip(ann_text_split, range_matches):
            i2b2_token_coords = I2B2Entry(
                text=text.strip(),
                start_line=int(text_range[0]),
                start_token=int(text_range[1]),
                end_line=int(text_range[2]),
                end_token=int(text_range[3]),
            )
            # sometimes the annotation has the incorrect end line index (one line earlier);
            # force it to be the same is the start line
            if i2b2_token_coords.end_line < i2b2_token_coords.start_line:
                operations_logger.warning(f"Found misaligned start/end doc lines, setting to be same: '{label_text}'")
                i2b2_token_coords.end_line = i2b2_token_coords.start_line

            i2b2_token_coords_list.append(i2b2_token_coords)

            # if "..." in text:
            #     # don't add this label for now, it's too complicated!
            #     # Examples:
            #     # '"long ... acting ... insulin" 115:9 115:9,116:0 116:0,116:2 116:2'
            #     # '"short-acting ... insulin" 116:0 116:0,116:2 116:2'
            #     # '"augmentin susp. 250mg/62.5 mg ( 5ml ) ( amoxicil... )" 25:0 25:9'
            #     # TODO: add parser that can pull the list of coordinates as discontinuous coordinates
            #     # https://brat.nlplab.org/standoff.html
            #     # the expected brat format for discontinuous labels:
            #     #   "label_id\tlabel_class\tlong acting insulin\t1 10; 15 20"
            #     raise ValueError(f"Label has ellipses, therefore is discontinuous: {ann_text}, label_text={label_text}")

        return i2b2_token_coords_list

    @staticmethod
    def get_token_line_char_coord(line: str):
        """
        Given a line of text, split the line into tokens, and get the token start and end positions
        End position is exclusive
        Only splits on whitespace, ignores punctuation (for now)

        :param: line
            string with text to parse
        """
        token_coords_list = []
        # group item at white spaces
        for m in re.finditer(r"\S+", line):  # generator over all non-whitespace matches
            index, item = m.start(), m.group()
            token_coords_list.append(
                {
                    "token": item,
                    "text_range": [index, index + len(item)],
                }  # (char_start, char_end), exclusive end
            )
        return token_coords_list

    @staticmethod
    def copy_raw_text_context(src_file_paths: List[str], output_folder: str, context: str):
        """
        Make a copy of all of the raw text files into the given context folder
        Appends .txt to the new filename

        :param: file_id_map
            dictionary with key "file_id" and value as source file path
        """
        context_path = os.path.join(output_folder, context)
        os.makedirs(context_path, exist_ok=True)
        for src_path in src_file_paths:
            dest_path = os.path.join(context_path, os.path.split(src_path)[1] + ".txt")
            shutil.copy(src_path, dest_path)
