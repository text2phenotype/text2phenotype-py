import io
import json
from typing import Optional

from requests import Response

from text2phenotype.apiclients.base_client import (
    BaseClient,
    CommonAPIMethodsMixin,
)
from text2phenotype.constants.environment import Environment

from .base_client import response_json


class IntakeClient(BaseClient, CommonAPIMethodsMixin):
    ENVIRONMENT_VARIABLE = Environment.INTAKE_URL
    API_ENDPOINT = '/intake/'

    def process_document_text(self, body: dict) -> Response:
        return self.post('/api/document/process/text', json=body)

    def process_document_file(self, content: bytes, filename: str, body: dict) -> Response:
        files = {
            'file': (filename, io.BytesIO(content)),
            'payload': (None, json.dumps(body), 'application/json'),
        }
        return self.post('/api/document/process/file', files=files)

    def process_document_corpus(self, body: dict) -> Response:
        return self.post('/api/document/process/corpus', json=body)

    def reprocess_job(self, uuid: str, body: Optional[dict] = None) -> Response:
        body = body or {}
        return self.post(f'/api/job/reprocess/{uuid}', json=body)

    def stop_job(self, uuid: str, payload: Optional[dict] = None) -> Response:
        payload = payload or {}
        return self.post(f'/api/job/stop/{uuid}', json=payload)

    def purge_job(self, uuid: str, payload: Optional[dict] = None) -> Response:
        payload = payload or {}
        return self.post(f'/api/job/purge/{uuid}', json=payload)


@response_json
class IntakeJsonClient(IntakeClient):
    """Implementation of "IntakeClient" returns JSON-deserialized response"""
    pass
