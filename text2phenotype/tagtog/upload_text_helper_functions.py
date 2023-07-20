import copy
import os
from typing import List, Tuple

from text2phenotype.annotations.file_helpers import AnnotationSet, Annotation
from text2phenotype.common import common
from text2phenotype.common.common import chunk_text_by_size
from text2phenotype.common.deduplication import duplicate_ranges
from text2phenotype.common.log import operations_logger
from text2phenotype.constants.features import LabLabel, CovidLabLabel
from text2phenotype.tagtog.tag_tog_annotation import TagTogAnnotationSet
from text2phenotype.tagtog.tag_tog_client import TagTogClient

LOCAL_TEMP_DIR = '/tmp'
DEFAULT_TAG_TOG_CHUNK_CHAR_SIZE = 2500
DATE_TYPE_MAPPING = {'collection_date': 'specimen_date'} # used during cyan migration to resolve variable name change


# used only for migration where sands labelling was ambiguous
def filter_lab_vs_covid_lab(annotation_set: AnnotationSet, covid: bool = False) -> AnnotationSet:
    bad_ids = []
    for entry_id in annotation_set.directory:
        annot: Annotation = annotation_set.directory[entry_id]
        if annot.label == 'lab':
            if annot.category_label == LabLabel.get_category_label().persistent_label and covid:
                covid_lab = 'sars' in annot.text.lower() or 'cov' in annot.text.lower() or 'coronavirus' in annot.text.lower()
                interp = 'detec' in annot.text.lower() or 'pos' in annot.text.lower() or 'neg' in annot.text.lower()
                if not covid_lab:
                    if not interp:
                        bad_ids.append(entry_id)

                    else:
                        annot.label = 'lab_interp'
                        annotation_set.directory[entry_id] = annot
        if annot.category_label == CovidLabLabel.get_category_label().persistent_label and not covid:
            bad_ids.append(entry_id)
    for id in bad_ids:
        del annotation_set.directory[id]
    return annotation_set



# only used during the cyan migration
def update_event_date_label(annotation_set: AnnotationSet) -> AnnotationSet:
    for entry_id in annotation_set.directory:
        annot: Annotation = annotation_set.directory[entry_id]
        if annot.label in DATE_TYPE_MAPPING:
            annot.label = DATE_TYPE_MAPPING[annot.label]
            annotation_set.directory[entry_id] = annot

    return annotation_set


def remove_duplicate_text(text: str, range_duplicates: list):
    duplicate_text_ranges = sorted(range_duplicates)
    new_text = text
    for dup_idx in range(len(duplicate_text_ranges) - 1, -1, -1):
        start_pos = duplicate_text_ranges[dup_idx][0]
        end_pos_dup = duplicate_text_ranges[dup_idx][1]
        new_text = new_text[:start_pos] + new_text[end_pos_dup:]
    return new_text


def update_duplicate_annotations(duplicate_ranges, ann_set: AnnotationSet, deduped_text: str):
    new_entries = ann_set.entries

    for dup_idx in range(len(duplicate_ranges) - 1, -1, -1):
        start_pos = duplicate_ranges[dup_idx][0]
        end_pos_dup = duplicate_ranges[dup_idx][1]
        range_diff = end_pos_dup - start_pos
        for i in range(len(new_entries) - 1, -1, -1):
            if new_entries[i] is not None and new_entries[i].label != 'dup':
                if new_entries[i].text_range[0] > start_pos:
                    # term fully contained within duplciate section
                    if new_entries[i].text_range[1] < end_pos_dup:
                        new_entries.pop(i)
                    elif new_entries[i].text_range[1] >= end_pos_dup and new_entries[i].text_range[0] <= end_pos_dup:
                        print('handle this case')
                    # term after from duplicate section
                    else:
                        entry = new_entries[i]
                        updated_entry = update_annotation_range(entry, entry.text_range[0] - range_diff, deduped_text)
                        new_entries[i] = updated_entry


    ann_set = AnnotationSet()
    ann_set.entries = [ent for ent in new_entries if ent is not None]

    return ann_set


def update_annotation_range(annotation: Annotation, new_start, text):
    """
    :param annotation: an Annotation object,must have text and text_range
    :param new_start: the  expected new start position  of the annotation
    :param text: the new text in which to find the annotation
    :return: none  if the annotation  text is  not found in the new text, else looks for  first occurence of
     annotation text in the new text after  the  expected start position.The find function is  used bc for some of  our
     docs the annotation range and the annotation text position  in the actual text do not actually match up
    """
    new_text = annotation.text.strip()
    validated_start = text.find(new_text.split()[0], new_start)
    if validated_start != -1:
        annotation.text_range = [validated_start, validated_start + len(new_text)]
        annotation.text = new_text
        return annotation


def chunk_text_ann(
        text: str,
        ann_set: AnnotationSet,
        chunk_size: int = DEFAULT_TAG_TOG_CHUNK_CHAR_SIZE,
        max_num_chunks: int = None,
        min_entities_per_chunk: int = 1,) -> List[Tuple[AnnotationSet, str]]:
    """
    :param text: the full raw text to be split into chunks
    :param ann_set: The annotation set for the full text that must be broken up as well
    :param chunk_size: The number of characters that a  chunk should be (will chunk at an ideal split point if one
     exists in the last 10% of this number of characters
    :param max_num_chunks: The max number of chunks you want out (useful for upload when trying to not upload 1000
    chunks from the same doc
    :param min_entities_per_chunk: The minimum number of annotations you want in a chunk to consider it worth
     uploding for review, defaults to 1
    :return: a list of tuples of chunked annotation set,  chunked text for all valid chunks
    """
    chunked_text = chunk_text_by_size(text, chunk_size)
    if len(chunked_text) == 1:
        return [(ann_set, text)]
    output = []
    operations_logger.info(f'Found {len(chunked_text)} chunks')
    ann_entries = [a for a in ann_set.entries  if len(a.text.replace('e', '').replace(' ', ''))>1]
    for chunk in chunked_text:
        chunk_start = chunk[0][0]
        chunk_end = chunk[0][1]
        partial_entries = [entry for entry in ann_entries if
                           entry.text_range[0] > chunk_start and entry.text_range[1] < chunk_end]
        for idx in range(len(partial_entries)):
            new_ent = copy.deepcopy(partial_entries[idx])
            if new_ent.label != 'dup':
                new_start = new_ent.text_range[0] - chunk_start
                new_ent = update_annotation_range(new_ent, new_start, chunk[1])
                partial_entries[idx] = new_ent
            else:
                partial_entries[idx] = None

        partial_ann_set = AnnotationSet()
        partial_ann_set.entries = [ent for ent in partial_entries if ent is not None]
        # if there are no  annotations  for  a chunk,   skip that chunk  for upload
        if len(partial_ann_set.entries) < min_entities_per_chunk:
            continue
        output.append((partial_ann_set, chunk[1]))
    operations_logger.info(f'returning {len(output)} chunks')
    if max_num_chunks is not None:
        output = output[:max_num_chunks]
    return output


def clean_text(text):
    """
    replaces all new line,tabs and page break characters with - bc tagtog freaks out and messes up all alighments
    if the first character is not a normal character to preserve character positions
    """
    i=0
    while text[i] in ['\n', ' ', '\t', '\x0c']:
        i += 1

    txt_1 = '-' * i + text[i:]
    txt_1 = txt_1.replace('\x0c', '\n')
    return txt_1