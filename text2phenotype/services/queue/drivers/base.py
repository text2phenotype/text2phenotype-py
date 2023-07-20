from typing import (
    Dict,
    Iterator,
    Optional
)

from text2phenotype.services.queue.messages import FileUploadedIntakeMessage


class Message:
    def __init__(self, queue, **kwargs) -> None:
        self._queue = queue
        raise NotImplementedError()

    def get_body(self) -> str:
        raise NotImplementedError()

    @property
    def body(self) -> str:
        return self.get_body()

    @property
    def queue(self):
        return self._queue

    def delete(self) -> None:
        raise NotImplementedError()

    def reject(self) -> None:
        raise NotImplementedError()

    def extend_visibility_timeout(self, extension: int):
        raise NotImplementedError()


class Queue:
    def __init__(self, service, **kwargs) -> None:
        self._service = service
        raise NotImplementedError()

    @property
    def service(self):
        return self._service

    def send_message(self,
                     body: str,
                     fifo_group_id: Optional[str]=None,
                     delay: Optional[float]=None,
                     deduplication: bool=False,
                     headers: Optional[Dict]=None) -> bool:
        raise NotImplementedError()

    def iter_messages(self) -> Iterator[Message]:
        raise NotImplementedError()

    def receive_message(self, timeout: Optional[int]=None) -> Message:
        raise NotImplementedError()

    def purge(self) -> None:
        raise NotImplementedError()


class QueueService:
    MESSAGE_CLASS = FileUploadedIntakeMessage

    def __init__(self, config: Dict[str, str]) -> None:
        self._config = config

    @property
    def config(self) -> Dict:
        if not hasattr(self, '_config'):
            self._config = {}

        if self._config is None:
            self._config = {}

        return self._config

    @property
    def options(self) -> Dict:
        return self.config.setdefault('options', {})

    def get_driver_specific_kwargs(self) -> Dict:
        kwargs = self.config.copy()
        del kwargs['options']
        return kwargs

    def get_queue(self, name: str) -> Queue:
        raise NotImplementedError()

    def check_connection(self, name: str) -> bool:
        """
        Checks connection to storage service
        """
        raise NotImplementedError('check_connection not implemented for this driver')

    def connection_keepalive(self):
        raise NotImplementedError()