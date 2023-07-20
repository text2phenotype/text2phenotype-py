from typing import (
    Dict,
    Iterator,
    NewType,
    Optional
)

import boto3
import time

from botocore.exceptions import ClientError
from hashlib import md5
from http import HTTPStatus

from text2phenotype.common.log import operations_logger
from text2phenotype.services.exceptions import QueueClientError
from text2phenotype.services.queue.messages import FileUploadedSQSMessage

from .base import (
    Message,
    Queue,
    QueueService
)


# Added types for typing annotations, because
# boto3 SQS.Message and SQS.Queue not available for importing
Boto3SQSQueue = NewType('Boto3SQSQueue', object)
Boto3SQSMessage = NewType('Boto3SQSMessage', object)


class SqsMessage(Message):

    MAX_VISIBILITY_TIMEOUT = 43200  # 12 hours

    def __init__(self,
                 queue: Queue,
                 sqs_message: Boto3SQSMessage) -> None:

        self._queue = queue
        self.sqs_message = sqs_message
        self.__existing_timeout = 30  # Default visibility timeout in SQS is 30 seconds

    def get_body(self) -> str:
        return self.sqs_message.body

    def reject(self, visibility_timeout: float=None) -> None:
        visibility_timeout = visibility_timeout or 0

        self.sqs_message.change_visibility(VisibilityTimeout=int(visibility_timeout))

    def delete(self) -> None:
        self.sqs_message.delete()

    def extend_visibility_timeout(self, extension: int):
        proposed = self.__existing_timeout + extension
        vis = proposed if proposed < self.MAX_VISIBILITY_TIMEOUT else self.MAX_VISIBILITY_TIMEOUT

        operations_logger.debug(f'Changing message visibility to {vis} seconds')
        self.sqs_message.change_visibility(VisibilityTimeout=int(vis))
        self.__existing_timeout = vis


class SqsQueue(Queue):
    def __init__(self,
                 service: QueueService,
                 sqs_queue: Boto3SQSQueue,
                 queue_name: str) -> None:

        self._service = service
        self.sqs_queue = sqs_queue
        self.name = queue_name

        self.__is_fifo = queue_name.lower().endswith('.fifo')

    def iter_messages(self) -> Iterator[SqsMessage]:
        while True:
            messages = self.sqs_queue.receive_messages(
                WaitTimeSeconds=20,
                MaxNumberOfMessages=1)

            if messages:
                yield SqsMessage(self, messages[0])

    def receive_message(self, timeout: Optional[int]=None) -> Optional[SqsMessage]:
        if timeout is None:
            for message in self.iter_messages():
                return message

        else:
            t2 = time.time() + timeout

            while True:
                wait_timeout = max(0, min(t2 - time.time(), 20))

                messages = self.sqs_queue.receive_messages(
                    WaitTimeSeconds=int(wait_timeout),
                    MaxNumberOfMessages=1)

                if messages:
                    return SqsMessage(self, messages[0])

                if time.time() >= t2:
                    break

    def send_message(self,
                     body: str,
                     fifo_group_id: Optional[str]=None,
                     delay: Optional[float]=None,
                     deduplication: bool=False,
                     headers: Optional[Dict]=None) -> bool:

        kwargs = {}

        if self.__is_fifo and fifo_group_id is not None:
            kwargs['MessageGroupId'] = fifo_group_id

        if not self.__is_fifo and delay is not None:
            kwargs['DelaySeconds'] = int(delay)

        if self.__is_fifo and deduplication:
            kwargs['MessageDeduplicationId'] = md5(body.encode('utf8')).hexdigest()

        resp = self.sqs_queue.send_message(
            MessageBody=body,
            **kwargs)

        return resp['ResponseMetadata']['HTTPStatusCode'] == HTTPStatus.OK.value

    def send_messages(self, entries: Iterator[Dict]) -> Dict:
        return self.sqs_queue.send_messages(Entries=entries)

    def purge(self) -> None:
        try:
            self.sqs_queue.purge()
        except ClientError as e:
            raise QueueClientError(e)


class SqsQueueService(QueueService):
    MESSAGE_CLASS = FileUploadedSQSMessage

    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.__resource = None

    @property
    def resource(self):
        if self.__resource is None:
            self.__resource = boto3.resource('sqs', **self.get_driver_specific_kwargs())
        return self.__resource

    def get_queue(self, name: str) -> SqsQueue:
        queue = self.resource.get_queue_by_name(QueueName=name)

        return SqsQueue(service=self,
                        sqs_queue=queue,
                        queue_name=name)

    def check_connection(self, name: str) -> bool:

        try:
            queue = self.get_queue(name)
        except Exception as err:
            connected = False
        else:
            connected = True

        return connected
