import unittest
from text2phenotype.constants.features.label_types import ProblemLabel, MedLabel, CancerLabel, SocialRiskFactorLabel, PHILabel

class TestLabelFromAlternativeTextLabels(unittest.TestCase):
    def test_not_included(self):
        self.assertEqual(ProblemLabel.get_from_alternative_text_labels('med'), None)
        self.assertEqual(MedLabel.get_from_alternative_text_labels(None), None)

    def test_included(self):
        self.assertEqual(MedLabel.get_from_alternative_text_labels('medication'), MedLabel.med)

        self.assertEqual(CancerLabel.get_from_alternative_text_labels('b0_benign'), CancerLabel.behavior)
        self.assertEqual(CancerLabel.get_from_alternative_text_labels('b1_uncertain'), CancerLabel.behavior)
        self.assertEqual(CancerLabel.get_from_alternative_text_labels('b2_in_situ'), CancerLabel.behavior)
        self.assertEqual(CancerLabel.get_from_alternative_text_labels('b3_mal_primary'), CancerLabel.behavior)
        self.assertEqual(CancerLabel.get_from_alternative_text_labels('b6_mal_metastatic'), CancerLabel.behavior)
        self.assertEqual(CancerLabel.get_from_alternative_text_labels('b9_mal_uncertain'), CancerLabel.behavior)

        self.assertEqual(SocialRiskFactorLabel.get_from_alternative_text_labels('social'), SocialRiskFactorLabel.social_status)

        self.assertEqual(PHILabel.get_from_alternative_text_labels('location'), PHILabel.street)
