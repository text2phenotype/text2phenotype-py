import unittest

from text2phenotype.common.dates import parse_dates

class TestBiomed587(unittest.TestCase):
    def test_parse_dates(self):
        self.assert_date(' 2095-03-28', 28, 3, 2095)
        self.assert_date('Nov 2093', 1, 11, 2093)
        self.assert_date('3/27', 27, 3, 9999)
        self.assert_date('04-Jul-2018', 4, 7, 2018)
        self.assert_date(' 9/17/64', 17, 9, 1964)
        self.assert_date('1/26/1910', 26, 1, 1910)
        self.assert_date('21 Jan 2013', 21, 1, 2013)
        self.assert_date('March 14, 2018', 14, 3, 2018)
        self.assert_date('03/14/2016', 14, 3, 2016)
        self.assert_date('2/13/15', 13, 2, 2015)
        self.assert_date('24 Feb 2014', 24, 2, 2014)
        self.assert_date('2/16/1953', 16, 2, 1953)
        self.assert_date('December 2015', 1, 12, 2015)
        self.assert_date('Jan 21,2020', 21, 1, 2020)
        self.assert_date('12 FEB2020',  12, 2, 2020)
        self.assert_date('12FEB2020', 12, 2, 2020)
        self.assert_date('FEB2012', 1,  2, 2012)

    def assert_date(self, text, day, month, year):
        output = parse_dates(text)
        self.assertGreaterEqual(len(output), 1, text)
        output_date = output[0][0]
        output_day = output_date.day
        output_month = output_date.month
        output_year = output_date.year
        if year is None:
            year = 9999
        if day is None:
            day = 1
        self.assertEqual(day, output_day)
        self.assertEqual(month, output_month)
        self.assertEqual(year, output_year)
