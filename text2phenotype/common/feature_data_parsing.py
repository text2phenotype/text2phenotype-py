import string
from typing import Dict, List
from collections import defaultdict
from collections import OrderedDict
from operator import itemgetter

import re


def normalize(text: str) -> List:
    """
    :param text: raw text
    :return: list of words
    """
    return re.findall(r"[\w]+", text)


def from_bsv(text: str) -> Dict:
    """
    :param text: text of a BSV file in format code|description
    :return: term frequency dict
    """
    bow = list()
    for line in text.splitlines():
        code, raw = line.split('|')
        for token in normalize(raw):
            bow.append(token)

    return sort_tf(from_bag_of_words(bow))


def from_text(text: str) -> Dict:
    """
    :return: term frequency dict
    """
    return from_bag_of_words(normalize(text))


def from_bag_of_words(bow: list) -> Dict:
    """
    Get TF for a bag of words (list)
    """
    d = defaultdict(int)
    for word in bow:
        d[word] += 1

    return sort_tf(d)


def sort_tf(term_freq_dict, reverse=True) -> Dict:
    """
    https://stackoverflow.com/questions/20944483/python-3-sort-a-dict-by-its-values
    """
    return OrderedDict(sorted(term_freq_dict.items(), key=itemgetter(1), reverse=reverse))


def guard_range(index: object) -> range:
    """
    Enforce range type for index

    :param index: range object or list having type [start,stop]
    :return: range of [start,stop] positions, used for text span matching
    """
    # if already a range return as range
    if isinstance(index, range):
        return index

    # if list type, return the last two items as start,stop
    if isinstance(index, list):
        return range(int(index[-2]), int(index[-1]))

    if isinstance(index, tuple):
        return range(int(index[0]), int(index[1]))

    raise Exception('Range type not supported :' + str(type(index)))


def overlap_ranges(range1: object, range2: object) -> set:
    """
    Return a set of character positions for two text spans

    Example overlap( range(0,6), range(2,4))

    :param range1: range or list [start,stop]
    :param range2: range or list [start,stop]
    :return:
    """
    r1, r2 = set(guard_range(range1)), set(guard_range(range2))
    char_map = r1.intersection(r2)

    return char_map


def remove_none(result: list) -> list:
    """
    :param result: list of any type
    :return: list without "None"
    """
    return list(filter(None, result))


def remove_punctuation(token: str) -> str:
    """
    https://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string
    :param token:
    :return:
    """
    return token.translate(str.maketrans('', '', string.punctuation))


def sort_uniq(unsorted: List[str]) -> List[str]:
    """
    :param unsorted: any unsorted list
    :return: sorted and filtered list of only unique strings
    """
    return sorted(list(set(remove_none(unsorted))))


def min_max_range(index) -> tuple:
    if isinstance(index, range):
        return index[0], index[-1]
    if isinstance(index, list):
        return int(index[-2]), int(index[-1])

    if isinstance(index, tuple):
        return int(index[0]), int(index[1])

    raise Exception('Range type not supported :' + str(type(index)))


def contain_range(range1, range2):
    """
    check if the range1 contains the range2, return True if it contains and False if it doesn't
    """
    r1 = guard_range(range1)
    r2 = guard_range(range2)
    if min(r2) >= min(r1) and max(r2) <= max(r1):
        return True
    else:
        return False


def has_numbers(value: str) -> bool:
    """this function is used to check if the input string has a number"""
    return any(char.isdigit() for char in value)

def is_int(value: str) -> bool:
    if isinstance(value, str):
        return value.strip().isdigit()
    elif isinstance(value, int):
        return True
    return False

def is_digit(value: str) -> bool:
    if isinstance(value, str):
        return value.strip().lstrip('-').replace('.', '', 1).isdigit()

    if isinstance(value, (int, float)):
        return True

    return False


def is_digit_punctuation(value: str) -> bool:
    return value is not None and all(char.isdigit() or char in string.punctuation for char in value)


def seconds_digit(value: str) -> bool:
    return value is not None and re.compile(r'\d+s').search(value) is not None


def probable_lab_unit(value: str) -> bool:
    if value is not None:
        match = LAB_UNIT_REGEX_CASE_SENSITIVE.search(value)
        if match is None:
            match = LAB_UNIT_REGEX.search(value)
        return match is not None
    else:
        return False


def probable_med_unit(value: str) -> bool:
    """
    :param value: token being parsed for med units
    :return: true if a token matches a common med unit formatting, only used in the MedOutput class in biomed currently
    """
    if value is not None:
        match = DRUG_UNIT.search(value)
        if match is not None:
            return match.span()[1] - match.span()[0] >= len(value.strip())
    return False

LAB_UNIT_REGEX = re.compile(r'((liter)|(centi)|(milli)|(gram)|(nano)|(pico)|(femto)|(unit)|(mole?))+',
                            flags=re.IGNORECASE)
LAB_UNIT_REGEX_CASE_SENSITIVE = re.compile(
    r'(?<![a-zA-Z])((mm)|([mdcu]?L)|([ncmk]?g)|([nm]?mol)|(mcg)|(mEq)|[I]U)(?![a-zA-Z])')

DRUG_UNIT = re.compile(
    r'(m|mc|u|k)?g|m?L|m?mol', re.IGNORECASE)

LAB_INTERP_TERMS = {'normal', 'abnormal', 'unremarkable', 'remarkable', 'low', 'high', 'positive', 'negative',
                    'nonreactive', 'non-reactive', 'elevated', 'within', 'wnl', 'reactive', 'elevation', 'baseline',
                    'base', 'not', 'done', 'detected', 'critical', 'process', 'pending'}
KNOWN_LAB_NAMES = {'covid-19', 'covid', 'naa', 'labcorp', 'covid19', 'covid', 'sars-cov-2', 'igg', 'naat', 'sars',
                   'cov', 'ab', 'coronavirus', 'lc', 'virus', 'covid-', 'test', 'swab', }

