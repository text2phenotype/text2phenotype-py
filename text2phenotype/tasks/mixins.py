import threading
from contextlib import contextmanager
from typing import (
    Dict,
    Iterator,
    Optional,
    Type,
)

import redis
import redis_lock

from text2phenotype.redis_client.client import RedisClient
from text2phenotype.tasks.job_task import JobTask
from text2phenotype.tasks.task_enums import WorkType
from text2phenotype.tasks.task_message import TaskMessage
from text2phenotype.tasks.work_tasks import (
    BaseTask,
    ChunkTask,
    DocumentTask,
    WorkTask,
)


class RedisMethodsMixin:
    """This mixin implements methods useful for communicate with Redis"""

    _redis_clients: Dict[WorkType, RedisClient] = {}

    @classmethod
    def _cached_properties_key(cls, redis_key: str) -> str:
        return f'{redis_key}-cached-properties'

    @classmethod
    def get_redis_client(cls, work_type: WorkType) -> RedisClient:
        client = cls._redis_clients.get(work_type)

        if client is None:
            client_name = getattr(cls, 'NAME', None)
            client = RedisClient(db=work_type.redis_db,
                                 client_name=client_name)
            cls._redis_clients[work_type] = client

        return client

    @classmethod
    def get_task(cls,
                 work_type: WorkType,
                 redis_key: str,
                 cached_properties: bool = False,
                 work_task_class: Optional[Type[BaseTask]] = None) -> Optional[BaseTask]:

        client = cls.get_redis_client(work_type)
        json_str = None

        if cached_properties:
            key = cls._cached_properties_key(redis_key)
            json_str = client.get(key)

        if json_str is None:
            json_str = client.get(redis_key)

        if not json_str:
            return None

        if work_task_class:
            return work_task_class.from_json(json_str)

        return BaseTask.from_json(json_str)

    @classmethod
    def refresh_task(cls, task: BaseTask, cached_properties: bool = False) -> Optional[BaseTask]:
        return cls.get_task(task.WORK_TYPE,
                            task.redis_key,
                            cached_properties=cached_properties,
                            work_task_class=type(task))

    @classmethod
    def set_task(cls, task: BaseTask):
        client = cls.get_redis_client(task.WORK_TYPE)

        # Write entire JSON to Redis
        resp = client.set(task.redis_key, task.to_json())
        if not resp:
            raise redis.RedisError()

        # Write small subset of properties if required
        if task.CACHED_PROPERTIES:
            key = cls._cached_properties_key(task.redis_key)
            fields_set = set(task.CACHED_PROPERTIES) | set(task.DEFAULT_CACHED_PROPERTIES)
            client.set(key, task.json(include=fields_set))

    @classmethod
    def delete_task(cls, task: BaseTask):
        client = cls.get_redis_client(task.WORK_TYPE)

        # Delete cached properties if required
        if task.CACHED_PROPERTIES:
            key = cls._cached_properties_key(task.redis_key)
            client.delete(key)

        # Delete entire JSON
        return client.delete(task.redis_key)

    @classmethod
    def lock_task(cls, task: BaseTask, expire: Optional[int] = None) -> redis_lock.Lock:
        client = cls.get_redis_client(task.WORK_TYPE)
        return client.lock(task.redis_key, expire)

    @classmethod
    @contextmanager
    def task_update_manager(cls,
                            work_task: BaseTask,
                            lock_expire: Optional[int] = None) -> Iterator[BaseTask]:
        """Context manager for safe updates of Redis resources in case of concurrency.

        The context manager do the next steps:
        1. Lock the Redis resource
        2. Refresh object state from Redis and pass fresh object to the context
        3. Update the object state in the Redis when context manager is finished

        Example:
            with cls.task_update_manager(work_task) as work_task:
                # "work_task" - the latest version of work_task from Redis

                # Updates must be fast because the resource is locked
                # until the context manager is completed

                work_task.job_id = uuid4().hex
                work_task.started_at = datetime.utcnow()

            # The updated object state will be saved in the Redis on exit from context manager
        """

        with cls.lock_task(work_task, expire=lock_expire):
            # Use initial object in case of Redis does not have the key
            work_task = cls.refresh_task(work_task) or work_task
            yield work_task
            cls.set_task(work_task)


class ThreadingLocalDataMixin:
    """This mixin defining common threading.local() storage"""

    # Because of "RMQConsumerWorker" works in multi-threading mode, the apropriate data should be
    # stored in the "threading.local" object
    _local_data = threading.local()

    @property
    def task_message(self):
        return getattr(self._local_data, 'task_message', None)

    @task_message.setter
    def task_message(self, v):
        setattr(self._local_data, 'task_message', v)

    def _clear_threading_local_data(self):
        """Clear custom values from threading local.

        In case of "concurrent.futures.ThreadPoolExecutor()" threads can be reused
        and it's can be a reason of side-effects related to artifacts left in the
        threading.local() storage after the previous task.
        """
        custom_attrs = set(dir(self._local_data)) - set(dir(threading.local))
        for attr in custom_attrs:
            if hasattr(self._local_data, attr):
                delattr(self._local_data, attr)


class WorkTaskMethodsMixin(RedisMethodsMixin, ThreadingLocalDataMixin):
    """This mixin implements a set of helpful methods for manipulate the
       `self.work_task` property.
    """

    @property
    def initial_task_message(self):
        return self.task_message

    @property
    def work_task(self) -> Optional[WorkTask]:
        return getattr(self._local_data, 'work_task', None)

    def init_work_task(self, message: TaskMessage):
        self.task_message = message
        self.refresh_work_task()

    def refresh_work_task(self):
        message = self.task_message
        if message:
            self._local_data.work_task = self.get_task(message.work_type,
                                                       message.redis_key)

    def save_work_task(self):
        if self.work_task.complete and not self.work_task.completed_at:
            self.work_task.completed_at = self._dt_now_utc()
        self.set_task(self.work_task)

    def get_document_task(self, cached_properties: bool = False) -> Optional[DocumentTask]:
        if self.work_task and self.work_task.document_id:
            return self.get_task(WorkType.document,
                                 self.work_task.document_id,
                                 cached_properties=cached_properties)
        return None

    def get_job_task(self, cached_properties: bool = False) -> Optional[JobTask]:
        if self.work_task and self.work_task.job_id:
            return self.get_task(WorkType.job,
                                 self.work_task.job_id,
                                 cached_properties=cached_properties)
        return None

    def get_chunk_task(self, chunk_id: str, cached_properties: bool = False) -> Optional[ChunkTask]:
        return self.get_task(WorkType.chunk, chunk_id, cached_properties=cached_properties)

    @contextmanager
    def task_update_manager(self,
                            work_task: Optional[BaseTask] = None,
                            lock_expire: Optional[int] = None) -> Iterator[BaseTask]:
        """Implementation of "task_update_manager()" use "self.work_task" by default"""

        if work_task:
            # Reuse base implementation
            with super().task_update_manager(work_task, lock_expire) as wt:
                yield wt

        elif self.work_task:
            # Refresh and save self.work_task
            with self.lock_task(self.work_task, lock_expire):
                self.refresh_work_task()
                yield self.work_task
                self.save_work_task()

        else:
            raise Exception('The current BaseTask is not defined')
