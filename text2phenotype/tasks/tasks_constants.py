import os


class TasksConstants:
    TEXT2PHENOTYPE_FHIR_ORGANIZATION = 'https://www.text2phenotype.com/fhir/organization.json'

    STORAGE_BASE_PREFIX = 'processed'
    STORAGE_DOCUMENTS_PREFIX = os.path.join(STORAGE_BASE_PREFIX, 'documents')
    STORAGE_CHUNKS_PREFIX = 'chunks'
    STORAGE_JOBS_PREFIX = os.path.join(STORAGE_BASE_PREFIX, 'jobs')

    STORAGE_PURGED_JOBS_PREFIX = os.path.join('purged', 'jobs')

    SOURCE_FILE_SUFFIX = 'source'
    DOCUMENT_TEXT_SUFFIX = 'extracted_text'

    METADATA_FILE_EXTENSION = 'metadata.json'
    MANIFEST_FILE_EXTENSION = 'manifest.json'

    BULK_WORKER_NAME = 'BulkIntakeWorker'
