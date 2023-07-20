import unittest

from text2phenotype.common.feature_data_parsing import is_digit, is_int

class TestIsDigit(unittest.TestCase):
    def test_is_digit(self):
        self.assertTrue(is_digit('1329'))
        self.assertTrue(is_digit('-4301'))
        self.assertTrue(is_digit('00'))
        self.assertFalse(is_digit(' '))
        self.assertFalse(is_digit(''))
        self.assertFalse(is_digit('.*'))
        self.assertTrue(is_digit('0.98'))
        self.assertTrue(is_digit('-.2'))
        self.assertFalse(is_digit('78aso9'))

    def test_is_int(self):
        self.assertTrue(is_int('1329'))
        self.assertFalse(is_int('-4301'))
        self.assertTrue(is_int('00'))
        self.assertFalse(is_int(' '))
        self.assertFalse(is_int(''))
        self.assertFalse(is_int('.*'))
        self.assertFalse(is_int('0.98'))
        self.assertFalse(is_int('-.2'))
        self.assertFalse(is_int('78aso9'))