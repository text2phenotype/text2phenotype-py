import os
import unittest

from text2phenotype.common.common import write_json, read_json
from text2phenotype.tagtog.splitting_pdfs import get_page_numbers, split_annotation_json


class SplitPdfTests(unittest.TestCase):
    __PAGE1_ENTITY = {
        "classId": "e_6",
        "part": "s1v1",
        "offsets": [
            {
                "start": 183,
                "text": "Adenocarcinoma"
            }
        ],
        "coordinates": [
            {
                "x": "180.75",
                "y": "385.00"
            },
            {
                "x": "411.75",
                "y": "403.50"
            }
        ],
        "confidence": {
            "state": "pre-added",
            "who": ["user:gsommers"],
            "prob": 1
        },
        "fields": {},
        "normalizations": {}
    }

    __PAGE2_ENTITY = {
        "classId": "e_19",
        "part": "s2v1",
        "offsets": [
            {
                "start": 1008,
                "text": "brain"
            }
        ],
        "coordinates": [
            {
                "x": "262.50",
                "y": "1730.50"
            },
            {
                "x": "363.75",
                "y": "1747.50"
            }
        ],
        "confidence":
            {
                "state": "pre-added",
                "who": [
                    "user:gsommers"
                ],
                "prob": 1
            },
        "fields": {},
        "normalizations": {}
    }

    __ANN_JSON_FILE = "./split_pdf_tests.ann.json"

    __ANN_JSON = {
        "annotatable": {
            "parts": [
                "s1v1",
                "s2v1"
            ]
        },
        "anncomplete": False,
        "sources": [],
        "metas": {},
        "entities": [
            __PAGE1_ENTITY,
            __PAGE2_ENTITY
        ],
        "relations": []
    }

    @classmethod
    def setUpClass(cls):
        write_json(cls.__ANN_JSON, cls.__ANN_JSON_FILE)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.__ANN_JSON_FILE):
            os.remove(cls.__ANN_JSON_FILE)

    def test_get_page_numbers_uniform(self):
        """Test where pages divide up evenly."""
        exp = [(0, 9), (10, 19), (20, 29)]
        obs = get_page_numbers(30, 10)
        self.assertListEqual(exp, obs)

    def test_get_page_numbers_increase_set_size(self):
        """Test where total number of pages forces target size to be exceeded."""
        exp = [(0, 10), (11, 21), (22, 31)]
        obs = get_page_numbers(32, 10)
        self.assertListEqual(exp, obs)

    def test_get_page_numbers_uniform_decrease_set_size(self):
        """Test where total number of pages forces subsets to be smaller than target size."""
        exp = [(0, 9), (10, 18), (19, 27)]
        obs = get_page_numbers(28, 10)
        self.assertListEqual(exp, obs)

    def test_get_page_numbers_regression1(self):
        """Test of real life fail (v1)."""
        exp = [(0, 54), (55, 109), (110, 163), (164, 217), (218, 271)]
        obs = get_page_numbers(272, 50)
        self.assertListEqual(exp, obs)

    def test_get_page_numbers_regression2(self):
        """Test of real life fail (v2)."""
        exp = [(0, 47), (48, 95), (96, 143), (144, 191), (192, 239), (240, 286), (287, 333)]
        obs = get_page_numbers(334, 50)
        self.assertListEqual(exp, obs)

    def test_split_annotation_json_keep_all(self):
        """Test where all of the original annotations should be preserved."""
        entity1 = self.__PAGE1_ENTITY.copy()
        entity1['part'] = 's1v1'
        entity2 = self.__PAGE2_ENTITY.copy()
        entity2['part'] = 's2v1'
        self.__test_split_annotation_json({0, 1}, [entity1, entity2])

    def test_split_annotation_json_none(self):
        """Test where none of the original annotations should be preserved."""
        self.__test_split_annotation_json({3}, [])

    def test_split_annotation_json_some(self):
        """Test where a subset of the original of the annotations should be preserved."""
        entity = self.__PAGE2_ENTITY.copy()
        entity['part'] = 's1v1'
        self.__test_split_annotation_json({1}, [entity])

    def __test_split_annotation_json(self, pages_to_keep, exp_entities):
        out_ann = './__test_split_annotation_json.json'

        split_annotation_json(self.__ANN_JSON_FILE, pages_to_keep, out_ann)

        try:
            obs_json = read_json(out_ann)

            for key, value in self.__ANN_JSON.items():
                if key == 'annotatable':
                    value['parts'] = [e["part"] for e in exp_entities]

                if key == 'entities':
                    value = exp_entities

                self.assertEqual(value, obs_json[key])
        finally:
            if os.path.exists(out_ann):
                os.remove(out_ann)


if __name__ == '__main__':
    unittest.main()
