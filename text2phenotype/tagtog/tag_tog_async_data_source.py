import datetime
import json
import os
import shutil

from typing import List, Tuple

from text2phenotype.annotations.file_helpers import AnnotationSet
from text2phenotype.common import common
from text2phenotype.common.log import operations_logger
from text2phenotype.constants.features.label_types import LabelEnum

from text2phenotype.tagtog.tag_tog_annotation import TagTogAnnotationSet
from text2phenotype.tagtog.tagtog_html_to_text import TagTogText


class TagTogAsyncDataSource:
    """
    This objects only purpose is to work on the unzipped version of the folder you get in tagtog
    when you download all via the ui. By running the write_raw_materials function,
    you will get an output at your parent_dir /gold_tag_tog_extracted.
    The output file structure is as follows
    /gold_tag_tog_extracted
        /tag_tog_text
            /tag_tog_folder ie: I2B2
                /text_file.txt
        /tag_tog_annotations
            /tag_tog_project_name
                /date of running the script
                    /annotator_member_id
                        /tag_tog_folder
                            /text_file
    """
    ANNOTATION_LEGEND_FN = 'annotations-legend.json'
    DOC_PATH_DIR = 'plain.html'
    ANN_JSON_DIR = 'ann.json'
    MASTER_DIR = 'master'
    MEMBERS = 'members'
    POOL = 'pool'
    HTML_SUFFIX = '.plain.html'
    ANN_JSON_SUFFIX = '.ann.json'
    MACHINE_ANNOTATION_EXT = '.annotation.json'

    OUTPUT_FOLDER = 'gold_tag_tog_extracted'
    TEXT_SUFFIX = '.txt'
    ANN_SUFFIX = '.ann'
    RAW_TEXT_OUT = 'tag_tog_text'
    ANNOTATION_FOLDER = 'tag_tog_annotations'

    def __init__(
        self,
        project: str,
        parent_dir: str,
        include_master_annotations: bool = True,
        require_complete: bool = False,
        label_type: LabelEnum = None,
        norm_text_field: str = None
    ):
        """
        Load all resource parameters to convert TagTog annotations to Text2phenotype annotations
        or vice versa

        :param project: name of TT project
        :param parent_dir: local path containing the project name
        :param include_master_annotations:
        :param require_complete: only use annotations marked "complete"
        :param label_type: specific label_type to use, avoids label collisions (eg between Lab & CovidLab)
        :param norm_text_field: str, name of Entity Field from TagTog that contains the "normalized"
            (visually correct) text from the annotation; used in PDF annotations
            This will use the ORIGINAL text_ranges (wont match the raw text positions) unless
            the `TagTogAnnotation.convert_to_gold` option is set to true,
            which will then use the "gold" text_ranges
            If None, dont apply normed text to annotation
        """
        self.parent_dir = parent_dir
        self.project = project
        self.tag_tog_all_dir = os.path.join(self.parent_dir, self.project)
        self.html_dir = os.path.join(self.tag_tog_all_dir, self.DOC_PATH_DIR, self.POOL)
        self.ann_json_dir = os.path.join(self.tag_tog_all_dir, self.ANN_JSON_DIR)
        self.require_complete = require_complete  # only include annotations that have been marked as complete
        self.label_type = label_type  # include this only if we expect a single labeltype, eg LabLabels
        self.norm_text_field = norm_text_field

        self.include_master_annotations = include_master_annotations

        self._annotation_legend = None
        self._original_text_dirs = None
        self.date = datetime.date.today().isoformat()

    @property
    def annotation_legend_fp(self):
        return os.path.join(self.parent_dir, self.project, self.ANNOTATION_LEGEND_FN)

    @property
    def annotation_legend(self):
        if not self._annotation_legend and os.path.isfile(self.annotation_legend_fp):
            self._annotation_legend = common.read_json(self.annotation_legend_fp)
        return self._annotation_legend

    @annotation_legend.setter
    def annotation_legend(self, value):
        self._annotation_legend = value

    @property
    def output_parent_dir(self) -> str:
        return os.path.join(self.parent_dir, self.OUTPUT_FOLDER)

    @property
    def annotation_parent_dir(self) -> str:
        """
        Return the output parent folder for the BRAT formatted annotations, currently the date extraction is run
        If using norm_text_field, will append "_norm" to the date
        """
        date_folder = self.date + "_norm" if self.norm_text_field else self.date
        return os.path.join(self.output_parent_dir, self.ANNOTATION_FOLDER, self.project, date_folder)

    @property
    def text_parent_dir(self) -> str:
        return os.path.join(self.output_parent_dir, self.RAW_TEXT_OUT)

    @staticmethod
    def trim(string):
        out_str = string.strip('/')
        return out_str

    @staticmethod
    def validate(ann_set: AnnotationSet, text: str):
        """
        Iterate through the annotations and compare to raw text
        If annotation text does not match the given text in the raw text:
            - see if text is nearby (within 100 characters) and update text_range
            - else, remove the annotation

        NOTE: different embedded text from PDF will possibly not match the raw text from a different OCR method
        This means that a different OCR (eg Google) will return different text than what is set in the .ann file.

        :param ann_set: AnnotationSet
        :param text: str, the raw text the annotations were derived from (from tagtog html)
        """
        entries_to_readd = []
        for ann in ann_set.entries:
            text_range = ann.text_range
            # check if the text from the annotation matches the actual text with that offset in the document
            if (
                ann.text != text[text_range[0]: text_range[1]] and
                ann.text != text[text_range[0]:text_range[1]].replace('\n', ' ')
            ):
                # if it's not try finding the text nearby and if you are able to find it, update the annotation range
                find_range = text.replace('\n', ' ').find(ann.text, text_range[0] - 100)
                ann_set.entries.remove(ann)
                if find_range > 0:
                    ann.text_range = [find_range, find_range + len(ann.text)]
                    entries_to_readd.append(ann)
                elif (len(ann.text) == text_range[1] - text_range[0] and
                      all([entry in text[text_range[0]:text_range[1]] for entry in ann.text.split()])):
                    ann.text = text[text_range[0]:text_range[1]]
                    entries_to_readd.append(ann)
                else:
                    # if you can't find the annotation text anywhere nearby, remove the annotation
                    operations_logger.info('Text and ann range do not match up, removing entry')
        operations_logger.info(f'returning annotation set with {len(ann_set.entries)} entries')
        ann_set.entries.extend(entries_to_readd)

    def __get_raw_text_raw_ann(
            self,
            html_path,
            ann_json_path,
            convert_to_gold: bool = False,
    ) -> Tuple[str, AnnotationSet]:
        """
        :param html_path: local path for the .html file
        :param ann_json_path: local path for the .ann_json path
        :param convert_to_gold: boolean, if True, convert annotation ranges to
            the expected position in the raw text file with character length changes

        :return: Tuple of [text, AnnotationSet]
        """
        tag_tog_text = TagTogText(common.read_text(html_path))
        ann_json = TagTogAnnotationSet(
            ann_json_content=common.read_json(ann_json_path),
            label_type=self.label_type,
            norm_text_field=self.norm_text_field,
            convert_to_gold=convert_to_gold,
        )
        annotation_set = ann_json.to_annotation_set(tag_tog_text.html_mapping_to_text, self.annotation_legend)
        # will create an error if the ranges don't add up
        if not self.norm_text_field:
            # validation will fail if using normalized text
            self.validate(annotation_set, tag_tog_text.raw_text)

        return tag_tog_text.raw_text, annotation_set

    def __html_path(self, file_id, project_subfolder=None):
        return os.path.join(
            self.html_dir, project_subfolder, f'{file_id}{self.HTML_SUFFIX}')

    def __ann_json_path(self, file_id, annotator_dir, project_subfolder=None):
        return os.path.join(
            self.ann_json_dir, annotator_dir, self.POOL, project_subfolder, f'{file_id}{self.ANN_JSON_SUFFIX}')

    def __create_out_file_system(self, project_subfolders: list, ann_dirs: list, create_combined: bool = False):
        os.makedirs(self.text_parent_dir, exist_ok=True)
        for subfolder in project_subfolders:
            os.makedirs(os.path.join(self.text_parent_dir, self.project, subfolder), exist_ok=True)

        for ann_dir in ann_dirs:
            ann_dir = os.path.join(self.annotation_parent_dir, ann_dir)
            for subfolder in project_subfolders:
                os.makedirs(os.path.join(ann_dir, subfolder), exist_ok=True)

        if create_combined:
            combined_ann_dir = os.path.join(self.annotation_parent_dir, "combined")
            os.makedirs(combined_ann_dir, exist_ok=True)
            for subfolder in project_subfolders:
                combined_subfolder = os.path.join(combined_ann_dir, subfolder)
                if os.path.exists(combined_subfolder) and os.path.isdir(combined_subfolder):
                    # if it already exists, zap it and recreate all content, since merging is weird
                    shutil.rmtree(combined_subfolder)
                os.makedirs(combined_subfolder, exist_ok=True)

    def raw_text_out_path(self, file_id, project_subfolder, suffix=TEXT_SUFFIX):
        if suffix != file_id[-len(suffix):]:
            file_name = f"{file_id}{suffix}"
        else:
            file_name = file_id
        return os.path.join(self.text_parent_dir, self.project, project_subfolder, file_name)

    def raw_ann_out_path(self, file_id, project_subfolder, annotator_dir):
        file_name = f"{file_id.split('.txt')[0]}{self.ANN_SUFFIX}"
        ann_dir = annotator_dir.replace(f'{self.MEMBERS}/', '')
        return os.path.join(self.annotation_parent_dir, ann_dir, project_subfolder, file_name)

    def _get_all_annotation_files(self):
        """
        :return: List tuple of (file_id, project_subfolder, annotator_path
        """
        if self.include_master_annotations:
            all_ann_files = common.get_file_list(self.ann_json_dir, self.ANN_JSON_SUFFIX, True)
        else:
            all_ann_files = common.get_file_list(
                os.path.join(self.ann_json_dir, self.MEMBERS), self.ANN_JSON_SUFFIX, True)
        output = []
        for file in all_ann_files:
            # try reading in annotation files, note that sometimes tag tog download have a non-json compatible output
            # due to an extra } at the end of the file so if a file can't be read in, rewrite the file locally in
            # json compatible form
            # TODO re-push the updated annotation file to tag tog
            try:
                ann_json = common.read_json(file)
            except:
                operations_logger.warning(f'ANN JSON not json compatible {file}')
                json_text = common.read_text(file)
                json_dict = json.loads(json_text[:-1])
                common.write_json(json_dict, file)
                continue
            if self.require_complete:
                if not common.read_json(file).get('anncomplete', False):
                    continue
            file_dir, file_id = os.path.split(file)
            file_id = file_id.replace(self.ANN_JSON_SUFFIX, '')
            file_dir_info = file_dir.replace(self.ann_json_dir, '')
            split_on_pool = file_dir_info.split(self.POOL)
            member_dir = split_on_pool[0]
            project_subfolder = split_on_pool[1]
            output.append((file_id, self.trim(project_subfolder), self.trim(member_dir)))
        return output

    def write_raw_materials_for_annotated_materials(
            self,
            create_combined: bool = False,
    ):
        """
        Create Text2phenotype formatted .ann and .txt files from TagTogAnnotations

        :param create_combined: bool, if true concatenate all annotation files into 'combined' folder
        :param norm_text_field: str, name of Entity Field from TagTog that contains the "normalized"
            (visually correct) text from the annotation; used in PDF annotations
        """
        all_annot = self._get_all_annotation_files()
        operations_logger.info(f'Found {len(all_annot)} annotations')
        proj_subfolders = set([entry[1] for entry in all_annot])
        ann_dirs = set([self.trim(entry[2].replace(self.MEMBERS, '')) for entry in all_annot])
        # make sure out dir exists locally
        self.__create_out_file_system(
            project_subfolders=list(proj_subfolders),
            ann_dirs=list(ann_dirs),
            create_combined=create_combined)
        for row in all_annot:
            file_id, project_subfolder, annotator = row
            html_path = self.__html_path(file_id=file_id, project_subfolder=project_subfolder)
            ann_path = self.__ann_json_path(file_id=file_id, annotator_dir=annotator, project_subfolder=project_subfolder)
            text, ann_set = self.__get_raw_text_raw_ann(html_path, ann_path)

            if isinstance(text,  str) and isinstance(ann_set, AnnotationSet):
                cleaned_file_id = file_id.split('-')[1]
                text_path = self.raw_text_out_path(file_id=cleaned_file_id, project_subfolder=project_subfolder)
                ann_path_out = self.raw_ann_out_path(
                    file_id=cleaned_file_id, annotator_dir=annotator, project_subfolder=project_subfolder)

                # write text and ann out
                assert os.path.isdir(os.path.dirname(text_path))
                assert os.path.isdir(os.path.dirname(ann_path_out))
                common.write_text(text, text_path)
                common.write_text(ann_set.to_file_content(), ann_path_out)
                if create_combined:
                    annotator_out = annotator.split("/")[-1]
                    combined_ann_path_out = ann_path_out.replace(f"/{annotator_out}/", "/combined/")
                    # TODO: add merge duplicates for files annotated by multiple people?
                    if os.path.isfile(combined_ann_path_out):
                        # append extension so we have both, but the duplicate isnt used
                        orig = combined_ann_path_out
                        combined_ann_path_out += f".duplicatefrom_{annotator_out}"
                        operations_logger.warning(f"COMBINE_ANN: Found duplicate file: {orig}, "
                                                  f"writing current ann to: {combined_ann_path_out}")
                    common.write_text(ann_set.to_file_content(), combined_ann_path_out)
            else:
                operations_logger.info('No text or ann set found')

    def write_normalized_ann_for_ann_materials(self):
        """
        Identify "normalized_text" entity label, use that text for .ann file if it exists
        """
        pass

    def get_tagtog_text(self, filename):
        """Given a target filename, return the TagTogText object for that file"""
        all_annot = self._get_all_annotation_files()
        matching = [row for row in all_annot if filename in row[0]]
        if len(matching) > 1:
            operations_logger.info(f"Found more than one match for filename: {filename}: {matching}")
        elif not matching:
            operations_logger.info(f"No match found for filename: {filename}")
        else:
            matching = matching[0]

        html_path = self.__html_path(file_id=matching[0], project_subfolder=matching[1])
        tag_tog_text = TagTogText(common.read_text(html_path))
        return tag_tog_text

