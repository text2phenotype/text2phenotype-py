import os
import shutil
import uuid
from unittest import TestCase

from text2phenotype.ocr.google import google_ocr_pdf_file
from text2phenotype.tests.decorators import skip_on_docker_build

from tests.ocr.fixtures import test_pdf, OCR_FIXTURES_DIR


@skip_on_docker_build
class TestGoogleOCR(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.work_dir = os.path.join(OCR_FIXTURES_DIR, uuid.uuid4().hex)
        cls.pdf_file = test_pdf

        os.mkdir(cls.work_dir)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(cls.work_dir)

    def test_ocr_works(self):

        text, result = google_ocr_pdf_file(self.pdf_file, self.work_dir, 0)

        # check that correct number of pages were created
        self.assertEqual(len(result), 3)

        # check full text reconstruction
        full_text = ''
        for page in result:
            full_text += page.text

        for page in result:
            for coord in page.coordinates:
                self.assertEqual(full_text[
                                 coord.document_index_first:coord.document_index_last + 1],
                                 coord.text)

