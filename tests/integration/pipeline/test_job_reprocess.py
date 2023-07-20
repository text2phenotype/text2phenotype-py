from http import HTTPStatus
from typing import Set

from text2phenotype.open_api.models.process import ReprocessOptions
from text2phenotype.tasks.job_task import JobTask
from text2phenotype.tasks.task_enums import (
    TaskEnum,
    WorkStatus,
)

from text2phenotype.tests.fixtures import john_stevens

from .base import PipelineTestCase


class TestJobReprocess(PipelineTestCase):
    REPROCESS_OPTIONS: ReprocessOptions = ReprocessOptions(
        force_all_documents=True,
        tasks=[TaskEnum.clinical_summary],
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create initial job which will be reprocessed
        with open(john_stevens.SOURCE_TXT_FILE, 'rb') as f:
            resp = cls.text2phenotype_api.process_document_file(f, cls.create_default_job())
            assert resp.ok

        cls.job_id = resp.json().get('job_id')
        cls.orig_job = cls.wait_until_job_complete(cls.job_id)
        cls.orig_doc = cls.get_document_task(cls.orig_job.document_ids[0])

        assert cls.orig_job.status == WorkStatus.completed_success
        assert cls.orig_job.reprocess_options is None
        assert set(cls.orig_job.document_info.keys()) == {cls.orig_doc.document_id}

    def setUp(self) -> None:
        super().setUp()
        self.orig_job = self.get_job_task(self.job_id)
        self.orig_doc = self.get_document_task(self.orig_doc.document_id)

    def get_updated_tasks_set(self, job_task: JobTask) -> Set[TaskEnum]:
        doc_task = self.get_document_task(job_task.document_ids[0])
        updated_tasks = set()

        for task in doc_task.task_statuses:
            task_completed_at = doc_task.task_statuses[task].completed_at
            orig_completed_at = self.orig_doc.task_statuses[task].completed_at

            if task_completed_at and orig_completed_at and task_completed_at > orig_completed_at:
                updated_tasks.add(task)

        return updated_tasks

    def test_reprocess_default_options(self):
        options = ReprocessOptions()

        resp = self.text2phenotype_api.reprocess_job(self.job_id, options)
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.json().get('job_id'), self.job_id)

        job = self.wait_until_job_complete(self.job_id)
        self.assertNotEqual(job.reprocess_options, self.orig_job.reprocess_options)

        expected_updated = set()  # Nothing should be updated
        self.assertEqual(self.get_updated_tasks_set(job), expected_updated)

    def test_reprocess_summary(self):
        options = self.REPROCESS_OPTIONS.copy(deep=True)
        options.tasks = [TaskEnum.clinical_summary]

        resp = self.text2phenotype_api.reprocess_job(self.job_id, options)
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.json().get('job_id'), self.job_id)

        job = self.wait_until_job_complete(self.job_id)
        self.assertEqual(job.status, WorkStatus.completed_success)
        self.assertGreater(job.completed_at, self.orig_job.completed_at)
        self.assertTrue(job.reprocess_options)
        self.assertSetEqual(set(job.document_ids), set(self.orig_job.document_ids))

        expected_updated = {TaskEnum.clinical_summary, TaskEnum.discharge}
        self.assertEqual(self.get_updated_tasks_set(job), expected_updated)

    def test_reprocess_chunk_task(self):
        options = self.REPROCESS_OPTIONS.copy(deep=True)
        options.tasks = [TaskEnum.lab]

        resp = self.text2phenotype_api.reprocess_job(self.job_id, options)
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.json().get('job_id'), self.job_id)

        job = self.wait_until_job_complete(self.job_id)
        self.assertEqual(job.status, WorkStatus.completed_success)

        expected_updated = {TaskEnum.disassemble, TaskEnum.lab, TaskEnum.reassemble,
                            TaskEnum.clinical_summary, TaskEnum.discharge}
        self.assertEqual(self.get_updated_tasks_set(job), expected_updated)

    def test_reprocess_active_job(self):
        options = self.REPROCESS_OPTIONS.copy()
        options.tasks = [TaskEnum.lab]

        # Call reprocess_job to start the processing
        resp = self.text2phenotype_api.reprocess_job(self.job_id, options)
        self.assertEqual(resp.status_code, HTTPStatus.OK)

        # Try to call reprocess again -> expecting BAD_REQUEST error
        resp = self.text2phenotype_api.reprocess_job(self.job_id, self.REPROCESS_OPTIONS)
        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)

        self.wait_until_job_complete(self.job_id)
