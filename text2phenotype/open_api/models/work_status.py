from pydantic import BaseModel

from text2phenotype.tasks.task_enums import WorkStatus


class BaseWorkStatusResponse(BaseModel):
    status: WorkStatus


class JobStatusResponse(BaseWorkStatusResponse):
    job_id: str


class DocumentStatusResponse(BaseWorkStatusResponse):
    document_id: str


class ChunkStatusResponse(BaseWorkStatusResponse):
    chunk_id: str
