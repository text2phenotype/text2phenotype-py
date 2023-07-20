import tempfile
import unittest
import uuid

from pathlib import Path

from text2phenotype.tasks.rmq_worker import WorkerHealthcheckFile


class TestWorkerHealthcheckFile(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_file_path = Path(tempfile.gettempdir(), f'text2phenotype-test-{uuid.uuid4().hex}.tmp')

    def tearDown(self):
        if self.tmp_file_path.is_file():
            self.tmp_file_path.unlink()

    def is_file_exists(self):
        return self.tmp_file_path.is_file()

    def test_context_manager(self):
        self.assertFalse(self.is_file_exists())

        with WorkerHealthcheckFile(self.tmp_file_path):
            self.assertTrue(self.is_file_exists())

            # Emulate simultanious usage in an other thread
            with WorkerHealthcheckFile(self.tmp_file_path):
                self.assertTrue(self.is_file_exists())

            self.assertTrue(self.is_file_exists())

        self.assertFalse(self.is_file_exists())
