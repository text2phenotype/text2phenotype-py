import unittest
from text2phenotype.mpi.data_structures import MPIInput, MPIMatch


class TestMPIInput(unittest.TestCase):
    def test_idempotent(self):
        a = {'document_id': 123, 'permitted_files': [1, 4, 5]}
        input_1 = MPIInput.from_dict(a)
        dict_1 = input_1.to_dict()
        input_2 = MPIInput.from_dict(dict_1)
        dict_2 = input_2.to_dict()

        self.assertDictEqual(a, dict_1)
        self.assertDictEqual(a, dict_2)


class TestMPIMatch(unittest.TestCase):
    def test_idempotent_match(self):
        a = {'doc_id': 123, 'probability': .5}
        input_1 = MPIMatch.from_dict(a)
        dict_1 = input_1.to_dict()
        input_2 = MPIMatch.from_dict(dict_1)
        dict_2 = input_2.to_dict()

        self.assertDictEqual(a, dict_1)
        self.assertDictEqual(a, dict_2)
