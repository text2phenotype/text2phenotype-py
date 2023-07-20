import unittest
from text2phenotype.annotations.file_helpers import AnnotationSet, Annotation


class TestBiomed2091(unittest.TestCase):
    ENTRIES = [
        Annotation(text='test', label='abc', text_range=[0, 4]),
        Annotation(text='case', label='def', text_range=[100, 104])
    ]
    SAMPLE_BIOMED_OUT = {
        'DiseaseDisorder': [
            {'text': 'Congestive heart failure', 'range': [1487, 1511], 'score': 0.9953607201220178,
             'label': 'diagnosis', 'polarity': 'positive', 'code': '84114007', 'cui': 'C0018801', 'tui': 'T047',
             'vocab': 'SNOMEDCT_US', 'preferredText': 'Heart failure'}],
        'SignSymptom': [
            {'text': 'fever', 'range': [3573, 3578], 'score': 0.6055685792049275, 'label': 'signsymptom',
             'polarity': 'positive', 'code': '420079008', 'cui': 'C0035021', 'tui': 'T047',
             'vocab': 'SNOMEDCT_US', 'preferredText': 'Relapsing Fever'}],
        'Medication': [
            {'text': 'Lasix', 'range': [1216, 1221], 'score': 0.9991767560674114, 'label': 'med',
             'polarity': 'positive', 'code': '202991', 'cui': 'C0699992', 'tui': 'T109', 'vocab': 'RXNORM',
             'preferredText': 'Lasix', 'date': '2019-05-21', 'medFrequencyNumber': [],
             'medFrequencyUnit': [], 'medStrengthNum': [], 'medStrengthUnit': ['mg', 1225, 1227]}],
        'Allergy': [],
        'Lab': [
            {'text': 'Sodium', 'range': [2731, 2737], 'score': 0.9881379060064677, 'label': 'lab',
             'polarity': None, 'code': '25197003', 'cui': 'C0337443', 'tui': 'T059',
             'vocab': 'SNOMEDCT_US', 'preferredText': 'SODIUM MEASUREMENT', 'date': None,
             'labValue': [], 'labUnit': [], 'labInterp': []}],
        'Smoking': []
    }

    def test_set_entries(self):
        ann_set = AnnotationSet()
        ann_set.entries = self.ENTRIES
        self.assertListEqual(ann_set.entries, self.ENTRIES)

        # asssert thata setting entries a second time overwrites previous entries
        entries_b = [Annotation(text='test', label='abc', text_range=[0, 4])]
        ann_set.entries = entries_b
        self.assertListEqual(ann_set.entries, entries_b)

    def test_from_biomed_output(self):
        ann_set = AnnotationSet.from_biomed_output_json(self.SAMPLE_BIOMED_OUT)
        self.assertEqual(len(ann_set.entries), 4)
        expected_entry_text = {'Sodium', 'Lasix', 'Congestive heart failure', 'fever'}
        expected_entry_labels = {'diagnosis', 'signsymptom', 'med',  'lab'}
        actual_texts = {a.text for a in ann_set.entries}
        actual_labels = {a.label  for a in ann_set.entries}
        self.assertSetEqual(actual_labels, expected_entry_labels)
        self.assertSetEqual(actual_texts, expected_entry_text)

    def test_has_matching_ann(self):
        repeated_entries = self.ENTRIES
        ann_set = AnnotationSet.from_list(repeated_entries)
        self.assertFalse(
            ann_set.has_matching_annotation("hoopy", [0, 10], "frood")
        )
        self.assertTrue(
            ann_set.has_matching_annotation(self.ENTRIES[1].label, self.ENTRIES[1].text_range, self.ENTRIES[1].text)
        )

    def test_remove_duplicate_entries(self):
        repeated_entries = self.ENTRIES + [self.ENTRIES[-1]]
        ann_set = AnnotationSet.from_list(repeated_entries)
        ann_set.remove_duplicate_entries()
        self.assertEqual(self.ENTRIES, ann_set.entries)
