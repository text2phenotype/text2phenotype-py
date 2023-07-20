import unittest

from text2phenotype.tasks.task_enums import (
    TaskEnum,
    TaskStatus,
    WorkStatus,
)
from text2phenotype.tasks.task_info import (
    AnnotationTaskInfo,
    AppIngestTaskInfo,
    DischargeTaskInfo,
)
from text2phenotype.tasks.work_tasks import WorkTask


class TestWorkTask(unittest.TestCase):
    def setUp(self) -> None:
        self.work_task_success = WorkTask(
            task_statuses={
                TaskEnum.app_ingest: AppIngestTaskInfo(status=TaskStatus.completed_success),
                TaskEnum.discharge: DischargeTaskInfo(status=TaskStatus.completed_success),
            }
        )
        self.work_task_failed = WorkTask(
            task_statuses={
                TaskEnum.app_ingest: AppIngestTaskInfo(status=TaskStatus.completed_success),
                TaskEnum.discharge: DischargeTaskInfo(status=TaskStatus.completed_failure),
            }
        )

    def test_successful(self):
        self.assertTrue(self.work_task_success.successful)
        self.assertFalse(self.work_task_failed.successful)

    def test_exclude_check_successful(self):
        self.assertTrue(self.work_task_failed.check_successful(exclude=(DischargeTaskInfo, )))
        self.assertFalse(self.work_task_failed.check_successful())

    def test_status_property(self):
        work_task = self.work_task_success.copy(deep=True)

        discharge_task = work_task.task_statuses[TaskEnum.discharge]
        annotate_task = work_task.task_statuses.setdefault(TaskEnum.annotate, AnnotationTaskInfo())

        PROCESSING_STATUSES = TaskStatus.submitted_statuses() | {TaskStatus.failed}

        with self.subTest('Check "processing" status'):
            # If at least one task in any "processing" status => WorkStatus.processing
            for status in PROCESSING_STATUSES:
                annotate_task.status = status
                self.assertEqual(work_task.status, WorkStatus.processing)

            for status in set(TaskStatus) - PROCESSING_STATUSES - {WorkStatus.not_started}:
                annotate_task.status = status
                self.assertNotEqual(work_task.status, WorkStatus.processing)

        with self.subTest('Check "canceling" status'):
            # One task "canceled" and other "processing" => WorkStatus.canceling
            discharge_task.status = TaskStatus.canceled

            for status in PROCESSING_STATUSES:
                annotate_task.status = status
                self.assertEqual(work_task.status, WorkStatus.canceling)

        with self.subTest('Check "completed_failure" status'):
            # One task was completed failure => WorkTask is completed failure
            annotate_task.status = TaskStatus.completed_failure

            for status in TaskStatus.completed_statuses():
                discharge_task.status = status
                self.assertEqual(work_task.status, WorkStatus.completed_failure)

        with self.subTest('Check min status'):
            annotate_task.status = TaskStatus.completed_success
            discharge_task.status = TaskStatus.completed_success

            for status in set(TaskStatus) - {TaskStatus.not_started}:
                annotate_task.status = status
                self.assertEqual(work_task.status, WorkStatus.from_task_status(status))

        with self.subTest('Check "not started" status'):
            # Each task is not started
            for task_info in work_task.task_statuses.values():
                task_info.status = TaskStatus.not_started
            self.assertEqual(work_task.status, WorkStatus.not_started)

            # One task "completed", other is not started
            annotate_task.status = TaskStatus.completed_success
            self.assertEqual(work_task.status, WorkStatus.processing)
