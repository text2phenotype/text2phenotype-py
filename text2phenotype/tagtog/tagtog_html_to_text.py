from lxml import html
import re

from text2phenotype.common import common
from text2phenotype.common.log import operations_logger
from text2phenotype.constants.common import OCR_PAGE_SPLITTING_KEY


class TagTogText:
    def __init__(self, html_input):
        self.html_input = html_input
        self.raw_text = None
        self.html_mapping_to_text = None
        self._page_break_char_ix = None
        self.ingest()

    def ingest(self):

        tree = html.fromstring(self.html_input)
        doc_metadata = self.get_doc_metadata(tree)
        if doc_metadata.get('charset') != 'UTF-8':
            raise TypeError("Cannot parse a document with charset != utf-8")

        txt, pos_mapping = self.parse_tree(tree)

        self.html_mapping_to_text = pos_mapping
        self.raw_text = txt

    @staticmethod
    def parse_tree(tree):
        article = tree.body
        txt = ""
        pos_mapping = dict()

        for art in article:
            for section in art:
                for div in section:
                    for p in div:
                        if 'id' in p.attrib:
                            pos_mapping[p.attrib['id']] = len(txt)
                            if p.text:
                                txt += p.text
                                txt += '\n'
                # ADD KEY FOR SECTION (IE: PAGE BREAKS)
                txt += OCR_PAGE_SPLITTING_KEY[0]
        return txt[:-1], pos_mapping

    @staticmethod
    def get_doc_metadata(tree):
        header = tree.head
        metadata = dict()
        for i in header.getiterator('meta'):
            metadata = {**metadata, **i.attrib}
        return metadata

    def offset_from_text_pos(self, text_pos):
        part = None
        offset = None
        for section, start in self.html_mapping_to_text.items():

            if text_pos >= start:
                part = section
                offset = text_pos - start
            else:
                break
        return part, offset

    def get_part_offsets_range(self, range: list):
        part = None
        offsets = []
        for entry in range:
            temp_part, temp_offset = self.offset_from_text_pos(entry)
            if part is not None and temp_part != part:
                operations_logger.warning('We do not currently support adding annotations that span multiple parts '
                                          'into tag tog, ignoring the whole annotation')
                return None, None
            else:
                part = temp_part
                offsets.append(temp_offset)
        return part, offsets

    @property
    def txt_page_break_pos(self):
        """
        Return the character positions of the first character of a page,
        eg following OCR_PAGE_SPLITTING_KEY '\x0c'
        """
        if not self._page_break_char_ix:
            self._page_break_char_ix = [0] + [
                x.start() + 1 for x in re.finditer(OCR_PAGE_SPLITTING_KEY[0], self.raw_text)
            ]
        return self._page_break_char_ix
