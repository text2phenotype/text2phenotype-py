import os
import unittest

from text2phenotype.common import zipcodes
from text2phenotype.constants.environment import Environment


class TestZipCodes(unittest.TestCase):

    def assertSanFrancisco(self, entry):
        """
        Assert that an extracted entry is actually in SF,CA,US
        :param entry: dictionary extracted from zip code CSV file
        """
        self.assertEqual(entry['city'], 'SAN FRANCISCO')
        self.assertEqual(entry['state'], 'CA')
        self.assertEqual(entry['country'], 'US')

    @unittest.skip("Review and refactor required")
    # AttributeError __enter__ from zipcodes
    def test_zip_codes(self):
        json_path = os.path.join(Environment.TEXT2PHENOTYPE_SAMPLES_PATH.value, 'zipcodes')

        entries = zipcodes.read_csv(json_path)

        self.assertSanFrancisco(entries['94103'])
        self.assertSanFrancisco(entries['94118'])
