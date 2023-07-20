import os

from text2phenotype.tasks.tasks_constants import TasksConstants


def get_metadata_chunk_storage_key(document_id: str, redis_key: str) -> str:
    chunk_key = os.path.join(
        TasksConstants.STORAGE_DOCUMENTS_PREFIX,
        document_id,
        TasksConstants.STORAGE_CHUNKS_PREFIX,
        redis_key,
        f'{redis_key}.{TasksConstants.METADATA_FILE_EXTENSION}'
    )
    return chunk_key


def get_metadata_document_storage_key(document_id: str) -> str:
    doc_key = os.path.join(
        TasksConstants.STORAGE_DOCUMENTS_PREFIX,
        document_id,
        f'{document_id}.{TasksConstants.METADATA_FILE_EXTENSION}'
    )
    return doc_key


def get_manifest_job_storage_key(job_id: str, purged: bool = False) -> str:
    storage_prefix = TasksConstants.STORAGE_JOBS_PREFIX if not purged \
                     else TasksConstants.STORAGE_PURGED_JOBS_PREFIX

    return os.path.join(storage_prefix,
                        job_id,
                        f'{job_id}.{TasksConstants.MANIFEST_FILE_EXTENSION}')
