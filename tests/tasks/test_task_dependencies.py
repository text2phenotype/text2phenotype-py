import json
import unittest

from text2phenotype.tasks.task_enums import (
    TaskEnum,
    TaskOperation,
    WorkType,
)
from text2phenotype.tasks.task_info import TaskDependencies, TASK_MAPPING


class TestTaskDependencies(unittest.TestCase):

    def test_get_document_tasks(self):
        operations = [TaskOperation.clinical_summary]
        doc_tasks = TaskDependencies.get_document_tasks(operations)
        self.assertSetEqual({TaskEnum.disassemble, TaskEnum.reassemble, TaskEnum.discharge, TaskEnum.clinical_summary},
                            set(doc_tasks.keys()))
        self._check_tasks_dict(doc_tasks, WorkType.document)

    def test_chunk_tasks(self):
        operations = [TaskOperation.clinical_summary,
                      TaskOperation.deid,
                      TaskOperation.demographics,
                      TaskOperation.oncology_summary]

        chunk_tasks = TaskDependencies.get_chunk_tasks(operations)

        self.assertSetEqual({TaskEnum.annotate,
                             TaskEnum.vectorize,
                             TaskEnum.demographics,
                             TaskEnum.phi_tokens,
                             TaskEnum.disease_sign,
                             TaskEnum.drug,
                             TaskEnum.lab,
                             TaskEnum.oncology_only,
                             TaskEnum.smoking,
                             TaskEnum.family_history},
                            set(chunk_tasks.keys()))

        self._check_tasks_dict(chunk_tasks, WorkType.chunk)

    def test_recursive_dependency(self):
        operations = [TaskOperation.clinical_summary]
        chunk_tasks = TaskDependencies.get_chunk_tasks(operations)

        # The "annotate" should be present in the result
        self.assertSetEqual({TaskEnum.disease_sign, TaskEnum.lab, TaskEnum.drug, TaskEnum.vectorize, TaskEnum.annotate,
                             TaskEnum.smoking, TaskEnum.family_history},

                            set(chunk_tasks.keys()))

    def _check_tasks_dict(self, tasks_dict, work_type):
        for k, v in tasks_dict.items():
            self.assertIs(k, v.TASK_TYPE)
            self.assertIs(v.WORK_TYPE, work_type)

    def test_klass_mapping_contains_all(self):
        """Ensure all tasks have a mapping to their TaskInfo class"""
        for task in TaskEnum:
            if task != TaskEnum.train_test:  # train test has special status and doesn't need special task info
                self.assertIn(task, TASK_MAPPING)

    def test_pdf_embedder_dependencies(self):
        pdf_dependencies = TaskDependencies.get_document_tasks(
            operations=[TaskOperation.clinical_summary, TaskOperation.pdf_embedder])
        self.assertIn(TaskEnum.clinical_summary, pdf_dependencies[TaskEnum.pdf_embedder].dependencies)

    def test_get_family_history_dependencies(self):
        family_history_dependencies = TaskDependencies.get_chunk_tasks(operations=[TaskOperation.family_history])
        self.assertDictEqual(
            json.loads(family_history_dependencies[TaskEnum.family_history].to_json()),
            {
                "task": "family_history", "status": "not started", "results_file_key": None,
                "error_messages": [], "attempts": 0, "started_at": None, "completed_at": None,
                "docker_image": None, "dependencies": ["vectorize"],
                'model_dependencies': [], "processing_duration": None}
        )

    def test_family_history_in_disease_depend(self):
        disease_sign_dependencies = TaskDependencies.get_chunk_tasks(operations=[TaskOperation.disease_sign])
        self.assertDictEqual(
            json.loads(disease_sign_dependencies[TaskEnum.disease_sign].to_json()),
            {
                "task": "disease_sign", "status": "not started", "results_file_key": None,
                "error_messages": [], "attempts": 0, "started_at": None, "completed_at": None,
                "docker_image": None, "dependencies": ["vectorize"],
                "processing_duration": None,
                "model_dependencies": ['family_history']}
        )
        self.assertDictEqual(
            json.loads(disease_sign_dependencies
                       [TaskEnum.family_history].to_json()),
            {
                "task": "family_history", "status": "not started", "results_file_key": None,
                "error_messages": [], "attempts": 0, "started_at": None, "completed_at": None,
                "docker_image": None, "dependencies": ["vectorize"],
                'model_dependencies': [], "processing_duration": None}
        )

    def test_phi_token_requires_demographics(self):
        phi_token_tasks = TaskDependencies.get_chunk_tasks(operations=[TaskOperation.phi_tokens])
        self.assertIn(TaskEnum.demographics, phi_token_tasks)
