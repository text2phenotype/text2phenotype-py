import copy
import json
import os
from enum import Enum
from typing import (
    List,
    Dict, Type)

import numpy as np

from text2phenotype.annotations.file_helpers import AnnotationSet, Annotation
from text2phenotype.common import common
from text2phenotype.common.feature_data_parsing import is_digit_punctuation, seconds_digit, probable_lab_unit, LAB_INTERP_TERMS

from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import Environment
from text2phenotype.constants.features.label_types import LabelEnum, LabLabel
from text2phenotype.services.storage.providers import get_storage_service, StorageProvidersEnum

CURRENT_FEATURE_SET_VERSION = "dev/20210104"


class DataSourceContext(Enum):
    train = "train"
    validation = 'validation'
    testing = 'testing'


class DataSource:
    HUMAN_ANNOTATION_SUFFIX = '.ann'
    MACHINE_ANNOTATION_SUFFIX = '.json'
    TEXT_SUFFIX = '.txt'

    def __init__(self,
                 dest_bucket: str = None,
                 source_bucket: str = None,
                 **kwargs):
        self.parent_dir: str = kwargs.get('parent_dir', Environment.DATA_ROOT.value)
        self.feature_set_version: str = kwargs.get('feature_set_version', CURRENT_FEATURE_SET_VERSION)

        # training dirs
        self.original_raw_text_dirs: List[str] = kwargs.get('original_raw_text_dirs', [])
        self.ann_dirs: List[str] = kwargs.get('ann_dirs', [])
        self.feature_set_subfolders: List[str] = kwargs.get('feature_set_subfolders', [])
        self.text_dir_prefix: str = kwargs.get("text_dir_prefix")

        # testing dirs biomed only
        self.testing_text_dirs: List[str] = kwargs.get('testing_text_dirs', self.original_raw_text_dirs)
        self.testing_ann_dirs: List[str] = kwargs.get('testing_ann_dirs', self.ann_dirs)
        self.testing_fs_subfolders: List[str] = kwargs.get('testing_fs_subfolders', [])

        # used for validation in biomed
        self.validation_text_dirs: List[str] = kwargs.get('validation_text_dirs', self.testing_text_dirs)
        self.validation_ann_dirs: List[str] = kwargs.get('validation_ann_dirs', self.testing_ann_dirs)
        self.validation_fs_subfolders: List[str] = kwargs.get('validation_fs_subfolders', self.testing_fs_subfolders)

        # used for active learning processes
        self.active_feature_set_dirs = kwargs.get('active_feature_set_dirs', [])
        self.active_text_dirs = kwargs.get('active_text_dirs', [])
        self.active_ann_jira = kwargs.get('active_ann_jira')

        # used only by feature set data source
        self.old_feature_set_version: str = kwargs.get('old_feature_set_version', None)

        # used primarily for combined label_types
        self.required_label_names: list = kwargs.get('required_label_names', [])

        # used during update feature annotations:
        self.annotate_new_files: bool = kwargs.get('annotate_new_files', False)

        # max number of tokens allowed in document for processing
        # Different than the max buffer size, BIOMED_MAX_DOC_WORD_COUNT
        self.max_token_count = kwargs.get('max_token_count', np.inf)
        # if true will include files for which there are no human annotations default behavior is to only
        # train/test on files with expert annotations
        self.include_all_ann_files: bool = kwargs.get('include_all_ann_files', False)

        # whether to use async mode
        self.async_mode: bool = kwargs.get('async_mode', False)
        if self.async_mode:
            self.TEXT_SUFFIX = '.extracted_text.txt'
            self.MACHINE_ANNOTATION_SUFFIX = '.extracted_text.json'

        if dest_bucket:
            self.storage_service_dest = get_storage_service(
                StorageProvidersEnum.S3, options={'bucket_name': dest_bucket})
        else:
            self.storage_service_dest = get_storage_service()
        self.source_bucket = source_bucket
        if source_bucket:
            self.storage_service_source = get_storage_service(
                StorageProvidersEnum.S3, options={'bucket_name': source_bucket})
        else:
            self.storage_service_source = get_storage_service()

    def get_files(self, dirs: List[str], file_ext: str, recurse: bool, model_type: str = None) -> List[str]:
        """
        Sync files from given dirs to local folder, based on given extension, and return the list of files

        :param dirs: List of s3 directories (prefixes) that we want to sync locally
        :param file_ext: file extension to filter only target file type
        :param recurse: bool, if true, sync the full file tree from dir, else just look at the first level
        :param model_type: expected model type, if trying to sync model folder
            NOTE: unclear how this is being used
        """
        files = []
        local_paths_out = []
        for folder in dirs:
            local_path = os.path.join(self.parent_dir, folder)
            operations_logger.info(f'Parent dir: {self.parent_dir}, folder: {folder}, local path: {local_path}')
            self.sync_down(folder, local_path)
            if model_type:
                operations_logger.debug(f'Using model type {model_type}')
                files.extend(common.get_model_file_list(local_path, file_ext, model_type, recurse))
            else:
                if not os.path.isdir(local_path):
                    # combine_paths() returns a combination that doesnt exist, eg manual sync to local parent_dir
                    operations_logger.info(f"Folder does not exist: {local_path}")
                    continue
                files.extend(common.get_file_list(local_path, file_ext, recurse))
            local_paths_out.append(local_path)
        operations_logger.info(f"Synced {len(files)} files to: {local_paths_out}")
        return files

    def get_active_learning_text_files(self, recurse: bool = True):
        active_text_files = []
        if self.active_text_dirs:
            dirs_to_get = self.active_text_dirs
            active_text_files.extend(self.get_files(dirs_to_get, self.TEXT_SUFFIX, recurse))
        operations_logger.info(f'Active Learning Text files: {len(active_text_files)}')
        return active_text_files

    def async_file_from_assumed_path(self, path):
        # takes in a/b/c.ext and outputs a/b/processed/documents/c/c.ext to mimic async pipeline
        doc_dir, doc_fn = os.path.split(path)
        doc_fn_split = doc_fn.split('.')
        doc_uuid = doc_fn_split[0]
        if len(doc_fn_split) > 0:
            operations_logger.warning(f'{doc_fn} has length greater than 2, this file name format is not supported')
        intermediate_dirs = os.path.join('processed', 'documents', doc_uuid)
        doc_ext = doc_fn_split[-1]
        new_doc_fn = f'{doc_uuid}.extracted_text.{doc_ext}'
        full_fp = os.path.join(doc_dir, intermediate_dirs, new_doc_fn)
        return full_fp

    def get_text_from_ann_file(self, ann_file: str, context: DataSourceContext = None):
        for ann_dir in self.ann_dirs_from_context(context):
            if ann_dir in ann_file:
                prefix = f'/{self.text_dir_prefix}/' if self.text_dir_prefix else "/"
                txt_file = ann_file\
                    .replace(f'/{ann_dir}/', prefix)\
                    .replace(self.HUMAN_ANNOTATION_SUFFIX, self.TEXT_SUFFIX)

                if os.path.isfile(txt_file):
                    return txt_file
                else:
                    updated_path_async = self.async_file_from_assumed_path(txt_file)
                    if os.path.isfile(updated_path_async):
                        return updated_path_async

        operations_logger.info(f'Failed to find text file for ann file: {ann_file}')

    def get_active_learning_jsons(self, recurse: bool = True):
        active_json_files = []
        if self.active_feature_set_dirs:
            dirs_to_get = self.active_feature_set_dirs
            active_json_files.extend(self.get_files(dirs_to_get, '.json', recurse))
        operations_logger.info(f'Active Learning JSON files: {len(active_json_files)}')
        return active_json_files

    def get_text_for_active_json(self, json_fp):
        if self.active_feature_set_dirs and self.active_text_dirs:
            for active_dir in self.active_feature_set_dirs:
                if active_dir in json_fp:
                    for text_dir in self.active_text_dirs:
                        if text_dir in json_fp:
                            base_path = json_fp.replace(active_dir, text_dir).replace('json', 'txt')
                            if os.path.exists(base_path):
                                return base_path

                            for folder in ['train', 'test']:
                                path = base_path.replace(f'{os.path.sep}{folder}{os.path.sep}', os.path.sep)
                                if os.path.exists(path):
                                    return path

    def get_original_raw_text_files(self, recurse: bool = True, orig_dir: str = None,
                                    context: DataSourceContext = None) -> List[str]:
        original_raw_text_files = []
        if orig_dir:
            dirs_to_get = [orig_dir]
        else:
            dirs_to_get = self.text_from_context(context=context)
        if dirs_to_get:
            original_raw_text_files.extend(self.get_files(dirs_to_get, self.TEXT_SUFFIX, recurse))
        if self.async_mode:
            original_raw_text_files = [file for file in original_raw_text_files if '/chunks/' not in file]
        operations_logger.info(f'Original raw text file count: {len(original_raw_text_files)}')
        return original_raw_text_files

    def get_feature_set_annotation_files(self, recurse: bool = True, orig_dir: str = None, get_old: bool = False,
                                         context: DataSourceContext = None):
        feature_set_annotation_files = []
        fs_version = self.feature_set_version

        subfolders = self.feature_set_subfolders_from_context(context)
        if subfolders:
            combined_subfolders = [os.path.join(fs_version, fs_subfolder) for fs_subfolder in
                                   subfolders]
        else:
            combined_subfolders = [fs_version]

        # get the new files as well as the old files
        if get_old:
            operations_logger.debug('Getting Old feature set version')
            fs_version = self.old_feature_set_version
            if subfolders:
                combined_subfolders.extend(
                    [os.path.join(fs_version, fs_subfolder) for fs_subfolder in subfolders])
            else:
                combined_subfolders.extend([fs_version])

        combined_paths = self.combine_paths(combined_subfolders, orig_dir=orig_dir, context=context)
        feature_set_annotation_files.extend(self.get_files(combined_paths, self.MACHINE_ANNOTATION_SUFFIX, recurse))

        operations_logger.info(f'Feature set annotation file count: {len(feature_set_annotation_files)}')
        return feature_set_annotation_files

    def text_from_context(self, context: DataSourceContext = None):
        if context == DataSourceContext.testing:
            return self.testing_text_dirs
        elif context == DataSourceContext.validation:
            return self.validation_text_dirs
        return self.original_raw_text_dirs

    def feature_set_subfolders_from_context(self, context: DataSourceContext = None):
        if context == DataSourceContext.testing:
            return self.testing_fs_subfolders
        elif context == DataSourceContext.validation:
            return self.validation_fs_subfolders
        return self.feature_set_subfolders

    @classmethod
    def get_brat_label(
            cls, ann_file: str, label_enum: [LabelEnum, Type[LabelEnum]], parse_labs=False
    ) -> List[Annotation]:
        """
        Get the BRAT formatted annotations from a .ann file
        This will split annotation phrases into separate labels
        :param ann_file: str, the absolute path to the target ann file
        :param label_enum: the target labels to pull from the annotation file
        :param parse_labs: bool, if true use rule based parsing to turn any "lab" label into a
            "value", "unit", or "interp"
        """
        if parse_labs and label_enum == LabLabel:
            # NOTE(mjp): this returns a list of Annotations, rather than the dict of annotations with ids as keys
            return cls.get_brat_lab_name_value_unit(ann_file)
        else:
            response_list = []
            res = cls.parse_brat_ann_with_link_info(ann_file)
            for tag in res:
                try:
                    label = label_enum.from_brat(res[tag].label)
                except ValueError:
                    continue
                except KeyError:
                    operations_logger.debug(ann_file, tag)
                    continue

                if label and label.value.column_index != 0:
                    res[tag].label = label.value.persistent_label
                    response_list.append(res[tag])
                    label = None
            return response_list

    @classmethod
    def get_brat_lab_name_value_unit(cls, ann_file):
        """
        this function is used to get the demographic types from the ann file
        filter out some of the un-related types such as "DATE" from deid types
        """
        lab_list = []
        res = cls.parse_brat_ann_with_link_info(ann_file)
        for tag in res:
            try:
                label = LabLabel.from_brat(res[tag].label)

            except ValueError:
                continue
            if label and label is not LabLabel.na:
                # can add a check here for checking start end position

                # change it to be lab name, lab value or lab unit labeling if necessary
                lab_text = res[tag].text

                # get the numbers (or unit) out, assign its aspect to be value, and change the range relatively
                tokens = cls.tokenize(lab_text)

                for token in tokens:
                    # find which one is the number, which one is the unit and which one is the term
                    lab_copy = copy.deepcopy(res[tag])
                    start_index = lab_text.index(token)
                    lab_copy.text_range = [res[tag].text_range[0] + start_index,
                                           res[tag].text_range[0] + start_index + len(token)]
                    lab_copy.text = token

                    if token.lower().strip() in LAB_INTERP_TERMS:
                        lab_copy.label = LabLabel.lab_interp.value.persistent_label
                    elif is_digit_punctuation(token) or seconds_digit(token):
                        lab_copy.label = LabLabel.lab_value.value.persistent_label
                    elif probable_lab_unit(token):
                        # potentially a lab unit
                        # needs a more comprehensive way to include lab unit
                        lab_copy.label = LabLabel.lab_unit.value.persistent_label
                    lab_list.append(lab_copy)

        return lab_list

    @staticmethod
    def parse_brat_ann_with_link_info(file_path: str) -> Dict[str, Annotation]:
        content = common.read_text(file_path)
        res = AnnotationSet.from_file_content(content=content).directory
        return res

    @staticmethod
    def get_token_size(files):

        total_tokens = 0
        for fn in files:
            with open(fn) as f:
                file_tc = len(json.load(f))
                total_tokens += file_tc

        return total_tokens

    def combine_paths(self, parent_paths: List[str], orig_dir: str = None, context: DataSourceContext = None):
        if not orig_dir:
            orig_text_dirs = self.text_from_context(context=context)
        else:
            orig_text_dirs = [orig_dir]
        combined_paths = []
        for orig_path in orig_text_dirs:
            for parent_path in parent_paths:
                combined_paths.append(os.path.join(parent_path, orig_path))
        return combined_paths

    def update_file_path(self, absolute_file_path, sub_dir):
        combined = os.path.join(self.feature_set_version, sub_dir)
        return absolute_file_path.replace(self.feature_set_version, combined)

    def sync_down(self, source_path: str, dest_path: str, options: list = None):
        if not Environment.USE_STORAGE_SERVICE.value:
            return
        s3_bucket = self.storage_service_source.get_container()
        operations_logger.info(f'Syncing down {source_path} to {dest_path}')
        s3_bucket.sync_down(source_path, dest_path,  additional_options=options)

    def sync_up(self, source_path: str, dest_path: str):
        if not Environment.USE_STORAGE_SERVICE.value:
            return
        if not os.path.isdir(source_path) and not os.path.isfile(source_path):
            operations_logger.info(f'{source_path} does not exist')
            return
        s3_bucket = self.storage_service_dest.get_container()
        operations_logger.info(f'Syncing up {source_path} to {dest_path}')
        s3_bucket.sync_up(source_path, dest_path)

    def ann_dirs_from_context(self, context: DataSourceContext = None):
        if context == DataSourceContext.testing:
            return self.testing_ann_dirs
        elif context == DataSourceContext.validation:
            return self.validation_ann_dirs
        elif context == DataSourceContext.train or not context:
            return self.ann_dirs
        else:
            raise ValueError(f"No such context: {context}")

    def get_ann_files(self, ann_dir: str = None, recurse: bool = True, orig_dir: str = None,
                      label_enum: LabelEnum = None, context: DataSourceContext = None) -> List[str]:
        ann_files = []
        ann_files_with_results = []
        if ann_dir:
            ann_dirs = [ann_dir]
        else:
            ann_dirs = self.ann_dirs_from_context(context)

        combined_paths = self.combine_paths(ann_dirs, orig_dir=orig_dir, context=context)
        operations_logger.info(f"combined_paths: {combined_paths}")
        ann_files.extend(self.get_files(combined_paths, self.HUMAN_ANNOTATION_SUFFIX, recurse))
        operations_logger.info(f"Total Number of ann files found: {len(ann_files)}")
        if self.include_all_ann_files:
            ann_files_with_results = ann_files
        else:
            for ann_file in ann_files:
                if label_enum and self.ann_file_inclusion(label_enum, ann_fp=ann_file):
                    ann_files_with_results.append(ann_file)
                elif not label_enum:
                    ann_files_with_results.append(ann_file)

        operations_logger.info(f'.ann file count: {len(ann_files_with_results)}')
        return ann_files_with_results

    def ann_file_inclusion(self, label_enum, ann_fp):
        brat_label = self.get_brat_label(ann_fp, label_enum)
        bool_val = len(brat_label) > 0
        if bool_val and self.required_label_names:
            labels = {entry.label for entry in brat_label}
            bool_val = len(set(self.required_label_names).difference(labels)) <= 0
            if not bool_val:
                operations_logger.info(f'Not all required labels were found, found: {labels}, '
                                       f'required_labels: {self.required_label_names}')
        return bool_val

    def to_json(self):
        return {
            'parent_dir': self.parent_dir,
            'original_raw_text_dirs': self.original_raw_text_dirs,
            'feature_set_version': self.feature_set_version,
            'ann_dirs': self.ann_dirs,
            'testing_text_dirs': self.testing_text_dirs,
            'testing_ann_dirs': self.testing_ann_dirs,
            'feature_set_jira': self.feature_set_version,
            'validation_text_dirs': self.validation_text_dirs,
            'validation_ann_dirs': self.validation_ann_dirs,
            'active_feature_set_dirs': self.active_feature_set_dirs,
            'active_text_dirs': self.active_text_dirs,
            'active_ann_jira': self.active_ann_jira,
            'feature_set_subfolders': self.feature_set_subfolders,
            'testing_fs_subfolders': self.testing_fs_subfolders,
            'validation_fs_subfolders': self.validation_fs_subfolders,
            'required_label_names': self.required_label_names,
            'max_token_count': self.max_token_count
        }

    def save(self, job_id: str, results_path=Environment.DATA_ROOT.value):
        path = os.path.join(results_path, job_id, 'data_source.json')
        return common.write_json(self.to_json(), path)
