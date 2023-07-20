from typing import List

from text2phenotype.annotations.file_helpers import Annotation, AnnotationSet
from text2phenotype.common.log import operations_logger
from text2phenotype.constants.common import VERSION_INFO_KEY
from text2phenotype.constants.features.label_types import LabelEnum, LabelList
from text2phenotype.tagtog.tagtog_html_to_text import TagTogText
from text2phenotype.constants.environment import Environment

VERBATIM_TEXT_HTML_PARTS = ['s1v1']


class TagTogEntity:
    def __init__(self, **kwargs):
        self.class_id = kwargs.get('classId')
        self.part = kwargs.get('part')
        offsets = kwargs.get('offsets')
        if offsets:
            self.text = offsets[0]['text']
            self.range = [offsets[0]['start'], offsets[0]['start'] + len(self.text)]
        else:
            self.text = kwargs.get('text')
            self.range = kwargs.get('text_range')
        self.score = kwargs.get('score', 1)

        self.fields = kwargs.get('fields')
        # other features in ann_json entities include, 'coordinates', 'confidence', 'fields', 'normalizations'

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"text={self.text!r}, class_id={self.class_id!r}, "
            f"text_range={self.range!r}, field_keys={list(self.fields.keys())}"
            ")"
        )

    def update_tag_tog_offset_to_range(self, html_part_pos_mapping: dict, ):
        if self.part not in html_part_pos_mapping:
            raise ValueError(f'Part {self.part} not found in the mapping of html part to raw_text position')
        updated_range = [self.range[0] + html_part_pos_mapping[self.part],
                         self.range[1] + html_part_pos_mapping[self.part]]
        return updated_range

    def update_class_label(self, annotation_legend: dict):
        if self.class_id not in annotation_legend:
            operations_logger.warn(f'Entity Label {self.class_id} not found in annotation legend {annotation_legend}')

        return annotation_legend.get(self.class_id)

    def to_annotation(self, html_part_map: dict, annotation_legend: dict, label_type=None, norm_text_field=None):
        """
        Convert TagTogAnnotation to Annotation

        :param html_part_map:
        :param annotation_legend:
        :param label_type: LabelEnum, the target label if we want to look within a specific label category
        :param norm_text_field: str, use `normalized_text` field from annotation legend as output text
        """
        text_range = self.update_tag_tog_offset_to_range(html_part_map)
        label: LabelEnum = self.get_label_type(
            self.update_class_label(annotation_legend), label_type=label_type)
        text_out = self.text

        if norm_text_field and self.fields:
            # if we have a target field to read in and it exists for the entity,
            # save the entity text
            tt_norm_key = self._get_norm_text_key(norm_text_field, annotation_legend)
            if tt_norm_key in self.fields.keys():
                text_out = self.fields[tt_norm_key]["value"]
                # text_range = [text_range[0], text_range[0] + len(text_out)]

        if label:
            return Annotation(
                text=text_out.replace('\n', ' '),
                text_range=text_range,
                label=label.value.persistent_label,
                coord_uuids=[],
                line_start=None,
                line_stop=None,
                category_label=None)
        else:
            operations_logger.warning(f"Error in finding label for annotation: {self.text}, {self.range}")

    @staticmethod
    def _get_norm_text_key(norm_text_field, annotation_legend):
        field_legend = {k: v for k, v in annotation_legend.items() if k.startswith("f")}
        if norm_text_field not in field_legend.values():
            raise ValueError(
                "Got unexpected target for normalized_text field: "
                f"{norm_text_field} not in {list(field_legend.values())}")
        # get the legend key that matches the norm_text_field
        tt_field = [k for k, v in field_legend.items() if v == norm_text_field][0]
        return tt_field

    @staticmethod
    def get_label_type(text: str, label_type: LabelEnum = None) -> LabelEnum:
        """
        Get the LabelType name from the text label. If the target LabelType is known, use that
        This avoids possible collisions, for example "lab" returning either LabLabel or CovidLabLabel

        :param text: label text from tag tog
        :param label_type: LabelEnum; if specified, look for label text match in this category
        """
        non_na_label = None
        if label_type:
            non_na_label = label_type.from_brat(text)
        else:
            # NOTE: may return an incorrect label name if the name exists in multiple LabelTypes
            for label_type_enum in LabelList:
                label = label_type_enum.from_brat(text)
                if label.value.column_index != 0 and label.value.persistent_label not in ['na',  'other']:
                    non_na_label = label

        return non_na_label

    @classmethod
    def from_annotation(
            cls,
            annotation: Annotation,
            inverse_annotation_legend,
            part=VERBATIM_TEXT_HTML_PARTS[0],
            text_range=None):
        if annotation.label in inverse_annotation_legend:
            class_id = inverse_annotation_legend.get(annotation.label)

            if class_id is None:
                raise ValueError(f'No class id found matching {annotation.label} in {inverse_annotation_legend}')
            if text_range is None:
                text_range = annotation.text_range

            return cls(text=annotation.text, text_range=text_range, classId=class_id, part=part)

    def to_json(self):
        return {
            'offsets': [{'start': self.range[0], "text": self.text}],
            'part': self.part,
            'classId': self.class_id,
            'fields': self.fields if self.fields else {},
            'coordinates': [],
            'confidence':
                {
                    "state": "pre-added",
                    "who": [f"user:{Environment.TAG_TOG_USER.value}"],
                    "prob": self.score
                },
            'normalizations': {}
        }


LAB_ATTRIBUTE_MAPPING = {'labInterp': 'lab_interp', 'labValue': 'lab_value', 'labUnit': 'lab_unit'}


class TagTogAnnotationSet:

    def __init__(
            self,
            ann_json_content: dict = None,
            entities: List[TagTogEntity] = None,
            label_type: LabelEnum = None,
            norm_text_field: str = None,
            convert_to_gold: bool = False
    ):
        """
        Create an annotation set from tag tog json
        If there is a singular expected label type, pass it in to avoid LabelType collisions

        :param label_type: specific label_type to use, avoids label collisions (eg between Lab & CovidLab)
        :param norm_text_field: name of the TT entity field that contains the normalized (visually corrected) text
        :param convert_to_gold: boolean, if True, convert annotation ranges to
            the expected position in the raw text file with character length changes
        """
        self.anncomplete: bool = False
        self.entities: List[TagTogEntity] = entities or []
        self.relations: List = []
        self.label_type = label_type
        self.norm_text_field = norm_text_field
        self.convert_to_gold = convert_to_gold
        if ann_json_content is not None:
            self.from_ann_json(ann_json_content)

    def from_ann_json(self, ann_json: dict):
        self.anncomplete = ann_json.get('anncomplete')

        if self.convert_to_gold:
            # add raw text offset for changes in normalized text length
            norm_char_offset = 0  # cumulative character offset
            entities = []
            for entity_dict in ann_json.get('entities'):
                fields = entity_dict.get("fields")
                offsets = entity_dict.get('offsets')
                if offsets:
                    offsets[0]["start"] += norm_char_offset
                if self.norm_text_field and fields and offsets:
                    # ew, this should be using the annotation legend
                    norm_text = fields[list(fields.keys())[0]]['value']
                    if offsets[0]["text"] != norm_text:
                        char_diff = len(norm_text) - len(offsets[0]["text"])
                        norm_char_offset += char_diff
                        offsets[0]["text"] = norm_text
                entities.append(TagTogEntity(**entity_dict))
            self.entities = entities
        else:
            self.entities = [
                TagTogEntity(**entity_dict)
                for entity_dict in ann_json.get('entities')]
        # self.relations = ann_json.get('relations')
        # other fields in the the ann_json are
        # annotatable: {'parts': a list of the section names}
        # sources: []
        # metas: {}
        # relations: [{'classId': 'r_7', 'type': 'linked', 'directed': False,
        # 'entities': ['s1p11|e_1|3,17', 's1p11|e_4|19,35'],  #(list of section for ent in link, entity_label, offsets),
        # 'confidence': {'state': 'pre-added', 'who': ['user:sfee'], 'prob': 1}}]

    def to_annotation_list(self, html_part_map, annotation_legend):
        return [
            entity.to_annotation(
                html_part_map=html_part_map,
                annotation_legend=annotation_legend,
                label_type=self.label_type,
                norm_text_field=self.norm_text_field
            )
            for entity in self.entities
        ]

    def sort_entities(self):
        self.entities = sorted(self.entities,  key=lambda x: x.range)

    def to_annotation_set(self, html_part_map: dict, annotation_legend: dict) -> AnnotationSet:
        """
        Create Text2phenotype AnnotationSet from TagTogAnnotation
        """
        id_num = 0
        directory = dict()
        ann_set = AnnotationSet()
        for ent in self.entities:
            annotation = ent.to_annotation(
                html_part_map=html_part_map,
                annotation_legend=annotation_legend,
                label_type=self.label_type,
                norm_text_field=self.norm_text_field
            )
            # annotation will be None if the label text isnt found
            # but will have label 'na' if label_type is specified and not matched
            if annotation:
                directory[f'T_{id_num}'] = annotation
                id_num += 1

        ann_set.directory = directory
        return ann_set

    def to_json(self, html_parts: List[str] = None):
        """
        :param html_parts: List of html_parts, if none assumes verbatim text record formatting
        :return: json file in the tag tog annjson format
        """
        if not html_parts:
            html_parts = VERBATIM_TEXT_HTML_PARTS
            operations_logger.info(
                'No html parts passed to function, assuming that the ann_json is for a verbatim text record')

        return {"anncomplete": True,
                "sources": [],
                "metas": {},
                "relations": [],
                "annotatable": {"parts": html_parts},
                "entities": [ent.to_json() for ent in self.entities]
                }

    def check_clean_entities(self, entry: TagTogEntity, text: str) -> List[TagTogEntity]:
        """
        :param entry: a single tag tog entity
        :param text: the full record text
        :return: list of tag tog entities that map to the text, splits annotations that contain new lines into two
         annotations bc tag tog gets mad if we don't, if the annotation does not match the text exactly,
          look around a little bit, sometimes tag tog messes up offsets
        """
        entry_list = []
        if isinstance(entry.text,  float):
            entry.text = text[entry.range[0]: entry.range[1]]
            entry_list.append(entry)
            return entry_list


        if text[entry.range[0]: entry.range[1]].strip() == entry.text.strip():
            entry_list.append(entry)

        elif '\n' in text[entry.range[0]: entry.range[1]].strip():
            if entry.text.replace(' ', '') == text[entry.range[0]: entry.range[1]].replace('\n', ' ').replace(' ', ''):
                # split entries
                offset = 0
                for txt in text[entry.range[0]: entry.range[1]].split('\n'):
                    if len(txt) >= 1:
                        new_entry = TagTogEntity(
                            text=txt,
                            text_range=[entry.range[0] + offset, entry.range[0] + offset + len(txt)],
                            classId=entry.class_id,
                            part=entry.part
                        )
                        offset += len(txt)
                        entry_list.append(new_entry)
                    offset += 1

        else:
            range_to_look_around = 10
            found_offset = text[entry.range[0] - range_to_look_around:entry.range[1] + range_to_look_around].find(
                entry.text)
            if found_offset > 0:
                entry.range = [entry.range[0] - range_to_look_around + found_offset,
                               entry.range[0] - range_to_look_around + found_offset + len(entry.text)]
                entry_list.append(entry)
            else:
                operations_logger.info("Could not find annotation in correct position of text")
        return entry_list

    def from_annotation_set_for_text(self,  annotation_set: AnnotationSet, inverse_annotation_legend: dict, text: str):
        """
        :param annotation_set: the annotation set object
        :param inverse_annotation_legend: dictionary of label that would be in annotation set to tag tog entity id
        :param text: raw text
        :return: None, updates self entities in place
        """
        for annotation in annotation_set.entries:
            entry = TagTogEntity.from_annotation(annotation, inverse_annotation_legend)
            if not entry:
                continue

            # ensure clean match up between annotation text and tag tog text, ensure there are no newlines
            self.entities.extend(self.check_clean_entities(entry, text=text))

    def from_annotation_set_with_tag_tog_text(
            self,
            annotation_set: AnnotationSet,
            inverse_annotation_legend: dict,
            tag_tog_text: TagTogText):
        """
        :param annotation_set:
        :param inverse_annotation_legend: dictionary of label that would be in annotation set to tag tog entity id
        :param tag_tog_text: tag tog text object initialized from a tag tog html output
        :return: None, updates self entities in place
        """
        for annotation in annotation_set.entries:
            part_start, offset_start = tag_tog_text.offset_from_text_pos(annotation.text_range[0])
            part_end, offset_end = tag_tog_text.offset_from_text_pos(annotation.text_range[1])
            if part_start == part_end:

                entry = TagTogEntity.from_annotation(annotation, inverse_annotation_legend,
                                                     part=part_start, text_range=[offset_start, offset_end])
                if not entry:
                    continue

                # ensure clean match up between annotation text and tag tog text, ensure there are no newlines
                part_start_index = tag_tog_text.html_mapping_to_text[part_start]
                self.entities.extend(self.check_clean_entities(entry, text=tag_tog_text.raw_text[part_start_index:]))
            else:
                operations_logger.warning(
                    "Trying to add an annotation that spans sections is not supported at this time")

    def from_biomed_summary_json(self, biomed_summary_json: dict, annotation_legend: dict, html_text_obj: TagTogText = None):
        """
        :param biomed_summary_json: the output of a biomed_get_summary/task operation json
        :param annotation_legend: mapping of text2phenotype_annotation_name to tag_tog_entity name
        :param html_text_obj: the TagTogText, usse None if  uploading verbatim text
        updates the AnnnotationSet list of entities in place (adding to already existing annotations)
        """
        for key in biomed_summary_json:
            if key != VERSION_INFO_KEY:
                operations_logger.info(f'There are {len(biomed_summary_json[key])}  {key} annotations')
                for entity in biomed_summary_json[key]:
                    self.entities.extend(self.dict_to_ann_json_entity(entity, annotation_legend, html_text_obj))

        operations_logger.info(f"There are annotations for {len(self.entities)} entities")

    @staticmethod
    def dict_to_ann_json_entity(biomed_output_json, annotation_legend, html_text_obj: TagTogText = None):
        """
        :param biomed_output_json: the output json of a biomed ouput or summary output type class
        :param annotation_legend: mapping of text2phenotype_annotation_name to tag_tog_entity name
        :param html_text_obj:
        :return:
        """
        label_ent = []
        # get part and offsets for the annotation
        if html_text_obj is None:
            part, offsets = VERBATIM_TEXT_HTML_PARTS[0],  biomed_output_json['range']
        else:
            part, offsets = html_text_obj.get_part_offsets_range(biomed_output_json['range'])
        if part is None:
            return label_ent

        # get the tag tog class it for the annotation class
        class_id = annotation_legend.get(biomed_output_json['label'])
        if class_id is None:
            operations_logger.warning(
                f"Label {biomed_output_json['label']} not found in annotation legend {annotation_legend}")
            return label_ent

        # append the created tag tog entity from the annotation
        label_ent.append(TagTogEntity(text_range=offsets, text=biomed_output_json['text'], part=part, classId=class_id))

        # if we are looking at a lab, add the attributes as predicted terms if the project allows for such things
        if biomed_output_json['label'] == 'lab':
            for lab_type in LAB_ATTRIBUTE_MAPPING:
                aspect = biomed_output_json[lab_type]
                if aspect:
                    if html_text_obj is None:
                        part, offsets = VERBATIM_TEXT_HTML_PARTS[0], aspect[1:]
                    else:
                        part, offsets = html_text_obj.get_part_offsets_range(aspect[1:])

                    class_id = annotation_legend.get(LAB_ATTRIBUTE_MAPPING[lab_type])
                    if part is not None and class_id is not None:
                        label_ent.append(
                            TagTogEntity(classId=class_id, part=part, text=str(aspect[0]), text_range=offsets))
                    else:
                        operations_logger.warning(f'Failed to add attribute entity for attribute: {lab_type} {aspect}')
        return label_ent

    def to_positions_for_disagree(self, part: str):
        out = list()
        for entity in self.entities:
            if entity.part == part:
                out.append([entity.range, entity.text, entity.class_id])
        return out
