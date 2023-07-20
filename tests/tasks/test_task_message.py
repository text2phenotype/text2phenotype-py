import unittest
from unittest.mock import patch

import semantic_version

import text2phenotype
from text2phenotype import tasks
from text2phenotype.tasks.task_message import TaskMessage


class TestTaskMessage(unittest.TestCase):

    def test_default_version(self):
        message = TaskMessage()
        self.assertEqual(tasks.__version__, message.version)
        self.assertEqual(tasks.__version__, message.dict().get('version'))

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            TaskMessage(version='1.9')

    def test_incompatibility(self):
        with patch.object(text2phenotype.tasks,
                          'version_spec',
                          new_callable=semantic_version.SimpleSpec,
                          expression='~=1.0.0'):
            with self.assertRaises(ValueError):
                TaskMessage(version='2.0.0')

    def test_compatibility(self):
        with patch.object(text2phenotype.tasks,
                          'version_spec',
                          new_callable=semantic_version.SimpleSpec,
                          expression='~=2.0.0'):
            message = TaskMessage(version='2.0.1')
            self.assertEqual(message.version, '2.0.1')

