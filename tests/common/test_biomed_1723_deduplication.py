import json
import unittest
from text2phenotype.common.deduplication import AllRanges
from text2phenotype.common.deduplication import duplicate_ranges


class TestAllRangesClass(unittest.TestCase):
    def test_empty_creation(self):
        all_ranges = AllRanges()
        self.assertEqual(all_ranges.ordered_ranges, [])

    def test_adding_explicitly(self):
        all_ranges = AllRanges()
        all_ranges.add_non_overlapping_range(0, (2, 10))
        all_ranges.add_non_overlapping_range(1, (20, 45))
        self.assertEqual(all_ranges.ordered_ranges, [(2, 10), (20, 45)])
        all_ranges.check_ordered_start_ranges()

    def test_adding_ranges_wou_index(self):
        all_ranges = AllRanges()
        all_ranges.add_range((15, 18))
        # assert everything matches
        all_ranges.check_ordered_start_ranges()

        all_ranges.add_range((17, 50))
        # assert everything matches
        all_ranges.check_ordered_start_ranges()

        self.assertEqual(all_ranges.ordered_ranges, [(15, 50)])

    def test_edge_case_1(self):
        all_ranges = AllRanges()
        all_ranges.add_range((15, 18))
        # assert everything matches
        all_ranges.check_ordered_start_ranges()

        all_ranges.add_range((18, 50))
        # assert everything matches
        all_ranges.check_ordered_start_ranges()

        self.assertEqual(all_ranges.ordered_ranges, [(15, 50)])

    def test_edge_case_2(self):
        all_ranges = AllRanges()
        all_ranges.add_range((15, 18))
        # assert everything matches
        all_ranges.check_ordered_start_ranges()

        all_ranges.add_range((16, 19))
        # assert everything matches
        all_ranges.check_ordered_start_ranges()

        self.assertEqual(all_ranges.ordered_ranges, [(15, 19)])

class TestDeduplicationFunction(unittest.TestCase):
    TEXT = "I am the lorax I speak for the trees. I speak for the trees for the trees have no tongues\n"
    MIN_SEGMENT_LEN = 20

    def test_non_duplicate_text(self):
        range_output = duplicate_ranges(self.TEXT, min_length=self.MIN_SEGMENT_LEN)
        self.assertEqual(range_output, [])
        # test json compatibility
        json_format = json.dumps(range_output)
        reloaded = json.loads(json_format)
        self.assertEqual(range_output, reloaded)

    def test_duplicated_text(self):
        range_output = duplicate_ranges(self.TEXT*3, min_length=self.MIN_SEGMENT_LEN)
        self.assertEqual(range_output, [(len(self.TEXT)-1, len(self.TEXT*3)-1)])
        # test json format
        json_format = json.dumps(range_output)
        reloaded = json.loads(json_format)
        self.assertEqual(range_output[0], tuple(reloaded[0]))

    def test_duplicated_insuficient_len(self):
        range_output = duplicate_ranges(self.TEXT*3)
        self.assertEqual(range_output, [])

    def test_non_existent_txt(self):
        range_output = duplicate_ranges('')
        self.assertEqual(range_output, [])




