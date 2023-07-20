from unittest.case import TestCase
from unittest.mock import (
    MagicMock,
    patch,
)

from fakeredis import FakeStrictRedis
from redis.sentinel import Sentinel

from text2phenotype.tasks.mixins import RedisMethodsMixin


class RedisPatchTestCase(TestCase):
    REDIS_CLIENT_PATCH_TARGET = 'text2phenotype.redis_client.client.Redis'

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.fake_redis_client = FakeStrictRedis()
        setattr(cls.fake_redis_client, 'client_setname', MagicMock())

        cls.redis_server = patch(cls.REDIS_CLIENT_PATCH_TARGET, return_value=cls.fake_redis_client)
        cls.redis_server.start()

        patch_sentinel_methods = {
            'slave_for': MagicMock(return_value=cls.fake_redis_client),
            'master_for': MagicMock(return_value=cls.fake_redis_client),
        }

        cls.redis_sentinel = patch.multiple(Sentinel, **patch_sentinel_methods)
        cls.redis_sentinel.start()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.redis_server.stop()
        cls.redis_sentinel.stop()

    def clear_fake_redis(self):
        """Clean up all Fake Redis data"""

        self.fake_redis_client.execute_command('FLUSHALL')  # Clean up Fake Redis

    def setUp(self) -> None:
        super().setUp()  # This explicit call required for multiple inheritance
        self.clear_fake_redis()
        RedisMethodsMixin._redis_clients = {}

    def tearDown(self) -> None:
        super().tearDown()  # This explicit call required for multiple inheritance
