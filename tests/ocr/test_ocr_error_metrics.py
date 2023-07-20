import os
import unittest

from text2phenotype.common import common
from text2phenotype.annotations.file_helpers import Annotation, AnnotationSet
from text2phenotype.ocr import ocr_error_metrics
from tests.ocr.fixtures import OCR_FIXTURES_DIR


class TestTextPair(unittest.TestCase):
    def test_init(self):
        match = ocr_error_metrics.TextPair("foo", "food")
        self.assertEqual(match.noisy_text, "foo")
        self.assertEqual(match.true_text, "food")

    def test_ratio_score(self):
        match = ocr_error_metrics.TextPair("foo", "food")
        self.assertEqual(0.86, match.ratio_score)

        self.assertEqual(1.00, ocr_error_metrics.TextPair("food", "food").ratio_score)
        self.assertEqual(0.75, ocr_error_metrics.TextPair("food", "Food").ratio_score)

        self.assertEqual(0.0, ocr_error_metrics.TextPair("foo", "bar").ratio_score)
        self.assertEqual(0.67, ocr_error_metrics.TextPair("bar", "baz").ratio_score)


class TestOCRErrorMetrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ann_fixture_path = os.path.join(OCR_FIXTURES_DIR, "ann")
        cls.ANN_SET_NOISY = AnnotationSet.from_file_content(
            common.read_text(os.path.join(ann_fixture_path, "lab_ann_noisy.ann")))
        cls.ANN_SET_TRUE = AnnotationSet.from_file_content(
            common.read_text(os.path.join(ann_fixture_path, "lab_ann_true.ann")))

        cls.pairs = ocr_error_metrics.match_annotation_sets(cls.ANN_SET_NOISY, cls.ANN_SET_TRUE)

    def test_match_annotation_sets(self):
        expected_pairs = [
            ocr_error_metrics.TextPair('20DEC13', '20DEC13'),
            ocr_error_metrics.TextPair('Sodium-Na', 'Sodium-Na'),
            ocr_error_metrics.TextPair('140', '140'),
            ocr_error_metrics.TextPair('meq/L', 'meq/L'),
            ocr_error_metrics.TextPair('Polassium-K', 'Potassium-K'),
            ocr_error_metrics.TextPair('4.8', '4.8'),
            ocr_error_metrics.TextPair('meq/L', 'meq/L'),
            ocr_error_metrics.TextPair('Chlorida-€1', 'Chloride-Cl'),
            ocr_error_metrics.TextPair('mogs |', 'meq/L'),
            ocr_error_metrics.TextPair('coz', 'CO2'),
            ocr_error_metrics.TextPair('meq/L', 'meq/L'),
            ocr_error_metrics.TextPair('BUN', 'BUN'),
            ocr_error_metrics.TextPair('mg/dl', 'mg/dl'),
            ocr_error_metrics.TextPair('Crealinine', 'Creatinine')
        ]
        self.assertEqual(expected_pairs, self.pairs)
        expected_scores = [1.0, 1.0, 1.0, 1.0, 0.91, 1.0, 1.0, 0.73, 0.18, 0.0, 1.0, 1.0, 1.0, 0.9]
        self.assertEqual(expected_scores, [pair.ratio_score for pair in self.pairs])

    def test_get_mean_score(self):
        self.assertEqual(0.8371428571428572, ocr_error_metrics.get_mean_score(self.pairs))

    def test_get_match_pct(self):
        self.assertEqual(0.6428571428571429, ocr_error_metrics.get_match_pct(self.pairs))

    def test_text_range_is_close(self):
        self.assertTrue(
            ocr_error_metrics.text_range_is_close(self.ANN_SET_NOISY.entries[2], self.ANN_SET_TRUE.entries[2])
        )
        self.assertFalse(
            ocr_error_metrics.text_range_is_close(self.ANN_SET_NOISY.entries[2], self.ANN_SET_TRUE.entries[1])
        )

    def test_get_similar_annotation(self):
        # test a single label match, "lab_value"
        found_ann = ocr_error_metrics.get_similar_annotation(self.ANN_SET_NOISY.entries[2], self.ANN_SET_TRUE)
        expected_ann = self.ANN_SET_TRUE.entries[2]
        self.assertEqual(expected_ann, found_ann)

        # test multiple label matches, "lab"
        found_ann = ocr_error_metrics.get_similar_annotation(self.ANN_SET_NOISY.entries[5], self.ANN_SET_TRUE)
        expected_ann = self.ANN_SET_TRUE.entries[5]
        self.assertEqual(expected_ann, found_ann)

        # test no match
        ann = Annotation(label="bar", text="foo", text_range=[1, 10])
        found_ann = ocr_error_metrics.get_similar_annotation(ann, self.ANN_SET_TRUE)
        self.assertEqual(None, found_ann)

    def test_get_similar_annotation_matching_text(self):
        target_ann = Annotation(label="foo", text="floop", text_range=[10, 15])
        ann_set = AnnotationSet.from_list([
            Annotation(label="foo", text="floop", text_range=[11, 16]),
            Annotation(label="foo", text="14", text_range=[8, 10]),
        ])
        found_ann = ocr_error_metrics.get_similar_annotation(target_ann, ann_set)
        expected_ann = ann_set.entries[0]
        self.assertEqual(expected_ann, found_ann)

    def test_get_similar_annotation_matching_range_use_distance(self):
        target_ann = self.ANN_SET_NOISY.entries[5]
        ann_set = self.ANN_SET_TRUE
        ann_set.add_annotation_no_coord(label="lab", text="Cl", text_range=[581, 583])
        found_ann = ocr_error_metrics.get_similar_annotation(target_ann, ann_set)
        expected_ann = self.ANN_SET_TRUE.entries[5]
        self.assertEqual(expected_ann, found_ann)


if __name__ == '__main__':
    unittest.main()
