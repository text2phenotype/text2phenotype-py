from typing import (
    Any,
    AnyStr,
    Dict,
    Optional
)
import copy
import json

from text2phenotype.constants.clinical_summary import AnnotationLabelEnum
from text2phenotype.constants.common import VERSION_INFO_KEY
from text2phenotype.entity.attributes import (
    LabAttributes,
    DrugAttributes,
    Polarity,
    TextSpan
)
from text2phenotype.entity.concept import Concept
from text2phenotype.entity.results import (
    Result,
    ResultType
)


class SummaryResult(Result):

    def __init__(self, source: Dict[Any, Any], type: str):
        self.label = None
        self.type = type
        self.text_span = None
        self.concept = None
        self.attributes = None
        self.polarity = None
        if source:
            self.from_dict(source)

    def is_medication(self) -> bool:
        return self.type == ResultType.drug_ner

    def is_lab(self) -> bool:
        return self.type == ResultType.lab_value

    def from_json(self, source: str, type: Optional[str]) -> None:
        if type:
            self.type = type
        return self.from_dict(json.loads(source))

    def from_dict(self, source: Dict[Any, Any]) -> None:
        text_span = [source.get('text'), ]
        if not source.get('range'):
            raise ValueError(f'No range found for input dict {source}')
        text_span.extend(source.get('range'))
        self.text_span = TextSpan(text_span)
        self.concept = Concept(source)
        self.label = source.get('label')
        polarity = source.get('polarity')
        self.polarity = Polarity(polarity) if polarity in [Polarity.POSITIVE, Polarity.NEGATIVE] else polarity
        if self.is_medication():
            self.attributes = DrugAttributes(source)
        elif self.is_lab():
            self.attributes = LabAttributes(source.get('attributes', {}))
        else:
            self.attributes = source.get('attributes')

    def to_json(self, source_format: bool = False) -> str:
        return json.dumps(self.to_dict(source_format))

    def to_dict(self, source_format: bool = False) -> Dict[Any, Any]:
        result = dict()
        result['label'] = self.label
        result['range'] = list(self.text_span.to_tuple())
        result['text'] = self.text_span.text if not source_format else self.text_span.to_json()
        polarity = self.polarity
        if isinstance(self.polarity, Polarity):
            polarity = self.polarity.polarity if not source_format else self.polarity.to_json()
        result['polarity'] = polarity
        if self.concept:
            result.update(self.concept.__dict__)
        if self.is_medication():
            if source_format:
                result.update(self.attributes.to_json())
            else:
                attributes = copy.deepcopy(self.attributes).__dict__
                result['medFrequencyNumber'] = attributes.get('medFrequencyNumber').text
                result['medFrequencyUnit'] = attributes.get('medFrequencyUnit').text
                result['medStrengthNum'] = attributes.get('medStrengthNum').text
                result['medStrengthUnit'] = attributes.get('medStrengthUnit').text
        elif self.is_lab():
            if source_format:
                result['attributes'] = self.attributes.to_json()
            else:
                result['attributes'] = {
                    'labValue': self.attributes.labValue.text if self.attributes.labValue else None,
                    'labValueUnit': self.attributes.labValueUnit.text if self.attributes.labValueUnit else None
                }
        else:
            result['attributes'] = self.attributes
        return result

    def to_table(self, tab='\t'):
        raise NotImplementedError

    @property
    def semantic_type(self):
        raise NotImplementedError


class ClinicalSummary:

    def __init__(self, source=None, **kwargs):
        if source:
            self.from_dict(source)

    def from_dict(self, summary_dict: Dict) -> None:
        for title, items in summary_dict.items():

            try:
                ann_label = AnnotationLabelEnum(title)
            except ValueError:
                # if title is not a member of AnnotationLabelEnum
                continue
            if not items or not isinstance(items, list):
                continue
            summary_type = ResultType.clinical
            if ann_label == AnnotationLabelEnum.LAB:
                summary_type = ResultType.lab_value
            if ann_label == AnnotationLabelEnum.MEDICATION:
                summary_type = ResultType.drug_ner
            setattr(self, title, [SummaryResult(item, summary_type) for item in items])

    def from_json(self, summary_json: AnyStr) -> None:
        return self.from_dict(json.loads(summary_json))

    def to_dict(self) -> Dict:
        result = {}
        data = vars(self)
        for title, items in data.items():
            if items:
                result[title] = [item.to_dict() for item in items]

        return result

    def to_json(self) -> AnyStr:
        return json.dumps(self.to_dict())

    def get_annotations(self) -> Dict:
        result = {}
        for k, v in self.to_dict().items():
            if v:
                result[k] = [item.get('text') for item in v]
        return result
