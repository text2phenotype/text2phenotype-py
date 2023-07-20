import copy
import threading
from string import punctuation
from typing import (
    Dict,
    Set,
    Tuple,
    List)

from text2phenotype.common.jsonifiers import JsonSerializableMethodsMixin
from text2phenotype.common.log import operations_logger
from text2phenotype.constants.english_stopwords import ENGLISH_STOPWORDS
from text2phenotype.constants.features import FeatureType

TOKEN = 'token'
RANGE = 'range'


class IndividualFeatureOutput(JsonSerializableMethodsMixin):
    def __init__(self, dictionary_input: dict = None):
        self.input_dict = dictionary_input if dictionary_input is not None else dict()

    def __len__(self):
        return len(self.token_indexes)

    @property
    def token_indexes(self) -> set:
        return set(self.input_dict.keys())

    @property
    def sorted_token_indexes(self) -> List[int]:
        return sorted([int(i) for i in self.input_dict])

    def __getitem__(self, token_index: [int, str]):
        item = self.input_dict.get(str(token_index))
        # allow for keys to be integers or strings and get either way
        if item is None:
            item = self.input_dict.get(int(token_index))
        return item

    def __contains__(self, item):
        return self.__getitem__(item) is not None

    def to_dict(self) -> Dict:
        return self.input_dict

    def items(self):
        return self.input_dict.items()


class FeatureServiceOutput(JsonSerializableMethodsMixin):
    STRING_KEYS = set()
    LIST_TYPE_FEATURES = set()

    def __init__(self):
        self.features = set()
        self.output_dict = dict()
        self.__lock = threading.Lock()

    def __deepcopy__(self, memodict={}):
        cpyobj = type(self)()
        cpyobj.features = copy.deepcopy(self.features)
        cpyobj.output_dict = copy.deepcopy(self.output_dict)
        return cpyobj

    def __getitem__(self, item):
        if not isinstance(item, tuple):
            feature = self.get_feature_type(item)
            token_idx = None
        else:
            feature = self.get_feature_type(item[0])
            token_idx = item[1]

        if feature in self.features or feature in self.STRING_KEYS:
            feature_val: IndividualFeatureOutput = self.output_dict[feature]
            if token_idx is not None:
                return feature_val[token_idx]
            return feature_val
        else:
            operations_logger.warning(
                f"Feature {item} not in Feature Service Output Dictionary, included features"
                f" are {self.features}")

    @property
    def feature_names(self):
        return {feat.name for feat in self.features}

    def get_feature_type(self, feature: [str, int, FeatureType]):
        if feature not in self.STRING_KEYS:
            if isinstance(feature, str):
                try:
                    feature = FeatureType[feature]
                except KeyError:
                    feature = None
            elif not isinstance(feature, FeatureType) and isinstance(feature, int):
                try:
                    feature = FeatureType(feature)
                except ValueError:
                    feature = None
        return feature

    def add_item(self, feature, annotation):
        with self.__lock:
            feature = self.get_feature_type(feature)
            if feature is not None:
                if not isinstance(annotation, IndividualFeatureOutput) and not self.list_feature(feature):
                    annotation = IndividualFeatureOutput(annotation)

                self.output_dict[feature] = annotation
                self.features.add(feature)

    def list_feature(self, feature_name) -> bool:
        return feature_name in self.STRING_KEYS or self.get_feature_type(feature_name) in self.LIST_TYPE_FEATURES


class MachineAnnotation(FeatureServiceOutput):
    STRING_KEYS = {TOKEN, RANGE}
    LIST_TYPE_FEATURES = {FeatureType.len, FeatureType.speech, FeatureType.speech_bin, TOKEN, RANGE}

    def __len__(self):
        return len(self.tokens)

    def __init__(self, tokenization_output: list = None, json_dict_input: dict = None, text_len: int = 0):
        super().__init__()
        self.__range_mapping_list = None
        self._text_len = text_len
        if json_dict_input is not None:
            self.fill_from_dict(json_dict_input)
        if tokenization_output is not None:
            self.fill_from_tokenization_result(tokenization_output)

    @property
    def range(self):
        return self.output_dict[RANGE]

    @property
    def tokens(self):
        return self.output_dict[TOKEN]

    @tokens.setter
    def tokens(self, value: list):
        self.output_dict[TOKEN] = value

    @property
    def range_to_token_idx_list(self):
        if not self.__range_mapping_list:
            self.__range_mapping_list = [None] * (self.text_len + 1)
            start = 0
            for j in range(len(self.range)):
                for i in range(self.range[j][0], self.range[j][1]):
                    self.__range_mapping_list[i] = j
                for t in range(start, self.range[j][0]):
                    if j >= 1:
                        prev_word_index = j - 1
                    else:
                        # if first word make it not annotate
                        prev_word_index = j + 1
                    next_word_index = j
                    self.__range_mapping_list[t] = (prev_word_index, next_word_index)
                start = self.range[j][1]
            self.__range_mapping_list[self.range[j][1]] = j

            if self.range[j][1] < self.text_len:
                self.__range_mapping_list[self.range[j][1] + 1: len(self.range)] = [(j, 0)] * (
                        self.text_len - self.range[j][1] + 1)
        return self.__range_mapping_list

    @property
    def text_len(self):
        if not self._text_len:
            self._text_len = self.range[-1][1]
        return self._text_len

    @text_len.setter
    def text_len(self, value):
        self._text_len = value

    def fill_from_tokenization_result(self, tokens):
        output_token = []
        output_speech = []
        output_range = []
        for token in tokens:
            output_token.append(token[TOKEN])
            output_speech.append(token['speech'])
            output_range.append(token[RANGE])
        self.output_dict[TOKEN] = output_token
        self.output_dict[FeatureType.speech] = output_speech
        self.output_dict[RANGE] = output_range
        self.features = self.features.union({FeatureType.speech})

    def to_dict(self) -> Dict:
        out = dict()
        for k, v in self.output_dict.items():
            if k in self.STRING_KEYS:
                out[k] = v
            elif k in self.LIST_TYPE_FEATURES:
                out[k.name] = v
            else:
                out[k.name] = v.to_dict()
        return out

    @staticmethod
    def get_response_type(value: [dict, list]):
        if isinstance(value, dict):
            value = IndividualFeatureOutput(value)
        return value

    def indexes_from_range(self, rnge: [list, tuple, range]) -> Set[int]:
        start = rnge[0]
        end = rnge[-1]
        start_token_idx = self.range_to_token_idx_list[start]
        end_token_idx = self.range_to_token_idx_list[end]
        out = set(range(start_token_idx, end_token_idx + 1))
        return out

    def fill_from_dict(self, data: Dict) -> None:
        for feature in data:
            real_feature = self.get_feature_type(feature)
            if real_feature:
                if real_feature in self.LIST_TYPE_FEATURES:
                    self.add_item(real_feature, data[feature])
                else:
                    self.add_item(real_feature, IndividualFeatureOutput(data[feature]))

    def valid_tokens(self, duplicate_tokens: Set[int] = None) -> Tuple[list, list]:
        real_vals = list()
        valid_tokens = list()
        duplicate_tokens = duplicate_tokens or []
        for idx in range(len(self.tokens)):
            punct_bool = True
            for char in self.tokens[idx]:
                if char not in punctuation:
                    punct_bool = False
            if self.tokens[idx] not in ENGLISH_STOPWORDS and not punct_bool and idx not in duplicate_tokens:
                real_vals.append(idx)
                valid_tokens.append(self.tokens[idx])
        operations_logger.debug(f'Number of valid tokens is {len(valid_tokens)} number of total tokens '
                                f'is {len(self.tokens)}')
        return valid_tokens, real_vals


class DocumentTypeAnnotation(MachineAnnotation):
    def __init__(self, annotation):
        super().__init__(json_dict_input=annotation.to_dict())
        self.__clean_annotations()
        self.__merge_annotations()

    def __clean_annotations(self):
        section_keys = self.output_dict[FeatureType.loinc_section].input_dict.keys()
        target_indices = [int(i) for i in section_keys]
        exclude_features = {FeatureType.len, FeatureType.len.name, FeatureType.len.value,
                            FeatureType.speech, FeatureType.speech.name, FeatureType.speech.value,
                            FeatureType.speech_bin, FeatureType.speech_bin.name, FeatureType.speech_bin.value}

        for feature in exclude_features:
            if feature in self.output_dict:
                del self.output_dict[feature]

        for feature, annotations in self.output_dict.items():
            if isinstance(annotations, list):
                self.output_dict[feature] = [annotations[i] for i in target_indices]
            else:
                self.output_dict[feature] = IndividualFeatureOutput(
                    {i: annotations[k] for i, k in enumerate(section_keys)})

    def __merge_annotations(self):
        ranges = self.output_dict['range']
        tokens = self.output_dict['token']
        sections = self.output_dict[FeatureType.loinc_section]

        section_list = sorted([(int(index), section) for index, section in sections.input_dict.items()])
        if not section_list:
            return

        new_tokens = [tokens[section_list[0][0]]]
        new_ranges = [ranges[section_list[0][0]]]
        new_sections = [section_list[0][1]]
        valid_indices = [0]
        for i in range(1, len(section_list)):
            index, section = section_list[i]
            curr_token = tokens[index]
            curr_range = ranges[index]

            loinc_code = self.__get_loinc_code(section)

            same_code = loinc_code == self.__get_loinc_code(section_list[i - 1][1])
            adj_index = new_ranges[-1][1] == curr_range[0] - 1
            if same_code and adj_index:
                new_tokens[-1] += ' ' + curr_token
                new_ranges[-1][1] = curr_range[1]
            else:
                new_sections.append(section)
                valid_indices.append(index)
                new_ranges.append(curr_range)
                new_tokens.append(curr_token)

        self.output_dict['range'] = new_ranges
        self.output_dict['token'] = new_tokens
        self.output_dict[FeatureType.loinc_section] = \
            IndividualFeatureOutput({str(i): section for i, section in enumerate(new_sections)})

        preprocessed_features = {'range', 'token', FeatureType.loinc_section}
        for feature, annotations in self.output_dict.items():
            if feature in preprocessed_features:
                continue

            if isinstance(annotations, list):
                self.output_dict[feature] = [annotations[i] for i in valid_indices]
            else:
                self.output_dict[feature] = IndividualFeatureOutput(
                    {new_i: annotations[old_i] for new_i, old_i in enumerate(valid_indices) if old_i in annotations})

    @staticmethod
    def __get_loinc_code(annotation):
        return annotation[0]['umlsConcept'][0]['cui']


class DefaultVectors(JsonSerializableMethodsMixin):
    def __init__(self, default_vectors: dict = None):
        self.defaults = dict()
        self.fill_from_dict(default_vectors) if default_vectors is not None else dict()

    def add_default(self, feature: [int, str, FeatureType], default_vector: list):
        self.defaults[self.get_feature_type(feature)] = default_vector

    def fill_from_dict(self, default_dictionary: Dict) -> None:
        for key, value in default_dictionary.items():
            self.add_default(key, value)

    @staticmethod
    def get_feature_type(feature: [str, int, FeatureType]):
        if isinstance(feature, str):
            feature = FeatureType[feature]
        elif isinstance(feature, int):
            feature = FeatureType(feature)
        return feature

    def __getitem__(self, feature):
        return self.defaults.get(self.get_feature_type(feature))

    def to_dict(self) -> Dict:
        return {k.name: v for k, v in self.defaults.items()}

    def total_len(self, features: list):
        return sum([len(self.__getitem__(feature)) for feature in features])


class Vectorization(FeatureServiceOutput):
    DEFAULTS = 'defaults'
    STRING_KEYS = {DEFAULTS}

    def __init__(self, default_vectors: DefaultVectors = None, json_input_dict: dict = None):
        super().__init__()
        self.defaults = default_vectors if isinstance(default_vectors, DefaultVectors) else DefaultVectors(default_vectors)
        if json_input_dict is not None:
            self.fill_from_dict(json_input_dict)

    def to_dict(self) -> Dict:
        out = dict()
        for k, v in self.output_dict.items():
            out[k.name] = v.to_dict()
            out[self.DEFAULTS] = self.defaults.to_dict()
        return out

    def fill_from_dict(self, data: dict) -> None:
        for k, v in data.items():
            if k == self.DEFAULTS:
                self.defaults = DefaultVectors(default_vectors=v)
            else:
                self.add_item(k, v)

    def __len__(self):
        return len(self.output_dict)

    def check_feature(self, feature):
        return self.get_feature_type(feature) in self.output_dict
