import bisect
import itertools
import json

from functools import wraps
from hashlib import sha256
from io import IOBase
from typing import (
    Dict,
    Iterable,
    List,
    Optional,
    Union,
)
from uuid import uuid4

import ijson
import numpy
import pandas

from recordclass import dataobject

from django.core.cache import cache as default_cache
from django.core.exceptions import ImproperlyConfigured
from django.utils.decorators import classproperty

from text2phenotype.common.log import operations_logger
from text2phenotype.common.feature_data_parsing import is_digit
from text2phenotype.constants.common import VERSION_INFO_KEY
from text2phenotype.constants.features.label_types import (
    DuplicateDocumentLabel,
    LabelList,
)
from text2phenotype.services import get_storage_service


DOCUMENT_INDEX_FIRST = 'document_index_first'
DOCUMENT_INDEX_LAST = 'document_index_last'

DEFAULT_CACHE_TTL = 3600  # One hour


class _JsonListGenerator(list):
    def __init__(self, generator):
        generator = iter(generator or [])

        # Check, maybe iterator is empty
        try:
            first_elem = next(generator)
            self.append(1)  # The list should be initialized somehow
            self.generator = itertools.chain([first_elem], generator)
        except StopIteration:
            self.generator = []

    def __iter__(self):
        return iter(self.generator)


class _JsonDictGenerator(dict):
    def __init__(self, items_generator):
        super().__init__({1: 1})  # The dict should be initialized somehow
        self.generator = items_generator or {}

    def items(self):
        return iter(self.generator)


class _GeneratorBytesStream(IOBase):
    """BytesStream from str/bytes iterables"""
    def __init__(self, gen, encoding: str = None):
        self.iterator = iter(gen)
        self.buffer = bytearray()
        self.encoding = encoding or 'utf8'

    def __iter__(self):
        return self.iterator

    def readable(self):
        return True

    def writable(self):
        return False

    def seekable(self):
        return False

    def read(self, size: Optional[int] = -1) -> bytes:
        if size is None:
            size = -1

        if not size:
            return b''

        data = self.buffer

        while len(data) < size or size < 0:
            try:
                chunk = next(self.iterator)
                if not isinstance(chunk, bytes):
                    chunk = chunk.encode(self.encoding)

                data += chunk

            except StopIteration:
                break

        if size < 0:
            return data

        self.buffer = data[size:]
        return data[:size]


class _JsonGeneratorBytesStream(_GeneratorBytesStream):
    """BytesStream from JSON serializable objects"""
    def __init__(self, gen, encoding: str = None):
        gen = json.JSONEncoder().iterencode(gen)
        super().__init__(gen, encoding)


class Cache:
    __cache_backend = None

    @classproperty
    def cache_backend(cls):
        if cls.__cache_backend is None:
            try:
                # Check the default cache-backend is available
                default_cache.get('test')
            except ImproperlyConfigured:
                # In the case of non-django applications the "settings.CACHES" property will not be
                # configured properly and django-cache-framework will raise this exception.
                # We need to replace default "cache" at least with "DummyCache" for code-compatibility.
                from django.core.cache.backends.dummy import DummyCache
                cls.__cache_backend = DummyCache(host='', params={})
            else:
                cls.__cache_backend = default_cache

        return cls.__cache_backend

    @classmethod
    def __make_cache_key(cls, obj, args, kwargs, vary_on=None):
        if isinstance(obj, type):  # if decorated classmethod (`cls` argument)
            class_name = obj.__name__
        else:
            class_name = obj.__class__.__name__

        vary_on = vary_on or []
        vary = [kwargs.get(k) for k in vary_on]

        # "repr()" used to distinguish the None and 'None' in the string
        key = f'{class_name}_{repr(args)}_{repr(vary)}'

        # "sha256()" used because the length of cache-key limited to 250 characters
        # https://docs.djangoproject.com/en/1.11/topics/cache/#cache-key-warnings
        return sha256(key.encode('utf8')).hexdigest()

    @classmethod
    def cached(cls, vary_on=None, timeout=DEFAULT_CACHE_TTL):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                key = cls.__make_cache_key(self, args, kwargs, vary_on)
                cached_obj = cls.cache_backend.get(key)

                if cached_obj is not None:
                    return cached_obj
                else:
                    obj = func(self, *args, **kwargs)
                    cls.cache_backend.set(key, obj, timeout=timeout)
                    return obj

            return wrapper

        return decorator

    @classmethod
    def update(cls, vary_on=None, timeout=DEFAULT_CACHE_TTL):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                key = cls.__make_cache_key(self, args, kwargs, vary_on)

                # If object is not present in the cache no need to do update
                # We put an object to the cache only when "use_cache()" called
                if key in cls.cache_backend:
                    cls.cache_backend.set(key, self, timeout=timeout)

                return func(self, *args, **kwargs)

            return wrapper

        return decorator

    @classmethod
    def clear(cls, vary_on=None, timeout=DEFAULT_CACHE_TTL):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                key = cls.__make_cache_key(self, args, kwargs, vary_on)
                cls.cache_backend.delete(key)
                return func(self, *args, **kwargs)

            return wrapper

        return decorator


class AnnotationSet:

    def __init__(self):
        self.directory = {}

    def __len__(self):
        return len(self.entries)

    @property
    def entries(self) -> List['Annotation']:
        return list(self.directory.values())

    @entries.setter
    def entries(self, value: List['Annotation']):
        # when setting entries, ensure no old entries exist
        self.directory = dict()
        for entry in value:
            self.directory[entry.uuid] = entry

    @Cache.update()
    def to_storage(self, filename: str, tid: str = None) -> bool:
        output = ''
        for entry in self.entries:
            output += entry.to_file_line()

        client = get_storage_service().get_container()
        res = client.write_bytes(output.encode('utf-8'), filename, tid=tid)

        return res

    @classmethod
    @Cache.cached()
    def from_storage(cls, filename: str) -> 'AnnotationSet':
        # Needs bucket to be read from env?
        client = get_storage_service().get_container()
        content = client.get_object_content(filename).decode('utf-8')
        return cls.from_file_content(content)

    @classmethod
    def from_file_content(cls, content: str):
        lines = content.split('\n')

        res = cls()
        for line in lines:
            if not line:
                break

            annotations_list = Annotation.from_file_line(line)
            for ann in annotations_list:
                if ann.uuid in res.directory:
                    ann.uuid = uuid4().hex

                res.directory[ann.uuid] = ann

        return res

    @classmethod
    def from_list(cls, ann_list: list):
        """
        Create AnnotationSet from a list of Annotation objects
        """
        res = cls()
        for ann in ann_list:
            if ann.uuid in res.directory:
                ann.uuid = uuid4().hex
            res.directory[ann.uuid] = ann
        return res

    def to_file_content(self) -> str:
        output = ""
        for entry in sorted(self.entries, key=lambda x: x.text_range):
            output += entry.to_file_line()
        return output

    @classmethod
    @Cache.clear()
    def delete_storage_file(cls, filename: str) -> None:
        client = get_storage_service().get_container()
        obj = client.get_object(filename)
        client.delete_object(obj)

    def add_annotation(self, coord_uuids: List[str],
                       label: str, category_label: str,
                       text_coord_set: 'TextCoordinateSet') -> 'Annotation':

        text = ''
        line_start = line_stop = None
        range_start = range_stop = None
        for tc_id in coord_uuids:
            coord = text_coord_set[tc_id]

            if line_start is None:
                line_start = coord.line
            line_stop = coord.line

            if range_start is None:
                range_start = coord.document_index_first
            range_stop = coord.document_index_last + 1

            text += coord.text
            if coord.hyphen:
                text += '-'

            if coord.spaces:
                text += ' ' * coord.spaces

            if coord.new_line and not coord.hyphen:
                text += ' '

        # prevention saving text for the duplicate category
        if category_label == DuplicateDocumentLabel.get_category_label().persistent_label:
            text = ''

        ann = Annotation(label=label, text_range=[range_start, range_stop],
                         text=text, coord_uuids=coord_uuids, line_start=line_start,
                         line_stop=line_stop, category_label=category_label)
        self.directory[ann.uuid] = ann

        return ann

    def add_annotation_no_coord(
            self,
            label: str,
            text_range: List[int],
            text: str
    ):
        ann = Annotation(
            label=label,
            text_range=text_range,
            text=text,
            category_label=None,
            coord_uuids=None,
            line_start=None,
            line_stop=None
        )
        self.directory[ann.uuid] = ann  # is this dict sorted when we use entries?

    @classmethod
    def from_biomed_output_json(cls, biomed_output_json: Dict[str, List[dict]]):
        """

        :param biomed_output_json: Dictionary output (ie: the current format for all single biomed model workers,
        Category: List[Biomed output dictionarys of format {text:, range:, label:, ...}
        :return: AnnotationSet
        """
        res = cls()
        for category, annotations in biomed_output_json.items():
            if category == VERSION_INFO_KEY:
                continue
            for ann in annotations:
                ann_range = ann['range']
                ann_label = ann['label']
                ann_text = ann['text']
                entry = Annotation(
                    category_label=category,
                    label=ann_label,
                    text_range=ann_range,
                    text=ann_text
                )
                res.directory[entry.uuid] = entry
        return res

    @staticmethod
    def _is_in_entries(entries: list, label: str, text_range: List[int], text: str) -> bool:
        """
        Internal generic method for checking if an Annotation exists in a list of Annotations

        :param entries: List[Annotation]
            equivalent to self.entries, but can be used to examine any list of Annotations
        :param label: target annotation label
        :param text_range: target annotation text_range
        :param text: target annotation text
        :return: bool, true if annotation components are already in the entries list
        """
        matching_range = (
            text_range == entry.text_range and
            label == entry.label and
            text == entry.text
            for entry in entries)
        return any(matching_range)

    def has_matching_annotation(
            self,
            label: str,
            text_range: List[int],
            text: str
    ) -> bool:
        """Return true if there is already an entry with the given text, label, and text_range"""
        return self._is_in_entries(self.entries, label, text_range, text)

    def remove_duplicate_entries(self):
        """
        Remove duplicate entries, with same label, text, and text_range
        """
        deduped_directory = {}
        for key, entry in self.directory.items():
            if not self._is_in_entries(list(deduped_directory.values()), entry.label, entry.text_range, entry.text):
                deduped_directory[key] = entry
        self.directory = deduped_directory

    def get_entries_by_label(self, label):
        """
        Filter method to return all entries with the given target label
        Returns entries by reference, so you can modify them in place
        """
        return [entry for entry in self.entries if entry.label == label]


class Annotation:
    def __init__(self,
                 label: str,
                 text_range: List[int],
                 text: str,
                 coord_uuids: Union[List[str], None] = None,
                 line_start: Union[int, None] = None,
                 line_stop: Union[int, None] = None,
                 category_label: Union[str, None] = None,
                 uuid: str = None):
        """
        Creates Annotation object in Brat style (uuid, label text_range, text) or Sands style

        TODO(mjp): This should be an abstract class and a factory design pattern
        returning the correct Annotation type (eg TagTogAnnotation, SandsAnnotation, BratAnnotation)
        depending on the parsing
        """
        self.label = label
        self.category_label = category_label
        self.text_range = text_range
        self.text = text
        self.coord_uuids = coord_uuids
        self.line_start = line_start
        self.line_stop = line_stop
        self.uuid = uuid or uuid4().hex

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"text={self.text!r}, label={self.label!r}, text_range={self.text_range!r})"
        )

    def to_file_line(self):
        output = (
            f'{self.uuid or uuid4().hex}'
        )
        # append category label, coord uuids and line Start/stop, if they exist
        if self.category_label and self.coord_uuids and self.line_start and self.line_stop:
            output += (
                f'\t{self.label}\t{self.text_range[0]} {self.text_range[1]}'
                f'\t{self.text}'
                f"\t{self.category_label}"
                f"\t{';'.join(str(u) for u in self.coord_uuids)}"
                f"\t{self.line_start} {self.line_stop}")
        else:
            # brat output does not have a tab between label and range
            output += (
                f'\t{self.label} {self.text_range[0]} {self.text_range[1]}'
                f'\t{self.text}'
            )
        output += "\n"

        return output

    @classmethod
    def from_file_line(cls, line: str) -> List['Annotation']:
        cls_list = []

        parts = line.strip().split('\t')
        # if we are using current sands formatting
        if len(parts) == 7:
            # note that for sands, label and range are separated by a tab, and in brat they are not
            uuid, label, range_raw, text, category_label, uuids_raw, lines_raw = parts

            if not range_raw.startswith('None'):
                text_range = [int(s) for s in range_raw.split(' ')]
                coord_uuids = uuids_raw.split(';')
                line_start, line_stop = [int(s) for s in lines_raw.split(' ')]
                cls_list.append(cls(uuid=uuid, label=label, text_range=text_range, text=text,
                                    category_label=category_label, coord_uuids=coord_uuids,
                                    line_start=line_start, line_stop=line_stop))
        else:
            res = cls.parse_brat_ann_line(parts)
            for entry in res:
                uuid = entry
                label = res[entry]['label']
                text_range = res[entry]['range']
                text = res[entry]['text']
                # BUG(2020.10.12): This line will return the first match with label, which may not
                # be the correct category
                # eg, "diagnosis" may return "DiseaseDisorder" or "Disability", as both types have a "diagnosis" attr
                category_label = cls.category_label_from_enum_label_name(label)
                coord_uuids = None
                line_start, line_stop = None, None
                cls_list.append(cls(uuid=uuid, label=label, text_range=text_range, text=text,
                                    category_label=category_label, coord_uuids=coord_uuids,
                                    line_start=line_start, line_stop=line_stop))

        return cls_list

    @staticmethod
    def parse_brat_ann_line(line_list: list):
        if len(line_list) <= 1:
            return []
        raw_brat_aspect = line_list[1]
        aspect_list = raw_brat_aspect.split(' ')  # check if get 3 element split on 'label_name range_start range_end'
        res = dict()
        if len(aspect_list) != 3:
            if len(aspect_list) == 2 and ';' not in raw_brat_aspect:
                # likely found AnnotatorNotes, looks like
                # "#1\tAnnotatorNotes T11\tproblem/dx: left main coronary artery disease"
                operations_logger.debug("found AnnotatorNotes, continue to next line")
            elif ';' not in raw_brat_aspect:
                # if there are not multiple ranges, eg "lab 3016 3059;3060 3119"
                operations_logger.error('invalid input format, continue to next line')
            else:
                # then there are links or fragments
                fragments = raw_brat_aspect.split(';')
                frag_aspect_list = fragments[0].split(' ')
                whole_text = str(line_list[2])
                aspect, start_index, end_index = str(frag_aspect_list[0]), int(frag_aspect_list[1]), int(
                    frag_aspect_list[2])
                tag = line_list[0].strip()
                if tag in res:
                    tag = uuid4().hex
                res[tag] = {'label': aspect,
                            'range': [start_index, end_index],
                            'text': whole_text[: end_index - start_index],
                            'link': []}

                cursor = end_index - start_index + 1
                fragment_num = 0

                for i in range(1, len(fragments)):
                    fragment_num += 1
                    start_index, end_index = int(fragments[i].split(' ')[0]), int(fragments[i].split(' ')[1])
                    f_tag = f'{tag}_{fragment_num}'
                    res[f_tag] = {'label': aspect,
                                  'range': [start_index, end_index],
                                  'text': whole_text[cursor: cursor + end_index - start_index],
                                  'link': [tag]}

                    for j in range(1, len(fragments) - 1):
                        res[tag]['link'].append('F' + str(fragment_num + j))

                    cursor += end_index - start_index + 1
        # if the length of the aspect list is 3, we have a more standard format of ("aspect", 12, 22)
        elif is_digit(aspect_list[1]) and is_digit(aspect_list[2]):
            aspect, start_index, end_index = str(aspect_list[0]), int(aspect_list[1]), int(aspect_list[2])
            tag = line_list[0].strip()
            if tag in res:
                tag = uuid4().hex
            res[tag] = {'label': aspect,
                        'range': [start_index, end_index],
                        'text': line_list[2],
                        'link': [tag]}
        return res

    @staticmethod
    def category_label_from_enum_label_name(label_name: str):
        """
        Return category label based on label name
        BUG: if "label_name" is not unique, this will return the first instance of the category label
            eg, "diagnosis" returns Disability instead of DiseaseDisorder,
            "signsymptom" returns Disability instead of SignSymptom,
        """
        for label_enum in LabelList:
            if label_name in label_enum.__members__:
                return label_enum.get_category_label().persistent_label


class TextCoordinateSet:
    def __init__(self):
        self.coordinates_list = []

        self._coordinates_dict = None
        self._lines = None

        self._dataframe = None

        self.__index_first = None
        self.__index_last = None

    def __getitem__(self, tc_id: str) -> 'TextCoordinate':
        try:
            index = int(tc_id)
        except ValueError:
            index = None

        if index is not None:
            return self.coordinates_list[index]
        return self._coordinates[tc_id]

    def __contains__(self, tc: 'TextCoordinate') -> bool:
        index = tc.order
        if len(self.coordinates_list) <= index:
            return False
        return self.coordinates_list[index] == tc  # Should be the same TextCoordinate

    def __iter__(self):
        return iter(self.coordinates_list)

    def __len__(self):
        return len(self.coordinates_list)

    def __bool__(self):
        return bool(self.coordinates_list)

    @property
    def _coordinates(self) -> Dict:
        # This additional dictionary increase memory usage about on 40%.
        # But "TextCoordinateSet.coordinates" is only used for lookup a TextCoordinate by uuid.
        # Added TextCoordinateSet.__getitem__ method instead which saves memory when it's possible.

        if self._coordinates_dict is None:
            self._coordinates_dict = {tc.uuid: tc for tc in self.coordinates_list}
        return self._coordinates_dict

    @property
    def lines(self) -> List[Union[int, str]]:
        if self._lines is None:
            self._lines = list(self.iter_lines())
        return self._lines

    def iter_lines(self) -> Iterable[List[List[Union[int, str]]]]:
        line = []

        for tc in self:
            line.append(tc.uuid)
            if tc.new_line:
                yield line
                line = []
        else:
            if line:
                yield line

    def get_lines_in_range(self, start: int, stop: int):
        result = []
        for line in self.lines[start:stop]:
            result.append([self[tc_id].to_dict() for tc_id in line])
        return result

    @property
    def dataframe(self) -> pandas.DataFrame:
        if self._dataframe is None:
            self._dataframe = pandas.DataFrame([tc.to_dict() for tc in self])
            if self:
                self._dataframe.set_index([DOCUMENT_INDEX_FIRST, DOCUMENT_INDEX_LAST])
        return self._dataframe

    @property
    def _index_first(self) -> numpy.array:
        if self.__index_first is None:
            self.__index_first = numpy.empty(len(self), dtype=numpy.uint32)
            for i, tc in enumerate(self):
                self.__index_first[i] = tc.document_index_first
        return self.__index_first

    @property
    def _index_last(self):
        if self.__index_last is None:
            self.__index_last = numpy.empty(len(self), dtype=numpy.uint32)
            for i, tc in enumerate(self):
                self.__index_last[i] = tc.document_index_last
        return self.__index_last

    def add_text_coordinate(self, text_coordinate: 'TextCoordinate') -> None:
        """ Add coordinate to the set"""
        self.coordinates_list.append(text_coordinate)

        # Add text coordinate to the "coordinates_dict" if defined
        if self._coordinates_dict is not None:
            self._coordinates_dict[text_coordinate.uuid] = text_coordinate

    def find_coords(self, start: int, stop: int) -> list:
        # "bisect" implementation works faster and takes less memory than pandas.DataFrame
        a = bisect.bisect_left(self._index_first, start)
        if 0 < a < len(self._index_first) and self._index_first[a] > start and start < self._index_last[a-1]:
            a -= 1
        b = bisect.bisect_right(self._index_last, stop-1, lo=a)
        # stop-1 because should be strict less (<)
        return self.coordinates_list[a:b]

    @Cache.update(vary_on=['directory_filename', 'lines_filename'])
    def to_storage(self, directory_filename: str, lines_filename: str,
                   storage_client=None, tid: str = None):

        storage_client = storage_client or get_storage_service()
        client = storage_client.get_container()

        coords_gen = _JsonDictGenerator((tc.uuid, tc.to_dict()) for tc in self)
        with _JsonGeneratorBytesStream(coords_gen) as stream:
            client.write_fileobj(stream, directory_filename, tid=tid)

        lines_gen = _JsonListGenerator(self.iter_lines())
        with _JsonGeneratorBytesStream(lines_gen) as stream:
            client.write_fileobj(stream, lines_filename, tid=tid)

    def fill_coordinates_from_stream(self, stream):
        self.coordinates_list = []
        self._coordinates_dict = None
        for _, v in ijson.kvitems(stream, ''):
            self.coordinates_list.append(TextCoordinate.from_dict(v))
        return self

    @classmethod
    @Cache.cached(vary_on=['directory_filename', 'lines_filename'])
    def from_storage(cls, directory_filename: str = None, lines_filename: str = None,
                     storage_client=None) -> 'TextCoordinateSet':

        if not directory_filename and not lines_filename:
            raise AttributeError("'directory_filename' and/or 'lines_filename' is required.")

        client = storage_client or get_storage_service()

        res = cls()

        if directory_filename:
            stream = client.get_content_stream(directory_filename)
            res.fill_coordinates_from_stream(stream)

        # No need to load "lines_file" if we already have "coordinates".
        # Faster to generate "lines" structure instead of load.
        if lines_filename and not directory_filename:
            res._lines = []
            stream = client.get_content_stream(lines_filename)

            for line in ijson.items(stream, ''):
                res._lines.append(line)

        return res

    def update_from_page_ranges(self, page_numbers: List):
        """
        :param page_numbers: The output from get_page_indices(text). List[((page_start_idx, page_end_idx), page_no)],
         ordered by page_no
        :return:Updates text coordinates in place so that doc index is page_index+page_start pos from the text
        """
        for text_coord in self.coordinates_list:
            text_coord.document_index_first = text_coord.page_index_first + page_numbers[text_coord.page-1][0][0]
            text_coord.document_index_last = text_coord.page_index_last + page_numbers[text_coord.page-1][0][0]


class TextCoordinateSetGenerator:
    """Memory optimized TextCoordinateSet generator.

    This class created to to be used in the "TextCoordinateSet.to_storage()" method.

    Example:
        coords_gen = (TextCoordinate.from_dict(data) for data in very_large_source)

        TextCoordinatSet.to_storage(TextCoordinateSetGenerator(coords_gen),
                                    directory_file_key,
                                    texy_lines_file_key)

    Instead of keep in memory all TextCoordinate objects this class uses an iterable/generator
    and does the only pass of the data.

    We have to collect in memory "text lines", because this data is required in the
    "TextCoordinateSet.to_storage()" method. But "lines" uses multiple times less memory
    than TextCoordinate objects use.
    """
    def __init__(self, coordinates_iter: Iterable['TextCoordinate']):
        self._lines = []  # Collect lines during the first pass of coordinates_iter
        self.coordinates_list = self._collect_lines_and_iter(coordinates_iter)

    def __iter__(self):
        return self.coordinates_list

    def _collect_lines_and_iter(self, tc_iter) -> Iterable['TextCoordinate']:
        line = []

        for tc in tc_iter:
            line.append(tc.uuid)

            if tc.new_line:
                self._lines.append(line)
                line = []

            yield tc

        else:
            if line:
                self._lines.append(line)

    def iter_lines(self) -> Iterable[List[List[Union[int, str]]]]:
        yield from self._lines


class TextCoordinate(dataobject):
    text: str
    order: int
    page_index_first: int
    page_index_last: int
    document_index_first: int
    document_index_last: int
    line: int
    page: int = 1
    hyphen: bool = False
    spaces: int = 0
    new_line: bool = False
    left: int = None
    top: int = None
    right: int = None
    bottom: int = None
    _uuid: str = None  # There is property "uuid" below

    def to_dict(self):
        return {
            'uuid': self.uuid,
            'text': self.text,
            'order': self.order,
            'page_index_first': self.page_index_first,
            'page_index_last': self.page_index_last,
            DOCUMENT_INDEX_FIRST: self.document_index_first,
            DOCUMENT_INDEX_LAST: self.document_index_last,
            'line': self.line,
            'page': self.page,
            'hyphen': self.hyphen,
            'spaces': self.spaces,
            'new_line': self.new_line,
            'left': self.left,
            'right': self.right,
            'top': self.top,
            'bottom': self.bottom,
        }

    @property
    def uuid(self) -> str:
        return self._uuid or str(self.order)

    @uuid.setter
    def uuid(self, value: str) -> None:
        if value and value == str(self.order):
            value = None
        self._uuid = value

    @classmethod
    def from_dict(cls, data):
        uuid_value = data.pop('uuid', None)
        tc = cls(**data)
        tc.uuid = uuid_value
        return tc

    @classmethod
    def create_new_coordinate(cls, char: str, current_index: int, order: int, line_number: int) -> 'TextCoordinate':
        return cls(
            text=char,
            page_index_first=current_index,
            page_index_last=current_index,
            document_index_first=current_index,
            document_index_last=current_index,
            order=order,
            line=line_number,
        )

    def add_spaces(self, count: int = 1) -> None:
        """ Add some spaces """
        self.spaces += count
