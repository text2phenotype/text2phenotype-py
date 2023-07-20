import unittest
from text2phenotype.ocr.windex import clean_text
from text2phenotype.ocr.windex import clean, spaces
from text2phenotype.ocr.windex import is_punctuation_line, is_long_token
from text2phenotype.ocr.windex import is_consecutive_char
from text2phenotype.ocr.windex import is_too_few_uniq_chars_for_len
from text2phenotype.ocr.windex import replace_non_ascii

class TestBiomed1376(unittest.TestCase):

    def test_is_long_token(self):

        # https://en.wikipedia.org/wiki/Longest_word_in_English
        self.assertFalse(is_long_token('Pseudopseudohypoparathyroidism'))

        # 31 == len
        self.assertTrue(is_long_token('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'))

    def test_is_repeat_char(self):
        self.assertFalse(is_consecutive_char('YYYY'))
        self.assertTrue(is_consecutive_char('YYYYYY'))
        self.assertTrue(is_consecutive_char('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'))

    def test_is_too_few_uniq_chars_for_len(self):
        """
        https://www.funtrivia.com/askft/Question112622.html
        """
        valid_extremes  = ['booboo', 'deeded', 'muumuu']
        valid_extremes += ['assesses', 'referrer', 'senselessness', 'defenselessness']
        valid_extremes += ['disinterestedness', 'institutionalisation']

        for token in valid_extremes:
            self.assertFalse(is_too_few_uniq_chars_for_len(token))

        invalid  = ['YYYYYYY', ':::::::', 'ነነነነነነነና', '...בבבבבבב', ':::::::::', '..........................!!.ir']
        invalid += ['WWYWWWWWWWWWW']

        for token in invalid:
            self.assertTrue(is_too_few_uniq_chars_for_len(token))

    def test_is_punctuation_line(self):

        self.assertTrue(is_punctuation_line(':::::::'))

    def test_replace_non_ascii(self):
        actual = 'áuwa wakiweka**'
        expect = ' uwa wakiweka**'

        self.assertEqual(replace_non_ascii(actual), expect)

        actual = "ننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننننيننلننينيني"
        expect = spaces(len(actual))

        self.assertEqual(replace_non_ascii(actual), expect)
