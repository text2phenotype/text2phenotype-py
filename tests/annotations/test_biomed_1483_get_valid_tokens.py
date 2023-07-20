import unittest
from text2phenotype.common.featureset_annotations import MachineAnnotation


class TestBiomed1483(unittest.TestCase):
    annotations = MachineAnnotation()

    def test_valid_tokens_all_valid(self):
        self.annotations.tokens = ['dinosaur', 'hypocardia.', 'apple']
        valid_tokens, valid_idx = self.annotations.valid_tokens()
        self.assertEqual(valid_idx, [0, 1, 2])

    def test_array_punctuation(self):
        self.annotations.tokens = [';.-', '{})*&', '!@%', '*']
        valid_tokens, valid_idx = self.annotations.valid_tokens()
        self.assertEqual(valid_idx, [])

    def test_stopwords(self):
        self.annotations.tokens = ['a', 'the', 'of', '.', ';']
        valid_tokens, valid_idx = self.annotations.valid_tokens()
        self.assertEqual(valid_idx, [])

    def test_avoid_duplicates(self):
        self.annotations.tokens = ['dinosaur', 'hypocardia.', 'apple', 'a', 'the', 'of', '.', ';']
        duplicate_tokens = {1, 3, 6}
        valid_tokens, valid_idx = self.annotations.valid_tokens(duplicate_tokens=duplicate_tokens)
        expected_tokens = ['dinosaur', 'apple']
        self.assertEqual(valid_tokens, expected_tokens)
        self.assertEqual(valid_idx, [0, 2])
