from collections import deque
from typing import (
    Dict,
    Optional,
)
from unittest.case import TestCase
from unittest.mock import patch


class MockRmqBasicPublisher:
    _queues: Dict[Optional[str], deque] = {}

    def __init__(self, queue_name: Optional[str] = None, **kwargs):
        self.queue = self._queues.setdefault(queue_name, deque())

    def __str__(self):
        return f'{self.__class__.__name__}({self._queues})'

    def publish_message(self, message: str) -> None:
        self.queue.append(message)

    def clear(self):
        self._queues.clear()

    @classmethod
    def get_queue(cls, queue_name: Optional[str] = None):
        return cls._queues.get(queue_name)

    @property
    def total_messages_count(cls):
        return sum(len(q) for q in cls._queues.values())


class RmqPatchTestCase(TestCase):
    RMQ_PUBLISHER_PATCH_TARGET: str = 'text2phenotype.tasks.rmq_worker.RMQBasicPublisher'

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()  # This explicit call required for multiple inheritance

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()  # This explicit call required for multiple inheritance

    def setUp(self) -> None:
        super().setUp()
        self.fake_rmq_client = MockRmqBasicPublisher()
        rmq_published_mock = patch(self.RMQ_PUBLISHER_PATCH_TARGET,
                                   side_effect=MockRmqBasicPublisher)
        rmq_published_mock.start()
        self.addCleanup(rmq_published_mock.stop)

    def tearDown(self) -> None:
        super().tearDown()
        self.fake_rmq_client.clear()
