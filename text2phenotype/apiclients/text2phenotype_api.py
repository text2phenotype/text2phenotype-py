from pathlib import Path
from typing import Optional

from requests import Response

from text2phenotype.constants.environment import Environment
from text2phenotype.open_api.models import (
    BaseProcessing,
    ChunkStatusResponse,
    DocumentProcessingCorpus,
    DocumentProcessingText,
    DocumentStatusResponse,
    JobStatusResponse,
    ReprocessOptions,
)
from text2phenotype.tasks.job_task import JobTask
from text2phenotype.tasks.work_tasks import (
    ChunkTask,
    DocumentTask,
)

from .base_client import (
    response_json,
    BaseClient,
    CommonAPIMethodsMixin,
)


class text2phenotypeApiClient(BaseClient, CommonAPIMethodsMixin):
    ENVIRONMENT_VARIABLE = Environment.text2phenotype_API_BASE
    API_ENDPOINT = '/api/v1/'

    def __init__(self,
                 api_base: Optional[str] = None,
                 text2phenotype_secret_key: Optional[str] = None):

        super().__init__(api_base)
        self.headers['X-API-KEY'] = text2phenotype_secret_key or Environment.text2phenotype_API_SECRET_KEY.value

    def process_document_corpus(self, body: DocumentProcessingCorpus) -> Response:
        return self.post('/document/process/corpus', json=body.dict())

    def process_document_file(self, file, body: BaseProcessing) -> Response:
        filename = Path(file.name).name

        files = {
            'file': (filename, file),
            'payload': (None, body.json(), 'application/json'),
        }

        return self.post('/document/process/file', files=files)

    def process_document_text(self, text: str, options: BaseProcessing) -> Response:
        text_processing: DocumentProcessingText = DocumentProcessingText.construct(**options.dict())
        text_processing.document_text = text
        return self.post('/document/process/text', json=text_processing.dict())

    def job_status(self, job_id: str) -> Response:
        return self.get(f'/job/status/{job_id}')

    def job_pickup(self, job_id: str) -> JobTask:
        return self.get(f'/job/pickup/{job_id}')

    def document_status(self, document_id: str) -> Response:
        return self.get(f'/document/status/{document_id}')

    def document_pickup(self, document_id: str) -> Response:
        return self.get(f'/document/pickup/{document_id}')

    def chunk_status(self, chunk_id: str) -> Response:
        return self.get(f'/chunk/status/{chunk_id}')

    def chunk_pickup(self, chunk_id: str) -> Response:
        return self.get(f'/chunk/pickup/{chunk_id}')

    def reprocess_job(self,
                      job_id: str,
                      reprocess_options: Optional[ReprocessOptions] = None) -> Response:

        endpoint = f'/job/reprocess/{job_id}'

        if reprocess_options:
            return self.post(endpoint, json=reprocess_options.dict())

        return self.get(endpoint)

    def stop_job(self, job_id: str) -> Response:
        return self.get(f'/job/stop/{job_id}')


@response_json
class text2phenotypeApiJsonClient(text2phenotypeApiClient):
    def job_status(self, job_id: str) -> JobStatusResponse:
        data = super().job_status(job_id)
        return JobStatusResponse.parse_obj(data)

    def job_pickup(self, job_id: str) -> JobTask:
        data = super().job_pickup(job_id)
        return JobTask.parse_obj(data)

    def document_status(self, document_id: str) -> DocumentStatusResponse:
        data = super().document_status(document_id)
        return DocumentStatusResponse.parse_obj(data)

    def document_pickup(self, document_id: str) -> DocumentTask:
        data = super().document_pickup(document_id)
        return DocumentTask.parse_obj(data)

    def chunk_status(self, chunk_id: str) -> ChunkStatusResponse:
        data = super().chunk_status(chunk_id)
        return ChunkStatusResponse.parse_obj(data)

    def chunk_pickup(self, chunk_id: str) -> ChunkTask:
        data = super().chunk_pickup(chunk_id)
        return ChunkTask.parse_obj(data)
