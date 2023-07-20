import unittest
from uuid import uuid4

from text2phenotype.constants.environment import Environment
from text2phenotype.tasks.job_task import (
    JobDocumentInfo,
    JobTask,
)
from text2phenotype.tasks.task_enums import (
    WorkStatus,
    WorkType,
)


class TestJobInfo(unittest.TestCase):

    def setUp(self) -> None:
        self.job_info = JobTask()

    def test_json_serialization(self):
        self.job_info.add_file('test 1', 'id 1')
        self.job_info.add_file('test 2', 'id 2')
        self.job_info.add_file('test 3', 'id 3')

        self.job_info.user_info = {'key_id': '123', 'user_uuid': '123', 'full_name': 'Full Name',
                                   'primary_email': 'email@domain.com'}

        data_str = self.job_info.to_json()  # ensure everything is json-serializable
        actual = JobTask.from_json(data_str)

        self.assertEqual(self.job_info.job_id, actual.job_id)
        self.assertListEqual(self.job_info.document_ids, actual.document_ids)
        self.assertDictEqual(self.job_info.processed_files, actual.processed_files)
        self.assertListEqual(self.job_info.operations, actual.operations)
        self.assertEqual(self.job_info.bulk_source_bucket, actual.bulk_source_bucket)
        self.assertEqual(self.job_info.bulk_source_directory, actual.bulk_source_directory)
        self.assertIsNotNone(actual.job_id)
        self.assertEqual(['id 1', 'id 2', 'id 3'], actual.document_ids)
        self.assertEqual(self.job_info.user_info, actual.user_info.dict())

    def test_expected_dict(self):
        expected_dict = {
            'version': Environment.TASK_WORKER_VERSION,
            'job_id': self.job_info.job_id,
            'required_features': [],
            'operations': [o.value for o in self.job_info.operations],
            'bulk_source_bucket': self.job_info.bulk_source_bucket,
            'bulk_source_directory': self.job_info.bulk_source_directory,
            'bulk_destination_directory': self.job_info.bulk_destination_directory,
            'started_at': self.job_info.started_at,
            'completed_at': self.job_info.completed_at,
            'total_duration': self.job_info.total_duration,
            'work_type': WorkType.job,
            'user_info': {'key_id': None, 'user_uuid': None, 'full_name': None, 'primary_email': None},
            'app_destination': None,
            'document_info': {doc_id: JobDocumentInfo(status=WorkStatus.processing)
                              for doc_id in self.job_info.document_ids},
            'legacy_document_ids': None,
            'biomed_version': None,
            'model_version': None,
            'reprocess_options': None,
            'user_canceled': None,
            'stop_documents_on_failure': True,
            'summary_tasks': [],
            'user_actions_log': self.job_info.user_actions_log,
            'deid_filter': None

        }
        self.assertDictEqual(expected_dict, self.job_info.dict())

    def test_job_task_deprecated_processed_files(self):
        doc1 = JobDocumentInfo(status=WorkStatus.completed_success)
        doc2 = JobDocumentInfo(status=WorkStatus.completed_failure)
        doc3 = JobDocumentInfo(status=WorkStatus.canceled)

        expected_doc_info = {
            uuid4().hex: doc1,
            uuid4().hex: doc2,
            uuid4().hex: doc3,
        }

        processed_files = {f'{doc_id}.txt': doc_id
                           for doc_id in expected_doc_info}

        def _common_asserts(job_task):
            self.assertEqual(set(job_task.document_ids),
                             set(expected_doc_info.keys()))

            # Check that "processed_files" not present in the serialized data
            self.assertNotIn('processed_files', job_task.dict())

            # Check "processed_files" property
            self.assertDictEqual(job_task.processed_files, processed_files)

        with self.subTest('No "document_info" section'):
            data = {
                'processed_files': processed_files.copy(),
            }

            job_task = JobTask.parse_obj(data)
            _common_asserts(job_task)

            for doc_id, doc in job_task.document_info.items():
                self.assertEqual(doc.status, WorkStatus.not_started)

        with self.subTest('"document_info" and "processed_files" both present'):
            data = {
                'processed_files': processed_files.copy(),
                'document_info': expected_doc_info.copy(),
            }

            job_task = JobTask.parse_obj(data)
            _common_asserts(job_task)

            for expected_filename, doc_id in processed_files.items():
                doc = job_task.document_info[doc_id]
                self.assertEqual(doc.status, expected_doc_info[doc_id].status)
                self.assertEqual(doc.filename, expected_filename)

        with self.subTest('Only "document_info" section present'):
            # Create "new style" document_info data
            good_doc_info = expected_doc_info.copy()

            for filename, doc_id in processed_files.items():
                good_doc_info[doc_id] = good_doc_info[doc_id].copy()
                good_doc_info[doc_id].filename = filename

            data = {
                'document_info': good_doc_info.copy(),
            }

            job_task = JobTask.parse_obj(data)
            _common_asserts(job_task)

            self.assertDictEqual(job_task.document_info,
                                 good_doc_info)
