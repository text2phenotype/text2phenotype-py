import json
import os
import shutil
import unittest
import uuid

from unittest.mock import patch
from typing import List, Tuple
from text2phenotype.common.log import logger
from text2phenotype.ocr import google
from text2phenotype.ocr.data_structures import OCRPageInfo
from tests.ocr.fixtures.biomed_636_files import biomed_636_samples, biomed_636_fixtures_dir

THRESHOLD_SET_TOKENS = 99 / 100
THRESHOLD_ORDER_TOKENS = 99 / 100


# ToDo: Fixtures need to be updated with new ocr processing results and/or sample sequences
@unittest.skip
class TestBiomed636(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.work_dir = os.path.join(biomed_636_fixtures_dir, uuid.uuid4().hex)
        os.mkdir(cls.work_dir)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(cls.work_dir)

    @staticmethod
    def get_pdf_expected_text(expected_file: str) -> str:
        """
        Get the text that we expect for this pdf_file
        :param expected_file:
        :return:
        """
        with open(expected_file) as fp:
            jp = json.load(fp)
        expected_pages = list()
        [expected_pages.append(OCRPageInfo.from_dict(x)) for x in jp]
        return str([x.text for x in expected_pages])

    @staticmethod
    def get_tokens_for_text(text: str) -> list:
        objects = text.split()
        return objects

    @patch('text2phenotype.ocr.google.make_pngs_from_pdf')
    def get_pdf_ocr_text(self, pdf_file: str, pngs: List[Tuple], mock_pngs) -> str:
        """
        DO OCR and get the text
        :param pdf_file: fixture file
        :param pngs: list of file paths to png files
        :param mock_pngs: the mock patch object for _ocr_make_png_files
        :return: formatted text of a document from the png's
        """
        inputs = [(pg, png) for pg, png in enumerate(pngs)]
        mock_pngs.return_value = inputs
        results = google.ocr_pdf_file(pdf_file, self.work_dir)
        return str([x.text for x in results])

    @unittest.skip
    def test_ocr_expected_actual(self):
        for pdf_file, expected_file, pngs in biomed_636_samples:
            print(f'Beginning ocr block test for {pdf_file}')
            actual = self.get_tokens_for_text(self.get_pdf_ocr_text(pdf_file, pngs))
            expected = self.get_tokens_for_text(self.get_pdf_expected_text(expected_file))
            # WEAK TEST SET OF WORDS ARE THE SAME
            #
            # Test that OCR is returning expected words
            #
            if set(expected) != set(actual):
                logger.warning('set of word tokens is different from expected')
                print([str(x) for x in actual])
                print([str(x) for x in expected])
                score = len(set(expected).intersection(set(actual))) / len(set(expected))
                self.assertGreater(score, THRESHOLD_SET_TOKENS,
                                   f'SET similarity score {score} was lower than threshold {THRESHOLD_SET_TOKENS}')
            # STRONGER TEST LIST OF WORDS IN ORDER
            #
            # Test that Text2phenotype OCR text layout is correct order
            #
            if expected != actual:
                print([str(x) for x in actual])
                print([str(x) for x in expected])
                same = list()
                index = 0
                # something like this
                for token in actual:
                    if token in expected:
                        actual.remove(token)  # "two pointers problem -- make sure same token order"
                        same.append(token)
                    else:
                        print(f'Token: {str(token)} at index: {str(index)} not in order for {pdf_file}')
                    index += 1
                score = len(same) / len(expected)

                self.assertGreater(score, THRESHOLD_ORDER_TOKENS,
                                   f'ORDER similarity score {score} was lower than threshold {THRESHOLD_ORDER_TOKENS}')
