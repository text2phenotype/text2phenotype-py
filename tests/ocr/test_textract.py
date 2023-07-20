import os
import tempfile
import unittest

from text2phenotype.common import common
from text2phenotype.ocr import textract
from text2phenotype.constants.common import OCR_PAGE_SPLITTING_KEY
from tests.ocr.fixtures import OCR_FIXTURES_DIR


class TestTextract(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.json_path = os.path.join(
            OCR_FIXTURES_DIR,
            "biomed_636_files/stephan_garcia/stephan-garcia_textract.json"
        )
        cls.textract_json = common.read_json(cls.json_path)

    def test_textract_json_to_txt_specific_examples(self):
        # This test is a generic test that examines the WHOLE text output for a file
        # Any discrepancies seen here are a result of something changing in raw text layout
        examples = [
            "biomed_636_files/stephan_garcia/stephan-garcia_textract.json",
            "biomed_636_files/Sample_MR_Jane_Doe/Sample_MR_Jane_Doe_textract.json",
            "biomed_636_files/sample_report1/sample_report1_textract.json",
            "biomed_636_files/sample_report2/sample_report2_textract.json",
            "steve_apple_concat/steve_apple_textract.json",
        ]
        for json_file in examples:
            json_path = os.path.join(
                OCR_FIXTURES_DIR,
                json_file
            )
            textract_json = common.read_json(json_path)
            txt = textract.textract_json_to_txt(textract_json)
            expected_text_path = json_path.replace(".json", ".txt")
            expected_text = common.read_text(expected_text_path)

            # shouldn't end with the page break character
            self.assertFalse(txt[-1] == OCR_PAGE_SPLITTING_KEY[0])
            self.assertEqual(expected_text, txt)

    def test_textract_json_to_txt_specific_examples_lines_only(self):
        # This test is a generic test that examines the WHOLE text output for a file
        # Any discrepancies seen here are a result of something changing in raw text layout
        examples = [
            "biomed_636_files/stephan_garcia/stephan-garcia_textract.json",
            "biomed_636_files/Sample_MR_Jane_Doe/Sample_MR_Jane_Doe_textract.json",
            "biomed_636_files/sample_report1/sample_report1_textract.json",
            "biomed_636_files/sample_report2/sample_report2_textract.json",
            "steve_apple_concat/steve_apple_textract.json",
        ]
        for json_file in examples:
            json_path = os.path.join(
                OCR_FIXTURES_DIR,
                json_file
            )
            textract_json = common.read_json(json_path)
            txt = textract.textract_json_to_txt(textract_json, lines_only=True)
            expected_text_path = json_path.replace(".json", "_lines.txt")
            if not os.path.exists(expected_text_path):
                common.write_text(txt, expected_text_path)
            expected_text = common.read_text(expected_text_path)

            # shouldn't end with the page break character
            self.assertFalse(txt[-1] == OCR_PAGE_SPLITTING_KEY[0])
            self.assertEqual(expected_text, txt)

    def test_tables_to_csv(self):
        doc = textract.textract_doc(self.textract_json)
        temp_file = tempfile.NamedTemporaryFile(suffix='.csv')
        out_path = textract.tables_to_csv(doc, temp_file.name)
        self.assertEqual(temp_file.name, out_path)
        assert os.path.isfile(out_path)

        expected_text = """PAGE 0,TABLE 0
General Risk Factors: ,Hypertension Exams/Tests: 
Lifestyle Tobacco: ,"50 pack years, but only smoking a few cigarettes a day for past year. "
Coffee: ,
Alcohol: ,"Moderate alcohol, several hard liquor drinks weekly, does not drink to excess. "
Recreational Drugs: ,
Counseling: ,
Exercise Patterns: ,Exercise history: minimal in the last 5 years. 
Hazardous Activities: ,
Other Additional History: ,Family history of prostate cancer and melanoma. 
"""
        self.assertEqual(expected_text, common.read_text(out_path))

    def test_table_to_text(self):
        doc = textract.textract_doc(self.textract_json)
        table_text = textract.table_to_text(doc.pages[0].tables[0], delimiter="|")
        expected_text = """General Risk Factors: |Hypertension Exams/Tests: 
Lifestyle Tobacco: |50 pack years, but only smoking a few cigarettes a day for past year. 
Coffee: |
Alcohol: |Moderate alcohol, several hard liquor drinks weekly, does not drink to excess. 
Recreational Drugs: |
Counseling: |
Exercise Patterns: |Exercise history: minimal in the last 5 years. 
Hazardous Activities: |
Other Additional History: |Family history of prostate cancer and melanoma. 
"""
        self.assertEqual(expected_text, table_text)

    def test_get_position_sort_key(self):
        object_list = [
            ('table_0', 0.36376217007637024, 0.06130549684166908, 0.07929789274930954),
            ('table_1', 0.362998366355896, 0.6146767139434814, 0.08099181950092316),
            ('table_2', 0.3624182641506195, 0.35771676898002625, 0.08048401027917862)]
        output = [textract._get_position_sort_key(item) for item in object_list]
        expected = [
            (0.36, 0.06130549684166908),
            (0.36, 0.6146767139434814),
            (0.36, 0.35771676898002625)]
        self.assertEqual(expected, output)

        # check the sort behavior itself
        expected_table_order = ['table_0', 'table_2', 'table_1']
        table_order = [item[0] for item in sorted(object_list, key=textract._get_position_sort_key)]
        self.assertEqual(expected_table_order, table_order)


if __name__ == '__main__':
    unittest.main()
