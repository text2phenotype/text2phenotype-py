import pika

from hashlib import md5
from typing import (
    Dict,
    Iterator,
    List,
    NewType,
    Optional,
)
from pika.adapters.blocking_connection import BlockingChannel

from text2phenotype.common.log import operations_logger
from text2phenotype.services.exceptions import QueueClientError
from text2phenotype.constants.environment import Environment

from .base import (
    Message,
    Queue,
    QueueService,
)

_RmqQueueType = NewType('RmqQueue', object)


class RmqMessage(Message):
    def __init__(self,
                 queue: _RmqQueueType,
                 method: pika.spec.Basic.Deliver,
                 properties: object,
                 body: str) -> None:
        self._queue = queue
        self.method = method
        self.properties = properties
        self._body = body.decode('utf8')

        self.max_receive_count = self.queue.service.options.get('max_receive_count', 0)

    @property
    def channel(self):
        return self.queue.channel

    def get_body(self) -> str:
        return self._body

    def delete(self) -> None:
        self.channel.basic_ack(delivery_tag=self.method.delivery_tag)

    def reject(self, visibility_timeout: float = None) -> None:
        headers = self.properties.headers
        headers.setdefault('x-receive-count', 0)
        headers['x-receive-count'] += 1

        if headers['x-receive-count'] < self.max_receive_count:
            self.delete()
            self.queue.send_message(
                body=self.body,
                delay=visibility_timeout,
                headers=headers)
            return

        self.channel.basic_reject(
            self.method.delivery_tag,
            requeue=False)

    def extend_visibility_timeout(self, extension: int):
        # RabbitMQ doesn't have a concept of timeouts, so no need to do this
        pass


class RmqQueue(Queue):

    def __init__(self,
                 service: QueueService,
                 rmq_channel: BlockingChannel,
                 queue_name: str):

        self._service = service
        self.channel = rmq_channel
        self.name = queue_name

        self.default_exchange = self.service.options.get('default_exchange', '')

    def iter_messages(self) -> Iterator[RmqMessage]:
        self.channel.cancel()

        for method, properties, body in self.channel.consume(queue=self.name, inactivity_timeout=30):
            if not method:
                continue

            yield RmqMessage(self, method, properties, body)

    def receive_message(self, timeout: Optional[int] = None) -> RmqMessage:
        self.channel.cancel()

        if timeout is None:
            for message in self.iter_messages():
                return message

        for method, properties, body in self.channel.consume(
                queue=self.name,
                inactivity_timeout=timeout):

            if method:
                return RmqMessage(self, method, properties, body)

            break

    def send_message(self,
                     body: str,
                     fifo_group_id: Optional[str] = None,
                     delay: Optional[float] = None,
                     deduplication: bool = False,
                     headers: Optional[Dict] = None) -> bool:

        headers = headers or {}

        if delay:
            headers['x-delay'] = int(delay * 1000)  # sec to ms

        if deduplication:
            headers['x-deduplication-header'] = md5(body.encode('utf8')).hexdigest()

        try:
            result = self.channel.basic_publish(
                exchange=self.default_exchange,
                routing_key=self.name,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    headers=headers
                )
            )
        except pika.connection.exceptions.ConnectionClosed:
            self.service.get_connection()
            self.channel = self.service.get_channel()

            result = self.channel.basic_publish(
                exchange=self.default_exchange,
                routing_key=self.name,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    headers=headers
                )
            )

        return result

    def send_messages(self, entries: List[Dict]) -> Dict:
        response = {
            'Successful': [],
            'Failed': []
        }

        for entry in entries:
            res = self.send_message(body=entry['MessageBody'])
            if res:
                response['Successful'].append({'Id': entry['Id']})
            else:
                response['Failed'].append({'Id': entry['Id']})

        return response

    def purge(self) -> None:
        try:
            self.channel.queue_purge(queue=self.name)
        except pika.connection.exceptions.ConnectionClosed:
            self.service.get_connection()
            self.channel = self.service.get_channel()
            self.channel.queue_purge(queue=self.name)
        except Exception as e:
            raise QueueClientError(e)

    def delete(self) -> None:
        self.channel.queue_delete(queue=self.name)


class RmqQueueService(QueueService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connection = None
        self._channel = None

    def get_connection(self) -> pika.BlockingConnection:
        if self._connection is None or self._connection.is_closed:
            self.connect()

        return self._connection

    def connect(self) -> None:
        params = self.get_driver_specific_kwargs()
        username = params.pop('username', None)
        password = params.pop('password', None)
        if username and password:
            params['credentials'] = pika.PlainCredentials(username, password)

        conn_params = pika.ConnectionParameters(**params,
                                                heartbeat=Environment.RMQ_HEARTBEAT.value,
                                                blocked_connection_timeout=Environment.RMQ_HEARTBEAT.value)
        self._connection = pika.BlockingConnection(conn_params)
        operations_logger.debug(f'Start connection with RMQ using params={params}')

    def get_channel(self) -> BlockingChannel:
        if self._channel is None or self._channel.is_closed:
            self._channel = self.get_connection().channel()
            self._channel.basic_qos(prefetch_count=1)
        return self._channel

    def get_queue(self, name: str) -> RmqQueue:
        return RmqQueue(service=self,
                        rmq_channel=self.get_channel(),
                        queue_name=name)

    def check_connection(self, name: str) -> bool:
        try:
            self.get_queue(name)
        except Exception:
            operations_logger.exception(f'Connection is failed', exc_info=True)
            connected = False
        else:
            connected = True

        return connected
