import uuid

import redis_lock
from redis import Redis
from redis.exceptions import ConnectionError
from redis.sentinel import Sentinel

from text2phenotype.common.decorators import retry
from text2phenotype.constants.environment import Environment
from text2phenotype.constants.redis import DatabaseMapping


class RedisClient:

    def __init__(self, db: int = DatabaseMapping.DOCUMENTS,
                 client_name: str = None):
        self._db = db
        self._reader = None
        self._writer = None
        self._redis_lock_id = uuid.uuid4().hex
        self.init_client(client_name=client_name)

    @retry((ConnectionError,), tries=6, backoff_factor=0.5)
    def init_client(self, client_name: str = None):
        common_settings = dict(
            decode_responses=True,
            db=self._db,
        )
        if Environment.REDIS_AUTH_REQUIRED.value:
            common_settings['password'] = Environment.REDIS_AUTH_PASSWORD.value

        if Environment.REDIS_HA_MODE.value:
            sentinels = [(Environment.REDIS_HOST.value, Environment.REDIS_HA_SENTINEL_PORT.value)]
            socket_timeout = Environment.REDIS_SOCKET_TIMEOUT.value
            sentinel = Sentinel(sentinels, socket_timeout=socket_timeout, **common_settings)

            self._reader = sentinel.slave_for(Environment.REDIS_HA_MASTER_NAME.value, socket_timeout=socket_timeout)
            self._writer = sentinel.master_for(Environment.REDIS_HA_MASTER_NAME.value, socket_timeout=socket_timeout)
        else:
            self._reader = self._writer = Redis(host=Environment.REDIS_HOST.value,
                                                port=Environment.REDIS_PORT.value,
                                                retry_on_timeout=True,
                                                **common_settings)

        if client_name:
            self._reader.client_setname(client_name)
            self._writer.client_setname(client_name)

    def lock(self, key: str, expire: int = None) -> redis_lock.Lock:
        expire = expire or Environment.REDIS_LOCK_EXPIRATION.value
        return redis_lock.Lock(self._writer, key, expire, id=self._redis_lock_id)

    def is_locked(self, key: str) -> bool:
        red_lock = redis_lock.Lock(self._writer, key)
        return red_lock.locked() and red_lock.get_owner_id() != self._redis_lock_id

    def set(self, key: str, val: str):
        return self._writer.set(key, val)

    def get(self, key: str) -> str:
        data = self._reader.get(key)
        if isinstance(data, bytes):
            return data.decode()
        return data

    def delete(self, key: str) -> str:
        return self._writer.delete(key)
