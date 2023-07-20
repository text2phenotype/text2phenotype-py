from http import HTTPStatus
from text2phenotype.open_api.models.process import (
    BaseProcessing,
)
from text2phenotype.tasks.task_enums import (
    TaskOperation,
    WorkStatus,
)

from tests.ocr.fixtures.biomed_636_files import ldiazfps

from .base import PipelineTestCase


TEST_FILE_PDF = ldiazfps[0]


class TestAllTaskOperations(PipelineTestCase):
    def test_all_operations(self):
        openapi_schemas = self.text2phenotype_api.get('/openapi.json').json()['components']['schemas']

        all_operations = set(TaskOperation(op)
                             for op in openapi_schemas['AllowedTextTaskOperations']['enum'])
        all_operations -= {TaskOperation.app_reprocess, TaskOperation.summary_custom}

        processing_options = self.create_default_job()

        # Include all operations
        processing_options.operations = list(all_operations)

        # Force execute each task to collect errors
        processing_options.stop_documents_on_failure = False

        with open(TEST_FILE_PDF, 'rb') as f:
            resp = self.text2phenotype_api.process_document_file(f, processing_options)

        self.assertEqual(resp.status_code, HTTPStatus.OK)
        job_id = resp.json().get('job_id')

        job = self.wait_until_job_complete(job_id)
        self.assertEqual(job.status, WorkStatus.completed_success)
