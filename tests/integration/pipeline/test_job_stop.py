from http import HTTPStatus
from typing import Set

from requests import Response

from text2phenotype.tasks.task_enums import (
    TaskEnum,
    TaskStatus,
    WorkStatus,
)

from text2phenotype.tests.fixtures import john_stevens

from .base import PipelineTestCase


class TestJobStop(PipelineTestCase):
    def test_job_stop(self):

        # Create initial job
        with open(john_stevens.SOURCE_TXT_FILE, 'rb') as f:
            resp = self.text2phenotype_api.process_document_file(f, self.create_default_job())
            self.assertEqual(resp.status_code, HTTPStatus.OK)

        job_id = resp.json().get('job_id')

        def _assert_api_response(resp: Response, expected_status: int = HTTPStatus.OK):
            self.assertEqual(resp.status_code, expected_status)
            self.assertEqual(resp.json().get('job_id'), job_id)

        job = self.get_job_task(job_id)
        self.assertFalse(job.user_canceled)
        self.assertIsNone(job.user_canceled_info)
        self.assertEqual(job.status, WorkStatus.processing)

        resp = self.text2phenotype_api.job_status(job_id)
        _assert_api_response(resp)
        self.assertEqual(resp.json().get('status'), WorkStatus.processing.value)

        # Stop this job
        resp = self.text2phenotype_api.stop_job(job_id)
        _assert_api_response(resp)

        # Check Job manifest
        job = self.get_job_task(job_id)
        self.assertTrue(job.user_canceled)
        self.assertIsNotNone(job.user_canceled_info)
        self.assertIn(job.status, {WorkStatus.canceling, WorkStatus.canceled})

        # Check job status
        resp = self.text2phenotype_api.job_status(job_id)
        _assert_api_response(resp)
        self.assertIn(resp.json().get('status'),
                      {WorkStatus.canceling.value, WorkStatus.canceled.value})

        # Wait untils the job will be completed
        job = self.wait_until_job_complete(job_id)
        self.assertEqual(job.status, WorkStatus.canceled)

        resp = self.text2phenotype_api.job_status(job_id)
        _assert_api_response(resp)
        self.assertEqual(resp.json().get('status'), WorkStatus.canceled.value)

        def _filter_tasks(work_task, task_status: TaskStatus) -> Set[TaskEnum]:
            return set(task for task, task_info in work_task.task_statuses.items()
                       if task_info.status is task_status)

        # Check document tasks
        doc = self.get_document_task(job.document_ids[0])
        completed_tasks = _filter_tasks(doc, TaskStatus.completed_success)
        canceled_tasks = _filter_tasks(doc, TaskStatus.canceled)

        self.assertTrue(canceled_tasks)
        self.assertEqual(completed_tasks | canceled_tasks, set(doc.task_statuses))

        expected_completed = {TaskEnum.discharge}
        expected_canceled = {TaskEnum.reassemble, TaskEnum.clinical_summary}
        self.assertTrue(expected_completed <= completed_tasks)
        self.assertTrue(expected_canceled <= canceled_tasks)

        # Try to perform job/stop again
        resp = self.text2phenotype_api.stop_job(job_id)
        _assert_api_response(resp, HTTPStatus.NOT_FOUND)
