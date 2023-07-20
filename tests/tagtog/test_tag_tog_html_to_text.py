import os

from text2phenotype.tagtog.tagtog_html_to_text import TagTogText
from text2phenotype.common import common
from tests.tagtog.tag_tog_file_base import TagTogBase


class TestTagTogHTMLTOTEXT(TagTogBase):

    def ensure_correct_output_format(self, tag_tog_text: TagTogText):
        self.assertTrue(isinstance(tag_tog_text.raw_text, str))
        self.assertTrue(isinstance(tag_tog_text.html_mapping_to_text, dict))
        self.assertTrue(isinstance(tag_tog_text.html_input, str))

    def ensure_matching_text(self, tag_tog_text, expected_text_fp):
        self.assertEqual(tag_tog_text.raw_text, common.read_text(expected_text_fp))

    def test_plain_loading_in_mult_types(self):
        for file in self.SPECIFIC_FILES:
            tag_tog_text_obj = TagTogText(common.read_text(
                os.path.join(self.BASE_DIR, self.DIR_TO_HTML, self.POOL, file)))
            self.ensure_correct_output_format(tag_tog_text_obj)
            self.ensure_matching_text(
                tag_tog_text_obj,
                os.path.join(self.BASE_DIR, self.TEXT_DIR, self.POOL, file.replace('.plain.html', '.txt')))

    def test_section_mapping(self):
        # test that each section ends w/ a \n  or \x0c character (indicating a section split)
        for file in self.SPECIFIC_FILES:
            tag_tog_text_obj = TagTogText(common.read_text(
                os.path.join(self.BASE_DIR, self.DIR_TO_HTML, self.POOL, file)))
            for key, value in tag_tog_text_obj.html_mapping_to_text.items():
                if value != 0:
                    self.assertIn(tag_tog_text_obj.raw_text[value - 1], ['\n', '\x0c'])

    def test_offset_from_range(self):
        file = self.SPECIFIC_FILES[0]
        tag_tog_text_obj = TagTogText(common.read_text(
            os.path.join(self.BASE_DIR, self.DIR_TO_HTML, self.POOL, file)))

        part1, offset1 = tag_tog_text_obj.offset_from_text_pos(34)
        self.assertEqual(part1, 's1p2')
        self.assertEqual(offset1, 3)
        part2, offset2 = tag_tog_text_obj.offset_from_text_pos(100)
        self.assertEqual(part2, 's1p5')
        self.assertEqual(offset2, 11)

    def test_txt_page_break_pos(self):
        expected_page_breaks = [
            [0],
            [0, 2451],
            [0, 1847],
            [0]
        ]
        for i, file in enumerate(self.SPECIFIC_FILES):
            tag_tog_text_obj = TagTogText(common.read_text(
                os.path.join(self.BASE_DIR, self.DIR_TO_HTML, self.POOL, file)))

            page_breaks = tag_tog_text_obj.txt_page_break_pos
            self.assertEqual(expected_page_breaks[i], page_breaks)

