import os
import sys
import time
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryFile
from typing import (
    Dict,
    IO,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)

import boto3
from awscli.clidriver import create_clidriver
from boto3.s3.transfer import TransferConfig
from botocore.client import Config
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
)
from botocore.session import Session

from text2phenotype.common.decorators import retry
from text2phenotype.common.log import operations_logger

from .base import (
    Container,
    Blob,
    StorageService
)


class S3Blob(Blob):

    def __init__(self,
                 name: str,
                 container: 'S3Container',
                 driver: 'S3Storage',
                 size: int = None) -> None:

        self.name = name
        self.size = size
        self.container = container
        self.driver = driver

    def delete(self) -> bool:
        return self.container.delete_object(self)

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def get_meta(self) -> Dict:
        return self.driver.resource.meta.client.get_object(Bucket=self.container.name,
                                                           Key=self.name)

    def get_content(self) -> bytes:
        return self.container.get_object_content(self.name)

    def download_fileobj(self, file_obj):
        self.container.download_fileobj(self.name, file_obj)

    def __repr__(self) -> str:
        return f'<Object: name={self.name}, container={self.container}, ' \
               f'driver={self.driver}, size={self.size}>'


class S3Container(Container):
    def __init__(self, name: str, driver: 'S3Storage') -> None:
        self.name = name
        self.driver = driver
        self.bucket_uri = f's3://{self.name}'

    def __get_s3_bucket_resource(self):
        return self.driver.resource.Bucket(self.name)

    def list_objects(self) -> List[S3Blob]:
        return list(self.iterate_objects())

    def iterate_objects(self, source_dir: Optional[Union[str, Path]] = None) -> Iterator[S3Blob]:
        bucket = self.__get_s3_bucket_resource()

        if source_dir:
            objects = bucket.objects.filter(Prefix=str(source_dir))
        else:
            objects = bucket.objects.all()
        try:
            for object_summary in objects:
                yield S3Blob(object_summary.key, self, self.driver, object_summary.size)
        except ClientError as err:
            operations_logger.exception(
                f"Error occurred while connecting to the '{self.name}' bucket.\n{err}")

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def delete_objects_permanently(
            self,
            prefix: Union[str, Path] = '') -> Tuple[List[str], List[str]]:
        """Permanently delete all versions of objects from S3 filtered by prefix"""

        operations_logger.info(f"Deleting objects permanently, "
                               f"Bucket = '{self.name}', Prefix = '{prefix}'")

        bucket = self.__get_s3_bucket_resource()
        resp_data = bucket.object_versions.filter(Prefix=str(prefix)).delete()

        deleted = []
        errors = []

        for details in resp_data:
            deleted.extend(obj['Key'] for obj in details.get('Deleted', []))
            errors.extend(obj['Key'] for obj in details.get('Errors', []))

        operations_logger.info(f'There are {len(deleted)} objects were deleted permanently, '
                               f'{len(errors)} errors.')

        return deleted, errors

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def get_object(self, object_name: str) -> S3Blob:
        object_summary = self.driver.resource.ObjectSummary(self.name, object_name)
        return S3Blob(object_name, self, self.driver, object_summary.size)

    def get_object_content(self, object_name: str) -> bytes:
        return self.driver.get_content(object_name, container_name=self.name)

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def get_object_content_stream(self, object_name: str, chunk_size: int) -> bytes:
        obj = self.driver.resource.Object(bucket_name=self.name, key=object_name)
        streaming_body = obj.get()['Body']
        while True:
            chunk = streaming_body.read(chunk_size)
            if not chunk:
                break
            yield chunk

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def delete_object(self, obj: S3Blob) -> bool:
        object_summary = self.driver.resource.ObjectSummary(self.name, obj.name)
        object_summary.delete()
        return True

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def write_bytes(self,
                    data: bytes,
                    file_name: Union[str, Path],
                    dest_dir: str = None,
                    tid: str = None) -> bool:

        file_name = str(file_name)
        with BytesIO(data) as buffer:
            return self.write_fileobj(buffer, file_name, dest_dir, tid)

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def write_fileobj(self,
                      file_obj: IO,
                      file_name: Union[str, Path],
                      dest_dir: str = None,
                      tid: str = None) -> bool:

        file_name = str(file_name)
        key = os.path.join(dest_dir, file_name) if dest_dir else file_name
        operations_logger.debug(f'writing {key} to s3 bucket {self.name}', tid=tid)
        operations_logger.debug(f'Put Object {file_name} in Bucket {self.name}', tid=tid)

        config = TransferConfig()

        try:
            self.driver.client.upload_fileobj(file_obj, self.name, key, Config=config)
        except Exception as e:
            operations_logger.exception(f"{sys.exc_info()[0].__qualname__}: {e}")
            raise e

    def write_file(
            self,
            file_path: Union[str, Path],
            dest_dir: str = None,
            file_name: Union[str, Path] = None,
            tid: str = None) -> bool:

        file_name = str(file_name)
        file_path = str(file_path)
        file_name = file_name or os.path.basename(file_path)
        object_key = os.path.join(dest_dir, file_name) if dest_dir else file_name
        operations_logger.debug(f'upload file {file_path} to bucket {self.name} with object key {object_key}')

        try:
            self.driver.client.upload_file(file_path, Bucket=self.name, Key=object_key)
        except Exception as e:
            operations_logger.exception(f"{sys.exc_info()[0].__qualname__}: {e}")
            raise e

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def download_fileobj(self, object_key: Union[str, Path], file_obj):
        object_key = str(object_key)
        operations_logger.debug(f'Downloading file {object_key} from bucket {self.name}')
        self.driver.client.download_fileobj(Bucket=self.name, Key=object_key, Fileobj=file_obj)
        return True

    def purge_objects(self) -> None:
        for object_summary in self.iterate_objects():
            object_summary.delete()

    @staticmethod
    def _sync(source_path: str, dest_path: str, additional_options: list = None) -> None:
        """Runs the same as a command line `aws s3 sync`.

        Creates destination dirs if they don't already exist.
        :param source_path: where the documents you want to sync currently live
        :param dest_path: where you want them to go
        :param additional_options: a list of additional s3 sync commands see
        https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html,
        must be separated eg: ['--quiet', '--exclude', '*']
        :return: None,
        """
        driver = create_clidriver()
        options = ['s3', 'sync', '--acl=bucket-owner-full-control',
                   source_path, dest_path, '--quiet']
        if additional_options:
            options.extend(additional_options)
        options = tuple(options)

        exit_code = driver.main(options)

        if exit_code != 0:
            raise RuntimeError(f'AWS CLI exited with code: {exit_code}')

    def sync_up(self, source_path: str, dest_path: Optional[str], additional_options: list = None):
        """
        Uploads the local data in source_path to the dest_path in the s3 bucket
        :param source_path: The absolute path to the local data
        :param dest_path: The relative path in the s3 bucket,
            defaults to root of the bucket
        """
        upload_to_path = self.bucket_uri
        if dest_path:
            upload_to_path = os.path.join(upload_to_path, dest_path)
        self._sync(source_path, upload_to_path, additional_options=additional_options)

    def sync_down(self,
                  source_path: Optional[str],
                  dest_path: str,
                  additional_options: Optional[List[str]] = None) -> None:
        """Downloads the data from the `source_path` in the s3 bucket to the local `dest_path`.

        :param source_path: The relative path in the s3 bucket from which sync the data,
            defaults to root of the bucket
        :param dest_path: The local path to which to sync the data
        """
        download_from_path = self.bucket_uri
        if source_path:
            download_from_path = os.path.join(download_from_path, source_path)
        self._sync(download_from_path, dest_path, additional_options=additional_options)

    def __str__(self):
        return f'<S3Container: name={self.name}, driver={self.driver}>'


class S3Storage(StorageService):
    __SESSIONS = {}  # typing: Dict[Tuple[str], boto3.Session] - cache of boto3 Session instances

    def __init__(self, bucket_name: str, aws_access_key_id: str, aws_secret_access_key: str,
                 aws_session_token: str = None, service_name: str = None, region_name: str = None,
                 endpoint_url: str = None, api_version: str = None, use_ssl: bool = True,
                 verify: Union[bool, str] = None, botocore_session: Session = None,
                 profile_name: str = None, config: Config = None) -> None:
        self.__client = None
        self.__resource = None
        self.__session = None
        self.__container = None

        self.__container_name = bucket_name
        self.__aws_access_key_id = aws_access_key_id
        self.__aws_secret_access_key = aws_secret_access_key
        self.__aws_session_token = aws_session_token
        self.__region_name = region_name
        self.__endpoint_url = endpoint_url

        self.__service_name = service_name
        self.__api_version = api_version
        self.__use_ssl = use_ssl
        self.__verify = verify
        self.__botocore_session = botocore_session
        self.__profile_name = profile_name
        self.__config = config

    @retry((NoCredentialsError, ClientError), logger=operations_logger, tries=10)
    def __validate_boto3_session(self, session, raise_exception=False):
        # Reduce the amount of `get_caller_identity()` API calls to be one per minute
        VALIDATION_TTL = 60  # One minute
        VALIDATION_EXPIRED_ATTRIBUTE = '_text2phenotype_validation_expired_at'

        validation_expired_at = getattr(session, VALIDATION_EXPIRED_ATTRIBUTE, 0)

        if time.time() >= validation_expired_at:
            try:
                # Request to STS fails if session is expired
                # https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html
                session.client('sts', endpoint_url=self.__endpoint_url).get_caller_identity()
                setattr(session, VALIDATION_EXPIRED_ATTRIBUTE, time.time() + VALIDATION_TTL)
            except (ClientError, NoCredentialsError):
                if raise_exception:
                    raise
                return False

        return True

    @retry((NoCredentialsError, ClientError), logger=operations_logger, tries=10)
    def __create_boto3_session(self):
        session = boto3.Session(
            aws_access_key_id=self.__aws_access_key_id,
            aws_secret_access_key=self.__aws_secret_access_key,
            aws_session_token=self.__aws_session_token,
            region_name=self.__region_name)

        self.__validate_boto3_session(session, raise_exception=True)
        return session

    @property
    def session(self):
        if self.__session is None:
            # Key is a tuple of Session() initial parameters
            cache_key = (
                self.__aws_access_key_id,
                self.__aws_secret_access_key,
                self.__aws_session_token,
                self.__region_name,
            )

            cached_session = self.__SESSIONS.get(cache_key)

            # Validate cached session
            if cached_session:
                operations_logger.debug('founded cached boto3.Session')

                if not self.__validate_boto3_session(cached_session):
                    del self.__SESSIONS[cache_key]
                    cached_session = None
                    operations_logger.debug('cached session object is invalid, removed from cache')

            if cached_session:
                self.__session = cached_session
            else:
                self.__session = self.__create_boto3_session()
                self.__SESSIONS[cache_key] = self.__session
                operations_logger.debug('new boto3.Session created, added to cache')

        return self.__session

    @property
    def client(self):
        if self.__client is None:
            self.__client = self.session.client('s3', endpoint_url=self.__endpoint_url)
            operations_logger.debug('s3 client created')
        return self.__client

    @property
    def resource(self):
        if self.__resource is None:
            self.__resource = self.session.resource('s3', endpoint_url=self.__endpoint_url)
            operations_logger.debug('s3 resource created')
        return self.__resource

    @property
    def container(self) -> S3Container:
        if self.__container is None:
            self.__container = self.get_container(self.__container_name)
        return self.__container

    def get_container(self, container_name: Optional[str] = None) -> S3Container:
        container_name = container_name if container_name else self.__container_name
        return S3Container(container_name, self)

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def download_file(self, s3_file_key: str, local_file_name: str, container_name: Optional[str] = None) -> str:
        if container_name is None:
            container_name = self.container.name

        self.client.download_file(container_name, s3_file_key, local_file_name)
        return local_file_name

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def get_content(self, file_name: str, container_name: Optional[str] = None) -> bytes:
        if container_name is None:
            container_name = self.container.name

        with TemporaryFile(buffering=1024) as f:
            self.client.download_fileobj(container_name, file_name, f)
            f.seek(0)
            return f.read()

    @retry((NoCredentialsError, ClientError), logger=operations_logger)
    def get_content_stream(self, file_name):
        obj = self.resource.Object(bucket_name=self.container.name, key=file_name)
        return obj.get()['Body']

    def check_connection(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.__container_name)
        except Exception:
            connected = False
        else:
            connected = True

        return connected
