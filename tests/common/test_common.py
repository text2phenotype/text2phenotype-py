import json
import os
import pickle
import stat
import unittest
from unittest.mock import mock_open, patch
from uuid import UUID

import numpy as np

from text2phenotype.common import common, speech


class TestCommon(unittest.TestCase):
    filepath = "/tmp/test.json"
    jason_text = 'Hi. Welcome to coding Python with Jason Brazeal'
    binary = os.urandom(32)
    txt_file_count = 2
    data = {"key": "value"}
    json_data = json.dumps(data)
    pkl_data = pickle.dumps(data)

    # read_text tests

    def test_read_text(self):
        with patch('builtins.open', mock_open(read_data=self.jason_text)):
            read = common.read_text(self.filepath)
            self.assertEqual(self.jason_text, read)

    def test_read_text_no_file_exception(self):
        mo = mock_open()
        mo.side_effect = FileNotFoundError()
        with patch('builtins.open', mo):
            with self.assertRaises(FileNotFoundError):
                common.read_text(self.filepath)

    def test_read_text_no_file_permission(self):
        mo = mock_open()
        mo.side_effect = PermissionError()
        with patch('builtins.open', mo):
            with self.assertRaises(PermissionError):
                common.read_text(self.filepath)

    # write_txt tests

    def test_write_text(self):
        mo = mock_open(read_data=self.jason_text)
        with patch('builtins.open', mo):
            common.write_text(self.jason_text, self.filepath)
            read = common.read_text(self.filepath)
            self.assertEqual(self.jason_text, read)

    def test_write_text_no_file_permission(self):
        mo = mock_open()
        mo.side_effect = PermissionError()
        with patch('builtins.open', mo):
            with self.assertRaises(PermissionError):
                common.write_text(self.jason_text, self.filepath)
                os.chmod(self.filepath, stat.S_IWUSR | stat.S_IRUSR)

    def test_write_bytes(self):
        encoded_data = str(self.binary).encode('utf-8')
        mo = mock_open(read_data=encoded_data)
        with patch('builtins.open', mo):
            common.write_bytes(str(self.binary), self.filepath)
            read = common.read_bytes(self.filepath)
            self.assertEqual(encoded_data, read)

    # read_bytes tests

    def test_read_bytes(self):
        mo = mock_open(read_data=self.binary)
        with patch('builtins.open', mo):
            read = common.read_bytes(self.filepath)
            self.assertEqual(self.binary, read)

    def test_read_bytes_no_file_exception(self):
        mo = mock_open()
        mo.side_effect = FileNotFoundError()
        with patch('builtins.open', mo):
            with self.assertRaises(FileNotFoundError):
                common.read_bytes(self.filepath)

    def test_read_bytes_no_file_permission(self):
        mo = mock_open()
        mo.side_effect = PermissionError()
        with patch('builtins.open', mo):
            with self.assertRaises(PermissionError):
                common.read_bytes(self.filepath)

    # write_json tests

    def test_write_json(self):
        mo = mock_open(read_data=self.json_data)
        with patch('builtins.open', mo):
            common.write_json(self.data, self.filepath)
            read = json.dumps(common.read_json(self.filepath))
            self.assertEqual(self.json_data, read)

    def test_write_json_no_file_permission(self):
        mo = mock_open()
        mo.side_effect = PermissionError()
        with patch('builtins.open', mo):
            with self.assertRaises(PermissionError):
                common.write_json(self.json_data, self.filepath)
                os.chmod(self.filepath, stat.S_IWUSR | stat.S_IRUSR)

    # read_json_tests

    def test_read_json(self):
        mo = mock_open(read_data=self.json_data)
        with patch('builtins.open', mo):
            read = json.dumps(common.read_json(self.filepath))
            self.assertEqual(self.json_data, read)

    def test_read_json_no_file_exception(self):
        with self.assertRaises(FileNotFoundError):
            common.read_json(self.filepath)

    def test_read_json_no_file_permission(self):
        mo = mock_open()
        mo.side_effect = PermissionError()
        with patch('builtins.open', mo):
            with self.assertRaises(PermissionError):
                common.read_json(self.filepath)

    # read/write pickle tests

    def test_write_pkl(self):
        filepath = self.filepath + ".pkl"
        mo = mock_open(read_data=self.pkl_data)
        with patch('builtins.open', mo):
            common.write_pkl(self.data, filepath)
            read = common.read_pkl(filepath)
            self.assertEqual(self.data, read)

    def test_read_pkl(self):
        filepath = self.filepath + ".pkl"
        mo = mock_open(read_data=self.pkl_data)
        with patch('builtins.open', mo):
            read = common.read_pkl(filepath)
            self.assertEqual(self.data, read)

    def test_read_write_pkl_w_numpy(self):
        filepath = self.filepath + ".pkl"
        data = self.data.copy()
        data["my_arr"] = np.array([0, 1, 2, 3], dtype=np.int32)
        pkl_data = pickle.dumps(data)

        mo = mock_open(read_data=pkl_data)
        with patch('builtins.open', mo):
            common.write_pkl(data, filepath)
            read = common.read_pkl(filepath)
            # manually testing dict for matches, cause unittest doesnt like matching numpy arrays
            self.assertSetEqual(set(data.keys()), set(read.keys()))
            self.assertEqual(data["key"], read['key'])
            np.testing.assert_array_equal(data["my_arr"], read["my_arr"])

    def test_read_pkl_no_file_exception(self):
        with self.assertRaises(FileNotFoundError):
            common.read_pkl(self.filepath)

    def test_read_pkl_no_file_permission(self):
        mo = mock_open()
        mo.side_effect = PermissionError()
        with patch('builtins.open', mo):
            with self.assertRaises(PermissionError):
                common.read_pkl(self.filepath)

    # read/write csv
    def test_csv_round_trip(self):
        contents = [["1", "2"], ["3", "4"]]
        file_name = "test_csv_round_trip.csv"

        try:
            common.write_csv(contents, file_name)

            for exp, obs in zip(contents, common.read_csv(file_name)):
                self.assertListEqual(exp, obs)
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

    # read/write escaped strings

    def test_to_escaped_string(self):
        content = {"foo": [1, 2, 3], "bar": 'baz'}
        escaped_str = common.to_escaped_string(content)
        self.assertEqual(
            escaped_str,
            r'"{\"foo\": [1, 2, 3], \"bar\": \"baz\"}"'
        )

    def test_from_escaped_string(self):
        content = r'"{\"foo\": [1, 2, 3], \"bar\": \"baz\"}"'
        expected = {"foo": [1, 2, 3], "bar": "baz"}
        out_dict = common.from_escaped_string(content)
        self.assertDictEqual(out_dict, expected)

    def test_from_escaped_string_raise_valueerror(self):
        # note the missing doublequotes in literal
        content = r'{\"foo\": [1, 2, 3], \"bar\": \"baz\"}'
        with self.assertRaises(ValueError):
            _ = common.from_escaped_string(content)

    def test_read_escaped_string_txt(self):
        content = r'"{\"foo\": [1, 2, 3], \"bar\": \"baz\"}"'
        expected = {"foo": [1, 2, 3], "bar": "baz"}
        filepath = "/tmp/test.txt"
        mo = mock_open(read_data=content)
        with patch('builtins.open', mo):
            read = common.read_escaped_string_txt(filepath)
            self.assertEqual(read, expected)

    def test_write_escaped_string_txt(self):
        content = {"foo": [1, 2, 3], "bar": "baz"}
        filepath = "/tmp/test.txt"
        mo = mock_open(read_data=common.to_escaped_string(content))
        with patch('builtins.open', mo):
            common.write_escaped_string_txt(content, filepath)
            read = common.read_escaped_string_txt(filepath)
            self.assertEqual(content, read)

    # get_file_name

    def test_get_file_name(self):
        filename = "filename.txt"
        filepart = "filename"
        result = common.get_file_name(filename)
        self.assertEqual(filepart, result)

    # get_file_type

    def test_get_file_type(self):
        filename = "filename.txt"
        filepart = ".txt"
        result = common.get_file_type(filename)
        self.assertEqual(filepart, result)

    # get_file_list

    def test_get_file_list(self):
        with patch('os.path.isfile', return_value=False):
            with patch('os.path.isdir', return_value=True):
                with patch('os.walk', return_value=[
                    ('/foo', (), ('bar.txt', 'baz.txt')),
                ]):
                    result = common.get_file_list(self.filepath, '.txt')
                    self.assertEqual(len(result), self.txt_file_count)

    # fuzzy_word_match tests

    def test_fuzzy_word_match(self):
        words1 = "monty"
        words2 = "MONTY"
        result = common.fuzzy_word_match(words1, words2)
        self.assertTrue(result)

    # rng tests

    def test_rng(self):
        val1 = common.rng(32)
        val2 = common.rng(32)
        self.assertEqual(32, len(val1))
        self.assertEqual(32, len(val2))
        self.assertNotEqual(val1, val2)

    # make_uuid

    def test_make_uuid(self):
        val1 = common.make_uuid()
        val2 = common.make_uuid()
        self.assertIsNotNone(val1)
        self.assertIsNotNone(val2)
        self.assertNotEqual(val1, val2)

    def test_make_uuid_validate_format(self):
        val1 = common.make_uuid()
        UUID(val1, version=4)

    # load_environment_variables not tested intentionally due to pending changes

    # extract_text_from_element

    def test_extract_text_from_element(self):
        htmlval = """
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
           "http://www.w3.org/TR/html4/strict.dtd">
        <html>
           <head>
              <title>Ok</title>
           </head>
           <body>
              <P>Some text goes here.
           </body>
        </html>"""

        plainval = "OkSome text goes here."
        readval = common.extract_text_from_element(htmlval)
        self.assertEqual(plainval, readval)

    def test_json_validator(self):
        self.assertTrue(common.json_validator(
            '{"actors":{"actor":[{"id":"1","firstName":"Tom","lastName":"Cruise"}]}}'
        ))
        # prints error: invalid json: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
        self.assertFalse(common.json_validator(
            '{{"actor":[{"id":"1","firstName":"Tom","lastName":"Cruise"}]}}'
        ))


class TestChunking(unittest.TestCase):
    INPUT_TEXT = """It’s expensive and time-consuming to get data out –
and even when you can, it can be really challenging to refine it into a usable,
meaningful format. That’s why it’s not surprising to us that 75% of all medical
communications still remain on fax.


Through extensive research into the breadth of how health data is typically
sought after, our platform extracts health information from fragmented data
sources.

We know health data is not standardized.


Our distinctive approach is in truly understanding the meaning behind what is
being captured cross-platforms. We address the realities of data fragmentation –
both unstructured and structured formats – and invest heavily in the significance
of providing a patient narrative that can be universally accessible.

Forcing healthcare providers and administrators to dig through records and play
phone tag is dangerously inefficient and robs patients of the care they need.
We can do better.
"""
    def test_get_sentences_None_text(self):
        self.assertListEqual([], common.get_sentences(None))

    def test_get_sentences_empty_text(self):
        self.assertListEqual([], common.get_sentences(""))

    def test_get_sentences_whitespace_text(self):
        self.assertListEqual([], common.get_sentences("""
  """))

    def test_get_sentences_valid_text(self):
        expected = [((2, 20), 'Here is some text.'),
                    ((25, 70), 'Here is some "funk " that makes nltk unhappy.')]

        self.assertListEqual(expected, common.get_sentences(f"""  {expected[0][1]}




{expected[1][1]}
          """))

    def test_chunk_text_None_text(self):
        self.assertListEqual([], speech.chunk_text(None, 50))

    def test_chunk_text_empty_text(self):
        self.assertListEqual([], speech.chunk_text("", 50))

    def test_chunk_text_whitespace_text(self):
        text = """
   """

        self.assertListEqual([((0, len(text)), text)], speech.chunk_text(text, 50))

    def test_chunk_document_single_chunk(self):
        text = """Here is some minimal text.
It should all stay together."""

        self.assertListEqual([((0, len(text)), text)], speech.chunk_text(text, 50))

    def test_chunk_test_split_line_split(self):
        text = 'medicine ' * 10 + '. \n is fun' + 'medicine' * 10
        chunks = speech.chunk_text(text=text, max_word_count=12)
        print(chunks)

    def test_chunk_document_multiple_chunks(self):
        expected_chunks = [((0, 452), 'It’s expensive and time-consuming to get data out –\nand even when you can,'
                                     ' it can be really challenging to refine it into a usable,\nmeaningful format. '
                                     'That’s why it’s not surprising to us that 75% of all medical\ncommunications still'
                                     ' remain on fax.\n\n\nThrough extensive research into the breadth of how health '
                                     'data is typically\nsought after, our platform extracts health information from '
                                     'fragmented data\nsources.\n\nWe know health data is not standardized.'),
                           ((452, 942), '\n\n\nOur distinctive approach is in truly understanding the meaning behind '
                                        'what is\nbeing captured cross-platforms. We address the realities of data '
                                        'fragmentation –\nboth unstructured and structured formats – and invest heavily'
                                        ' in the significance\nof providing a patient narrative that can be universally'
                                        ' accessible.\n\nForcing healthcare providers and administrators to dig through'
                                        ' records and play\nphone tag is dangerously inefficient and robs patients of'
                                        ' the care they need.\nWe can do better.\n')]

        output = speech.chunk_text(self.INPUT_TEXT, 100)
        self.assertListEqual(output, expected_chunks)

    def test_chunk_large_chunk_size(self):
        output = speech.chunk_text(self.INPUT_TEXT, 1000)
        self.assertEqual(output[0][1], self.INPUT_TEXT)
        self.assertEqual(len(output), 1)


    def test_chunk_document_small_chunk_size(self):

        expected_chunks = [((0, 121), 'It’s expensive and time-consuming to get data out –\nand even when you can, '
                                      'it can be really challenging to refine it into'),
                           ((121, 211), ' a usable,\nmeaningful format. That’s why it’s not surprising to us that 75% '
                                        'of all medical'),
                           ((211, 368), '\ncommunications still remain on fax.\n\n\nThrough extensive research into the '
                                        'breadth of how health data is typically\nsought after, our platform extracts '
                                        'health'),
                           ((368, 529), ' information from fragmented data\nsources.\n\nWe know health data is not '
                                        'standardized.\n\n\nOur distinctive approach is in truly understanding the '
                                        'meaning behind what'),
                           ((529, 695), ' is\nbeing captured cross-platforms. We address the realities of data'
                                        ' fragmentation –\nboth unstructured and structured formats – and invest'
                                        ' heavily in the significance'),
                           ((695, 845), '\nof providing a patient narrative that can be universally accessible.\n\n'
                                        'Forcing healthcare providers and administrators to dig through records and '
                                        'play'),
                           ((845, 942), '\nphone tag is dangerously inefficient and robs patients of the care they '
                                        'need.\nWe can do better.\n')]

        output = speech.chunk_text(self.INPUT_TEXT, 25)
        self.assertListEqual(output, expected_chunks)

