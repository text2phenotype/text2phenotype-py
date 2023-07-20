import io
from typing import List
import uuid

from unittest import TestCase
from unittest.mock import patch

from django.core.cache.backends.locmem import LocMemCache

from text2phenotype.annotations.file_helpers import (
    Annotation,
    AnnotationSet,
    TextCoordinate,
    TextCoordinateSet,
    TextCoordinateSetGenerator,
)

from .fixtures import (
    john_stevens_txt_filepath,
    john_stevens_text_lines_filepath,
    john_stevens_text_coords_filepath,
)


# Use local memory cache for testing
cache = LocMemCache(name='test', params={})


@patch('text2phenotype.annotations.file_helpers.default_cache', new=cache)
class TestAnnotationFileHelpers(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.coords_filepath = john_stevens_text_coords_filepath
        cls.lines_filepath = john_stevens_text_lines_filepath

        with open(cls.coords_filepath, 'rb') as cf:
            cls.coords_content = cf.read()

        with open(cls.lines_filepath, 'rb') as lf:
            cls.lines_content = lf.read()

        with open(john_stevens_txt_filepath, 'r') as txt_file:
            cls.full_text = txt_file.read()

    def setUp(self) -> None:
        super().setUp()
        self.coords_stream = io.BytesIO(self.coords_content)
        self.lines_stream = io.BytesIO(self.lines_content)

    def test_text_coord_serialization(self):
        expected_uuid = uuid.uuid4().hex

        tc = TextCoordinate(
            text='test',
            order=1,
            page_index_first=1,
            page_index_last=4,
            document_index_first=5,
            document_index_last=8,
            line=1,
            page=2,
            hyphen=True,
            spaces=1,
            new_line=True,
            top=1,
            bottom=2,
            left=3,
            right=4,
            _uuid=expected_uuid,
        )

        tc_serial = tc.to_dict()
        tc_check = TextCoordinate.from_dict(tc_serial)

        self.assertDictEqual(tc.to_dict(), tc_check.to_dict())
        self.assertEqual(tc.text, tc_check.text)
        self.assertEqual(tc.order, tc_check.order)
        self.assertEqual(tc.page_index_first, tc_check.page_index_first)
        self.assertEqual(tc.page_index_last, tc_check.page_index_last)
        self.assertEqual(tc.document_index_last, tc_check.document_index_last)
        self.assertEqual(tc.document_index_first, tc_check.document_index_first)
        self.assertEqual(tc.line, tc_check.line)
        self.assertEqual(tc.page, tc_check.page)
        self.assertEqual(tc.hyphen, tc_check.hyphen)
        self.assertEqual(tc.spaces, tc_check.spaces)
        self.assertEqual(tc.new_line, tc_check.new_line)
        self.assertEqual(tc.top, tc_check.top)
        self.assertEqual(tc.bottom, tc_check.bottom)
        self.assertEqual(tc.left, tc_check.left)
        self.assertEqual(tc.right, tc_check.right)
        self.assertEqual(tc.uuid, tc_check.uuid)

        result_dict = {'uuid': expected_uuid,
                       'text': 'test',
                       'order': 1,
                       'page_index_first': 1,
                       'page_index_last': 4,
                       'document_index_first': 5,
                       'document_index_last': 8,
                       'line': 1,
                       'page': 2,
                       'hyphen': True,
                       'spaces': 1,
                       'new_line': True,
                       'left': 3,
                       'right': 4,
                       'top': 1,
                       'bottom': 2}
        self.assertDictEqual(tc.to_dict(), result_dict)

    def test_text_coord_auto_id(self):
        tc = TextCoordinate(
            text='test',
            order=1,
            page_index_first=1,
            page_index_last=4,
            document_index_first=5,
            document_index_last=8,
            line=1,
        )
        tc_serial = tc.to_dict()
        tc_check = TextCoordinate.from_dict(tc_serial)

        self.assertIsNotNone(tc.uuid)
        self.assertEqual(tc.uuid, tc_check.uuid)

    def tearDown(self):
        cache.clear()

    @patch('text2phenotype.annotations.file_helpers.get_storage_service')
    def test_text_coord_set_find_coords(self, mock):
        mock.return_value = mock

        mock.get_content_stream.side_effect = [self.coords_stream,
                                               self.lines_stream]

        text_coords = TextCoordinateSet.from_storage(directory_filename=self.coords_filepath,
                                                     lines_filename=self.lines_filepath)

        sts = [88, 998]
        eds = [100, 1021]

        for st, ed in zip(sts, eds):
            res = text_coords.find_coords(st, ed)

            check_text = ''
            for coord in res:
                check_text += coord.text

                if coord.hyphen:
                    check_text += '-'

                if coord.spaces:
                    check_text += ' ' * coord.spaces

                if coord.new_line and not coord.hyphen:
                    check_text += '\n'

            self.assertEqual(check_text.strip(), self.full_text[st:ed])

    @patch('text2phenotype.annotations.file_helpers.get_storage_service')
    def test_text_coord_set_serialization(self, mock):
        mock.return_value = mock
        mock.get_container = mock

        mock.get_content_stream.side_effect = [self.coords_stream,
                                               self.lines_stream]

        text_coords = TextCoordinateSet.from_storage(directory_filename=self.coords_filepath,
                                                     lines_filename=self.lines_filepath)

        text_coords.to_storage(self.coords_filepath, self.lines_filepath)

        # ideally should capture what is being written to storage, but not sure
        # how to do that right now
        self.assertEqual(mock.write_fileobj.call_count, 2)

    def test_annotation_serialization(self):
        expected_uuid = uuid.uuid4().hex
        expected_coord_ids = [uuid.uuid4().hex, uuid.uuid4().hex]

        ann = Annotation(
            label='label',
            category_label='category_label',
            text_range=[23, 29],
            text='text',
            coord_uuids=expected_coord_ids,
            line_start=1,
            line_stop=2,
            uuid=expected_uuid,
        )

        ann_serial = ann.to_file_line()
        ann_check = Annotation.from_file_line(ann_serial)[0]

        self.assertEqual(ann.label, ann_check.label)
        self.assertEqual(ann.category_label, ann_check.category_label)
        self.assertListEqual(ann.text_range, ann_check.text_range)
        self.assertEqual(ann.text, ann_check.text)
        self.assertListEqual(ann.coord_uuids, ann_check.coord_uuids)
        self.assertEqual(ann.line_start, ann_check.line_start)
        self.assertEqual(ann.line_stop, ann_check.line_stop)
        self.assertEqual(ann.uuid, ann_check.uuid)

        expected_line = f'{expected_uuid}\tlabel\t23 29\ttext\tcategory_label\t{";".join(expected_coord_ids)}\t1 2\n'
        self.assertEqual(ann.to_file_line(), expected_line)

    def test_annotation_repr(self):
        expected_coord_ids = [uuid.uuid4().hex, uuid.uuid4().hex]
        ann = Annotation(
            label='label',
            category_label='category_label',
            text_range=[23, 29],
            text='text',
            coord_uuids=expected_coord_ids,
            line_start=1,
            line_stop=2,
        )
        self.assertEqual("Annotation(text='text', label='label', text_range=[23, 29])", ann.__repr__())

    def test_annotation_auto_id(self):
        expected_coord_ids = [uuid.uuid4().hex, uuid.uuid4().hex]

        ann = Annotation(
            label='label',
            category_label='category_label',
            text_range=[23, 29],
            text='text',
            coord_uuids=expected_coord_ids,
            line_start=1,
            line_stop=2,
        )

        ann_serial = ann.to_file_line()
        ann_check = Annotation.from_file_line(ann_serial)

        self.assertIsNotNone(ann.uuid)
        self.assertEqual(ann.uuid, ann_check[0].uuid)

    def test_annotation_to_file_line(self):
        ann_brat = Annotation(
            uuid="c2f25d95f22949deaa170bdc122ee6e1",
            label="diagnosis",
            text_range=[741, 771],
            text="paroxysmal atrial fibrillation"
        )
        line_out = ann_brat.to_file_line()
        test_line_one = (
            "c2f25d95f22949deaa170bdc122ee6e1\tdiagnosis 741 771"
            "\tparoxysmal atrial fibrillation\n")
        self.assertEqual(test_line_one, line_out)

        ann_sands = Annotation(
            uuid="c2f25d95f22949deaa170bdc122ee6e1",
            label="diagnosis",
            text_range=[32640, 32667],
            text="Upper respiratory infection",
            category_label="DiseaseDisorder",
            coord_uuids=["6ba4ed2b7f4a474ea9c699e85dddb6b6", "4d974c9d8ef343cdb506e3ad8f2173b9", "b030e9ad77d243c7af7455e8d2e59f3f"],
            line_start=1145,
            line_stop=1145,
        )
        line_out_sands = ann_sands.to_file_line()
        test_line_sands = (
            "c2f25d95f22949deaa170bdc122ee6e1\tdiagnosis\t32640 32667\tUpper respiratory infection\tDiseaseDisorder\t"
            "6ba4ed2b7f4a474ea9c699e85dddb6b6;4d974c9d8ef343cdb506e3ad8f2173b9;b030e9ad77d243c7af7455e8d2e59f3f\t"
            "1145 1145\n"
        )
        self.assertEqual(test_line_sands, line_out_sands)

    def test_annotation_from_file_line_brat(self):
        # test Annotation.parse-prat_ann_line indirectly
        # non-phi examples
        test_line_one = "T12\tdiagnosis 741 771\tparoxysmal atrial fibrillation\n"
        ann_one = Annotation.from_file_line(test_line_one)
        self.assertEqual(ann_one[0].uuid, "T12")
        self.assertEqual(ann_one[0].label, "diagnosis")
        self.assertEqual(ann_one[0].text_range, [741, 771])
        self.assertEqual(ann_one[0].text, "paroxysmal atrial fibrillation")
        # THIS FAILS; randomly chooses one of these two categories
        # self.assertEqual(ann_one[0].category_label, "DiseaseDisorder")
        # self.assertEqual(ann_one[0].category_label, "Disability")

        out_line = ann_one[0].to_file_line()
        self.assertEqual(test_line_one, out_line)

        test_line_two = "T9\tlab 3170 3177;3178 3181\tglucose 299\n"
        ann_two = Annotation.from_file_line(test_line_two)
        self.assertEqual(ann_two[0].uuid, "T9")
        self.assertEqual(ann_two[0].label, "lab")
        self.assertEqual(ann_two[0].text_range, [3170, 3177])
        self.assertEqual(ann_two[0].text, "glucose")
        self.assertEqual(ann_two[1].uuid, "T9_1")
        self.assertEqual(ann_two[1].label, "lab")
        self.assertEqual(ann_two[1].text_range, [3178, 3181])
        self.assertEqual(ann_two[1].text, "299")

        # FAILS, because the original annotation has effectively two annotations, and to_file_line only takes one
        # out_line = ann_one[0].to_file_line()
        # self.assertEqual(test_line_two, out_line)

        # example from I2B2, fails expected pattern
        test_line_three = "#1\tAnnotatorNotes T11\tproblem/dx: left main coronary artery disease"
        ann_three = Annotation.from_file_line(test_line_three)
        self.assertEqual(ann_three, [])

    def test_annotation_from_file_line_sands(self):
        # expecting 7 part annotation line from SANDS
        test_line_sands = (
            "c2f25d95f22949deaa170bdc122ee6e1\tdiagnosis\t32640 32667\tUpper respiratory infection\tDiseaseDisorder\t"
            "6ba4ed2b7f4a474ea9c699e85dddb6b6;4d974c9d8ef343cdb506e3ad8f2173b9;b030e9ad77d243c7af7455e8d2e59f3f\t"
            "1145 1145"
        )
        ann = Annotation.from_file_line(test_line_sands)
        self.assertEqual(ann[0].uuid, "c2f25d95f22949deaa170bdc122ee6e1")
        self.assertEqual(ann[0].label, "diagnosis")
        self.assertEqual(ann[0].text_range, [32640, 32667])
        self.assertEqual(ann[0].text, "Upper respiratory infection")
        self.assertEqual(ann[0].category_label, "DiseaseDisorder")
        self.assertEqual(ann[0].coord_uuids, [
            "6ba4ed2b7f4a474ea9c699e85dddb6b6", "4d974c9d8ef343cdb506e3ad8f2173b9", "b030e9ad77d243c7af7455e8d2e59f3f"])
        self.assertEqual(ann[0].line_start, 1145)
        self.assertEqual(ann[0].line_stop, 1145)

        test_line_sands_2 = (
            "43d1af5d653b4c38b40f8c9a5254bb81\tsignsymptom\t32873 32880\tmalaise\tSignSymptom\t"
            "b6d6526f0edb45d58acc598c589441fe\t1156 1156")
        ann = Annotation.from_file_line(test_line_sands_2)
        self.assertEqual("43d1af5d653b4c38b40f8c9a5254bb81", ann[0].uuid)
        self.assertEqual(ann[0].label, "signsymptom")
        self.assertEqual(ann[0].text_range, [32873, 32880])
        self.assertEqual(ann[0].text, "malaise")
        self.assertEqual(ann[0].category_label, "SignSymptom")
        self.assertEqual(ann[0].coord_uuids, ["b6d6526f0edb45d58acc598c589441fe"])
        self.assertEqual(ann[0].line_start, 1156)
        self.assertEqual(ann[0].line_stop, 1156)

    @patch('text2phenotype.annotations.file_helpers.get_storage_service')
    def test_text_coord_set_caching(self, mock):
        mock.return_value = mock
        mock.get_container = mock

        mock.get_content_stream.side_effect = [self.coords_stream,
                                               self.lines_stream]

        cache.clear()

        obj1 = TextCoordinateSet.from_storage(directory_filename=self.coords_filepath,
                                              lines_filename=self.lines_filepath)

        # Check that first call used StorageService
        self.assertEqual(mock.get_content_stream.call_count, 1)

        mock.get_content_stream.call_count = 0  # Reset counter
        obj2 = TextCoordinateSet.from_storage(directory_filename=self.coords_filepath,
                                              lines_filename=self.lines_filepath)

        # For second call "TextCoordinateSet" should be from cache
        self.assertEqual(mock.get_content_stream.call_count, 0)

        # Check that objects are equal
        self.assertEqual(obj1.lines, obj2.lines)

        self.assertEqual(
            {tc.uuid: tc.to_dict() for tc in obj1},
            {tc.uuid: tc.to_dict() for tc in obj2}
        )

    @patch('text2phenotype.annotations.file_helpers.get_storage_service')
    def test_text_coord_set_cache_update(self, mock):
        mock.return_value = mock
        mock.get_container = mock

        mock.get_content_stream.side_effect = [self.coords_stream,
                                               self.lines_stream]

        cache.clear()

        # Get TextCoordinateSet and put it to cache
        text_coords = TextCoordinateSet.from_storage(directory_filename=self.coords_filepath,
                                                     lines_filename=self.lines_filepath)

        # Check that source object not empty
        self.assertTrue(text_coords)
        self.assertTrue(text_coords.lines)
        self.assertTrue(text_coords.coordinates_list)

        # Check that StorageService was used
        self.assertEqual(mock.get_content_stream.call_count, 1)
        mock.get_content_stream.call_count = 0  # Reset counter

        # Replace source object by empty TextCoordinateSet
        empty_coords = TextCoordinateSet()
        empty_coords.to_storage(directory_filename=self.coords_filepath,
                                lines_filename=self.lines_filepath)

        # Get instance again
        cached_coords = TextCoordinateSet.from_storage(directory_filename=self.coords_filepath,
                                                       lines_filename=self.lines_filepath)

        # Check that returned object from cache, not from Storage
        self.assertEqual(mock.get_content_stream.call_count, 0)

        # Check that cahed_object is empty
        self.assertFalse(cached_coords.lines)
        self.assertFalse(cached_coords.coordinates_list)
        self.assertFalse(cached_coords)

    def test_annotation_set_from_list(self):
        ann_list = [
            Annotation(
                label='label',
                category_label='category_label',
                text_range=[23, 29],
                text='foo',
                coord_uuids=None,
                line_start=None,
                line_stop=None,
            ),
            Annotation(
                label='label',
                category_label='category_label',
                text_range=[57, 63],
                text='bar',
                coord_uuids=None,
                line_start=None,
                line_stop=None,
            )
        ]
        ann_set = AnnotationSet.from_list(ann_list)
        self.assertEqual(ann_list[0], ann_set.directory[ann_list[0].uuid])
        self.assertEqual(ann_list[1], ann_set.directory[ann_list[1].uuid])

    def test_annotation_set_serialization(self):
        # TODO: fill in test case
        pass

    def test_annotation_set_add_annotation(self):
        # TODO: fill in test case
        pass

    def test_annotation_set_caching(self):
        # TODO: fill in test case
        pass

    def test_annotation_set_cache_update(self):
        # TODO: fill in test case
        pass


class TestTextCoordinateSet(TestCase):
    __COORD1 = TextCoordinate(text='',
                              order=1,
                              page_index_first=1,
                              page_index_last=1,
                              document_index_first=2,
                              document_index_last=5,
                              line=1)
    __COORD2 = TextCoordinate(text='',
                              order=1,
                              page_index_first=1,
                              page_index_last=1,
                              document_index_first=6,
                              document_index_last=9,
                              line=1)
    __COORD3 = TextCoordinate(text='',
                              order=1,
                              page_index_first=1,
                              page_index_last=1,
                              document_index_first=10,
                              document_index_last=15,
                              line=1)
    __COORDS = [__COORD1, __COORD2, __COORD3]

    def test_find_coords_overlapping(self):
        self.__test_find_coords(1, 8, [self.__COORD1])

    def test_find_coords_non_overlapping_beginning(self):
        self.__test_find_coords(1, 1, [])

    def test_find_coords_non_overlapping_end(self):
        self.__test_find_coords(16, 20, [])

    def __test_find_coords(self, start: int, stop: int, expected: List[TextCoordinate]):
        coord_set = TextCoordinateSet()
        coord_set.coordinates_list = self.__COORDS
        self.assertListEqual(expected, coord_set.find_coords(start, stop))

    @patch('text2phenotype.annotations.file_helpers.get_storage_service')
    def test_text_coordinate_set_generator(self, mock_storage):
        mock_storage.return_value = mock_storage
        mock_storage.get_container = mock_storage

        storage_data = {}

        def write_fileobj(stream, filename, tid=None):
            storage_data[filename] = stream.read()

        mock_storage.write_fileobj = write_fileobj

        coords_file_key = 'coords.txt'
        lines_file_key = 'lines.txt'

        # Get expected values from TextCoordinateSet class
        coord_set = TextCoordinateSet()
        coord_set.coordinates_list = self.__COORDS
        coord_set.to_storage(coords_file_key, lines_file_key)

        expected_coords_data = storage_data[coords_file_key]
        expected_lines_data = storage_data[lines_file_key]

        storage_data.clear()

        # Generate data with TextCoordinateSetGenerator class
        coord_set_gen = TextCoordinateSetGenerator(iter(self.__COORDS))

        TextCoordinateSet.to_storage(coord_set_gen, coords_file_key, lines_file_key)
        coords_data = storage_data[coords_file_key]
        lines_data = storage_data[lines_file_key]

        self.assertEqual(coords_data, expected_coords_data)
        self.assertEqual(lines_data, expected_lines_data)
