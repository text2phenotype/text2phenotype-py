import inspect
from contextlib import contextmanager
from typing import (
    Iterable,
    Set
)

import pika
from pika.exceptions import ChannelClosedByBroker
from pika.adapters.blocking_connection import BlockingChannel

from text2phenotype.constants.environment import Environment
from text2phenotype.common.log import operations_logger


class RMQBasicPublisher:
    # The set of queues which were checked and exist in the RabbitMQ
    __checked_queues: Set[str] = set()

    def __init__(self, queue_name: str, client_tag: str = None):
        if client_tag:
            client_tag = f'RMQBasicPublisher ({client_tag})'
        else:
            client_tag = 'RMQBasicPublisher'

        self._parameters = pika.ConnectionParameters(
            credentials=pika.PlainCredentials(Environment.RMQ_USERNAME.value,
                                              Environment.RMQ_PASSWORD.value),
            host=Environment.RMQ_HOST.value,
            port=Environment.RMQ_PORT.value,
            heartbeat=Environment.RMQ_HEARTBEAT.value,
            client_properties={'product': client_tag},
            connection_attempts=Environment.RMQ_CONNECTION_ATTEMPTS.value,
            retry_delay=Environment.RMQ_CONNECTION_RETRY_DELAY.value,
        )

        if not self.check_if_queue_exists(queue_name):
            raise SystemError(f"Queue '{queue_name}' is required "
                              f"but does not exist in the RabbitMQ")

        self._queue_name = queue_name

    @contextmanager
    def open_channel(self) -> Iterable[BlockingChannel]:
        """Context manager closes connection to RabbitMQ automatically"""
        with pika.BlockingConnection(self._parameters) as connection:
            yield connection.channel()

    def publish_message(self, message: str):
        frame = inspect.stack()[-1]
        operations_logger.debug(f"'publish_message' was called from "
                                f"File '{frame.filename}', line {frame.lineno}")

        operations_logger.info(f"Publishing '{message}' to queue '{self._queue_name}'")

        try:
            with self.open_channel() as channel:
                channel.basic_publish(Environment.RMQ_DEFAULT_EXCHANGE.value,
                                      self._queue_name, message,
                                      pika.BasicProperties(delivery_mode=2))

        except Exception:
            operations_logger.error(f"Failed to publish message: '{message}' "
                                    f"to the queue '{self._queue_name}'")
            raise

        else:
            operations_logger.info('Published successfully')

    def check_connection(self):
        try:
            with self.open_channel() as channel:
                return channel.is_open
        except Exception:
            return False

    def check_if_queue_exists(self, queue_name) -> bool:
        """Check that queue exists in the RabbitMQ"""
        if queue_name in self.__checked_queues:
            return True

        operations_logger.info(f"Checking queue '{queue_name}' in the RabbitMQ")

        try:
            with self.open_channel() as channel:
                channel.queue_declare(queue_name, passive=True)

        except ChannelClosedByBroker:
            operations_logger.error(f"Queue '{queue_name}' does not exist in the RabbitMQ.")
            return False

        else:
            operations_logger.info(f"Queue '{queue_name}' exists in the RabbitMQ.")
            self.__checked_queues.add(queue_name)
            return True
