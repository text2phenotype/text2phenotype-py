import csv
import json
import os
import random
import uuid
import pickle
from datetime import datetime
from getpass import getuser
from time import time
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    Tuple
)

import nltk
from bs4 import BeautifulSoup

from text2phenotype.common import jsonifiers
from text2phenotype.common.log import operations_logger


###############################################################################
#
# File read/write/list operations
#
###############################################################################
from text2phenotype.constants.common import BEGINNING_SECTIONS


def read_text(text_file: str, encoding: str = 'UTF-8') -> str:
    """
    Read text from file
    :param text_file: absolute path to file
    :param encoding: provided file's encoding
    :return: file text contents
    """
    with m_open(file=text_file, encoding=encoding) as t_file:
        return t_file.read()


def write_text(contents: str, file_path: str, encoding: str = 'UTF-8') -> str:
    """
    Write file contents
    :param contents: string contents
    :param file_path: absolute path of target file
    :param encoding: provided file's encoding
    :return: text_file name
    """
    with m_open(file=file_path, mode='w', encoding=encoding) as file_path:
        file_path.write(contents)
        file_path.close()
        return file_path.name


def write_bytes(data: str, file_path: str) -> None:
    """
    Writes provided bytes to provided file path
    :param data: bytes contents
    :param file_path: absolute path to file
    :return:
    """
    with m_open(file=file_path, mode='wb') as bytes_file:
        bytes_file.write(data.encode('UTF-8'))


def read_bytes(binary_file: str) -> bytes:
    """
    Read bytes from binary file
    :param binary_file: absolute path to file
    :return: bytes file contents
    """
    with m_open(file=binary_file, mode='rb') as bin_file:
        return bytes(bin_file.read())


def write_json(contents: Dict[Any, Any], json_file_path: str, encoding: str = 'UTF-8') -> str:
    """
    Write JSON to file
    :param contents: json (dict) contents
    :param json_file_path: absolute destination file path
    :param encoding: provided file's encoding
    :return: file name
    """
    directory = os.path.dirname(json_file_path)
    os.makedirs(directory, exist_ok=True)
    with m_open(file=json_file_path, mode='w', encoding=encoding) as json_file_path:
        json.dump(contents, json_file_path, indent=4, cls=jsonifiers.CustomJsonEncoder)
        return json_file_path.name


def read_json(json_file: str, encoding: str = 'UTF-8') -> Dict[Any, Any]:
    """
    Read json from file
    :param json_file: absolute path to file
    :param encoding: provided file's encoding
    :return: json file contents
    """
    with m_open(file=json_file, encoding=encoding) as j_file:
        return json.load(j_file)


def write_pkl(contents: Any, pkl_file_path: str) -> Any:
    """
    Write pickled object to file
    :param contents: a python object (preferrably serializable)
    :param pkl_file_path: absolute destination file path
    :return: file name
    """
    directory = os.path.dirname(pkl_file_path)
    os.makedirs(directory, exist_ok=True)
    with m_open(file=pkl_file_path, mode="wb") as pkl_file:
        pickle.dump(contents, pkl_file)
        return pkl_file.name


def read_pkl(pkl_file_path: str) -> Any:
    """
    Read pickled object from file
    :param pkl_file_path: absolute path to file
    :return: json file contents
    """
    with m_open(file=pkl_file_path, mode="rb") as f:
        return pickle.load(f)


def write_csv(rows: Iterable[List[str]], file_csv: str, delimiter: str = ',', quote_char: str = '"'):
    """Parse csv file.
    :param rows: The contents to write to file.
    :param file_csv: absolute path to the csv
    :param delimiter: the delimiter used in the csv
    :param quote_char: the quote character used in the csv
    :return: an iterator of row values
    """
    with open(file_csv, 'w+') as csvfile:
        writer = csv.writer(csvfile, delimiter=delimiter, quotechar=quote_char)

        for row in rows:
            writer.writerow(row)


def read_csv(file_csv: str, delimiter: str = ',', quote_char: str = '"') -> Generator[List[str], None, None]:
    """
    Parse csv file
    :param file_csv: absolute path to the csv
    :param delimiter: the delimiter used in the csv
    :param quote_char: the quote character used in the csv
    :return: an iterator of row values
    """
    with m_open(file=file_csv) as csv_file:
        for row in csv.reader(csv_file, delimiter=delimiter, quotechar=quote_char):
            yield row


def to_escaped_string(contents: dict) -> str:
    """
    Convert a JSON-able dict to a string, with:
     - literal double quotes escaped: "foo" -> \"foo\"
     - wrapped in unescaped double quotes
    :param contents: json (dict) contents
    :return: str
    """
    converted_string = json.dumps(contents, cls=jsonifiers.CustomJsonEncoder).replace('"', r'\"')
    converted_string = f'"{converted_string}"'
    return converted_string


def from_escaped_string(contents: str) -> dict:
    """
    Convert a literal string (escaped double-quotes \" wrapped in outer "") to a dict
    :param contents:
    :return: dict, jsonable
    :raises ValueError: when literal str does not start or end with doublequote
    """
    if not contents.startswith('"') or not contents.endswith('"'):
        raise ValueError("content string does not start with a literal double_quote; check for malformed literal str")
    converted_string = contents[1:-1].replace(r'\"', '"')
    out_dict = json.loads(converted_string)
    return out_dict


def write_escaped_string_txt(contents: dict, file_path: str) -> None:
    """
    Write a json-able dict to a txt file, as a literal string with internal double quotes escaped
    :param contents: json (dict) contents
    :param file_path: absolute destination file path
    """
    write_text(to_escaped_string(contents), file_path=file_path)


def read_escaped_string_txt(file_path: str) -> dict:
    """
    Read aa txt file containing a literal string with internal double quotes escaped, return jsonable dict
    :param file_path: absolute source file path
    :return: dict, jsonable
    """
    return from_escaped_string(read_text(file_path))


def get_file_name(filepath: str) -> str:
    """
    https://stackoverflow.com/questions/541390/extracting-extension-from-filename-in-python
    :param filepath: full name of file with extension
    :return: file name
    """
    filename, file_extension = os.path.splitext(filepath)
    return filename


def get_file_type(filepath: str) -> str:
    """
    https://stackoverflow.com/questions/541390/extracting-extension-from-filename-in-python
    :param filepath: full name of file with extension
    :return: file extension
    """
    filename, file_extension = os.path.splitext(filepath)
    return file_extension


def get_file_list(location: str, file_type: str, recurse: bool = False) -> List[str]:
    """
    Get list of files matching particular file_type in target location.

    https://stackoverflow.com/questions/2212643/python-recursive-folder-read

    :param location: absolute directory path
    :param file_type: extension of files to get
    :param recurse: whether to recurse
    :return: list of absolute file paths for all files found at the location
    """
    files = []
    if os.path.isfile(location):
        if matches_file_type(location, file_type):
            files = [location]
    elif os.path.isdir(location):
        root = os.path.abspath(location)
        for dir_path, dir_names, file_names in os.walk(root):
            for filename in file_names:
                if matches_file_type(filename, file_type):
                    file_path = os.path.join(dir_path, filename)
                    files.append(file_path)
            if not recurse:
                break
    else:
        raise ValueError(f'No file or directory passed: {location}')
    return files


def matches_file_type(file_name: str, file_type: str) -> bool:
    return file_name[-(len(file_type)):] == file_type


def get_model_file_list(location: str, file_ext: str, model_type: str, recurse: bool = False) -> List[str]:
    """
    Get list of files matching particular file_type in target location.

    https://stackoverflow.com/questions/2212643/python-recursive-folder-read
    :param location: absolute directory path
    :param file_ext: extension of files to get
    :param model_type: the model type for files to get
    :param recurse: whether to recurse
    :return: list of absolute file paths for all files found at the location
    """
    files = []
    if os.path.isfile(location):
        name, ext = os.path.splitext(location)
        if file_ext.lower() == ext.lower() and name.endswith(model_type):
            files = [location]
    elif os.path.isdir(location):
        root = os.path.abspath(location)
        for dir_path, dir_names, file_names in os.walk(root):
            for filename in file_names:
                name, ext = os.path.splitext(filename)
                if file_ext.lower() == ext.lower() and name.endswith(model_type):
                    file_path = os.path.join(dir_path, filename)
                    files.append(file_path)
            if not recurse:
                break
    else:
        raise ValueError(f'No file or directory passed: {location}')
    return files


def list_from_csv_column(file_csv: str, column: str, delimiter: str = ',', quote_char: str = '"') -> List[str]:
    """
    Parses csv file and returns all values from the provided column
    :param file_csv: absolute path to the csv
    :param column: the column from which to gather values
    :param delimiter: the delimiter used in the csv
    :param quote_char: the quote character used in the csv
    :return: a list of all values from the requested column
    """
    return [row[column] for row in read_csv(file_csv=file_csv, delimiter=delimiter, quote_char=quote_char)]


def m_open(**kwargs):
    """
    Wrapper for built in open with exception handling and logging
    :return: file like object
    """
    try:
        return open(**kwargs)
    except Exception:
        operations_logger.exception('m_open raised an exception', exc_info=True)
        raise


###############################################################################
#
# Unique numbers / identifiers
#
###############################################################################

def rng(length: int) -> str:
    """
    Random Number Generator. Useful for making random patient IDs and other metadata.
    :param length: how long to make the random number string
    """
    return ''.join([str(random.randrange(0, 10)) for _ in range(length)])


def make_uuid() -> str:
    return str(uuid.uuid4())


###############################################################################
#
# Environment
#
###############################################################################


def fuzzy_word_match(txt1: str, txt2: str) -> bool:
    """
    Match if the tokens of two strings belong to the same set.
    :param txt1: first string to compare
    :param txt2: second string to compare
    :return: True if the words fuzzily match, if not, False
    """
    if txt1 and txt2:
        txt1 = set(txt1.lower().split())
        txt2 = set(txt2.lower().split())
        return len(txt1 & txt2) == len(txt1)


def extract_text_from_element(title: str) -> str:
    """
    Given an html element, strip out any elements and return only the text
    :param str title: HTML element (like a div) to extract text
    :return: stripped element text
    """
    soup = BeautifulSoup(title, "lxml")
    clean_value = soup.get_text("", strip=True)
    return clean_value


def iter_sentence(text: str) -> Iterator[Tuple[Tuple[int, int], str]]:
    """
    Break text into individual sentences.
    :param text: The text to process
    :return: The Iterator of sentence (indices in original text, text).
    """
    if not text or text.isspace():
        return []

    remaining_text = text.lstrip()
    start_index = len(text) - len(remaining_text)

    for sentence in nltk.sent_tokenize(remaining_text):
        if not remaining_text.startswith(sentence):
            raise Exception("NLTK returned some funk!")

        end_index = start_index + len(sentence)
        yield (start_index, end_index), sentence

        remaining_text = remaining_text[len(sentence):]
        text_len = len(remaining_text)
        remaining_text = remaining_text.lstrip()
        start_index = end_index + text_len - len(remaining_text)


def get_sentences(text: str) -> List[Tuple[Tuple[int, int], str]]:
    return list(iter_sentence(text))


def chunk_text_by_size(text: str, max_chunk_characters: int) -> List[Tuple[Tuple[int, int], str]]:
    """
    Break a document into chunks.
    :param text: The document text
    :param max_chunk_characters: The maximum number of characters in each chunk.
    :return: The list of chunk (indices in original text, text).
    """
    if not text or text.isspace():
        return []
    text_len = len(text)
    chunks = []
    start = 0
    while start <= text_len:
        end = get_best_split_point(text, start_point=start, max_chunk_len=max_chunk_characters,
                                   min_chunk_size=int(max_chunk_characters * 0.9))
        text_chunk = text[start: end]
        chunks.append(((start, end), text_chunk))
        start = end
    return chunks


def get_best_split_point(text, start_point: int, max_chunk_len: int, min_chunk_size: int) -> int:
    # if theres a good split point between max chunk size and min chunk size, split on the point closes to max
    max_end_point = start_point + max_chunk_len
    if max_end_point < len(text):
        for section_name in BEGINNING_SECTIONS:
            end_point = text.lower().rfind(section_name, start_point+min_chunk_size, max_end_point)
            if end_point != -1:
                return end_point

    return max_end_point


def longest_span(query, document, casesensitive=False):
    """
    Get longest spanning text position for the source 'query' against target document 'text'.

    :param query: "Adenocarcinoma of lung, stage II"
    :param document: 'Wedge biopsy of right upper lobe showing: Adenocarcinoma, Grade 2, Measuring 1 cm in diameter'
    :return: position_text for the longest_span
    """
    # I'm feeling lucky -- match the whole querystring to the target text
    match = match_query(query, document, casesensitive)
    if match:
        return match

    # Match the longest single token
    for token in sort_by_length(query):
        match = match_query(token, document)
        if match:
            return match

    # No match found.
    return None


def clean_text(text):
    """
    Clean a text string of spurious characters
    :param text:
    :return:
    """
    text = text.replace(' MG/ACTUAT', ' ')
    return text.upper().replace('.', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ')


def match_query(query, document, casesensitive=False):
    """
    Get position of query in text
    :param query: 'Adenocarcinoma'
    :param document: 'Wedge biopsy of right upper lobe showing: Adenocarcinoma, Grade 2, Measuring 1 cm in diameter'
    :return: list containing [query, start, end] positions, or None if query is not in text
    """
    if not casesensitive:
        query, document = clean_text(query), clean_text(document)

    if query in document:
        first = document.index(query)
        last = first + len(query)
        return [query, first, last]
    else:
        return None


def sort_by_length(tokens):
    """
    sort by length ( Longest tokens first )
    :param tokens: str like "Adenocarcinoma of lung, stage II"
    :return: list like ['Erythromycin', 'Allergy']
    """
    if not isinstance(tokens, list):
        tokens = tokens.split()

    tokens.sort(key=lambda s: len(s))
    return reversed(tokens)


def version_text(name: str) -> str:
    """
    Get label of version
    :param name: prepend for version
    :return: str like '1.1.1_DEID_refactor_AndyMC_2018-03-26_1522100250.1957161'
    """
    date_format = '%Y-%m-%d'
    return f'{name}_{getuser()}_{datetime.now().date().strftime(date_format)}_{time()}'


def json_validator(data):
    """
    return True if valid, False if not valid, logs error
    """
    try:
        json.loads(data)
        return True
    except ValueError as error:
        operations_logger.info("invalid json: %s" % error)
        return False