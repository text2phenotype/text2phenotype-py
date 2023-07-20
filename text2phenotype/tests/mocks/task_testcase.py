from unittest.mock import patch

from . import (
    RedisPatchTestCase,
    RmqPatchTestCase,
    StoragePatchTestCase,
)
from ...tasks.rmq_worker import WorkTaskMethodsMixin


class TaskTestCase(RedisPatchTestCase, StoragePatchTestCase, RmqPatchTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.worker = None
        self.refresh_work_task_patcher = None

    def tearDown(self) -> None:
        super().tearDown()
        self.set_initial_work_task(None)
        if self.worker:
            self.worker._clear_threading_local_data()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    @property
    def worker_private_local(self):
        return self.worker._local_data  # Access to private attribute

    def set_initial_work_task(self, work_task, patch_path=None):
        if self.refresh_work_task_patcher:
            self.refresh_work_task_patcher.stop()
            self.refresh_work_task_patcher = None

        if self.worker:
            self.worker_private_local.work_task = work_task

        if work_task:
            self.refresh_work_task_patcher = patch.object(WorkTaskMethodsMixin, 'refresh_work_task')
            self.refresh_work_task_patcher.start()
