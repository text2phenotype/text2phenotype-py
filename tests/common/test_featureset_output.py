import unittest
from text2phenotype.common.featureset_annotations import MachineAnnotation, Vectorization
from text2phenotype.constants.features import FeatureType


class TestBiomed1306AnnotationClass(unittest.TestCase):
    ANNOTATION = {'1': ['abc', 'def']}
    VECTORIZATION = {'1': [0, 1, 0]}
    FEATURETYPE = FeatureType.clinical

    def test_add_annotation_by_feature_type(self):
        annotation = MachineAnnotation()
        # test adding with feature type object
        annotation.add_item(self.FEATURETYPE, self.ANNOTATION)

        self.assertEqual(annotation.to_dict(), {self.FEATURETYPE.name: self.ANNOTATION})
        self.assertEqual(annotation.feature_names, {self.FEATURETYPE.name})
        self.assertEqual(annotation[self.FEATURETYPE].to_dict(), self.ANNOTATION)

    def test_add_annotation_by_int(self):
        annotation = MachineAnnotation()
        # test adding with feature type object
        annotation.add_item(self.FEATURETYPE.value, self.ANNOTATION)

        self.assertEqual(annotation.to_dict(), {self.FEATURETYPE.name: self.ANNOTATION})
        self.assertEqual(annotation.feature_names, {self.FEATURETYPE.name})
        self.assertEqual(annotation[self.FEATURETYPE.value].to_dict(), self.ANNOTATION)

    def test_add_annotation_by_str(self):
        annotation = MachineAnnotation()
        # test adding with feature type object
        annotation.add_item(self.FEATURETYPE.name, self.ANNOTATION)

        self.assertEqual(annotation.to_dict()[self.FEATURETYPE.name], self.ANNOTATION)
        self.assertEqual(annotation.feature_names, {self.FEATURETYPE.name})
        self.assertEqual(annotation[self.FEATURETYPE.name, 1], self.ANNOTATION['1'])
        self.assertEqual(annotation[FeatureType.speech, 1], None)
        self.assertEqual(annotation[self.FEATURETYPE, 2], None)

    def test_add_vectorization_feat_type(self):
        vectorization = Vectorization()
        # test adding with feature type object
        vectorization.add_item(self.FEATURETYPE, self.VECTORIZATION)

        self.assertEqual(vectorization.to_dict()[self.FEATURETYPE.name], self.VECTORIZATION)
        self.assertEqual(vectorization.feature_names, {self.FEATURETYPE.name})
        self.assertEqual(vectorization[self.FEATURETYPE].to_dict(), self.VECTORIZATION)

    def test_add_vectorization_by_int(self):
        vectorization = Vectorization()
        # test adding with feature type object
        vectorization.add_item(self.FEATURETYPE.value, self.VECTORIZATION)

        self.assertEqual(vectorization.to_dict()[self.FEATURETYPE.name], self.VECTORIZATION)
        self.assertEqual(vectorization.feature_names, {self.FEATURETYPE.name})
        self.assertEqual(vectorization[self.FEATURETYPE.value].to_dict(), self.VECTORIZATION)

    def test_add_vectorization_by_str(self):
        vectorization = Vectorization()
        # test adding with feature type object
        vectorization.add_item(self.FEATURETYPE.name, self.VECTORIZATION)

        self.assertEqual(vectorization.to_dict()[self.FEATURETYPE.name], self.VECTORIZATION)
        self.assertEqual(vectorization.feature_names, {self.FEATURETYPE.name})
        self.assertEqual(vectorization[self.FEATURETYPE.name].to_dict(), self.VECTORIZATION)

    def test_annotation_from_speech_results(self):
        tokenization_results = [{'token': 'Page', 'len': 4, 'range': [0, 4], 'speech': 'NN', 'speech_bin': 'Nouns'},
                                {'token': '1', 'len': 1, 'range': [5, 6], 'speech': 'CD', 'speech_bin': 'Numbers'},
                                {'token': 'of', 'len': 2, 'range': [7, 9], 'speech': 'IN', 'speech_bin': 'com_dep_wd'},
                                {'token': '3', 'len': 1, 'range': [10, 11], 'speech': 'CD', 'speech_bin': 'Numbers'},
                                {'token': 'PATIENT', 'len': 7, 'range': [12, 19], 'speech': 'NNS',
                                 'speech_bin': 'Nouns'}]
        annotations = MachineAnnotation(tokenization_output=tokenization_results)
        self.assertEqual(len(annotations), 5)
        # test get tokens
        self.assertEqual(annotations['token'], ['Page', '1', 'of', '3', 'PATIENT'])
        self.assertEqual(annotations.tokens, ['Page', '1', 'of', '3', 'PATIENT'])
        # test get ranges
        self.assertEqual(annotations.range, annotations['range'])

        # test annotation range mapping functionality
        self.assertEqual(annotations.range_to_token_idx_list,
                         [0, 0, 0, 0, (0, 1), 1, (1, 2), 2, 2, (2, 3), 3, (3, 4), 4, 4, 4, 4, 4, 4, 4, 4])


    def test_vectorization_from_defaults(self):
        defaults = {FeatureType.clinical: [0,0],
                    FeatureType.topography_code.name: [1, 2, 2],
                    FeatureType.topography.value:[0]}
        vectors = Vectorization(default_vectors=defaults)
        self.assertEqual(vectors.defaults.to_dict(), {'clinical': [0, 0],
                                                      'topography_code': [1, 2, 2],
                                                      'topography': [0]})



