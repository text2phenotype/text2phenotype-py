import io
import os
from typing import (
    Iterator,
    List,
    Optional,
    Tuple,
)
from unittest import TestCase
from unittest.mock import (
    MagicMock,
    patch,
)

from text2phenotype.services.storage.drivers import S3Storage


class File:
    def __init__(self, name=None, data=None, storage: 'MockStorageContainer' = None):
        self.name = name
        self.data = data
        self.storage = storage

    def delete(self):
        if self.storage:
            del self.storage[self.name]

    @staticmethod
    def download_fileobj(*args, **kwargs):
        return MagicMock()


class MockStorageContainer(dict):

    def __init__(self, name=None):
        super().__init__()
        self.name = name or 'default'

    def write_bytes(self,
                    data: bytes,
                    file_name: str,
                    dest_dir: str = None,
                    tid: str = None) -> bool:
        key = os.path.join(dest_dir, file_name) if dest_dir else file_name
        self[key] = data
        return True

    def write_file(self,
                   file_path: str,
                   dest_dir: str = None,
                   file_name: str = None,
                   tid: str = None) -> bool:
        file_name = file_name or os.path.basename(file_path)
        object_key = os.path.join(dest_dir, file_name) if dest_dir else file_name
        if os.path.splitext(file_path)[1] != '.pdf': # this open doesn't work for pdfs for some reason
            with open(file_path) as f:
                data = f.read()
            self[object_key] = data
        return True

    def write_fileobj(self,
                      file_obj: io.IOBase,
                      file_name: str = None,
                      dest_dir: str = None,
                      tid: str = None) -> bool:
        object_key = os.path.join(dest_dir, file_name) if dest_dir else file_name
        self[object_key] = file_obj.read()
        return True

    def download_file(self, s3_file_key: str, local_file_name: str, container_name: Optional[str] = None) -> bytes:
        return local_file_name

    def get_content(self, key: str) -> str:
        return self.get(key)

    def get_container(self, name: Optional[str] = None):
        return self

    @property
    def container(self):
        return self

    def delete_objects_permanently(self, prefix: str = '') -> Tuple[List[str], List[str]]:
        deleted = []
        errors = []

        prefix = str(prefix)
        for key in list(self.keys()):
            if str(key).startswith(prefix) and key in self:
                del self[key]
                deleted.append(key)

        return deleted, errors

    def iterate_objects(self, source_dir=None, **kwargs) -> Iterator[File]:
        pattern = str(source_dir) if source_dir else ''
        for key in list(self.keys()):
            if str(key).startswith(pattern) and key in self:
                yield File(name=key, data=self[key], storage=self)

    def get_object(self, object_name: str) -> Optional[File]:
        data = self.get(object_name)
        if data:
            return File(name=object_name, data=data)

    def download_object_bytes(self, storage_key):
        return self.get(storage_key)

    get_object_content = get_content


class StoragePatchTestCase(TestCase):
    GET_STORAGE_SERVICE_PATCH_TARGET = 'text2phenotype.tasks.rmq_worker.get_storage_service'

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()  # This explicit call required for multiple inheritance

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()  # This explicit call required for multiple inheritance

    def setUp(self) -> None:
        super().setUp()
        self.s3_container = MockStorageContainer()

        get_storage_mock = patch(self.GET_STORAGE_SERVICE_PATCH_TARGET, return_value=self.s3_container)
        get_storage_mock.start()
        self.addCleanup(get_storage_mock.stop)

        s3_storage_mock = patch.object(S3Storage, 'get_container', return_value=self.s3_container)
        s3_storage_mock.start()
        self.addCleanup(s3_storage_mock.stop)

    def tearDown(self) -> None:
        super().tearDown()
        self.s3_container.clear()
