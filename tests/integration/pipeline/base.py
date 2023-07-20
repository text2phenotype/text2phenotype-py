import functools
import inspect
import itertools
import json
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import (
    Callable,
    List,
    Optional,
)

from pydantic import BaseModel
from requests import (
    ConnectionError,
    Response,
)

from text2phenotype.apiclients import Text2phenotypeApiClient
from text2phenotype.common.version_info import get_version_info
from text2phenotype.common.log import operations_logger
from text2phenotype.open_api.models.process import (
    BaseProcessing,
    DocumentProcessingCorpus,
)
from text2phenotype.tasks.job_task import JobTask
from text2phenotype.tasks.task_enums import (
    TaskOperation,
    WorkStatus,
)
from text2phenotype.tasks.work_tasks import (
    ChunkTask,
    DocumentTask,
    WorkTask,
)

from tests.integration import IntegrationTestCase
from tests.integration.environment import TestsEnvironment


TEXT2PHENOTYPE_API_PRODUCT_ID = 'text2phenotype-api'
TEXT2PHENOTYPE_PY_VERSION_INFO = get_version_info(TestsEnvironment.root_dir)


class PipelineTestCase(IntegrationTestCase):
    DEFAULT_REQUESTS_KWARGS = {
        'timeout': (5, None),  # 5 sec, (connection_timeout, read_timeout)
        'verify': False,  # Ignore verifying the SSL certificate
    }

    PROCESS_CLINICAL_SUMMARY: BaseProcessing = BaseProcessing(
        operations=[TaskOperation.clinical_summary],
        app_destination='Pipeline Integration Tests'
    )

    text2phenotype_api: Text2phenotypeApiClient = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.text2phenotype_api: Text2phenotypeApiClient = Text2phenotypeApiClient()
        cls.text2phenotype_api.default_kwargs = cls.DEFAULT_REQUESTS_KWARGS.copy()

        cls.check_connectivity()

    @classmethod
    @functools.lru_cache(None)
    def check_connectivity(cls) -> None:
        if not cls.text2phenotype_api.headers.get('X-API-KEY'):
            raise SystemError(
                '"MDL_COMN_TEXT2PHENOTYPE_API_SECRET_KEY" is required but does not defined '
                'in the environment')

        try:
            version_info = cls.text2phenotype_api.version()
        except ConnectionError:
            raise SystemError(f'Can\'t connect to Text2phenotype API ({cls.text2phenotype_api.api_base}). '
                              f'Check "MDL_COMN_TEXT2PHENOTYPE_API_BASE" variable and VPN connection.')

        if not version_info or version_info.get('product_id') != TEXT2PHENOTYPE_API_PRODUCT_ID:
            raise SystemError(f'Expecting Text2phenotype API but other service responses. '
                              f'{version_info}')

    @classmethod
    def generate_tid(cls, caller_stack_offset: int = 1) -> str:
        """Generate Transaction ID for Job with the test details.

        Format:
            <class_name> :: <test_method> :: <active_branch> :: <commit_id>

        For example:
            TestDocumentProcessing :: test_process_file_pdf :: MAPPS-123 :: 3fd303c
        """

        parts = [cls.__name__]
        stack = inspect.stack()

        # Find test function in the stack
        for frame in stack:
            if frame[3].startswith('test_'):
                parts.append(frame[3])
                break
        else:
            # Get nearest caller as fallback
            if len(stack) > caller_stack_offset:
                parts.append(inspect.stack()[caller_stack_offset][3])
            elif len(stack) > 1:
                parts.append(inspect.stack()[1][3])

        # Add Git branch / commit id
        parts.extend([TEXT2PHENOTYPE_PY_VERSION_INFO.active_branch,
                      TEXT2PHENOTYPE_PY_VERSION_INFO.commit_id[:7]])

        return ' :: '.join(parts)

    @classmethod
    def create_default_job(cls) -> BaseProcessing:
        processing_payload = cls.PROCESS_CLINICAL_SUMMARY.copy(deep=True)
        processing_payload.tid = cls.generate_tid(caller_stack_offset=2)
        return processing_payload

    @classmethod
    def create_default_corpus_job(cls) -> DocumentProcessingCorpus:
        process_corpus = DocumentProcessingCorpus.construct(**cls.create_default_job().dict())
        process_corpus.source_bucket = TestsEnvironment.CORPUS_SOURCE_BUCKET.value
        process_corpus.source_directory = TestsEnvironment.CORPUS_SOURCE_DIRECTORY.value

        destination_directory = Path(TestsEnvironment.CORPUS_DESTINATION_DIRECTORY.value)
        results_dir = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S.%f')
        process_corpus.destination_directory = str(destination_directory / results_dir)

        process_corpus.tid = cls.generate_tid(caller_stack_offset=2)
        return process_corpus

    @classmethod
    def get_job_task(cls, job_id) -> JobTask:
        """Create JobTask object from the Text2phenotypeApi.job_pickup() response"""
        resp = cls.text2phenotype_api.job_pickup(job_id)
        if isinstance(resp, Response):
            resp = resp.json()
        return JobTask.parse_obj(resp)

    @classmethod
    def get_document_task(cls, doc_id) -> DocumentTask:
        """Create DocumentTask object from the Text2phenotypeApi.document_pickup() response"""
        resp = cls.text2phenotype_api.document_pickup(doc_id)
        if isinstance(resp, Response):
            resp = resp.json()
        return DocumentTask.parse_obj(resp)

    @classmethod
    def get_chunk_task(cls, chunk_id) -> ChunkTask:
        """Create ChunkTask object from the Text2phenotypeApi.chunk_pickup() response"""
        resp = cls.text2phenotype_api.chunk_pickup(chunk_id)
        if isinstance(resp, Response):
            resp = resp.json()  # Parse JSON
        return ChunkTask.parse_obj(resp)

    @classmethod
    def wait_until(cls,
                   func: Callable,
                   timeout: Optional[int] = None,
                   sleep_timeout: float = 1.0) -> bool:
        """Wait until func() returns true or timeout exceeded"""

        timeout = timeout or TestsEnvironment.DEFAULT_WAITING_TIMEOUT.value
        t1 = time.time()

        while True:
            if func():
                return True

            if time.time() - t1 > timeout:
                return False

            time.sleep(sleep_timeout)

    @classmethod
    def wait_until_job_complete(cls, job_id: str, timeout: int = 60) -> JobTask:
        """Wait until a Job will be completed or timeout exceeded.

        Timeout will be reset if any kind of metadata was updated.
        """

        def _get_hash_from_all_metadata(job: JobTask) -> int:
            """Calculate hash from all metadata JSONs to detect any update"""

            # Fetch all docs
            docs = [cls.get_document_task(doc_id) for doc_id in sorted(job.document_ids)]

            # Fetch all chunks
            chunks = []
            for doc in docs:
                for chunk_id in sorted(doc.chunks):
                    chunks.append(cls.get_chunk_task(chunk_id))

            return hash(tuple(obj.json() for obj in itertools.chain([job], docs, chunks)))

        job = cls.get_job_task(job_id)
        last_hash = _get_hash_from_all_metadata(job)
        t1 = time.time()

        while True:
            job = cls.get_job_task(job_id)

            if job and job.complete:
                break

            if time.time() - t1 > timeout:
                job_hash = _get_hash_from_all_metadata(job)

                # Nothing changed
                if job_hash == last_hash:
                    break

                # Reset timeout if something was updated
                last_hash = job_hash
                t1 = time.time()

            time.sleep(2)

        job_summary = cls.create_job_summary(job)

        if job.status is WorkStatus.completed_success:
            operations_logger.info(f'Job completed successfully:\n\n{job_summary}')
        else:
            operations_logger.error(f'Job failed:\n\n{job_summary}')

        return job

    @classmethod
    def create_job_summary(cls, job: JobTask) -> str:
        def _as_enum_values_list(enum_items_iterable) -> List[str]:
            return [item.value for item in enum_items_iterable]

        def _as_json_serializable_list(objects_list: BaseModel) -> dict:
            return [json.loads(pydantic_obj.json()) for pydantic_obj in objects_list]

        def _collect_task_statuses(work_task: WorkTask) -> dict:
            statuses = {}
            errors = {}
            docker_images = {}

            for task, task_info in work_task.task_statuses.items():
                statuses.setdefault(task_info.status.value, []).append(task.value)

                if task_info.error_messages:
                    errors[task.value] = task_info.error_messages
                    docker_images.setdefault(task_info.docker_image, []).append(task.value)

            return {'statuses': statuses, 'error_messages': errors, 'docker_images': docker_images}

        job_details = {}
        job_details['job_id'] = job.job_id
        job_details['status'] = job.status.value
        job_details['operations'] = _as_enum_values_list(job.operations)
        job_details['summary_tasks'] = _as_json_serializable_list(job.summary_tasks)

        doc_statuses = job_details.setdefault('document_statuses', {})
        for doc_id, doc_info in job.document_info.items():
            doc_statuses[doc_id] = doc_info.status.value

        # Coolect documents details
        documents: dict = job_details.setdefault('documents', {})
        for doc_id in job.document_ids:
            doc_details: dict = documents.setdefault(doc_id, {})

            doc = cls.get_document_task(doc_id)
            doc_details['filename'] = job.document_info[doc_id].filename
            doc_details['performed_tasks'] = _as_enum_values_list(doc.performed_tasks)
            doc_details['failed_tasks'] = _as_enum_values_list(doc.failed_tasks)

            doc_failed_chunks = doc_details.setdefault('failed_chunks', {})
            for chunk_id, failed_tasks in doc.failed_chunks.items():
                doc_failed_chunks[chunk_id] = _as_enum_values_list(failed_tasks)

            doc_details['document_task_statuses'] = _collect_task_statuses(doc)

            # Collect chunks details
            chunks = doc_details.setdefault('chunks', {})
            for chunk_id in doc.chunks:
                chunk_details: dict = chunks.setdefault(chunk_id, {})

                chunk = cls.get_chunk_task(chunk_id)
                chunk_details['status'] = chunk.status.value
                chunk_details['performed_tasks'] = _as_enum_values_list(chunk.performed_tasks)
                chunk_details['chunk_task_statuses'] = _collect_task_statuses(chunk)

        # Log job summary as YAML
        return yaml.safe_dump(job_details, sort_keys=False, default_flow_style=False)
