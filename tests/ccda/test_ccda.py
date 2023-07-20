import unittest
from text2phenotype.ccda import ccda
from text2phenotype.ccda.section import Template


class TestCCDA(unittest.TestCase):

    def test_document_templates(self):
        """
        Test that all supported CCDA DocumentType sections (identified by LOINC code) are implemented by a CCDA section template.
        :return:
        """
        for doc_type in ccda.DocumentType:
            doc_class = ccda.get_document_class(doc_type)

            for section in list(doc_class):
                template = ccda.section_template_map.get(section.value)

                self.assertTrue(isinstance(template, Template))