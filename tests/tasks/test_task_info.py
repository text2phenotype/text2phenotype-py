from datetime import datetime, timezone
import json
import unittest

from text2phenotype.tasks.task_info import TaskInfo, AnnotationTaskInfo
from text2phenotype.tasks.task_enums import (
    TaskEnum,
    TaskStatus,
)


class TestTaskInfo(unittest.TestCase):

    def setUp(self) -> None:
        self.datetime_now = datetime.now(timezone.utc)
        self.initial_data = {
            'status': TaskStatus.started.value,
            'results_file_key': 'example file key',
            'error_messages': ['uh oh', 'problems!'],
            'attempts': 2,
            'started_at': self.datetime_now,
            'requires_ocr': True,
            'docker_image': 'test_docker_image:latest',
        }
        self.task_result = AnnotationTaskInfo(**self.initial_data)

    def test_json_serialization(self):
        data = self.task_result.dict()
        actual = TaskInfo.create(**data)

        self.assertIsInstance(actual, AnnotationTaskInfo)

        self.assertEqual(self.task_result.TASK_TYPE, actual.task)
        self.assertEqual(self.task_result.status, actual.status)
        self.assertEqual(self.task_result.results_file_key, actual.results_file_key)
        self.assertListEqual(self.task_result.error_messages, actual.error_messages)
        self.assertEqual(self.task_result.attempts, actual.attempts)
        self.assertEqual(self.task_result.started_at, actual.started_at)
        self.assertEqual(self.task_result.completed_at, actual.completed_at)
        self.assertListEqual(self.task_result.dependencies, actual.dependencies)
        self.assertEqual(self.task_result.docker_image, actual.docker_image)

    def test_expected_dict(self):
        expected_data = {
            'started_at': self.datetime_now.isoformat(),
            'completed_at': None,
            'processing_duration': None,
            'task': TaskEnum.annotate.value,
            'results_file_key': self.task_result.results_file_key,
            'error_messages': self.task_result.error_messages,
            'model_dependencies': [],
            'dependencies': [TaskEnum.ocr.value]
        }
        self.initial_data.update(expected_data)
        self.initial_data.pop('requires_ocr')
        self.assertDictEqual(self.initial_data, json.loads(self.task_result.to_json()))

    def test_expected_customer_facing_dict(self):
        expected_data = {
            'task': TaskEnum.annotate.value,
            'status': TaskStatus.started.value,
            'results_file_key': self.initial_data['results_file_key'],
            'started_at': self.datetime_now.isoformat(),
            'completed_at': None,
        }
        self.assertDictEqual(expected_data, json.loads(self.task_result.to_customer_facing_json()))
