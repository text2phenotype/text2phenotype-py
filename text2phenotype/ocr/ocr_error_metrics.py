"""
Calculate Word Error Rate (WER) and Character Error Rate (CER)
from known true text (annotated) and OCR text

Can also use `fuzzywuzzy.process()` to find the closest N matches from a list of text
"""
from typing import Union, Tuple, List
from fuzzywuzzy import fuzz

import numpy as np

from text2phenotype.common.log import operations_logger
from text2phenotype.annotations.file_helpers import AnnotationSet, Annotation


class TextPair:
    """
    Collect a pair of text matches, eg noisy/"dirty" (OCR) and true/"clean" (normalized)
    Order doesnt matter, other than for consistency
    Use this in a list to look at the scores for a given "document"
    """
    def __init__(self, noisy_text: str, true_text: str, label=None):
        self.noisy_text = noisy_text
        self.true_text = true_text
        self.label = label

    def __eq__(self, other):
        if isinstance(other, TextPair):
            return self.noisy_text == other.noisy_text and self.true_text == other.true_text
        else:
            operations_logger.warning(f"Trying to compare type '{type(other)}' to TextPair")
            return False

    def __repr__(self):
        label_str = f"label='{self.label}'" if self.label else ""
        return (
            f"{self.__class__.__name__}(" +
            f"noisy_text='{self.noisy_text}', " +
            f"true_text='{self.true_text}'" +
            label_str +
            ")"
        )

    @property
    def ratio_score(self) -> float:
        """
        Float score between 0 and 1.0, based on Levenshtein distance
        """
        return fuzz.ratio(self.noisy_text, self.true_text) / 100


def match_annotation_sets(
        ann_set_noisy: AnnotationSet,
        ann_set_true: AnnotationSet,
        char_range_match_threshold: int = 4,
):
    """
    Given a noisy and a true set of annotations, return the average Levenschtein Distance over all entries
    :param ann_set_noisy: true annotations
    :param ann_set_true: true annotations
    :param char_range_match_threshold: how many characters away to look for a match
    """
    # find a matching annotation
    text_pairs = []
    for ann in ann_set_noisy.entries:
        matched_ann = get_similar_annotation(
            ann, ann_set_true,
            char_range_match_threshold=char_range_match_threshold)
        if matched_ann:  # can get None if no matches
            text_pairs.append(TextPair(ann.text, matched_ann.text, label=ann.label))

    return text_pairs


def get_mean_score(text_pairs: List[TextPair]) -> float:
    """
    For a set of text pairs, return the average ratio score across the sets
    """
    # weighted average based on max string length?
    avg_match_score = np.mean([entry.ratio_score for entry in text_pairs])
    return float(avg_match_score)


def get_match_pct(text_pairs: List[TextPair]) -> float:
    """
    What percentage of text pairs per document were a complete match?
    A complete match has a ratio score of 1.0
    """
    return get_num_matches(text_pairs) / len(text_pairs)


def get_num_matches(text_pairs: List[TextPair]) -> int:
    """
    How many 100% matches were there in the set (accuracy)
    """
    return sum([pair.ratio_score == 1.0 for pair in text_pairs])


def text_range_is_close(ann_1: Annotation, ann_2: Annotation, range_bounds: int = 4) -> bool:
    """
    Return True if two annotations have the same label and approximately similar text_ranges, else false
    :param ann_1: Annotation
    :param ann_2: Annotation
    :param range_bounds: int, allowed difference in range;
        eg if ann1 has end within +- range_bounds of end of ann2, it matches
    :return: bool
    """
    return (
        ann_2.text_range[0] - range_bounds <= ann_1.text_range[0] <= ann_2.text_range[0] + range_bounds or
        ann_2.text_range[1] - range_bounds <= ann_1.text_range[1] <= ann_2.text_range[1] + range_bounds
    )


def text_range_distance(text_range_1: list, text_range_2: list):
    """Get L2 distance between text coordinates"""
    return np.sqrt((text_range_1[0] - text_range_2[0]) ** 2 + (text_range_1[1] - text_range_2[1]) ** 2)


def get_similar_annotation(
        ann: Annotation,
        ann_set: AnnotationSet,
        char_range_match_threshold: int = 400,
        similarity_threshold: int = 50,
) -> Union[Annotation, None]:
    """
    :param ann: noisy annotation we want to match to the true text
    :param ann_set: true annotations
    :param char_range_match_threshold: how many characters away to look for a match
    :param similarity_threshold: output of fuzz.ratio that we threshold for similar text
    :return:
    """
    matching_label = [
        entry for entry in ann_set.entries
        if ann.label == entry.label
    ]
    # find annotations in a similar text range
    matching_range = [
        entry for entry in matching_label
        if text_range_is_close(ann, entry, range_bounds=char_range_match_threshold)
    ]
    if not matching_range:
        operations_logger.warning(f"No matches found for {ann}")
        match = None
    elif len(matching_range) > 1:
        # found more than one matching range
        # look for matching text next to narrow it down
        # NOTE: we look for matching text AFTER range bc may be multiple anns with same text and diff range
        # TODO: another option is to use fuzzywuzzy to find closest text?
        text_similarity = [fuzz.ratio(ann.text, entry.text) for entry in matching_range]
        matching_text = [matching_range[i] for i, score in enumerate(text_similarity) if score > similarity_threshold]

        # matching_text = [entry for entry in matching_range if ann.text == entry.text]
        if len(matching_text) == 1:
            # if we have a text match with the fuzzy range match, choose that
            match = matching_text[0]
        else:
            # zero or more than one text match, get the range distance and find closest
            operations_logger.debug(f"More than one match found for {ann}: {matching_text}, selecting the closest")
            distances = [text_range_distance(ann.text_range, entry.text_range) for entry in matching_range]
            match = matching_range[np.argmin(distances)]

    else:
        # found one matching range, use that
        match = matching_range[0]

    return match
