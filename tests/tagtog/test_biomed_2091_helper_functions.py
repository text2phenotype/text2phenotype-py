import unittest

from text2phenotype.annotations.file_helpers import AnnotationSet, Annotation
from text2phenotype.common.deduplication import duplicate_ranges
from text2phenotype.tagtog.upload_text_helper_functions import remove_duplicate_text, update_duplicate_annotations, \
    update_annotation_range, chunk_text_ann, clean_text


class TestBiomed2091HelperFunctions(unittest.TestCase):
    TEXT = '\n \t\x0cDobby is a free elf. \n\n\n \t\x0cDobby is a free elf. \n\n Hello world'
    DUPLICATE_RANGES = duplicate_ranges(txt=TEXT, min_length=10)
    ANNOTATION_SET = AnnotationSet()
    ANNOTATION_SET.entries = [
        Annotation(text='world', text_range=[61, 66], label='1'),
        Annotation(text='Dobby', label='2', text_range=[4, 9]),
        Annotation(text='Dobby', label='3', text_range=[31, 36])
    ]

    def test_remove_duplicate_text(self):
        duplicate_removed_text = remove_duplicate_text(text=self.TEXT, range_duplicates=self.DUPLICATE_RANGES)
        expected_deduped_text = '\n \t\x0cDobby is a free elf. \n\n Hello world'
        self.assertEqual(duplicate_removed_text, expected_deduped_text)

    def test_update_annotations_for_duplicates(self):
        deduped_text = remove_duplicate_text(text=self.TEXT, range_duplicates=self.DUPLICATE_RANGES)
        updated_annotations = update_duplicate_annotations(
            duplicate_ranges=self.DUPLICATE_RANGES,
            ann_set=self.ANNOTATION_SET,
            deduped_text=deduped_text
        )
        self.assertEqual(len(updated_annotations), 2)
        for entry in updated_annotations.entries:
            self.assertEqual(deduped_text[entry.text_range[0]:entry.text_range[1]], entry.text)
            if entry.text == 'Dobby':
                self.assertEqual(list(entry.text_range), [4, 9])
            elif entry.text == 'world':
                self.assertEqual(list(entry.text_range), [34, 39])

    def test_update_annotation_range(self):
        annotation = Annotation(text='world', text_range=[61, 66], label='1')
        updated_annotation = update_annotation_range(annotation=annotation, new_start=0, text="world")
        self.assertEqual(updated_annotation.text_range, [0, 5])

        updated_annotation = update_annotation_range(annotation=annotation, new_start=0, text="hello world")
        self.assertEqual(updated_annotation.text_range, [6, 11])

        updated_annotation = update_annotation_range(annotation=annotation, new_start=0, text="hello")
        self.assertIsNone(updated_annotation)

    def test_chunk_ann_text(self):
        output = chunk_text_ann(text=self.TEXT, ann_set=self.ANNOTATION_SET, chunk_size=40)
        self.assertEqual(len(output), 2)
        for i in range(len(output)):
            text = output[i][1]
            ann_set = output[i][0]
            for annotation in ann_set.entries:
                self.assertEqual(annotation.text, text[annotation.text_range[0]:annotation.text_range[1]])

    def test_clean_text(self):
        cleaned_text = clean_text(self.TEXT)
        expected_cleaned = '----Dobby is a free elf. \n\n\n \t\nDobby is a free elf. \n\n Hello world'

        self.assertEqual(cleaned_text, expected_cleaned)

