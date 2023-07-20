import os
import unittest

from text2phenotype.annotations.file_helpers import Annotation, AnnotationSet
from text2phenotype.common import common
from text2phenotype.constants.features import LabLabel, MedLabel, CovidLabLabel, HeartDiseaseLabel
from text2phenotype.tagtog.tag_tog_annotation import TagTogAnnotationSet, TagTogEntity
from text2phenotype.tagtog.tag_tog_async_data_source import TagTogAsyncDataSource
from text2phenotype.tagtog.tagtog_html_to_text import TagTogText
from tests.tagtog.tag_tog_file_base import TagTogBase


class TestTagTogAnnotationSet(TagTogBase):
    def test_read_ann_json(self):
        for file in self.SPECIFIC_FILES:
            ann_fp = os.path.join(self.BASE_DIR, self.ANN_DIR, self.POOL, file.replace('.plain.html', '.ann.json'))
            if os.path.isfile(ann_fp):
                ann_set = TagTogAnnotationSet(common.read_json(ann_fp))
                for ent in ann_set.entities:
                    self.assertTrue(isinstance(ent, TagTogEntity))

    def test_to_annotation_set(self):
        for file in self.SPECIFIC_FILES:
            ann_fp = os.path.join(self.BASE_DIR, self.ANN_DIR, self.POOL, file.replace('.plain.html', '.ann.json'))
            if os.path.isfile(ann_fp):
                ann_set = TagTogAnnotationSet(common.read_json(ann_fp))
                html_file = os.path.join(self.BASE_DIR, self.DIR_TO_HTML, self.POOL, file)
                tag_tog_text = TagTogText(common.read_text(html_file))
                text2phenotype_annotation_set = ann_set.to_annotation_set(
                    html_part_map=tag_tog_text.html_mapping_to_text,
                    annotation_legend=self.annotation_legend)

                self.assertTrue(isinstance(text2phenotype_annotation_set, AnnotationSet))
                self.assertEqual(len(text2phenotype_annotation_set.entries),
                                 len([ent for ent in ann_set.entities if ent.class_id != 'e_13']))

                TagTogAsyncDataSource.validate(text2phenotype_annotation_set, tag_tog_text.raw_text)

    def test_to_annotation_set_fields(self):
        norm_field = {
            "f_15": {
                "value": "Definitely not SARS",
                "confidence": {
                    "state": "pre-added",
                    "who": ["user:mpesavento"],
                    "prob": 1
                }
            }
        }
        norm_text_field = "normalized_text"
        ann_legend = self.annotation_legend.copy()
        ann_legend["f_15"] = norm_text_field
        test_file = self.SPECIFIC_FILES[0]
        ann_fp = os.path.join(self.BASE_DIR, self.ANN_DIR, self.POOL, test_file.replace('.plain.html', '.ann.json'))
        ann_json = common.read_json(ann_fp)

        # remove any non CovidLabLabel entities, cause we are only dealing with one label for normalized text
        ann_json["entities"] = [ent for ent in ann_json["entities"] if ent["classId"] != "e_13"]
        ann_json["entities"][0]["fields"] = norm_field
        ann_set = TagTogAnnotationSet(ann_json, label_type=CovidLabLabel, norm_text_field=norm_text_field)

        html_file = os.path.join(self.BASE_DIR, self.DIR_TO_HTML, self.POOL, test_file)
        tag_tog_text = TagTogText(common.read_text(html_file))
        text2phenotype_annotation_set = ann_set.to_annotation_set(
            html_part_map=tag_tog_text.html_mapping_to_text,
            annotation_legend=ann_legend)

        self.assertTrue(isinstance(text2phenotype_annotation_set, AnnotationSet))
        self.assertEqual(len(text2phenotype_annotation_set.entries),
                         len([ent for ent in ann_set.entities if ent.class_id != 'e_13']))
        normed_ann = text2phenotype_annotation_set.entries[0]
        self.assertEqual("covid_lab", normed_ann.label)
        self.assertEqual(norm_field["f_15"]["value"], normed_ann.text)
        # sanity check to make sure the normed annotation is what we expect
        # here, that means the normed "gold" text range, matching the reformatted gold text output
        self.assertEqual([403, 418], normed_ann.text_range)


class TestTagTogEntity(unittest.TestCase):
    entity_in = TagTogEntity(**{
        'classId': 'e_3',
        'part': 's1p1',
        'offsets': [{'start': 14, 'text': 'Crystal'}],
        'coordinates': [],
        'confidence': {
            'state': 'pre-added',
            'who': ['user:sfee'],
            'prob': 1},
        'fields': {
            'f_14': {
                'value': 'pat_first',
                'confidence': {'state': 'pre-added', 'who': ['user:sfee'], 'prob': 1}}},
        'normalizations': {}})
    html_part_range_mapping = {'s1p1': 4}

    annotation_legend = {
        "e_3": "lab_unit",
        "f_14": "demographic_type",
        "e_2": "lab_value",
        "r_7": "i5eqfxw4x80(e_1|e_4)",
        "f_10": "code",
        "f_12": "preferredText",
        "f_8": "lstm_pro",
        "r_5": "gwnnk3vywfc(e_1|e_2)",
        "r_6": "l4eki63fu9m(e_1|e_3)",
        "f_11": "cui",
        "e_4": "lab_interp",
        "f_9": "label",
        "e_1": "lab",
        "e_13": "patient_demographic"
    }

    def test_update_range(self):
        self.assertEqual(self.entity_in.range, [14, 21])
        updated_range = self.entity_in.update_tag_tog_offset_to_range(self.html_part_range_mapping)
        self.assertEqual(updated_range, [18, 25])

    def test_update_label(self):
        updated_label = self.entity_in.update_class_label(self.annotation_legend)
        self.assertEqual(updated_label, self.annotation_legend['e_3'])

    def test_turn_into_base_annotation(self):
        annot = self.entity_in.to_annotation(self.html_part_range_mapping, self.annotation_legend)
        self.assertTrue(isinstance(annot, Annotation))
        self.assertEqual(annot.text, self.entity_in.text)
        self.assertEqual(annot.text_range, self.entity_in.update_tag_tog_offset_to_range(self.html_part_range_mapping))
        self.assertEqual(annot.label, self.entity_in.update_class_label(self.annotation_legend))

    def test_turn_into_base_annotation_labeltype(self):
        # given a specific LabelEnum, create an annotation using that label
        annot = self.entity_in.to_annotation(self.html_part_range_mapping, self.annotation_legend, label_type=LabLabel)
        self.assertEqual(annot.text_range, self.entity_in.update_tag_tog_offset_to_range(self.html_part_range_mapping))
        self.assertEqual(annot.label, self.entity_in.update_class_label(self.annotation_legend))

        # if the label_type doesn't match anything in the annotation_legend, it will return "na"
        annot = self.entity_in.to_annotation(self.html_part_range_mapping, self.annotation_legend, label_type=MedLabel)
        self.assertEqual(annot.label, "na")

    def test_get_label_enum(self):
        ent_clss = TagTogEntity()
        self.assertIn(ent_clss.get_label_type('lab'), [LabLabel.lab, CovidLabLabel.lab])
        self.assertIn(ent_clss.get_label_type('medication'), [MedLabel.med, HeartDiseaseLabel.medication])
        self.assertEqual(ent_clss.get_label_type('aoasdf'), None)
        self.assertEqual(ent_clss.get_label_type('other'), None)

        # test specifying the expected label type
        self.assertEqual(ent_clss.get_label_type('lab', label_type=LabLabel), LabLabel.lab)
        self.assertEqual(ent_clss.get_label_type('medication', label_type=MedLabel), MedLabel.med)


if __name__ == '__main__':
    unittest.main()
