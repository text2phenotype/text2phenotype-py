import json
import unittest

from text2phenotype.constants.environment import Environment
from text2phenotype.tasks.task_enums import (
    TaskEnum,
    TaskStatus,
    WorkType,
)
from text2phenotype.tasks.task_info import (
    AnnotationTaskInfo,
    ClinicalSummaryTaskInfo,
    VectorizeTaskInfo,
)
from text2phenotype.tasks.work_tasks import ChunkTask


class TestChunkTask(unittest.TestCase):
    DOCUMENT_ID = 'document_id'
    JOB_ID = 'job_id'
    TEXT_SPAN = [0, 459]
    CHUNK_NUM = 1
    CHUNK_SIZE = 460
    TEXT_FILE_KEY = 'text-file-key'

    TASK_STATUSES = {
        TaskEnum.annotate: AnnotationTaskInfo(),
        TaskEnum.vectorize: VectorizeTaskInfo(),
        TaskEnum.clinical_summary: ClinicalSummaryTaskInfo(),
    }
    TASK_STATUSES[TaskEnum.annotate].status = TaskStatus.failed
    TASK_STATUSES[TaskEnum.annotate].attempts = 2

    PERFORMED_TASKS = [TaskEnum.annotate, TaskEnum.annotate]

    def setUp(self) -> None:
        self.initial_data = {
            'document_id': self.DOCUMENT_ID,
            'job_id': self.JOB_ID,
            'text_span': self.TEXT_SPAN,
            'chunk_num': self.CHUNK_NUM,
            'chunk_size': self.CHUNK_SIZE,
            'text_file_key': self.TEXT_FILE_KEY,
            'task_statuses': self.TASK_STATUSES,
            'performed_tasks': self.PERFORMED_TASKS,
        }
        self.chunk_task = ChunkTask(**self.initial_data)

    def test_json_serialization(self):
        data = self.chunk_task.to_json()
        actual = ChunkTask.from_json(data)

        self.assertEqual(actual.document_id, self.DOCUMENT_ID)
        self.assertEqual(actual.job_id, self.JOB_ID)
        self.assertListEqual(actual.text_span, self.TEXT_SPAN)
        self.assertEqual(actual.chunk_num, self.CHUNK_NUM)

        self.assertListEqual(actual.performed_tasks, self.PERFORMED_TASKS)

        for real_key, real_status in self.TASK_STATUSES.items():
            self.assertIn(real_key, actual.task_statuses)
            real_dict = json.loads(real_status.to_json())
            actual_dict = json.loads(actual.task_statuses[real_key].to_json())
            self.assertDictEqual(real_dict, actual_dict)

        self.assertEqual(actual.started_at, self.chunk_task.started_at)
        self.assertIsNotNone(actual.started_at)

        self.assertEqual(actual.completed_at, self.chunk_task.completed_at)

    def test_expected_dict(self):
        expected_dict = {
            'version': Environment.TASK_WORKER_VERSION,
            'started_at': self.chunk_task.started_at.isoformat(),
            'completed_at': None,
            'processing_duration': None,
            'total_duration': None,
            'work_type': WorkType.chunk.value,
            'task_statuses': {k.value: json.loads(v.to_json()) for k, v in self.TASK_STATUSES.items()},
            'performed_tasks': [k.value for k in self.PERFORMED_TASKS],
            'model_version': None,
        }

        self.initial_data.update(expected_dict)
        self.assertDictEqual(self.initial_data, json.loads(self.chunk_task.to_json()))
