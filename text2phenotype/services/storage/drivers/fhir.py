import os
import json

# TODO: Revisit this once a valid use case presents itself -Adam
# from text2phenotype.apiclients.fhir import FHIRClient, FHIREndpoint
from text2phenotype.services.storage.drivers.base import Blob, Container, StorageService

from typing import (
    Dict,
    Iterator,
    List,
    Optional
)


class FHIRBlob(Blob):
    # TODO: Not currently in use -Adam
    def __init__(self, identifier: str, container: 'FHIRContainer', driver: 'FHIRStorage', size: int = None) -> None:
        self.identifier = identifier
        self.size = size
        self.container = container
        self.driver = driver

    def get_meta(self) -> Dict:
        return self.driver.get_meta(self)

    def delete(self) -> bool:
        return self.container.delete_object(self)

    def get_content(self) -> bytes:
        return self.driver.get_content(self.identifier)


class FHIRContainer(Container):
    def __init__(self, driver: 'FHIRStorage') -> None:
        self.driver = driver

    def list_objects(self) -> List[FHIRBlob]:
        return list(self.iterate_objects())

    def iterate_objects(self) -> Iterator[FHIRBlob]:
        response = self.driver.fhir_client._get_all_resources(FHIREndpoint.document)
        items = json.loads(response.text)
        if items is not None:
            for item in items:
                resource = item['resource']
                yield FHIRBlob(identifier=resource['id'], size=10, container=self, driver=self.driver)

    def get_object(self, object_name: str) -> FHIRBlob:
        return FHIRBlob(identifier=object_name, size=10, container=self, driver=self.driver)

    def get_object_content(self, object_name: str) -> bytes:
        blob = self.get_object(object_name)
        return blob.get_content()

    def delete_object(self, obj: FHIRBlob) -> bool:
        return self.driver.fhir_client._delete_resource(obj.identifier, FHIREndpoint.document)

    def write_bytes(self, data: bytes, file_name: str, dest_dir: str = None, tid: str = None) -> bool:
        return self.driver.fhir_client._send_resource(data.decode('utf-8'), FHIREndpoint.document)

    def write_file(self, file_path: str, dest_dir: str = None) -> bool:
        with open(file_path, 'rb') as rb_file:
            contents = rb_file.read()

        file_name = os.path.basename(file_path)
        data_result = self.write_bytes(
            data=contents,
            file_name=file_name
        )
        return data_result

    def purge_objects(self) -> None:
        for resource in self.iterate_objects():
            resource.delete()

    def get_object_content_stream(self, object_name: str, chunk_size: int) -> bytes:
        pass

    def sync_down(self, source_path: Optional[str], dest_path: str):
        pass

    def sync_up(self, source_path: str, dest_path: Optional[str]):
        pass


class FHIRStorage(StorageService):
    def __init__(self, client_host):
        self.__fhirClient = FHIRClient(client_host)

    @property
    def fhir_client(self):
        return self.__fhirClient

    def get_container(self, container_name: Optional[str] = None) -> FHIRContainer:
        return FHIRContainer(driver=self)

    def get_document_data(self, file_object: FHIRBlob) -> dict:
        return json.loads(self.fhir_client._get_resource(file_object.identifier, FHIREndpoint.document).text)

    def get_content(self, file_name: str) -> bytes:
        document_data = json.loads(self.fhir_client._get_resource(file_name, FHIREndpoint.document).text)
        return document_data.get('content', '').encode('utf-8')

    def get_meta(self, file_object: FHIRBlob) -> Dict:
        document_data = self.get_document_data(file_object)
        return document_data.get('meta', {})

    def check_connection(self) -> bool:
        return self.fhir_client.check_connection()
