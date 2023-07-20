import json
import unittest

from hashlib import sha256

from text2phenotype.tasks.document_info import DocumentInfo


class TestDocumentInfo(unittest.TestCase):

    def setUp(self) -> None:
        self.initial_data = {
            'document_id': 'id',
            'text_file_key': 'temp/temp.txt',
            'source_file_key': 'temp/src.txt',
            'source': 'upload',
            'source_hash': sha256(b'').hexdigest(),
            'document_size': 0,
            'tid': 'tid',
        }
        self.doc_info = DocumentInfo(**self.initial_data)

    def test_json_serialization(self):
        data = json.loads(self.doc_info.to_json())  # ensure everything is json-serializable
        actual = DocumentInfo(**data)

        self.assertEqual(self.doc_info.document_id, actual.document_id)
        self.assertEqual(self.doc_info.source_file_key, actual.source_file_key)
        self.assertEqual(self.doc_info.text_file_key, actual.text_file_key)
        self.assertEqual(self.doc_info.source, actual.source)
        self.assertEqual(self.doc_info.source_hash, actual.source_hash)
        self.assertEqual(self.doc_info.document_size, actual.document_size)
        self.assertEqual(self.doc_info.tid, actual.tid)

    def test_expected_dict(self):
        self.assertDictEqual(json.loads(self.doc_info.to_json()), self.initial_data)

    def test_expected_customer_dict(self):
        res = {
            'document_id': self.initial_data['document_id'],
            'source': self.initial_data['source'],
            'source_hash': self.initial_data['source_hash'],
            'tid': self.initial_data['tid'],
        }
        self.assertDictEqual(res, json.loads(self.doc_info.to_customer_facing_json()))
