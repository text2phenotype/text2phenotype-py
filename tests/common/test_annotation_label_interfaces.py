from enum import Enum
from unittest import TestCase

from text2phenotype.common.annotations import (
    AnnotationLabelConfig,
    AnnotationCategoryConfig,
)


class SampleCategoryVegetable(Enum):
    # DB Values must be unique
    NA = AnnotationLabelConfig(color='#ffffff', column_index=0, label='N/A', visibility=False, order=999, persistent_label='na')
    CARROT = AnnotationLabelConfig(color='#ffa600', column_index=1, label='Carrot', visibility=True, order=1, persistent_label='carrot')
    SNAP_PEA = AnnotationLabelConfig(color='#438f47', column_index=2, label='Snap Pea', visibility=True, order=0, persistent_label='snap_pea')
    EGGPLANT = AnnotationLabelConfig(color='#6a2191', column_index=3, label='Eggplant', visibility=True, order=2, persistent_label='eggplant')

    @classmethod
    def get_annotation_label(cls):
        return AnnotationLabelConfig(label='Vegetable',
                                     persistent_label='vegetable',  # IMMUTABLE
                                     color='#0dff00',  # Neon Green
                                     visibility=True,  # Will show in Annotator mode AND in Regular mode BY DEFAULT.
                                     # Category-level visibility affects only the behavior of SANDS in "Regular" mode.
                                     column_index=None,  # meaningless at category level
                                     order=7,  # relative order for category to appear in annotation tool
                                     )

    @classmethod
    def to_dict(cls):
        # Get JSON-compatible dictionary for HTTP response
        res_cat = AnnotationCategoryConfig(category_label=cls.get_annotation_label(),
                                           label_enum=cls)
        return res_cat.to_dict()


class TestAnnotationCategoryLabelInterfaces(TestCase):

    CORRECT_CATEGORY = {'color': '#0dff00', 'column_index': None, 'label': 'Vegetable', 'order': 7, 'persistent_label': 'vegetable', 'visibility': True}

    CORRECT_LABELS = [{'color': '#ffffff', 'column_index': 0, 'label': 'N/A', 'order': 999, 'persistent_label': 'na', 'visibility': False},
                      {'color': '#ffa600', 'column_index': 1, 'label': 'Carrot', 'order': 1, 'persistent_label': 'carrot', 'visibility': True},
                      {'color': '#438f47', 'column_index': 2, 'label': 'Snap Pea', 'order': 0, 'persistent_label': 'snap_pea', 'visibility': True},
                      {'color': '#6a2191', 'column_index': 3, 'label': 'Eggplant', 'order': 2, 'persistent_label': 'eggplant', 'visibility': True}]

    def test_to_dict_from_dict(self):
        dat = AnnotationCategoryConfig(category_label=SampleCategoryVegetable.get_annotation_label(),
                                       label_enum=SampleCategoryVegetable)
        res = dat.to_dict()

        expected = {
            AnnotationCategoryConfig.CAT_LABEL: self.CORRECT_CATEGORY,
            AnnotationCategoryConfig.LABELS: self.CORRECT_LABELS,
        }
        self.assertDictEqual(res, expected)

        res_obj = AnnotationCategoryConfig.from_dict(res)
        self.assertEqual(res_obj.category_label.color, '#0dff00')
        self.assertEqual(res_obj.category_label.label, 'Vegetable')
        self.assertEqual(res_obj.category_label.column_index, None)
        self.assertTrue(res_obj.category_label.visibility)
        self.assertEqual(res_obj.category_label.order, 7)
        self.assertEqual(res_obj.category_label.persistent_label, 'vegetable')

        for item in SampleCategoryVegetable:
            self.assertIn(item.value, dat.labels)
            self.assertIn(item.value, res_obj.labels)

    def test_example_class(self):
        res = SampleCategoryVegetable.to_dict()
        expected = {
            AnnotationCategoryConfig.CAT_LABEL: self.CORRECT_CATEGORY,
            AnnotationCategoryConfig.LABELS: self.CORRECT_LABELS,
        }
        self.assertDictEqual(res, expected)
