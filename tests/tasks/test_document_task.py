import json
import unittest
from hashlib import sha256

from text2phenotype.common import common
from text2phenotype.constants.environment import Environment
from text2phenotype.tasks.task_enums import (
    TaskEnum,
    TaskOperation,
    TaskStatus,
    WorkType,
)
from text2phenotype.tasks.task_info import (
    DeidTaskInfo,
    OCRTaskInfo,
    OperationInfo,
)
from text2phenotype.tasks.work_tasks import DocumentTask, WorkTask


class TestDocumentTask(unittest.TestCase):
    TASK_STATUSES = {
        TaskEnum.ocr: OCRTaskInfo(),
        TaskEnum.deid: DeidTaskInfo(requires_ocr=True),
    }
    PERFORMED_TASKS = [TaskEnum.annotate, TaskEnum.annotate]

    def setUp(self) -> None:
        self.initial_data = {
            'document_info': {
                'document_id': 'id',
                'text_file_key': 'temp/temp.txt',
                'source_file_key': 'temp/src.txt',
                'source': 'upload',
                'source_hash': sha256(b'').hexdigest(),
                'document_size': 0,
                'tid': 'tid',
            },
            'task_statuses': self.TASK_STATUSES,
            'performed_tasks': self.PERFORMED_TASKS,
            'completed_at': None,
            'operations': [TaskOperation.oncology_summary.value, TaskOperation.deid.value],
            'chunks': ['1', '2', '3'],
            'chunk_tasks': [],
        }
        self.doc_task = DocumentTask(**self.initial_data)

    def test_json_serialization(self):
        self.doc_task.task_statuses[TaskEnum.ocr].status = TaskStatus.failed
        self.doc_task.task_statuses[TaskEnum.ocr].attempts = 2

        data = self.doc_task.to_json()
        actual = DocumentTask.from_json(data)

        self.assertListEqual(actual.operations, self.doc_task.operations)
        self.assertListEqual(actual.performed_tasks, self.doc_task.performed_tasks)

        for real_key, real_status in self.doc_task.task_statuses.items():
            self.assertIn(real_key, actual.task_statuses)
            real_dict = json.loads(real_status.to_json())
            actual_dict = json.loads(actual.task_statuses[real_key].to_json())
            self.assertDictEqual(real_dict, actual_dict)

        for task in actual.performed_tasks:
            self.assertIsInstance(task, TaskEnum)

        self.assertEqual(actual.started_at, self.doc_task.started_at)
        self.assertEqual(actual.completed_at, self.doc_task.completed_at)

        for real_key, real_status in self.doc_task.operation_statuses.items():
            self.assertIn(real_key, actual.operation_statuses)
            real_dict = json.loads(real_status.json())
            actual_dict = json.loads(actual.operation_statuses[real_key].to_json())
            self.assertDictEqual(real_dict, actual_dict)

        self.assertListEqual(actual.chunks, self.doc_task.chunks)

    def test_expected_dict(self):
        expected_dict = {
            'version': Environment.TASK_WORKER_VERSION,
            'started_at': self.doc_task.started_at.isoformat(),
            'completed_at': None,
            'total_duration': None,
            'work_type': WorkType.document.value,
            'task_statuses': {k.value: json.loads(v.to_json()) for k, v in self.TASK_STATUSES.items()},
            'performed_tasks': [k.value for k in self.PERFORMED_TASKS],
            'operation_statuses': {op: OperationInfo(operation=op) for op in self.doc_task.operations},
            'job_id': None,
            'model_version': None,
            'failed_tasks': [],
            'failed_chunks': {},
            'summary_tasks': [],
        }
        self.initial_data.update(expected_dict)
        self.assertDictEqual(self.initial_data, json.loads(self.doc_task.to_json()))
