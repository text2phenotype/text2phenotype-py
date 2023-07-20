import unittest

from text2phenotype.ocr.data_structures import OCRPageInfo, OCRCoordinate


class TestOCRDataStructures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.PAGE = 1
        cls.TEXT = "This is example text"
        cls.PNG_PATH = "/opt/text2phenotype/example/path.png"
        
        cls.EXAMPLE_COORD_DICTS = [
            {'text': 'This', 'page': 1, 'top': 1, 'right': 2, 'bottom': 3,
             'left': 4, 'phi_type': 'example1', 'phi_score': 0.10},
            {'text': 'is', 'page': 1, 'top': 6, 'right': 7, 'bottom': 8,
             'left': 9, 'phi_type': 'example2', 'phi_score': 0.20},
            {'text': 'example', 'page': 1, 'top': 10, 'right': 11, 'bottom': 12,
             'left': 13, 'phi_type': 'example3', 'phi_score': 0.30},
            {'text': 'text', 'page': 1, 'top': 14, 'right': 15, 'bottom': 16,
             'left': 17, 'phi_type': 'example4', 'phi_score': 0.40},
        ]
    
    def test_ocr_page_info_from_dict(self):

        test_dict = {'page': self.PAGE, 'text': self.TEXT,
                     'png_path': self.PNG_PATH}

        page_info = OCRPageInfo.from_dict(test_dict)

        self.assertEqual(page_info.page, self.PAGE)
        self.assertEqual(page_info.text, self.TEXT)
        self.assertEqual(page_info.png_path, self.PNG_PATH)
        self.assertEqual(page_info.coordinates, [])
    
    def test_ocr_page_info_from_dict_no_png_path(self):
        test_dict = {'page': self.PAGE, 'text': self.TEXT}

        page_info = OCRPageInfo.from_dict(test_dict)

        self.assertEqual(page_info.page, self.PAGE)
        self.assertEqual(page_info.text, self.TEXT)
        self.assertIsNone(page_info.png_path)
        self.assertEqual(page_info.coordinates, [])

    def test_ocr_page_info_to_dict(self):
        page_info = OCRPageInfo(text=self.TEXT, png_path=self.PNG_PATH,
                                page=self.PAGE)
        page_dict = page_info.to_dict()
        
        self.assertEqual(page_dict['page'], self.PAGE)
        self.assertEqual(page_dict['text'], self.TEXT)
        self.assertEqual(page_dict['png_path'], self.PNG_PATH)
        self.assertEqual(page_dict['coordinates'], [])

    def test_ocr_page_info_to_dict_from_dict_with_coords(self):
        page_info = OCRPageInfo(text=self.TEXT, png_path=self.PNG_PATH,
                                page=self.PAGE)

        for coord_dict in self.EXAMPLE_COORD_DICTS:
            coord = OCRCoordinate(text=coord_dict['text'],
                                  page=coord_dict['page'],
                                  top=coord_dict['top'],
                                  right=coord_dict['right'],
                                  bottom=coord_dict['bottom'],
                                  left=coord_dict['left'],
                                  phi_score=coord_dict['phi_score'],
                                  phi_type=coord_dict['phi_type'])
            page_info.coordinates.append(coord)

        test_dict = page_info.to_dict()
        page_info_test = OCRPageInfo.from_dict(test_dict)

        self.assertEqual(page_info.text, page_info_test.text)
        self.assertEqual(page_info.page, page_info_test.page)
        self.assertEqual(page_info.png_path, page_info_test.png_path)
        for co1, co2 in zip(page_info.coordinates, page_info_test.coordinates):
            self.assertEqual(co1.text, co2.text)
            self.assertEqual(co1.page, co2.page)
            self.assertEqual(co1.top, co2.top)
            self.assertEqual(co1.right, co2.right)
            self.assertEqual(co1.bottom, co2.bottom)
            self.assertEqual(co1.left, co2.left)
            self.assertEqual(co1.phi_type, co2.phi_type)
            self.assertEqual(co1.phi_score, co2.phi_score)

    def test_ocr_coordinate_to_dict(self):
        coord = OCRCoordinate(text="This", page=1, top=1, right=2, bottom=3,
                              left=4, phi_type="name", phi_score=0.87)
        test_dict = coord.to_dict()

        self.assertEqual(coord.text, test_dict['text'])
        self.assertEqual(coord.page, test_dict['page'])
        self.assertEqual(coord.top, test_dict['top'])
        self.assertEqual(coord.right, test_dict['right'])
        self.assertEqual(coord.bottom, test_dict['bottom'])
        self.assertEqual(coord.left, test_dict['left'])
        self.assertEqual(coord.phi_type, test_dict['phi_type'])
        self.assertEqual(coord.phi_score, test_dict['phi_score'])

    def test_ocr_coordinate_from_dict(self):
        test_dict = {'text': 'This', 'page': 1, 'top': 1, 'right': 2,
                     'bottom': 3, 'left': 4, 'phi_type': 'name',
                     'phi_score': 0.87}
        coord = OCRCoordinate.from_dict(test_dict)

        self.assertEqual(coord.text, test_dict['text'])
        self.assertEqual(coord.page, test_dict['page'])
        self.assertEqual(coord.top, test_dict['top'])
        self.assertEqual(coord.right, test_dict['right'])
        self.assertEqual(coord.bottom, test_dict['bottom'])
        self.assertEqual(coord.left, test_dict['left'])
        self.assertEqual(coord.phi_type, test_dict['phi_type'])
        self.assertEqual(coord.phi_score, test_dict['phi_score'])
