from typing import (
    List,
    Optional,
)

from requests import Response

from text2phenotype.constants.environment import Environment

from .base_client import BaseClient


class BiomedTrainingSandsClient(BaseClient):
    ENVIRONMENT_VARIABLE = Environment.BIOMED_TRAINING_SANDS_URL
    API_ENDPOINT = '/api/biomed_training/'

    def __init__(self, api_base: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__(api_base=api_base)

        if api_key is None:
            api_key = Environment.BIOMED_TRAINING_API_KEY.value

        self.headers['X-Api-Key'] = api_key

    def destination_documents(self, destination_uuid: str) -> Response:
        params = {
            'destination_uuid': destination_uuid,
        }
        return self.get('/destination_documents/', params)

    def filenames(self, document_uuids: List[str]) -> Response:
        data = {
            'document_uuids': document_uuids,
        }
        return self.post('/filenames/', data)

    def document_uuid(self, async_doc_ids: List[str]) -> Response:
        data = {
            'async_doc_ids': async_doc_ids,
        }
        return self.post('/document_uuid/', data)

    def done_annotations(self) -> Response:
        return self.get('/done_annotations/')
