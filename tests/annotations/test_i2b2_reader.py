"""
Stub for I2B2 annotation reader
We have a few i2b2 processors that should be tested with known examples

When it is time, move the I2B2 annotation reader to a Annotation subtype,
and move these tests tos omewhere functional
"""

import unittest

from text2phenotype.annotations.i2b2_reader import I2B2Reader, I2B2Entry
from text2phenotype.annotations.file_helpers import Annotation

class I2B2AnnotationReader(unittest.TestCase):
    RAW_MED_ANNOTATION_LINES = """
m="acetylsalicylic acid" 16:0 16:1||do="325 mg" 16:2 16:3||mo="po" 16:4 16:4||f="qd" 16:5 16:5||du="nm"||r="nm"||ln="list"
m="colace ( docusate sodium )" 17:0 17:4||do="100 mg" 17:5 17:6||mo="po" 17:7 17:7||f="bid" 17:8 17:8||du="nm"||r="nm"||ln="list"
m="enalapril maleate" 18:0 18:1||do="10 mg" 18:2 18:3||mo="po" 18:4 18:4||f="bid" 18:5 18:5||du="nm"||r="nm"||ln="list"
m="nph humulin insulin ( insulin nph human )" 33:0 33:7||do="2 units" 34:0 34:1||mo="nm"||f="qam;" 34:2 34:2||du="nm"||r="nm"||ln="list"
m="nph humulin insulin ( insulin nph human )" 33:0 33:7||do="2 units" 34:7 34:8||mo="nm"||f="qam" 34:9 34:9||du="nm"||r="nm"||ln="list"
m="nph humulin insulin ( insulin nph human )" 33:0 33:7||do="3 units" 34:10 34:11||mo="nm"||f="qpm" 34:12 34:12||du="nm"||r="nm"||ln="list"
m="nph humulin insulin ( insulin nph human )" 33:0 33:7||do="3 units" 34:3 34:4||mo="sc" 34:6 34:6||f="qpm" 34:5 34:5||du="nm"||r="nm"||ln="list"
m="ntg 1/150 ( nitroglycerin 1/150 ( 0.4 mg ) )" 35:0 35:9||do="1 tab" 36:0 36:1||mo="sl" 36:2 36:2||f="q5min x 3 prn" 36:3 36:6||du="nm"||r="chest pain" 36:7 36:8||ln="list"
"""

    def setUp(self) -> None:
        self.i2b2_reader = I2B2Reader()


    def test_extract_i2b2_text_and_token_coords(self):
        med_annotations = [
            'm="heparin" 142:3 142:3',
            'm="zocor ( simvastatin )" 37:0 37:3',
            'm="acetylsalicylic acid" 16:0 16:1',
            'm="ntg 1/150 ( nitroglycerin 1/150 ( 0.4 mg ) )" 35:0 35:9',
        ]
        expected_text_coords = [
            I2B2Entry(text="heparin", start_line=142, start_token=3, end_line=142, end_token=3),
            I2B2Entry(
                text="zocor ( simvastatin )",
                start_line=37,
                start_token=0,
                end_line=37,
                end_token=3,
            ),
            I2B2Entry(
                text="acetylsalicylic acid",
                start_line=16,
                start_token=0,
                end_line=16,
                end_token=1,
            ),
            I2B2Entry(
                text="ntg 1/150 ( nitroglycerin 1/150 ( 0.4 mg ) )",
                start_line=35,
                start_token=0,
                end_line=35,
                end_token=9,
            ),
        ]
        for i2b2_text, expected_dict in zip(med_annotations, expected_text_coords):
            text_coords = self.i2b2_reader.extract_i2b2_text_coords(i2b2_text)
            self.assertEqual([expected_dict], text_coords)

    def test_extract_i2b2_text_coords_bad_end_line(self):
        ann_text = '"ischemics" 79:0 78:0'
        expected_coords = [
            I2B2Entry(
                text="ischemics",
                start_line=79,
                start_token=0,
                end_line=79,  # note that this is changed from the text
                end_token=0
            )]
        text_coords = self.i2b2_reader.extract_i2b2_text_coords(ann_text)
        self.assertEqual(expected_coords, text_coords)

    def test_get_token_line_char_coord(self):
        doc_text_lines = [
            "HISTORY OF PRESENT ILLNESS: The patient is a 61-year-old lady with",
            "known history of coronary artery",
            "disease , who underwent coronary artery bypass grafting x three in",
        ]
        expected_char_coord_lines = [
            [
                {"token": "HISTORY", "text_range": [0, 7]},
                {"token": "OF", "text_range": [8, 10]},
                {"token": "PRESENT", "text_range": [11, 18]},
                {"token": "ILLNESS:", "text_range": [19, 27]},
                {"token": "The", "text_range": [28, 31]},
                {"token": "patient", "text_range": [32, 39]},
                {"token": "is", "text_range": [40, 42]},
                {"token": "a", "text_range": [43, 44]},
                {"token": "61-year-old", "text_range": [45, 56]},
                {"token": "lady", "text_range": [57, 61]},
                {"token": "with", "text_range": [62, 66]},
            ], [
                {"token": "known", "text_range": [0, 5]},
                {"token": "history", "text_range": [6, 13]},
                {"token": "of", "text_range": [14, 16]},
                {"token": "coronary", "text_range": [17, 25]},
                {"token": "artery", "text_range": [26, 32]},
            ], [
                {"token": "disease", "text_range": [0, 7]},
                {"token": ",", "text_range": [8, 9]},
                {"token": "who", "text_range": [10, 13]},
                {"token": "underwent", "text_range": [14, 23]},
                {"token": "coronary", "text_range": [24, 32]},
                {"token": "artery", "text_range": [33, 39]},
                {"token": "bypass", "text_range": [40, 46]},
                {"token": "grafting", "text_range": [47, 55]},
                {"token": "x", "text_range": [56, 57]},
                {"token": "three", "text_range": [58, 63]},
                {"token": "in", "text_range": [64, 66]},
            ],
        ]
        for line, expected_coords in zip(doc_text_lines, expected_char_coord_lines):
            token_char_coord = self.i2b2_reader.get_token_line_char_coord(line)
            self.assertEqual(expected_coords, token_char_coord)

    def test_extract_i2b2_text_coords_value_error(self):
        bad_ann_text = 'no quoted text'
        with self.assertRaises(ValueError):
            _ = self.i2b2_reader.extract_i2b2_text_coords(bad_ann_text)

    def test_disjoint_label_text(self):
        doc_text = """5. Diabetes type 2. She was treated with a Portland protocol
during her ICU course wand was switched to a long and
short-acting subcutaneous insulin approaching her home dose of NPH BID."""
        ann_lines_full = [
            'm="long ... acting ... insulin" 115:9 115:9,116:0 116:0,116:2 116:2||do="nm"||mo="subcutaneous" 116:1 116:1||f="nm"||du="nm"||r="nm"||ln="narrative"',
            'm="short-acting ... insulin" 116:0 116:0,116:2 116:2||do="nm"||mo="subcutaneous" 116:1 116:1||f="nm"||du="nm"||r="nm"||ln="narrative"'
        ]
        ann_lines = [
            '"long ... acting ... insulin" 115:9 115:9,116:0 116:0,116:2 116:2',
            '"short-acting ... insulin" 116:0 116:0,116:2 116:2',
        ]
        # we expect
        expected_label_lists = [[
            I2B2Entry(
                text='long',
                start_line=115,
                start_token=9,
                end_line=115,
                end_token=9),
            I2B2Entry(
                text='acting',
                start_line=116,
                start_token=0,
                end_line=116,
                end_token=0),
            I2B2Entry(
                text='insulin',
                start_line=116,
                start_token=2,
                end_line=116,
                end_token=2)
        ], [
            I2B2Entry(
                text='short-acting',
                start_line=116,
                start_token=0,
                end_line=116,
                end_token=0),
            I2B2Entry(
                text='insulin',
                start_line=116,
                start_token=2,
                end_line=116,
                end_token=2)
            ],
        ]
        for ann_line, expected_annotations in zip(ann_lines, expected_label_lists):
            annotation_list = self.i2b2_reader.extract_i2b2_text_coords(ann_line)
            self.assertEqual(expected_annotations, annotation_list)

    def test_bad_end_token_value(self):
        # note only 12 tokens in first line, so get indexing error
        raw_text = """the PACU in stable condition. Her pain was well controlled with PCA
analgesia on POD0 and transitioned to po elixir analgesia following a"""
        raw_text = "\n" * 50 + raw_text  # add prefix lines so line coordinates match
        ann_lines = [
            'm="pca analgesia" 51:11 51:12||do="nm"||mo="nm"||f="nm"||du="nm"||r="pain" 51:6 51:6||ln="narrative"'
        ]
        # the raw text has upper case, the annotation is only lower case
        labeled_text = "pca analgesia"
        raw_text_concat = raw_text.replace("\n", " ").lower()

        doc_token_coords = self.i2b2_reader.get_doc_token_ranges(raw_text)
        ann_set = self.i2b2_reader.get_label_annotation_set(
            ann_lines, doc_token_coords, "m", "Medication", raw_text=raw_text)

        # test the annotation text
        annotation = ann_set.entries[0]
        self.assertEqual(labeled_text, annotation.text)

        # find the full text coordinate positions
        start_char_idx = raw_text_concat.find(labeled_text)
        assert start_char_idx != -1, "Should have found the target string, check the intention of this test"
        label_range = [start_char_idx, start_char_idx + len(labeled_text)]
        self.assertEqual(label_range, annotation.text_range)

    def test_pluralization_in_annotation(self):
        # note only 12 tokens in first line, so get indexing error
        raw_text = """1. Please continue to take the antibiotic Clindamycin until you run out
of pills."""
        raw_text = "\n" * 114 + raw_text  # add prefix lines so line coordinates match
        ann_lines = [
            'm="antibiotic clindamycin" 115:6 115:7||do="nm"||mo="nm"||f="nm"||du="until you run out of pills." 115:8 116:1||r="nm"||ln="narrative"',
            'm="antibiotics" 115:6 115:6||do="nm"||mo="nm"||f="nm"||du="until you run out of pills." 115:8 116:1||r="nm"||ln="narrative"',
            'm="clindamycin" 115:7 115:7||do="nm"||mo="nm"||f="nm"||du="until you run out of pills." 115:8 116:1||r="nm"||ln="narrative"',
        ]
        # the raw text has upper case, the annotation is only lower case
        matching_text = [
            "antibiotic clindamycin",
            "antibiotic",
            "clindamycin",
        ]

        doc_token_coords = self.i2b2_reader.get_doc_token_ranges(raw_text)
        ann_set = self.i2b2_reader.get_label_annotation_set(
            ann_lines, doc_token_coords, "m", "Medication", raw_text=raw_text)

        raw_text_concat = raw_text.replace("\n", " ").lower()
        for i, annotation in enumerate(ann_set.entries):
            expected_ann_text = matching_text[i]
            self.assertEqual(expected_ann_text, annotation.text)

            # find the full text coordinate positions
            start_char_idx = raw_text_concat.find(expected_ann_text)
            assert start_char_idx != -1, "Should have found the target string, check the intention of this test"
            label_range = [start_char_idx, start_char_idx + len(expected_ann_text)]
            self.assertEqual(label_range, annotation.text_range)

    def test_text_line_starts_with_space(self):
        raw_text = " spit , folate 1 mg p.o. q.d. , vitamin E 400 units p.o. q.d. , Haldol 2 mg IV q. 6 p.r.n. agitation , Colace 100 mg b.i.d. , Senna 2 tablets p.o. b.i.d."
        raw_text = "\n" * 42 + raw_text
        ann_lines = ['c="agitation" 43:23 43:23||t="problem"']
        expected_ann = dict(
            text='agitation',
            label="Problem",
            text_range=[133, 142])

        doc_token_coords = self.i2b2_reader.get_doc_token_ranges(raw_text)
        ann_set = self.i2b2_reader.get_label_annotation_set(
            ann_lines, doc_token_coords, "c", "Problem", raw_text=raw_text
        )
        self.assertEqual(expected_ann["text"], ann_set.entries[0].text)
        self.assertEqual(expected_ann["label"], ann_set.entries[0].label)
        self.assertEqual(expected_ann["text_range"], ann_set.entries[0].text_range)


if __name__ == "__main__":
    unittest.main()
