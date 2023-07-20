import unittest
import io

from pathlib import Path
from unittest.mock import MagicMock

from text2phenotype.services.storage.drivers.s3 import S3Container


class TestStorageS3(unittest.TestCase):
    def setUp(self):
        fake_driver = MagicMock()
        self.boto3_client_mock = fake_driver.client
        self.s3_container = S3Container(name='test-bucket', driver=fake_driver)

    def test_path_object_for_file_name(self):
        with self.subTest('Test write_bytes()'):
            # test write_bytes() method by sending file_name as path
            self.s3_container.write_bytes(b'test bytes', file_name=Path('test_path/test.txt'))
            args, kwargs = self.boto3_client_mock.upload_fileobj.call_args
            self.assertIsInstance(args[2], str)

            # test write_bytes() method by sending file_name as str
            self.s3_container.write_bytes(b'test bytes', file_name='test.txt')
            args, kwargs = self.boto3_client_mock.upload_fileobj.call_args
            self.assertIsInstance(args[2], str)

        with self.subTest('Test write_file()'):
            # test write_file() method by sending file_name as path
            self.s3_container.write_file('/test/path', file_name=Path('test_path/test.txt'))
            args, kwargs = self.boto3_client_mock.upload_file.call_args
            self.assertIsInstance(kwargs.get('Key'), str)

            # test write_file() method by sending file_name as str
            self.s3_container.write_file('/test/path', file_name='test.txt')
            args, kwargs = self.boto3_client_mock.upload_file.call_args
            self.assertIsInstance(kwargs.get('Key'), str)

            # test write_file() method by sending file_path as path
            self.s3_container.write_file(Path('/test/path'), file_name=Path('test.txt'))
            args, kwargs = self.boto3_client_mock.upload_file.call_args
            self.assertIsInstance(args[0], str)

            # test write_file() method by sending file_path as str
            self.s3_container.write_file('/test/path', file_name=Path('test.txt'))
            args, kwargs = self.boto3_client_mock.upload_file.call_args
            self.assertIsInstance(args[0], str)

        with self.subTest('Test write_fileobj()'):
            # test write_fileobj() method by sending file_name as path
            self.s3_container.write_fileobj(io.BytesIO(b'test'), Path('test_path/test.txt'))
            args, kwargs = self.boto3_client_mock.upload_fileobj.call_args
            self.assertIsInstance(args[2], str)

            # test write_fileobj() method by sending file_name as str
            self.s3_container.write_fileobj(io.BytesIO(b'test'), 'test.txt')
            args, kwargs = self.boto3_client_mock.upload_fileobj.call_args
            self.assertIsInstance(args[2], str)

        with self.subTest('Test download_fileobj()'):
            # test download_fileobj() method by sending file_name as path
            self.s3_container.download_fileobj(Path('test_path/test.txt'), io.BytesIO(b'test'),)
            args, kwargs = self.boto3_client_mock.download_fileobj.call_args
            self.assertIsInstance(kwargs.get('Key'), str)

            # test download_fileobj() method by sending file_name as str
            self.s3_container.download_fileobj('test.txt', io.BytesIO(b'test'),)
            args, kwargs = self.boto3_client_mock.download_fileobj.call_args
            self.assertIsInstance(kwargs.get('Key'), str)
