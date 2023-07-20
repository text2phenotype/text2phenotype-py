import unittest
from text2phenotype.common import xps


class TestXPS(unittest.TestCase):

    @unittest.skip("Review and refactor required")
    # test.xps not found
    def test_xps_to_text(self):
        text = xps.xps_to_text("test.xps")
        self.assertEqual("1   \nThis is just a test.", text)
