import unittest
import uuid

from text2phenotype.tasks.job_task import (
    JobDocumentInfo,
    JobTask,
)
from text2phenotype.tasks.task_enums import WorkStatus


class TestJobTask(unittest.TestCase):

    def setUp(self) -> None:
        self.job_task = JobTask()

    def test_job_task_processing_status(self):
        self.job_task.document_info[uuid.uuid4().hex] = JobDocumentInfo(status=WorkStatus.processing)
        self.job_task.document_info[uuid.uuid4().hex] = JobDocumentInfo(status=WorkStatus.completed_failure)
        self.job_task.document_info[uuid.uuid4().hex] = JobDocumentInfo(status=WorkStatus.not_started)
        self.job_task.document_info[uuid.uuid4().hex] = JobDocumentInfo(status=WorkStatus.completed_success)
        self.assertEqual(self.job_task.status, WorkStatus.processing)

    def test_job_task_failed_status(self):
        self.job_task.document_info[uuid.uuid4().hex] = JobDocumentInfo(status=WorkStatus.completed_success)
        self.job_task.document_info[uuid.uuid4().hex] = JobDocumentInfo(status=WorkStatus.completed_failure)
        self.assertEqual(self.job_task.status, WorkStatus.completed_failure)
