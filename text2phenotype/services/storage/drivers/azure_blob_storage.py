from typing import (
    Dict,
    Iterator,
    List,
    Optional
)
import os
from requests import Session

from azure.storage.blob.models import (
    Blob as AzureBlobModel,
    BlobProperties,
    ContainerProperties,
    ContentSettings,
    Include,
    ResourceProperties,
)
from azure.storage.blob import BlockBlobService
from azure.storage.common import TokenCredential

from text2phenotype.common.log import operations_logger
from text2phenotype.services.storage.exceptions import (
    ContainerExistsException,
    BlobExistsException
)
from .base import (
    Blob,
    Container,
    StorageService
)


class AzureBlob(Blob):

    def __init__(self, container: 'AzureContainer', driver: 'AzureBlobStorage',
                 azure_blob_object: AzureBlobModel = AzureBlobModel()) -> None:

        self.azure_blob_object: AzureBlobModel = azure_blob_object
        self.container = container
        self.driver = driver

    @property
    def name(self) -> str:
        return self.azure_blob_object.name

    @property
    def snapshot(self) -> str:
        return self.azure_blob_object.snapshot

    @property
    def meta(self) -> Dict:
        """
        return the latest metadata (or make a request if the metadata was not received)
        :return: metadata dictionary
        """
        return self.azure_blob_object.metadata or self.get_meta()

    @property
    def properties(self) -> BlobProperties:
        return self.azure_blob_object.properties or self.get_properties()

    @property
    def is_deleted(self) -> bool:
        return self.azure_blob_object.deleted

    def get_meta(self) -> Dict[str, str]:
        return self.driver.client.get_blob_metadata(container_name=self.container.name, blob_name=self.name)

    def set_meta(self, metadata: Dict[str, str]) -> ResourceProperties:
        try:
            return self.driver.client.set_blob_metadata(self.container.name, self.name, metadata)
        except:
            operations_logger.exception(f'An error occurred when setting meta for blob {self.name}'
                                        f' of container {self.container.name}', exc_info=True)

    def get_properties(self) -> BlobProperties:
        return self.driver.client.get_blob_properties(container_name=self.container.name,
                                                      blob_name=self.name).properties

    def set_properties(self, settings: ContentSettings) -> ResourceProperties:
        try:
            return self.driver.client.set_blob_metadata(self.container.name, self.name, settings)
        except:
            operations_logger.exception(f'An error occurred when setting properties for blob {self.name}'
                                        f' of container {self.container.name}', exc_info=True)

    def delete(self) -> bool:
        return self.container.delete_object(self)

    def get_content(self) -> Optional[bytes]:
        try:
            return self.container.get_object_content(self.name)
        except:
            operations_logger.exception(f'An error occurred when getting content', exc_info=True)
            return None

    def __repr__(self) -> str:
        return f'<Object: name={self.name}, container={self.container}, driver={self.driver}>'


class AzureContainer(Container):

    def __init__(self, name: str, driver: 'AzureBlobStorage'):
        self.name = name
        self.driver = driver

    @property
    def meta(self) -> Dict[str, str]:
        try:
            return self.driver.client.get_container_metadata(self.name)
        except:
            operations_logger.exception(f'An error occured when getting metadata for container {self.name}',
                                        exc_info=True)

    @property
    def properties(self) -> ContainerProperties:
        try:
            return self.driver.client.get_container_properties(self.name).properties
        except:
            operations_logger.exception(f'An error occured when getting properties for container {self.name}',
                                        exc_info=True)

    def set_meta(self, meta: Dict[str, str]) -> ResourceProperties:
        try:
            return self.driver.client.set_container_metadata(self.name, meta)
        except:
            operations_logger.exception(f'An error occurred when setting metadata for container {self.name}')

    def iterate_objects(self, prefix: str = None, num_results: int = None, include: Include = None,
                        delimiter: str = None, marker: str = None, timeout: int = None) -> Iterator[AzureBlob]:
        # custom iteration
        for blob in self.driver.client.list_blobs(self.name, prefix, num_results, include, delimiter, marker, timeout):
            yield AzureBlob(azure_blob_object=blob, container=self, driver=self.driver)

    def __iter__(self) -> Iterator[AzureBlob]:
        # default iteration
        for blob in self.iterate_objects():
            yield blob

    def list_objects(self) -> List[AzureBlob]:
        return list(self.iterate_objects())

    def get_object(self, object_name: str) -> AzureBlob:
        if self.driver.client.exists(container_name=self.name, blob_name=object_name):
            blob: AzureBlobModel = self.driver.client.get_blob_properties(container_name=self.name,blob_name=object_name)
            return AzureBlob(azure_blob_object=blob, container=self, driver=self.driver)
        else:
            raise BlobExistsException(f'Blob {object_name} does not exist in container {self.name}')

    def get_object_content(self, object_name: str) -> bytes:
        if self.driver.client.exists(container_name=self.name, blob_name=object_name):
            blob: AzureBlobModel = self.driver.client.get_blob_to_bytes(container_name=self.name, blob_name=object_name)
            return blob.content
        else:
            raise BlobExistsException(f'Blob {object_name} does not exist in container {self.name}')

    def delete_object(self, obj: AzureBlob) -> bool:
        try:
            self.driver.client.delete_blob(container_name=self.name, blob_name=obj.name)
            return True
        except:
            operations_logger.exception(f'An error occurred when delete {obj} object', exc_info=True)
            return False

    def write_bytes(self, data: bytes, file_name: str, tid: str = None, dest_dir: str = None) -> bool:
        operations_logger.info(f'writing {file_name} to Azure container {self.name}', tid=tid)

        try:
            self.driver.client.create_blob_from_bytes(container_name=self.name, blob_name=file_name, blob=data)
        except:
            operations_logger.exception(f'An error occurred when writing to the Azure container {self.name}',
                                        exc_info=True, tid=tid)
            return False
        return True

    def write_file(self, file_path: str, dest_dir: str = None) -> bool:
        operations_logger.debug(f'upload file {file_path} to Azure container {self.name}')

        try:
            file_name: str = os.path.basename(file_path)
            self.driver.client.create_blob_from_path(container_name=self.name, blob_name=file_name, file_path=file_path)

            return True

        except:
            operations_logger.exception(f'An error occurred when upload file {file_path} '
                                        f'to Azure container {self.name}',
                                        exc_info=True)
            return False

    def purge_objects(self) -> None:
        for blob in self.iterate_objects():
            blob.delete()

    def sync_down(self, source_path: Optional[str], dest_path: str):
        raise NotImplemented()

    def sync_up(self, source_path: str, dest_path: Optional[str]):
        raise NotImplemented()


class AzureBlobStorage(StorageService):

    def __init__(self, container_name: str, account_name: str, account_key: str,
                 create_container_if_does_not_exist: bool = True, sas_token: str = None, is_emulated: bool = False,
                 protocol: str = 'https', endpoint_suffix: str = 'core.windows.net', custom_domain: str = None,
                 request_session: Session = None, connection_string: str = None, socket_timeout: int = None,
                 token_credential: TokenCredential = None) -> None:

        self.__client: Optional[BlockBlobService] = None
        self.__container: Optional[AzureContainer] = None
        self.__create_container_if_does_not_exist = create_container_if_does_not_exist

        self.__container_name = container_name
        self.__account_name = account_name
        self.__account_key = account_key
        self.__sas_token = sas_token
        self.__is_emulated = is_emulated
        self.__protocol = protocol
        self.__endpoint_suffix = endpoint_suffix
        self.__custom_domain = custom_domain
        self.__request_session = request_session
        self.__connection_string = connection_string
        self.__socket_timeout = socket_timeout
        self.__token_credential = token_credential

    @property
    def client(self):
        if self.__client is None:
            self.__client = BlockBlobService(account_name=self.__account_name,
                                             account_key=self.__account_key,
                                             sas_token=self.__sas_token,
                                             is_emulated=self.__is_emulated,
                                             protocol=self.__protocol,
                                             endpoint_suffix=self.__endpoint_suffix,
                                             custom_domain=self.__custom_domain,
                                             request_session=self.__request_session,
                                             connection_string=self.__connection_string,
                                             socket_timeout=self.__socket_timeout,
                                             token_credential=self.__token_credential)
        return self.__client

    @property
    def container(self):

        if self.__container is None:
            try:
                self.__container = self.get_container(self.__container_name)

            except ContainerExistsException:
                if self.__create_container_if_does_not_exist:
                    self.create_container(self.__container_name)
                    self.__container = self.get_container(self.__container_name)
                else:
                    operations_logger.info(f'Container {self.__container_name} does not exist'
                                           f' and cannot be created', exc_info=True)

        return self.__container

    def iterate_containers(self, prefix: str = None,
                           num_results: int = None,
                           include_metadata: bool = False,
                           marker: str = None,
                           timeout: int = None) -> Iterator[AzureContainer]:
        # custom container iteration
        for container in self.client.list_containers(prefix, num_results, include_metadata, marker, timeout):
            yield AzureContainer(name=container.name, driver=self)

    def __iter__(self) -> Iterator[AzureContainer]:
        for container in self.iterate_containers():
            yield container

    def get_container(self, container_name: Optional[str] = None) -> AzureContainer:
        container_name = container_name if container_name else self.__container_name
        if self.client.exists(container_name=container_name):
            return AzureContainer(name=container_name, driver=self)
        else:
            raise ContainerExistsException(f"Container {container_name} does not exist")

    def create_container(self, container_name: str):
        operations_logger.info(f'Creating container {container_name}')
        try:
            self.client.create_container(container_name=container_name)
        except:
            operations_logger.exception(f'An error occurred when creating container', exc_info=True)

    def delete_container(self, container_name: str):
        try:
            self.client.delete_container(container_name)
            operations_logger.info(f'Container {self.__container_name} was marked for delete')
        except:
            operations_logger.exception(f'An error occurred when deleting container {self.__container_name}')

    def check_connection(self) -> bool:
        try:
            resp: bool = self.client.exists(container_name=self.__container_name)
        except:
            connected = False
        else:
            connected = True
            if not resp:
                operations_logger.info(f"Connection to the Azure Blob Storage is OK, "
                                       f"but container {self.__container_name} does not exist")

        return connected

    def get_content(self, file_name: str) -> bytes:
        operations_logger.debug(f'getting {file_name} from {self.container.name}')
        return self.container.get_object_content(file_name)
