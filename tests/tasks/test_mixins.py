from typing import (
    ClassVar,
    Set,
)
from uuid import uuid4

from text2phenotype.tasks.job_task import JobTask
from text2phenotype.tasks.mixins import RedisMethodsMixin
from text2phenotype.tasks.task_enums import WorkType
from text2phenotype.tasks.work_tasks import (
    DocumentInfo,
    DocumentTask,
    WorkTask,
)
from text2phenotype.tests.mocks import RedisPatchTestCase


class TestRedisMethodsMixin(RedisPatchTestCase):
    def setUp(self):
        super().setUp()

        self.job_task = JobTask(job_id=uuid4().hex)

        doc_info = DocumentInfo(document_id=uuid4().hex,
                                source='',
                                tid='')
        self.doc_task = DocumentTask(document_info=doc_info,
                                     job_id=self.job_task.job_id)

        self.job_task.add_file(f'{self.doc_task.document_id}.txt', self.doc_task.document_id)

    def test_get_task(self):
        self.fake_redis_client.set(self.doc_task.redis_key, self.doc_task.json())

        doc_task = RedisMethodsMixin.get_task(self.doc_task.WORK_TYPE, self.doc_task.redis_key)
        self.assertEqual(doc_task, self.doc_task)

    def test_set_task(self):
        RedisMethodsMixin.set_task(self.doc_task)

        json_str = self.fake_redis_client.get(self.doc_task.redis_key)
        doc_task = DocumentTask.from_json(json_str)
        self.assertEqual(doc_task, self.doc_task)

    def test_delete_task(self):
        RedisMethodsMixin.set_task(self.doc_task)
        json_str = self.fake_redis_client.get(self.doc_task.redis_key)
        self.assertIsNotNone(json_str)

        RedisMethodsMixin.delete_task(self.doc_task)
        json_str = self.fake_redis_client.get(self.doc_task.redis_key)
        self.assertIsNone(json_str)

    def test_no_cached_properties(self):
        redis_key = uuid4().hex

        # Emulate a WorkTask without CACHED_PROPERTIES
        class TestWorkTask(WorkTask):
            WORK_TYPE: ClassVar[WorkType] = WorkType.document
            CACHED_PROPERTIES: ClassVar[Set[str]] = set()

            @property
            def redis_key(self):
                return redis_key

        test_task = TestWorkTask()
        self.assertFalse(test_task.CACHED_PROPERTIES)
        cached_properties_key = RedisMethodsMixin._cached_properties_key(test_task.redis_key)

        # Check that additional "cached-properties" record won't be created
        RedisMethodsMixin.set_task(test_task)
        json_str = self.fake_redis_client.get(cached_properties_key)
        self.assertIsNone(json_str)

        json_str = self.fake_redis_client.get(redis_key)
        self.assertIsNotNone(json_str)

    def test_cached_properties(self):
        # JobTask has required cached properties
        self.assertTrue(self.job_task.CACHED_PROPERTIES)
        self.job_task.user_canceled = False

        cached_properties_key = RedisMethodsMixin._cached_properties_key(self.job_task.redis_key)

        def _check_cached_properties(cached_job):
            self.assertLess(len(cached_job.json()), len(self.job_task.json()))

            self.assertTrue(self.job_task.document_info)
            self.assertTrue(self.job_task.processed_files)

            self.assertFalse(cached_job.document_info)
            self.assertFalse(cached_job.processed_files)

            cached_data = cached_job.dict()
            original_data = self.job_task.dict()

            for key in self.job_task.CACHED_PROPERTIES:
                self.assertEqual(cached_data[key], original_data[key])

        with self.subTest('Check create cached properties'):
            json_str = self.fake_redis_client.get(cached_properties_key)
            self.assertIsNone(json_str)

            RedisMethodsMixin.set_task(self.job_task)
            json_str = self.fake_redis_client.get(cached_properties_key)
            self.assertIsNotNone(json_str)

            cached_job_task = JobTask.from_json(json_str)
            self.assertIsNotNone(cached_job_task)
            _check_cached_properties(cached_job_task)

        with self.subTest('Check update cached properties'):
            self.job_task.user_canceled = True
            RedisMethodsMixin.set_task(self.job_task)

            cached_job_task = RedisMethodsMixin.refresh_task(cached_job_task, cached_properties=True)
            _check_cached_properties(cached_job_task)

        with self.subTest('Check delete cached properties'):
            RedisMethodsMixin.delete_task(self.job_task)
            json_str = self.fake_redis_client.get(cached_properties_key)
            self.assertIsNone(json_str)

            cached_job_task = RedisMethodsMixin.refresh_task(self.job_task, cached_properties=True)
            self.assertIsNone(cached_job_task)
