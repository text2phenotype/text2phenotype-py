from bisect import bisect_left
import re

from text2phenotype.constants.environment import Environment


class AllRanges:
    # this is a class to store all unique range objects effectively and combine them as they get added
    def __init__(self):
        self.ordered_ranges = []

    # make sure start_ranges are ordered
    def check_ordered_start_ranges(self):
        old_start = -1
        for i in self.ordered_ranges:
            if i[0] <= old_start:
                raise ValueError('Start ranges are not ordered')
            old_start = i[0]

    # type check indexes being passed
    def assert_valid_index(self, index):
        if not isinstance(index, int):
            raise ValueError(f'Provided index: {index} is not an integer')
        if index > len(self.ordered_ranges):
            raise ValueError(f'Provided index {index} is outside the range for current ranges '
                             f'size = {len(self.ordered_ranges)}')

    # type check ranges being passed in
    @staticmethod
    def assert_valid_range(input_range):
        if not input_range or len(input_range) != 2:
            raise ValueError(f'Provided new_range must be a list or tuple of length 2, was {input_range}')
        if input_range[1] <= input_range[0]:
            raise ValueError(f'Provided new_range {input_range} has len <= 0')

    # when provided with the index where a new range should be inserted, insert the range and start position
    def add_non_overlapping_range(self, index, new_range):
        # input type checking
        self.assert_valid_range(new_range)
        self.assert_valid_index(index)

        # insert the values
        self.ordered_ranges.insert(index, new_range)

    # given a new range, find the current range_index for which the new range would start before it (or if there is
    # overlap such that the new range would be included at the tail end of the range 1 before this return that value)
    def get_start_index(self, new_range):
        index = bisect_left(self.ordered_ranges, new_range)
        if index > 0 and new_range[0] <= self.ordered_ranges[index - 1][1]:
            return index - 1
        else:
            return index

    def remove_index(self, index):
        self.assert_valid_index(index)

        self.ordered_ranges.pop(index)

    # get the index of ranges that the new range must end before
    def get_end_index(self, new_range):
        index = bisect_left(self.ordered_ranges, (new_range[1], None))
        return index

    def check_not_range_enclosed(self, start_idx, end_idx, new_range):
        # if the new range is wholly included within a range already measured, don't change anything
        return not (end_idx == start_idx + 1 and new_range[0] >= self.ordered_ranges[start_idx][0] and
                    new_range[1] <= self.ordered_ranges[end_idx - 1][1])

    def add_range(self, new_range):
        start_idx = self.get_start_index(new_range)
        end_idx = self.get_end_index(new_range)
        if self.check_not_range_enclosed(start_idx, end_idx, new_range):
            # this means that the range will get combined with at least one already existing range
            if end_idx != start_idx:
                # get the full new range
                new_range = (min(self.ordered_ranges[start_idx][0], new_range[0]),
                             max(self.ordered_ranges[end_idx - 1][1], new_range[1]))

                # delete all currently existing overlaping ranges that will be included in the new range
                for i in range(end_idx - 1, start_idx - 1, -1):
                    self.remove_index(i)
            # add the new_range
            self.add_non_overlapping_range(start_idx, new_range)


def getsubs(txt, all_new_lines, new_lines_idx, max_length=2000, min_length=800):
    loc = all_new_lines[new_lines_idx]
    i = min(loc + max_length, len(txt))
    min_index = bisect_left(all_new_lines, min(loc + min_length, len(txt)), )
    max_index = bisect_left(all_new_lines, i)
    if loc + min_length >= len(txt):
        yield txt[loc:], loc, len(txt)
    for k in range(min_index, max_index):
        substr = txt[loc: all_new_lines[k]]
        if all_new_lines[k] - loc < min_length:
            raise ValueError('Substring length less than allowed length')
        if all_new_lines[k] - loc > max_length:
            raise ValueError('Substring length greater than maximum permitted segment length')
        yield substr, loc, all_new_lines[k]


def index_all_newlines(txt):
    return [match.span()[0] for match in re.finditer('\n', txt)]


def get_max_distance_between_new_lines(new_lines_indexes):
    max_len = 0
    for i in range(1, len(new_lines_indexes)):
        max_len = max(max_len, new_lines_indexes[i] - new_lines_indexes[i - 1])
    return max_len


def duplicate_ranges(txt, min_length=Environment.MIN_DUPLICATE_SEGMENT_LEN.value, buffer_len=10):
    """
    :param txt: the full text of a document
    :param min_length: the minimum segment length that can be considered duplicate (length is in characters),
    a valid segment must begin and end with \n. This is to ensure that we are not randomly splitting the text in the
    middle of a paragraph
    :param buffer_len: a buffer to add around the max_length to make sure new lines are included
    :return: A list of tuples of ranges of the text that are duplicates
    The run time of this function varies with min_length, the smaller the min length the more segments to check with a
    min length between 600-800 chars 1MB of text took <1s to process. This function will only find exact matches and is
    case and punctuation sensitive.
    """
    duplicated_ranges = AllRanges()
    substrings = set()
    # find all new lines first then only loop over those (rather than running n2 on the whole text)
    all_newlines = index_all_newlines(txt)
    if len(all_newlines) > 0 and len(txt) > 0:
        first_seq_idx = bisect_left(all_newlines, min_length)
        if first_seq_idx < len(all_newlines):
            substrings.add('\n' + txt[0:all_newlines[first_seq_idx]])
    # this calculation ensures that all segments sandwiched between new lines will be checked for duplication
    max_length = min_length + get_max_distance_between_new_lines(all_newlines) + buffer_len
    # looping through all the new line locations
    for k in range(len(all_newlines)):
        if all_newlines[k] + min_length < len(txt):
            # get all valid segments that are of length > min length and < max length
            for sub, loc, j in getsubs(txt, all_newlines, k, max_length=max_length, min_length=min_length):
                # if the segment has been seen before, add the range of the segment to our AllRanges object
                if sub in substrings:
                    duplicated_ranges.add_range((loc, j))

                # otherwise add to our set of substrings that will get checked on subsequent runs
                else:
                    substrings.add(sub)

    return duplicated_ranges.ordered_ranges
