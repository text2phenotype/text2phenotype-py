import unittest
import os

from text2phenotype.ccda import ccda
from text2phenotype.ccda import empi
from text2phenotype.ccda import summarize
from text2phenotype.common.errors import CCDAError
from text2phenotype.common.log import logger
from text2phenotype.common import common
from text2phenotype.constants.environment import Environment
from text2phenotype.ccda.ccda import __ccda_samples__

class TestCCDA(unittest.TestCase):
    """
    text2phenotype-samples is required to run these unit tests.
    """
    CCDA_SAMPLES = os.path.join(Environment.TEXT2PHENOTYPE_SAMPLES_PATH.value, 'ccda')

    @unittest.skip("https://git.text2phenotype.com/data-management/nlp/text2phenotype-samples.git")
    def test_process_ccda_samples(self):
        """
        Test parsing 3,000+ 'standard' samples from multiple EMR vendors.
        Provides good functional test coverage of CCDA parsing
        """
        ccda.process_ccda_samples(self.CCDA_SAMPLES)

    @unittest.skip("https://r.details.loinc.org/LOINC/75323-6.html?sections=Comprehensive")
    def test_get_loinc_codes(self):
        """
        Test that every 'section' in the CCDA samples is known to the CCDA DocumentType.
        """
        for vendor in __ccda_samples__:
            for sample_xml in common.get_file_list(os.path.join(self.CCDA_SAMPLES, vendor), '.xml'):

                # logger.debug(sample_xml)

                for code, displayName in ccda.get_loinc_codes(sample_xml).items():
                    template = ccda.section_template_map.get(code)

                    if template is None:
                        raise CCDAError("[ %s ] no template [ '%s',  # %s] " % (sample_xml, code, displayName) )

                    doc_type    = ccda.get_document_type(sample_xml)
                    doc_class   = ccda.get_document_class(doc_type)
                    doc_sections= [entry.value for entry in list(doc_class)]

                    if code not in doc_sections:
                        logger.error('[doc_type %s ] [doc_class %s ] ' % (doc_type, doc_class))
                        raise CCDAError("[ %s ] missing[ '%s',  # %s] " % (sample_xml, code, displayName) )

    @unittest.skip("https://git.text2phenotype.com/data-management/nlp/text2phenotype-samples.git")
    def test_ccda2summary_file(self, sample_xml=os.path.join(Environment.TEXT2PHENOTYPE_SAMPLES_PATH.value, 'ccda', 'HL7', 'stephan-garcia-ccda.xml')):
        """
        Test that we can write a simple summary of CCDA XML content.
        """
        logger.debug(sample_xml)
        res = summarize.ccda2summary(sample_xml)
        common.write_json(res, sample_xml+'.summary.json')

    @unittest.skip("https://git.text2phenotype.com/data-management/nlp/text2phenotype-samples.git")
    def test_ccda2summary_bulk(self):
        """
        Test that we can write a simple summary of CCDA XML content.
        """
        for vendor in __ccda_samples__:
            for sample_xml in common.get_file_list(os.path.join(Environment.TEXT2PHENOTYPE_SAMPLES_PATH.value, 'ccda', vendor), '.xml'):
                self.test_ccda2summary_file(sample_xml)

    @unittest.skip("https://git.text2phenotype.com/data-management/nlp/text2phenotype-samples.git")
    def test_ccda_empi_patient_demographics_bulk(self):
        """
        Test extraction of basic patient demographics for all CCDA samples.
        """
        for vendor in ccda.__ccda_samples__:
            for xml_file in common.get_file_list(os.path.join(Environment.TEXT2PHENOTYPE_SAMPLES_PATH.value, 'ccda', vendor), '.xml'):
                self.test_ccda_empi_patient_demographics_file(xml_file)

    @unittest.skip("https://git.text2phenotype.com/data-management/nlp/text2phenotype-samples.git")
    def test_ccda_empi_patient_demographics_file(self, xml_file=os.path.join(Environment.TEXT2PHENOTYPE_SAMPLES_PATH.value, 'ccda', 'HL7', 'CCDA.sample.xml')):
        """
        Test extraction of bare-minimum demographics data
        :param xml_file:
        :return: Demographics
        """
        root = ccda.parse(xml_file)
        dem  = empi.get_demographics(root)

        self.assertIsNotNone(dem.sex)
        self.assertIsNotNone(dem.dob)

        common.write_json(dem.__dict__, xml_file+'.demographics.json')

        return dem
