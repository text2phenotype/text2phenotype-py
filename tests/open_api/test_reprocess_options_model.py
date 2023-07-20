import unittest

from text2phenotype.open_api.models.process import ReprocessOptions


class TestReprocessOptionsModel(unittest.TestCase):
    def test_legacy_fields(self):
        legacy_name = 'include_successful_documents'
        actual_name = 'force_all_documents'

        with self.subTest('Test "include_successful_documents" field'):
            res = ReprocessOptions()
            self.assertEqual(res.force_all_documents, False)
            self.assertNotIn(legacy_name, res.dict())

            res = ReprocessOptions(include_successful_documents=True)
            self.assertEqual(res.force_all_documents, True)
            self.assertNotIn(legacy_name, res.dict())

            res = ReprocessOptions(include_successful_documents=False)
            self.assertEqual(res.force_all_documents, False)
            self.assertNotIn(legacy_name, res.dict())
