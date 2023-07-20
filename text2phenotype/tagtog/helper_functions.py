import os
from typing import List

from text2phenotype.annotations.file_helpers import AnnotationSet
from text2phenotype.common import common
from text2phenotype.common.common import chunk_text_by_size
from text2phenotype.common.deduplication import duplicate_ranges
from text2phenotype.common.log import operations_logger
from text2phenotype.tagtog.tag_tog_annotation import TagTogAnnotationSet
from text2phenotype.tagtog.tag_tog_client import TagTogClient
from text2phenotype.tagtog.tagtog_html_to_text import TagTogText
from text2phenotype.tagtog.upload_text_helper_functions import (
    DEFAULT_TAG_TOG_CHUNK_CHAR_SIZE,
    remove_duplicate_text,
    chunk_text_ann,
    update_duplicate_annotations,
    clean_text)

TMP_DIR = '/tmp'


def upload_raw_text(
        text: str,
        doc_id: str,
        tag_tog_client: TagTogClient,
        tag_tog_folder: str = 'pool',
        deduplicate: bool = True,
        split_into_chunks: bool = True
):
    """
    :param text: the original raw text you want to use
    :param doc_id: tag tog doc id, similar to filename in tag tog
    :param tag_tog_client:
    :param tag_tog_folder: Can either be the last_subfolder, or the full folder path (pool/a/DOCS)
    :return: None, uploads an unannotated raw text document to tag tog in the verbatim style
    """
    if deduplicate:
        range_duplicates = duplicate_ranges(text, min_length=2500)
        text = remove_duplicate_text(text, range_duplicates=range_duplicates)
    if split_into_chunks:
        chunked_text = chunk_text_by_size(text, DEFAULT_TAG_TOG_CHUNK_CHAR_SIZE)
        for chunk in chunked_text:
            upload_raw_text(text=chunk[1], tag_tog_client=tag_tog_client,
                            tag_tog_folder=tag_tog_folder, deduplicate=False, split_into_chunks=False,
                            doc_id=doc_id)

    # write and upload text files (allows for larger file sizing)
    text = clean_text(text)

    new_text_fp = os.path.join(TMP_DIR, tag_tog_client.project, f'{doc_id}.txt')
    os.makedirs(os.path.dirname(new_text_fp), exist_ok=True)
    common.write_text(text, new_text_fp)

    a = tag_tog_client.push_text_verbatim(new_text_fp, folder=tag_tog_folder)
    if not a.ok:
        operations_logger.warning(f"DOCUMENT FAILED with error message: {a.text}")

    return new_text_fp


def upload_raw_text_with_annotation_set(
        text: str,
        ann_set: AnnotationSet,
        doc_id: str,
        tag_tog_client: TagTogClient,
        tag_tog_folder: str = 'pool',
        member_ids: List[str] = None,
        deduplicate: bool = True,
        split_into_chunks: bool = True):
    """
    :param text: raw text, string form
    :param ann_set: annotation set object that has pre-annotations
    :param doc_id: document id you want to pass to tag tog
    :param tag_tog_client: initialized with the project and project owner name
    :param tag_tog_folder: subfolder you wish to upload to, defaults to pool
    :param member_ids: Which member ids you want to upload the annotations to
    :param deduplicate: whether or not to deduplicate the text before uploading
    :param split_into_chunks: whether or not to split the text into chunks for upload
    :return: None, Uploads a pre-annotated text file to tag tog
    """
    if deduplicate:
        range_duplicates = duplicate_ranges(text)
        text = remove_duplicate_text(text, range_duplicates=range_duplicates)
        ann_set = update_duplicate_annotations(duplicate_ranges=range_duplicates, ann_set=ann_set, deduped_text=text)
    if split_into_chunks:
        output = chunk_text_ann(text=text, ann_set=ann_set)
        counter = 0
        for entry in output:
            doc_id_split = doc_id.split('.')
            chunk_doc_id = f'{doc_id_split[0]}_chunk_{counter}'
            counter += 1
            upload_raw_text_with_annotation_set(
                text=entry[1], ann_set=entry[0], tag_tog_folder=tag_tog_folder,
                tag_tog_client=tag_tog_client, doc_id=chunk_doc_id, split_into_chunks=False, deduplicate=False,
                member_ids=member_ids)
    text = clean_text(text)

    # enure member_ids is valid
    if member_ids is None:
        member_ids = ['master']
    if isinstance(member_ids, str):
        member_ids = [member_ids]

    # write out the  text and  ann json locally, this is a necessary step for any larger files
    new_text_fp = os.path.join(TMP_DIR, tag_tog_client.project, f'{doc_id}.txt')
    os.makedirs(os.path.dirname(new_text_fp), exist_ok=True)

    ann_json: TagTogAnnotationSet = TagTogAnnotationSet()
    ann_json.from_annotation_set_for_text(
        ann_set, inverse_annotation_legend=tag_tog_client.inverse_annotation_legend, text=text
    )

    ann_json_dict = ann_json.to_json()
    ann_json_dict['anncomplete'] = False

    ann_json_path = new_text_fp.replace('.txt', '.ann.json')
    common.write_text(text, new_text_fp)
    common.write_json(ann_json_dict, ann_json_path)

    for member in member_ids:
        a = tag_tog_client.push_text_ann_verbatim_from_fp(
            new_text_fp, ann_json_path, folder=tag_tog_folder, annotator_id=member,
            base_fp=os.path.dirname(new_text_fp)
        )
        if not a.ok:
            operations_logger.warning(f"DOCUMENT FAILED with error message: {a.text}")

    return new_text_fp, ann_json_path


def add_annotation_to_doc_id(
        doc_id: str,
        tag_tog_client: TagTogClient,
        ann_set: AnnotationSet,
        member_ids: list,
        html_text: str = None):
    """
    :param doc_id: the tag tog document id
    :param tag_tog_client:
    :param ann_set: the annotation Set object that contains the annoations you want to overwrite the current annotations with
    :param member_ids: the tag tog user ids for whom you want to create/overwrite annottaions for
    :return: None, adds annotations in the tag tog ui, NOTE: THIS IS DESTRUCTIVE NOT ADDITIVE
    """
    if not html_text:
        html_text = tag_tog_client.get_html_by_doc_id(doc_id=doc_id).text
    tag_tog_text: TagTogText = TagTogText(html_text)

    new_text_fp = os.path.join(TMP_DIR, tag_tog_client.project, f'{doc_id}.html')
    os.makedirs(os.path.dirname(new_text_fp), exist_ok=True)

    ann_json: TagTogAnnotationSet = TagTogAnnotationSet()

    ann_json.from_annotation_set_with_tag_tog_text(
        ann_set, inverse_annotation_legend=tag_tog_client.inverse_annotation_legend, tag_tog_text=tag_tog_text
    )

    ann_json_dict = ann_json.to_json(html_parts=list(tag_tog_text.html_mapping_to_text.keys()))
    ann_json_dict['anncomplete'] = False

    # enure member_ids is valid
    if member_ids is None:
        member_ids = ['master']
    if isinstance(member_ids, str):
        member_ids = [member_ids]

    for member in member_ids:
        a = tag_tog_client.update_annotations(
            html_text=html_text, ann_json_dict=ann_json_dict, member=member, doc_id=doc_id)

        if not a.ok:
            operations_logger.warning(f"DOCUMENT FAILED with error message: {a.text}")

def add_tag_tog_annotation_to_doc_id(
        doc_id: str,
        tag_tog_client: TagTogClient,
        ann_json: TagTogAnnotationSet,
        member_ids: list = None,
        html_text: str = None):
    """
    :param doc_id: the tag tog document id
    :param tag_tog_client:
    :param ann_set: the annotation Set object that contains the annoations you want to overwrite the current annotations with
    :param member_ids: the tag tog user ids for whom you want to create/overwrite annottaions for
    :return: None, adds annotations in the tag tog ui, NOTE: THIS IS DESTRUCTIVE NOT ADDITIVE
    """
    if not html_text:
        html_text = tag_tog_client.get_html_by_doc_id(doc_id=doc_id).text
    tag_tog_text: TagTogText = TagTogText(html_text)

    new_text_fp = os.path.join(TMP_DIR, tag_tog_client.project, f'{doc_id}.html')
    os.makedirs(os.path.dirname(new_text_fp), exist_ok=True)

    ann_json_dict = ann_json.to_json(html_parts=list(tag_tog_text.html_mapping_to_text.keys()))
    ann_json_dict['anncomplete'] = False

    # enure member_ids is valid
    if member_ids is None:
        member_ids = ['master']
    if isinstance(member_ids, str):
        member_ids = [member_ids]

    for member in member_ids:
        a = tag_tog_client.update_annotations(
            html_text=html_text, ann_json_dict=ann_json_dict, member=member, doc_id=doc_id)

        if not a.ok:
            operations_logger.warning(f"DOCUMENT FAILED with error message: {a.text}")

