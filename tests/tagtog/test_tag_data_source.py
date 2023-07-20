import unittest
import os

from text2phenotype.tagtog.tag_tog_async_data_source import TagTogAsyncDataSource


class TestTagTogDataSource(unittest.TestCase):
    data_source = TagTogAsyncDataSource(
        parent_dir=os.path.dirname(__file__),

        project='tag_tog_sample_output',
        include_master_annotations=False,
        require_complete=True)

    def test_get_all_ann_files(self):

        ds = TagTogAsyncDataSource(parent_dir=os.path.dirname(__file__),
                                   project='tag_tog_sample_output', include_master_annotations=True)

        actual_ann_files = ds._get_all_annotation_files()

        expected = [
            ('aj7TDeRicOq1RkTN_W0ybYJHR1e0-text', '', 'master'),
            ('aj7TDeRicOq1RkTN_W0ybYJHR1e0-text', '', 'members/sfee'),
            ('acPInTouQOC_eYqpL1pHMGolTdei-6_text2phenotype_smart.pdf', 'OpenEMR', 'members/sfee'),
            ('a9zIFuYOKAoe4oce9LYnEMq4vSfe-john_stevens', 'OpenEMR', 'members/sfee')]

        self.assertEqual(len(actual_ann_files), len(expected))

        for entry in expected:
            self.assertIn(entry, actual_ann_files)

    def test_get_all_exclude_master(self):
        actual_ann_files = self.data_source._get_all_annotation_files()
        expected = [('a9zIFuYOKAoe4oce9LYnEMq4vSfe-john_stevens', 'OpenEMR', 'members/sfee')]

        self.assertEqual(len(actual_ann_files), len(expected))
        for entry in expected:
            self.assertIn(entry, actual_ann_files)

    def test_write_output(self):
        self.data_source.write_raw_materials_for_annotated_materials()
        self.assertTrue(os.path.exists(
            self.data_source.raw_text_out_path(
                file_id='john_stevens', project_subfolder='OpenEMR')))
        self.assertTrue(os.path.exists(
            self.data_source.raw_ann_out_path(
                file_id='john_stevens', project_subfolder='OpenEMR',
                annotator_dir='members/sfee')))
