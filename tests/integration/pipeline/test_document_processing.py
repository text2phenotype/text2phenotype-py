from text2phenotype.apiclients import response_json
from text2phenotype.tasks.task_enums import (
    TaskOperation,
    WorkStatus,
)

from text2phenotype.tests.fixtures import john_stevens

from .base import PipelineTestCase


class TestDocumentProcessing(PipelineTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.text2phenotype_api = response_json(cls.text2phenotype_api)

    def assert_job_completed_success(self, job_resp: dict) -> None:
        job_id = job_resp.get('job_id')
        self.assertTrue(job_id)

        job = self.get_job_task(job_id)

        # Corpus jobs may have no documents at this moment
        if not job.bulk_source_bucket:
            self.assertTrue(job.document_ids)

        job = self.wait_until_job_complete(job_id)
        self.assertEqual(job.status, WorkStatus.completed_success)

    def test_process_corpus(self):
        process_corpus = self.create_default_corpus_job()
        job_resp = self.text2phenotype_api.process_document_corpus(process_corpus)
        self.assert_job_completed_success(job_resp)

    def test_process_file_txt(self):
        filepath = john_stevens.SOURCE_TXT_FILE
        with open(filepath, 'rb') as f:
            job_resp = self.text2phenotype_api.process_document_file(f, self.create_default_job())
            self.assert_job_completed_success(job_resp)

    def test_process_file_pdf(self):
        filepath = john_stevens.SOURCE_PDF_FILE
        with open(filepath, 'rb') as f:
            job_resp = self.text2phenotype_api.process_document_file(f, self.create_default_job())
            self.assert_job_completed_success(job_resp)

    def test_process_text(self):
        with open(john_stevens.SOURCE_TXT_FILE, 'r') as f:
            text = f.read()

        job_resp = self.text2phenotype_api.process_document_text(text, self.create_default_job())
        self.assert_job_completed_success(job_resp)

    def test_app_ingest(self):
        options = self.create_default_job()
        options.operations = [TaskOperation.app_ingest]

        with open(john_stevens.SOURCE_TXT_FILE, 'r') as f:
            text = f.read()

        job_resp = self.text2phenotype_api.process_document_text(text, options)
        self.assert_job_completed_success(job_resp)
