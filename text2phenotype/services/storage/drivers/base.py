from typing import (
    Dict,
    Iterator,
    List,
    Optional
)
from abc import ABC, abstractmethod


class Blob(ABC):
    """
    Represents an object (BLOB).
    """

    @abstractmethod
    def get_meta(self) -> Dict:
        pass

    @abstractmethod
    def delete(self) -> bool:
        pass

    @abstractmethod
    def get_content(self) -> bytes:
        pass


class Container(ABC):
    """
    Represents a container (bucket) which can hold multiple objects.
    """

    @abstractmethod
    def list_objects(self) -> List[Blob]:
        pass

    @abstractmethod
    def iterate_objects(self, source_dir: str = None) -> Iterator[Blob]:
        pass

    @abstractmethod
    def get_object(self, object_name: str) -> Blob:
        pass

    @abstractmethod
    def get_object_content(self, object_name: str) -> bytes:
        pass

    @abstractmethod
    def get_object_content_stream(self, object_name: str, chunk_size: int) -> bytes:
        pass

    @abstractmethod
    def delete_object(self, obj: Blob) -> bool:
        pass

    @abstractmethod
    def write_bytes(self, data: bytes, file_name: str, tid: str = None, dest_dir: str = None) -> bool:
        pass

    @abstractmethod
    def write_file(self, file_path: str, dest_dir: str = None) -> bool:
        pass

    @abstractmethod
    def purge_objects(self) -> None:
        pass

    @abstractmethod
    def sync_down(self, source_path: Optional[str], dest_path: str):
        pass

    @abstractmethod
    def sync_up(self, source_path: str, dest_path: Optional[str]):
        pass


class StorageService(ABC):
    @property
    @abstractmethod
    def container(self) -> Container:
        pass

    @abstractmethod
    def get_container(self, container_name: Optional[str] = None) -> Container:
        """
        Return a container instance.
        """
        pass

    @abstractmethod
    def get_content(self, file_name: str) -> bytes:
        """
        Return an file contents.
        """
        pass

    @abstractmethod
    def download_file(self, s3_file_key: str, local_file_name: str, container_name: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def check_connection(self) -> bool:
        """
        Checks connection to storage service
        """
        pass
