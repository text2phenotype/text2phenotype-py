import re
from enum import Enum
from math import ceil
from typing import (
    Dict,
    List,
    Tuple,
)

import nltk
from nltk.tokenize import TreebankWordTokenizer
from nltk.tokenize.util import align_tokens

from text2phenotype.apm.metrics import text2phenotype_capture_span
from text2phenotype.common.common import (
    get_best_split_point,
    iter_sentence,
)
from text2phenotype.common.featureset_annotations import MachineAnnotation


# https://svn.apache.org/repos/asf/ctakes/sandbox/ctakes-scrubber-deid/
# https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/1472-6947-13-112


class PartOfSpeechBin(Enum):
    unknown = ['NULL', ',', '.', ':', '$', '(', ')', '"', "'", "''", '``', '#', 'POS']
    com_dep_wd = ['CC', 'CT', 'DT', 'EX', 'IN', 'MD', 'PDT', 'RP', 'TO', 'UH', 'WDT']
    FW_Symb = ['FW', 'SYM']
    Adjectives = ['JJ', 'JJR', 'JJS']
    Nouns = ['NN', 'NNS', 'NNP', 'NNPS']
    Adverbs = ['WRB', 'RB', 'RBR', 'RBS']
    Verbs = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
    Pronouns = ['PRP', 'PRP$', 'WP', 'WP$']
    Numbers = ['CD', 'LS']

    @classmethod
    def get_pos_bin_dict(cls) -> Dict[str, List[str]]:
        """
        :return: dict having entries['pos']='bin'
        """
        lookup = dict()
        for bins, mappings in cls.__members__.items():
            for pos in mappings.value:
                lookup[pos] = bins
        return lookup


class _Text2phenotypeTokenizer(TreebankWordTokenizer):
    """Tokenizer to address quote issue that native NLTK fails on."""

    def span_tokenize(self, text):
        raw_tokens = self.tokenize(text)

        if ('"' in text) or ("''" in text):
            tokens = self.__replace_quotes(text, raw_tokens)
        else:
            tokens = raw_tokens

        for tok in align_tokens(tokens, text):
            yield tok

    @staticmethod
    def __split_quote_string(quotes: str) -> List[str]:
        return [quotes[i:i + 2] for i in range(0, len(quotes), 2)]

    @classmethod
    def __replace_quotes(cls, text: str, raw_tokens: List[str]) -> List[str]:
        quotes = {'"', "``", "''"}

        # Find double quotes and converted quotes
        matched = [m.group() for m in re.finditer(r"``|'{2}|\"", text)]

        # Replace converted quotes back to double quotes
        # Note: in NLTK, this is failing on the case when the token consists of more than just quotes
        tokens = []
        for tok in raw_tokens:
            if tok[0] in quotes or tok[:2] in quotes:
                match = matched.pop(0)

                if match != tok[0:len(match)]:
                    tokens.append(match)
                    continue

            tokens.append(tok)

        return tokens


def __split_punctuation(tokens, index: int, punct: str) -> int:
    """
    Handle tokens with special punctuation.
    :param tokens: The list of tokens.
    :param index: The current index being processed.
    :param punct: The punctiation mark to handle.
    :returns: The current index.
    """
    current_span, current_text = tokens[index]
    if len(current_text) > 1 and punct in current_text:
        split_words = current_text.split(punct, 1)

        text1 = ''.join([split_words[0], punct])
        end1 = current_span[0] + len(text1)
        tokens[index] = ((current_span[0], end1), text1)

        if split_words[1]:
            tokens.insert(index + 1, ((end1, current_span[1]), split_words[1]))

    return index


@text2phenotype_capture_span()
def tokenize(text: str, tid: str = None) -> List[dict]:
    """
    Use NLK to turn text into list of {'token', 'len', 'speech', 'speech_bin', and 'range'}

    NLTK (Python Natural Language ToolKit Tokenization)

    :param text: "The patient name is Richen Zhang"
    :return: list tokens with start and end positions
       [ (the,0,2), (patient,4,10), .... ]
    """
    tokens = []
    for sent_range, sentence in iter_sentence(text):
        sent_start = sent_range[0]
        clean_sentence = sentence.replace('\'\'', '``')
        sent_tokens = [((span[0] + sent_start, span[1] + sent_start), sentence[span[0]:span[1]])
                       for span in _Text2phenotypeTokenizer().span_tokenize(clean_sentence)]

        i = 0
        while i < len(sent_tokens):
            i = __split_punctuation(sent_tokens, i, ':')
            i = __split_punctuation(sent_tokens, i, ';')
            i = __split_punctuation(sent_tokens, i, ',')
            i += 1

        tokens.extend(sent_tokens)

    # add POS information now that tokens have been adjusted
    pos_bin_index = PartOfSpeechBin.get_pos_bin_dict()
    speech_tags = nltk.pos_tag([token[1] for token in tokens])
    features = list()
    for token, speech_tag in zip(tokens, speech_tags):
        span, text = token
        speech = speech_tag[1]

        features.append({'token': text,
                         'range': [span[0], span[1]],
                         'speech': speech})

    return features


def chunk_text(text: str, max_word_count: int) -> List[Tuple[Tuple[int, int], str]]:
    """
    Break a document into chunks.
    :param text: The document text
    :param max_word_count: The maximum number of words in each chunk.
    :return: The list of chunk (indices in original text, text).
    """
    if not text:
        return []

    if text.isspace():
        return [((0, len(text)), text)]
    # splits chunks so that they contain the greatest number of complete sentences such that
    # total_chunK_word_count <=max_word_count
    chunks = []
    token_dict = tokenize(text)
    machine_annotation = MachineAnnotation(tokenization_output=token_dict, text_len=len(text))
    start_token = 0
    start_pos = 0
    while start_pos < len(text):
        if max_word_count + start_token >= len(machine_annotation):
            chunks.append(((start_pos, len(text)), text[start_pos: len(text)]))
            start_pos = len(text)

        else:
            max_chunk_len = machine_annotation.range[max_word_count + start_token][1]-start_pos
            min_chunk_len = machine_annotation.range[ceil(max_word_count*.8) + start_token][1]-start_pos
            end_pos = get_best_split_point(text,
                                           start_point=start_pos,
                                           max_chunk_len=max_chunk_len,
                                           min_chunk_size=min_chunk_len)


            text_chunk = text[start_pos: end_pos]
            chunks.append(((start_pos, end_pos), text_chunk))
            if end_pos < len(text):
                token_idx = machine_annotation.range_to_token_idx_list[end_pos]
            else:
                break
            start_token = token_idx if isinstance(token_idx, int) else min(token_idx)
            start_pos = end_pos
    return chunks
