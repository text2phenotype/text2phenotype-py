import os
import unittest

from text2phenotype.common import common
from text2phenotype.constants.environment import Environment
from text2phenotype.ccda import ccda

@unittest.skip('https://git.text2phenotype.com/data-management/nlp/text2phenotype-samples.git')
class TestCCDA_allergies(unittest.TestCase):
    """
    text2phenotype-samples is required to run these unit tests.
    """
    def test_allergies(self):

        CCDA_SAMPLES = os.path.join(Environment.TEXT2PHENOTYPE_SAMPLES_PATH.value, 'ccda', 'Partners')

        expected = '48765-2'

        for f in common.get_file_list(CCDA_SAMPLES, '.xml'):

            print(f)
            parsed = ccda.read_ccda_file(f)
            sections = [s['template']['section'] for s in parsed['section']]

            self.assertTrue(expected in sections)