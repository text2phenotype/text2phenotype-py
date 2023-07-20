from abc import (
    ABC,
    abstractmethod,
)
from threading import Thread
from typing import (
    Any,
    List,
)

from .simple_queue import SimpleQueue


class AbstractWorker(Thread, ABC):
    def __init__(self, queue: SimpleQueue, tid: str):
        super().__init__()
        self.daemon = True
        self.queue = queue
        self.tid = tid
        self.errors: List[str] = []

    def is_close_message(self, msg: Any) -> bool:
        return self.queue.is_close_message(msg)

    @abstractmethod
    def run(self) -> None:
        pass


def close_worker_pool(worker_pool: List[AbstractWorker], queue: SimpleQueue) -> List[str]:
    """ Close queues, workers and return error list """
    errors = []

    # Put "CLOSE_WORKER_MESSAGE" for each worker
    for _ in worker_pool:
        queue.close()

    # Wait for all workers to finish
    for worker in worker_pool:
        errors.extend(worker.errors)
        worker.join()

    return errors
