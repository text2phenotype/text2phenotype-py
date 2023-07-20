from http import HTTPStatus
from typing import Optional

from text2phenotype.open_api.models.process import ReprocessOptions
from text2phenotype.tests.fixtures import john_stevens
from text2phenotype.tasks.task_info import SummaryTask
from text2phenotype.tasks.task_enums import (
    TaskEnum,
    TaskOperation,
    ModelTask,
    WorkStatus,
)
from tests.ocr.fixtures.biomed_636_files import ldiazfps

from .base import PipelineTestCase


TEST_FILE_PDF = ldiazfps[0]
TEST_FILE_TXT = john_stevens.SOURCE_TXT_FILE


class TestSummaryCustom(PipelineTestCase):
    def test_summary_custom(self):
        processing_options = self.create_default_job()

        processing_options.operations.append(TaskOperation.summary_custom)
        processing_options.summary_custom = [
            SummaryTask(models=[ModelTask.drug],
                        results_filename='summary1.json'),

            SummaryTask(models=[ModelTask.smoking, ModelTask.drug],
                        results_filename='summary2.json'),

            SummaryTask(models=[ModelTask.covid_lab, ModelTask.smoking, ModelTask.drug],
                        results_filename='summary3.json')
        ]

        with open(TEST_FILE_PDF, 'rb') as f:
            resp = self.text2phenotype_api.process_document_file(f, processing_options)

        self.assertEqual(resp.status_code, HTTPStatus.OK)
        job_id = resp.json().get('job_id')

        job = self.wait_until_job_complete(job_id)
        self.assertEqual(job.status, WorkStatus.completed_success)

    def test_reprocess(self):
        processing_options = self.create_default_job()
        processing_options.operations = [TaskOperation.summary_custom]

        processing_options.summary_custom = [
            SummaryTask(models=[ModelTask.smoking],
                        results_filename='summary1.json'),

            SummaryTask(models=[ModelTask.lab],
                        results_filename='summary2.json'),
        ]

        with self.subTest('Initial "summary_custom" job'):
            with open(TEST_FILE_TXT, 'rb') as f:
                resp = self.text2phenotype_api.process_document_file(f, processing_options)

            self.assertEqual(resp.status_code, HTTPStatus.OK)
            job_id = resp.json().get('job_id')

            job = self.wait_until_job_complete(job_id)
            self.assertEqual(job.status, WorkStatus.completed_success)

        with self.subTest('Reprocess "summary_custom" job'):
            job = self.get_job_task(job.job_id)

            doc = self.get_document_task(job.document_ids[0])
            doc_summary_results = doc.task_statuses[TaskEnum.summary_custom].summary_results
            self.assertEqual(len(doc_summary_results), 2)

            summary_task = SummaryTask(models=[ModelTask.smoking, ModelTask.lab, ModelTask.drug],
                                       results_filename='summary3.json')

            reprocess_options = ReprocessOptions(summary_custom=[summary_task])

            resp = self.text2phenotype_api.reprocess_job(job.job_id, reprocess_options)
            self.assertEqual(resp.status_code, HTTPStatus.OK)

            job = self.wait_until_job_complete(job.job_id)
            self.assertEqual(job.status, WorkStatus.completed_success)

            doc = self.get_document_task(job.document_ids[0])
            doc_summary_results = doc.task_statuses[TaskEnum.summary_custom].summary_results
            self.assertEqual(len(doc_summary_results), 1)

    def test_corpus_job(self):
        process_corpus = self.create_default_corpus_job()
        process_corpus.operations = [TaskOperation.summary_custom]
        process_corpus.summary_custom = [
            SummaryTask(models=[ModelTask.smoking, ModelTask.lab],
                        results_filename='summary1.json'),

            SummaryTask(models=[ModelTask.lab, ModelTask.genetics],
                        results_filename='summary2.json'),
        ]

        resp = self.text2phenotype_api.process_document_corpus(process_corpus)
        self.assertEqual(resp.status_code, HTTPStatus.OK)

        job_id = resp.json()['job_id']
        job = self.wait_until_job_complete(job_id)

        self.assertEqual(job.status, WorkStatus.completed_success)
