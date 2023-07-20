from enum import Enum
from queue import Queue
from typing import Any


class QueueControlMessages(Enum):
    close_worker = 'close_worker'


class SimpleQueue(Queue):
    CLOSE_WORKER_MESSAGE = QueueControlMessages.close_worker

    def close(self):
        self.put(self.CLOSE_WORKER_MESSAGE)

    def is_close_message(self, msg: Any) -> bool:
         return msg is self.CLOSE_WORKER_MESSAGE
