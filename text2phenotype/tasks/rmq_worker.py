import concurrent.futures
import functools
import json
import os
import signal
import stat
import sys
import threading
import time
from abc import (
    ABC,
    abstractmethod,
)
from collections import Counter
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path
from typing import (
    Dict,
    List,
    Optional,
    Union,
)

import pika
import psutil
from pydantic import ValidationError

from text2phenotype import tasks
from text2phenotype.common.log import operations_logger
from text2phenotype.common.log_formatters import (
    OperationsFormatter,
    WorkerFormatter,
)
from text2phenotype.common.version_info import (
    get_version_info,
    VersionInfo,
)
from text2phenotype.constants.docker import MDL_SIGTERM
from text2phenotype.constants.environment import Environment
from text2phenotype.services.queue.drivers.rmq_updated import RMQBasicPublisher
from text2phenotype.services.storage import get_storage_service
from text2phenotype.services.storage.drivers import StorageService
from text2phenotype.tasks.mixins import (
    RedisMethodsMixin,
    ThreadingLocalDataMixin,
    WorkTaskMethodsMixin,
)
from text2phenotype.tasks.task_enums import (
    TaskEnum,
    TaskStatus,
    WorkType,
)
from text2phenotype.tasks.task_info import TaskInfo
from text2phenotype.tasks.task_message import TaskMessage
from text2phenotype.tasks.tasks_constants import TasksConstants
from text2phenotype.tasks.work_tasks import DocumentTask


def redis_logger(func):
    @functools.wraps(func)
    def wrapper(worker: RMQConsumerWorker, deliver: pika.spec.Basic.Deliver, message_body: str, **kwargs):
        message = TaskMessage.construct(**json.loads(message_body))
        doc_id_args = message.redis_key.split('_')
        document_id = doc_id_args[0]
        chunk_number = doc_id_args[1] if len(doc_id_args) > 1 else None

        worker_formatter = WorkerFormatter(
            worker_name=worker.__class__.__name__,
            document_id=document_id,
            chunk_number=chunk_number,
        )
        if worker.QUEUE_NAME == Environment.BULK_INTAKE_QUEUE.value:
            worker_formatter.document_id = None
            worker_formatter.job_id = document_id

        # Set formatters
        formatter_map = {}
        for handler in operations_logger.logger.handlers:
            formatter_map[handler] = handler.formatter
            if isinstance(handler.formatter, OperationsFormatter):
                handler.setFormatter(worker_formatter)
        try:
            result = func(worker, deliver, message_body, **kwargs)
        finally:
            # Reset formatters
            for handler in operations_logger.logger.handlers:
                handler.setFormatter(formatter_map[handler])
        return result

    return wrapper


class WorkerHealthcheckFile:
    FILE_MODE: int = 0o644

    __counter: Counter = Counter()
    __lock: threading.Lock = threading.Lock()

    def __init__(self, filepath: Optional[str] = None):
        filepath = filepath or Environment.WORKER_HEALTHCHECK_FILE.value
        self.__path = Path(filepath)

    @property
    def filepath(self) -> str:
        return str(self.__path.absolute())

    def touch(self) -> None:
        self.__path.touch(mode=self.FILE_MODE, exist_ok=True)

    def exists(self) -> bool:
        return Path(self.filepath).is_file()

    def age_max(self) -> int:
        return Environment.WORKER_HEALTHCHECK_MAX_AGE.value

    def age_in_seconds(self) -> int:
        return round(time.time() - os.stat(self.filepath)[stat.ST_MTIME])

    def is_expired(self) -> bool:
        return self.age_in_seconds() > self.age_max()

    @property
    def __count(self) -> int:
        return self.__counter[self.filepath]

    @__count.setter
    def __count(self, value: int) -> None:
        if value < 0:
            value = 0
        self.__counter[self.filepath] = value

    def __enter__(self) -> 'WorkerHealthcheckFile':
        with self.__lock:
            self.touch()
            self.__count += 1
            return self

    def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
        with self.__lock:
            self.__count -= 1

            if self.__count > 0:
                self.touch()
            else:
                try:
                    self.__path.unlink()
                except FileNotFoundError:
                    pass

    def __repr__(self) -> str:
        return f"""{self.__class__.__name__}('{self.filepath}')"""


class MemoryWatcher(threading.Thread):
    def __init__(self, memory_limit: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__timeout = 0.5  # sec
        self.daemon = True
        self.memory_limit = memory_limit  # bytes
        self.process = psutil.Process()
        self.start()

    def run(self) -> None:
        operations_logger.info(f'MemoryWatcher is started. Memory limit is {self.memory_limit} bytes')
        while True:
            time.sleep(self.__timeout)
            rss = self.process.memory_info().rss  # bytes
            memory_percentage = int(rss / self.memory_limit * 100)
            if memory_percentage > 95:
                operations_logger.error(f'The memory usage limit is exceeded. '
                                        f'Percentage = {memory_percentage}%, '
                                        f'Limit = {self.memory_limit} bytes, '
                                        f'Used = {rss} bytes')
                operations_logger.critical('Emergency shutdown')
                self.process.send_signal(MDL_SIGTERM)  # The current process should be terminated after that
                break
        operations_logger.info('MemoryWatcher is stopped')


class RMQConsumerWorker(RedisMethodsMixin, ThreadingLocalDataMixin, ABC):
    """
    This is the Text2phenotype base class for an asynchronous RMQ Consumer.
    Inspired by (mostly copied from):
    https://github.com/pika/pika/blob/master/examples/asynchronous_consumer_example.py
    """
    QUEUE_NAME: str = None
    NAME: str = None
    ROOT_PATH: str = None

    def __init__(self):
        if not self.NAME:
            self.NAME = self.__class__.__name__

        # State vars
        self._reconnect_delay = 0
        self._should_reconnect = False
        self._consuming = False
        self._was_consuming = False
        self._closing = False

        # Connection vars
        self.__connection = None
        self._channel = None
        self._consumer_tag = None
        self._prefetch_count = 1

        # Application params
        self._exchange_name = Environment.RMQ_DEFAULT_EXCHANGE.value

        # External clients
        self._storage_client = None

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self._prefetch_count)
        self.futures: List[concurrent.futures.Future] = list()

        memory_limit = Environment.WORKER_MEMORY_LIMIT.value
        memory_watcher_enabled = Environment.MEMORY_WATCHER_ENABLED.value
        if memory_watcher_enabled and memory_limit:
            self.process_terminator = MemoryWatcher(memory_limit)
        else:
            if not memory_watcher_enabled:
                operations_logger.warning("MemoryWatcher was not started because the feature flag is disabled")
            else:
                operations_logger.warning('MemoryWatcher was not started because the memory limit is not set')

    @property
    def _connection(self):
        return self.__connection

    # Utilities for external services
    @property
    def storage_client(self) -> StorageService:
        if not self._storage_client:
            self._storage_client = get_storage_service()
        return self._storage_client

    @property
    @functools.lru_cache(None)
    def version_info(self) -> VersionInfo:
        return get_version_info(self.ROOT_PATH)

    def publish_message(self,
                        queue_name: str,
                        message: Union[str, TaskMessage],
                        client_tag: Optional[str] = None) -> None:

        if isinstance(message, TaskMessage):
            message = message.copy(deep=True)
            message.sender = self.NAME
            message_body = message.to_json()
        else:
            message_body = message

        client = RMQBasicPublisher(queue_name=queue_name, client_tag=client_tag)
        client.publish_message(message_body)

    def task_message_from_json(self, message_body: str):
        return TaskMessage.from_json(message_body)

    def process_wrapper(self,
                        message_body: str,
                        delivery: pika.spec.Basic.Deliver):

        operations_logger.info(f'Received the message from queue {self.QUEUE_NAME}. '
                               f'Thread ID {threading.get_ident()}, '
                               f'Delivery Tag {delivery.delivery_tag}, '
                               f'Message Body {message_body}')

        # In case of "concurrent.futures.ThreadPoolExecutor()" threads can be reused
        # and it's can be a reason of side-effects related to artifacts left in the
        # threading.local() storage after the previous task.
        self._clear_threading_local_data()

        self.task_message = self.task_message_from_json(message_body)
        with WorkerHealthcheckFile():
            redis_logger(self.process_message())

        try:
            version_info = json.dumps(self.version_info.to_dict())
        except Exception:
            version_info = None

        operations_logger.info(f'Finished processing the message.'
                               f'Thread ID {threading.get_ident()}, '
                               f'Delivery Tag {delivery.delivery_tag}, '
                               f'Message Body {message_body}, '
                               f'Version Info: {version_info}')

    def process_message(self):
        return self.do_work()

    @abstractmethod
    def do_work(self) -> None:
        pass

    def on_message(self,
                   ch: pika.spec.Channel,
                   deliver: pika.spec.Basic.Deliver,
                   props: pika.spec.BasicProperties,
                   body: bytes) -> concurrent.futures.Future:

        future = self.executor.submit(self.process_wrapper, body.decode(), deliver)
        setattr(future, 'deliver', deliver)
        setattr(future, 'message', body.decode())
        future.add_done_callback(self.on_process_done)

        self.futures = [f for f in self.futures if not f.done()]
        self.futures.append(future)
        return future

    def on_process_done(self, future: concurrent.futures.Future):
        """Finish processing message, nack, ack or requeue message"""
        deliver: pika.spec.Basic.Deliver = getattr(future, 'deliver')

        exc = future.exception()
        if not exc:
            # Successful case
            operations_logger.debug(f'Acking message {deliver.delivery_tag}')
            self.accept(deliver.delivery_tag)
        elif isinstance(exc, ValidationError) and not deliver.redelivered:
            operations_logger.error(f'Invalid message: {exc.json()}')
            operations_logger.debug(f'Reject and requeue message {deliver.delivery_tag}')
            self.requeue(deliver.delivery_tag)
        else:
            operations_logger.exception(f'Exception: {exc}')
            operations_logger.debug(f'Nacking message {deliver.delivery_tag}')
            self.reject(deliver.delivery_tag)

    def exit_with_grace(self, signum, frame):
        operations_logger.info(f'Exiting with grace on signal #{signum}.')
        self.stop(timeout=60)

        # Forward the caught signal to a group of sub-processes
        current_process = psutil.Process()
        for proc in current_process.children(recursive=True):
            operations_logger.info(f'Sending signal #{signum} to the sub-process PID {proc.pid}')
            proc.send_signal(signum)

        operations_logger.info('Aborting Python process with exit code = 0. Bye.')
        sys.exit(0)

    # Core functionality for RMQ Consumer
    def start(self):
        # Add exit_with_grace() handler to required system signals
        for signum in (signal.SIGINT, signal.SIGTERM, MDL_SIGTERM):
            operations_logger.debug(f'Setting up `exit_with_grace` handler for signal #{signum}')
            signal.signal(signum, self.exit_with_grace)

        operations_logger.info(f'Starting up {self.NAME}, Version = {tasks.__version__} ...')
        while True:
            self.__connection = pika.SelectConnection(
                parameters=pika.ConnectionParameters(
                    credentials=pika.PlainCredentials(Environment.RMQ_USERNAME.value,
                                                      Environment.RMQ_PASSWORD.value),
                    host=Environment.RMQ_HOST.value,
                    port=Environment.RMQ_PORT.value,
                    heartbeat=Environment.RMQ_HEARTBEAT.value,
                    client_properties={'product': f'{self.QUEUE_NAME} consumer'},
                    connection_attempts=Environment.RMQ_CONNECTION_ATTEMPTS.value,
                    retry_delay=Environment.RMQ_CONNECTION_RETRY_DELAY.value,
                ),
                on_open_callback=self.on_connection_open,
                on_open_error_callback=self.on_connection_open_error,
                on_close_callback=self.on_connection_closed,
            )
            self._connection.ioloop.start()
            self._maybe_reconnect()

    def stop(self, timeout: Optional[float] = None):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection.
        """
        operations_logger.info(f'Stopping RabbitMQ consumer..')

        if not self._closing:
            self._closing = True
            operations_logger.info('Closing connection to the RabbitMQ')

            if self._consuming and self._channel:
                operations_logger.debug('Sending a Basic.Cancel RPC command to RabbitMQ')
                self._channel.basic_cancel(
                    callback=functools.partial(self.on_cancelok, userdata=self._consumer_tag),
                    consumer_tag=self._consumer_tag,
                )
            else:
                self._connection.ioloop.stop()

        operations_logger.info(f'Waiting {timeout} seconds till current tasks are finished')
        concurrent.futures.wait(self.futures, timeout)

        operations_logger.info('Shutdown threads pool executor')
        self.executor.shutdown(wait=False)

        operations_logger.info('Stopped')

    # Callbacks
    def on_connection_open(self, _unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.
        :param pika.SelectConnection _unused_connection: The connection
        """
        operations_logger.debug('Connection opened')
        operations_logger.debug('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.
        Since the channel is now open, we'll declare the exchange to use.
        :param pika.channel.Channel channel: The channel object
        """
        operations_logger.debug('Channel opened')
        self._channel = channel
        operations_logger.debug('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)
        operations_logger.debug('Declaring exchange: %s', self._exchange_name)
        # Note: using functools.partial is not required, it is demonstrating
        # how arbitrary data can be passed to the callback when it is called
        self._channel.exchange_declare(
            exchange=self._exchange_name,
            exchange_type=Environment.RMQ_DEFAULT_EXCHANGE_TYPE.value,
            callback=functools.partial(self.on_exchange_declareok, userdata=self._exchange_name),
            passive=True,
        )

    def on_exchange_declareok(self, _unused_frame, userdata):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.
        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame
        :param str|unicode userdata: Extra user data (exchange name)
        """
        operations_logger.debug('Exchange declared: %s', userdata)
        operations_logger.debug('Declaring queue %s', self.QUEUE_NAME)
        cb = functools.partial(self.on_queue_declareok, userdata=self.QUEUE_NAME)
        self._channel.queue_declare(queue=self.QUEUE_NAME, callback=cb, passive=True)

    def on_connection_open_error(self, _unused_connection, err):
        """This method is called by pika if the connection to RabbitMQ
        can't be established.
        :param pika.SelectConnection _unused_connection: The connection
        :param Exception err: The error
        """
        operations_logger.error('Connection open failed: %s', err)
        self._should_reconnect = True
        self.stop()

    def on_connection_closed(self, *args):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.
        :param pika.connection.Connection connection: The closed connection obj
        :param Exception reason: exception representing reason for loss of
            connection.
        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            operations_logger.warning(f'Connection closed, reconnect necessary: {args}')
            self._should_reconnect = True
            self.stop()

    def on_channel_closed(self, *args):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.
        :param pika.channel.Channel: The closed channel
        :param Exception reason: why the channel was closed
        """
        operations_logger.warning(f'Channel was closed {args}')
        self._consuming = False
        if not self._connection.is_closing or not self._connection.is_closed:
            operations_logger.info('Closing connection')
            self._connection.close()
        operations_logger.info('Connection is closed')

    def on_queue_declareok(self, _unused_frame, userdata):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.
        :param pika.frame.Method _unused_frame: The Queue.DeclareOk frame
        :param str|unicode userdata: Extra user data (queue name)
        """
        queue_name = userdata
        operations_logger.debug(f'Binding {self._exchange_name} to {queue_name} with {self.QUEUE_NAME}')
        self._channel.queue_bind(
            callback=self.on_bindok,
            queue=queue_name,
            exchange=self._exchange_name,
            routing_key=self.QUEUE_NAME,
        )

    def on_bindok(self, *args, **kwargs):
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will set the prefetch count for the channel.
        :param pika.frame.Method _unused_frame: The Queue.BindOk response frame
        :param str|unicode userdata: Extra user data (queue name)
        """
        operations_logger.debug('Queue bound')
        self._channel.basic_qos(
            prefetch_count=self._prefetch_count,
            callback=self.on_basic_qos_ok,
        )

    def on_basic_qos_ok(self, _unused_frame):
        """Invoked by pika when the Basic.QoS method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.
        :param pika.frame.Method _unused_frame: The Basic.QosOk response frame
        """
        operations_logger.debug('QOS set to: %d', self._prefetch_count)
        operations_logger.debug('Issuing consumer related RPC commands')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)
        self._consumer_tag = self._channel.basic_consume(self.QUEUE_NAME, self.on_message)
        self._was_consuming = True
        self._consuming = True

    def reject(self, delivery_tag: int):
        """Add callback for reject message"""
        self._connection.ioloop.add_callback_threadsafe(
            functools.partial(self._channel.basic_reject, delivery_tag, requeue=False)
        )

    def requeue(self, delivery_tag: int):
        """Add callback for return message to the queue"""
        self._connection.ioloop.add_callback_threadsafe(
            functools.partial(self._channel.basic_reject, delivery_tag, requeue=True)
        )

    def accept(self, delivery_tag: int):
        """Add callback for accept message"""
        self._connection.ioloop.add_callback_threadsafe(
            functools.partial(self._channel.basic_ack, delivery_tag)
        )

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer receiving messages.
        :param pika.frame.Method method_frame: The Basic.Cancel frame
        """
        operations_logger.debug('Consumer was cancelled remotely, shutting down: %r', method_frame)
        if self._channel:
            self._channel.close()

    def on_cancelok(self, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.
        :param pika.frame.Method _unused_frame: The Basic.CancelOk frame
        :param str|unicode userdata: Extra user data (consumer tag)
        """
        self._consuming = False
        operations_logger.debug('RabbitMQ acknowledged the cancellation of the consumer: %s', userdata)
        operations_logger.debug('Closing the channel')
        self._channel.close()

    # Non-public methods
    def _dt_now_utc(self):
        return datetime.now(timezone.utc)

    def _get_reconnect_delay(self):
        if self._was_consuming:
            self._reconnect_delay = 0
        else:
            self._reconnect_delay += 1
        if self._reconnect_delay > 30:
            self._reconnect_delay = 30
        return self._reconnect_delay

    def _maybe_reconnect(self):
        if self._should_reconnect:
            self.stop()
            reconnect_delay = self._get_reconnect_delay()
            operations_logger.info('Reconnecting after %d seconds', reconnect_delay)
            time.sleep(reconnect_delay)
            self._reset_connection_attrs()

    def _reset_connection_attrs(self):
        self.__connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._consuming = False
        self._reconnect_delay = 0
        self._should_reconnect = False
        self._was_consuming = False


class RMQConsumerTaskWorker(WorkTaskMethodsMixin, RMQConsumerWorker):
    TASK_TYPE: TaskEnum = None
    RESULTS_FILE_EXTENSION: str = None
    WORK_TYPE: WorkType = None
    NAME: str = 'RMQConsumerTaskWorker'

    @property
    def task_info(self) -> TaskInfo:
        return self.work_task.task_statuses[self.TASK_TYPE]

    @property
    def tid(self):
        return self.work_task.redis_key

    def on_process_done(self, future: concurrent.futures.Future):
        super().on_process_done(future)
        message_body: str = getattr(future, 'message')
        # If the message is successful, send it back to the sequencer
        if not future.exception():
            message = self.task_message_from_json(message_body)
            self.publish_message(Environment.SEQUENCER_QUEUE.value, message)
        else:
            operations_logger.debug('The task has failed. There is no need to send it to Sequencer.')

    def exit_with_grace(self, signum, frame):
        operations_logger.info(f'{self.NAME} worker got #{signum} signal. '
                               f'Worker is terminating gracefully..')

        for future in concurrent.futures.wait(self.futures, timeout=0).not_done:
            message_body: str = getattr(future, 'message')
            message = self.task_message_from_json(message_body)

            operations_logger.info(f'Task "{self.TASK_TYPE.value}" is still in process, '
                                   f'but it will be stopped forcibly',
                                   tid=message.redis_key)

            work_task = self.get_task(WorkType[message.work_type], message.redis_key)

            with self.task_update_manager(work_task) as wt:
                task_info = wt.task_statuses[self.TASK_TYPE]

                task_info.status = TaskStatus.failed
                task_info.error_messages.append('Forced termination of work')
                task_info.completed_at = self._dt_now_utc()

            # to send message back to sequencer
            self.publish_message(Environment.SEQUENCER_QUEUE.value, message)

        super().exit_with_grace(signum, frame)

    def publish_message(self, queue_name: str, message: Union[str, TaskMessage]) -> None:
        super().publish_message(queue_name, message,
                                client_tag=f'{self.TASK_TYPE.value} task worker')

    def init_task_result(self) -> TaskInfo:
        task_result = self.task_info
        task_result.results_file_key = None
        task_result.error_messages = []
        task_result.docker_image = self.version_info.docker_image
        return task_result

    def get_intermediate_result_filename(self, object_name) -> str:
        if self.work_task.work_type is WorkType.document:
            return os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                                self.work_task.document_id, object_name)
        else:
            return os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                                self.work_task.document_id,
                                TasksConstants.STORAGE_CHUNKS_PREFIX,
                                self.work_task.redis_key, object_name)

    # TODO: this should be a function from utils.py
    def get_results_filename(self) -> str:
        if self.work_task.work_type is WorkType.document:
            return os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                                self.work_task.document_id,
                                f'{self.work_task.document_id}.'
                                f'{self.RESULTS_FILE_EXTENSION}')
        elif self.work_task.work_type is WorkType.chunk:
            return os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                                self.work_task.document_id,
                                TasksConstants.STORAGE_CHUNKS_PREFIX,
                                self.work_task.redis_key,
                                f'{self.work_task.redis_key}.'
                                f'{self.RESULTS_FILE_EXTENSION}')

    def download_object_bytes(self, storage_key: str) -> bytes:
        """
        Download a file from storage and return its bytes

        :param storage_key: source location in the storage
        """
        operations_logger.info(f'{self.NAME} begin downloading document '
                               f'{storage_key}', tid=self.tid)
        object_bytes = self.storage_client.get_content(storage_key)
        operations_logger.debug(f'{self.TASK_TYPE.value} Worker done '
                                f'downloading object.  Bytes: {len(object_bytes)}',
                                tid=self.tid)

        return object_bytes

    def download_object_str(self, storage_key: str) -> str:
        """
        Download a text file from storage and return its text

        :param storage_key: source location in the storage
        """
        object_bytes = self.download_object_bytes(storage_key)
        return object_bytes.decode('utf-8')

    def upload_results(self, results: bytes or str):
        if isinstance(results, bytes):
            data = results
        else:
            data = results.encode('utf-8')

        file_key = self.get_results_filename()
        self.storage_client.container.write_bytes(data=data,
                                                  file_name=file_key,
                                                  tid=self.tid)

        return file_key

    def upload_results_file(self, local_path_to_results):
        file_key = self.get_results_filename()
        operations_logger.info(f'uploading {local_path_to_results}  to {file_key}')
        self.storage_client.container.write_file(
            file_path=local_path_to_results,
            dest_dir=os.path.dirname(file_key),
            file_name=os.path.basename(file_key),
            tid=None
        )
        return file_key

    def upload_intermediate_result(self, content: bytes, object_name: str):
        file_key = self.get_intermediate_result_filename(object_name)
        self.storage_client.container.write_bytes(data=content,
                                                  file_name=file_key,
                                                  tid=self.tid)

        return file_key

    def get_json_results_from_storage(self, source_task: TaskEnum) -> List or Dict:
        source_result = self.work_task.task_statuses.get(source_task)
        if not source_result:
            raise ValueError(f'{source_task.value} task does not exist!')
        result_json = self.download_object_str(source_result.results_file_key)
        result_data = json.loads(result_json, strict=False) if result_json else None

        return result_data

    def process_message(self):
        # Check work type of current task
        if self.task_message.work_type is not self.WORK_TYPE:
            raise Exception(f'Received message {self.task_message} is not compatible '
                            f'with {self.WORK_TYPE.value} task worker!')

        self.init_work_task(self.task_message)

        # Perform all required checks
        if not self.__is_it_necessary_to_perform_work_task():
            return

        # Set Task "started_at" timestamp and increment attempts
        with self.task_update_manager():
            self.task_info.started_at = self._dt_now_utc()
            self.task_info.completed_at = None
            self.task_info.status = TaskStatus.started
            self.task_info.attempts += 1

        operations_logger.info(f'TaskWorker ({self.TASK_TYPE.value}) '
                               f'starting work on new task for '
                               f'{self.work_task.work_type.value} = '
                               f'{self.work_task.redis_key}, '
                               f'attempt # {self.task_info.attempts}',
                               tid=self.tid)
        try:
            task_result = self.do_work()
        except Exception as err:
            operations_logger.exception(f'An exception occurred in the '
                                        f'TaskWorker ({self.TASK_TYPE.value})',
                                        exc_info=True,
                                        tid=self.tid)

            # get most up-to-date version before saving the update
            with self.task_update_manager():
                self.task_info.status = TaskStatus.failed
                self.task_info.error_messages.append(repr(err))
                self.task_info.completed_at = self._dt_now_utc()
        else:
            self.mark_task_as_completed(task_result)
            self.update_task_result(task_result)

    def mark_task_as_completed(self, task_result):
        task_result.completed_at = self._dt_now_utc()  # Set Task "completed_at" timestamp

        if not task_result.complete:
            task_result.status = TaskStatus.completed_success

        operations_logger.info(f'TaskWorker ({self.TASK_TYPE.value}) '
                               f'task completed for '
                               f'{self.work_task.work_type.value} = '
                               f'{self.work_task.redis_key}. Task status '
                               f'= {task_result.status.value}',
                               tid=self.tid)

    def update_task_result(self, task_result):
        # get most up-to-date version before saving the update
        with self.task_update_manager():
            self.work_task.task_statuses[self.TASK_TYPE] = task_result

    def __is_it_necessary_to_perform_work_task(self) -> bool:
        """Perform all checks to ensure that current task is ready to be processed"""

        message = self.task_message

        task_details_message = f'Task "{self.TASK_TYPE.value}" for ' \
                               f'{message.work_type.value} = {message.redis_key}'

        # Ensure that we find the work_task metadata in the Redis
        if not self.work_task:
            operations_logger.error(f'{task_details_message} can\'t be initialized properly. '
                                    f'Sending back to Sequencer')
            return False

        task_details_message += f' (Job: {self.work_task.job_id})'

        # Check if requested task is already done
        if self.task_info.complete:
            operations_logger.info(f'{task_details_message} is already done. '
                                   f'(might indicate issue acking message with RMQ). '
                                   f'Sending back to Sequencer.')
            return False

        # Check if current job is canceled
        job_task = self.get_job_task(cached_properties=True)

        if job_task.user_canceled:
            with self.task_update_manager():
                self.task_info.started_at = self._dt_now_utc()
                self.task_info.completed_at = self._dt_now_utc()
                self.task_info.status = TaskStatus.canceled
                self.task_info.attempts += 1

            operations_logger.info(f'{task_details_message}. '
                                   f'Job was canceled, no need to perform this task. '
                                   f'Sending back to Sequencer.')
            return False

        # Check if current document is already failed
        if job_task.stop_documents_on_failure:
            doc_task = self.get_document_task(cached_properties=True)
        else:
            # No need to retrieve document task from the Redis
            # if "stop_documents_on_failure" feature is disabled
            doc_task = None

        if job_task.stop_documents_on_failure and doc_task.failed_tasks:
            failed_task = doc_task.failed_tasks[0]

            operations_logger.info(f'{task_details_message} is not required '
                                   f'because the "{failed_task}" already completed failure '
                                   f'and document won\'t be processed successfully. '
                                   f'Sending back to Sequencer.')

            with self.task_update_manager():
                self.task_info.started_at = self._dt_now_utc()
                self.task_info.completed_at = self._dt_now_utc()
                self.task_info.status = TaskStatus.canceled
                self.task_info.attempts += 1

                self.task_info.error_messages.append(
                    f'Task was marked as "{TaskStatus.canceled.value}" because of '
                    f'the current document has failed in the "{failed_task}" worker '
                    f'and won\'t be processed successfully.')
            return False

        # Check the number of attempts
        if self.task_info.attempts >= Environment.RETRY_TASK_COUNT_MAX.value:
            operations_logger.info(f'{task_details_message} has exceeded retries. '
                                   f'Sending back to Sequencer.')

            doc_task: DocumentTask = doc_task or self.get_document_task()

            with self.task_update_manager(doc_task) as doc_task:
                doc_task.failed_tasks.append(self.TASK_TYPE)

                # Save info about failed chunks for more convenient problem investigation
                if self.work_task.WORK_TYPE is WorkType.chunk:
                    chunk_id = self.work_task.redis_key
                    doc_task.failed_chunks.setdefault(chunk_id, []).append(self.TASK_TYPE)

            with self.task_update_manager():
                self.task_info.started_at = self._dt_now_utc()
                self.task_info.completed_at = self._dt_now_utc()
                self.task_info.status = TaskStatus.completed_failure
                self.task_info.attempts += 1  # Indicate that one more attempt was performed

                self.task_info.error_messages.append(
                    f'Task has exceeded retries. '
                    f'(Attempts: {self.task_info.attempts}, '
                    f'max retries: {Environment.RETRY_TASK_COUNT_MAX.value} )')
            return False

        # Now work-task looks good and ready to be processed
        return True

    @abstractmethod
    def do_work(self) -> TaskInfo:
        pass
