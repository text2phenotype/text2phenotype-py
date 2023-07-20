from typing import (
    Any,
    Dict
)
from text2phenotype.entity.attributes import (
    DrugAttributes,
    Polarity,
    TextSpan
)
from text2phenotype.entity.entity import (
    DrugEntity,
    LabEntity
)


class HepCFormSuggestions:
    def __init__(self):
        self.lab_suggestions = list()
        self.medication_suggestions = list()
        self.other_suggestions = list()

    @classmethod
    def build_from_list(cls, suggestions):
        self = cls()

        for item in suggestions:
            suggestion = item.get('suggest')
            evidence = item.get('evidence')
            if not evidence:
                continue

            polarity = evidence.get('polarity')
            otext = evidence.get('text')
            text = otext[0] if otext is not None else ''
            attributes = evidence.get('attributes', {}) or {}

            if attributes.get('labValue'):
                self.lab_suggestions.append(LabSuggestion.create(suggestion=suggestion, data=attributes))
            elif suggestion == 'medication_statement':
                self.medication_suggestions.append(MedicationSuggestion.create(med_name=text, polarity=polarity, data=attributes))
            else:
                self.other_suggestions.append(Suggestion.create(suggestion=suggestion, polarity=polarity, text=text))

        return self


class Suggestion:

    def __init__(self):
        self.suggestion = None
        self.polarity = None
        self.text = ""

    @classmethod
    def create(cls, suggestion: str, polarity: str, text: str) -> 'Suggestion':
        sugg = cls()
        sugg.suggestion = suggestion
        sugg.polarity = Polarity(polarity).is_positive() if polarity else None
        sugg.text = text

        return sugg


class MedicationSuggestion(Suggestion):

    def __init__(self):
        super().__init__()

        self.suggestion = 'medication_statement'
        self.med_entity = None

    @classmethod
    def create(cls, med_name: str, polarity: str, data: Dict[str, Any]) -> 'MedicationSuggestion':
        sugg = cls()
        drug_data = data.copy()
        drug_data.update({'polarity': polarity})
        sugg.drug_entity = DrugEntity(text=med_name, concept=None, attributes=DrugAttributes(drug_data))
        return sugg


class LabSuggestion(Suggestion):

    def __init__(self):
        super().__init__()
        self.lab_entity = None

    @classmethod
    def create(cls, suggestion: str, data: Dict[str, Any]) -> 'LabSuggestion':
        sugg = cls()
        sugg.suggestion = suggestion
        sugg.lab_entity = LabEntity(
            value=next(iter(data.get('labValue')), None),
            units=TextSpan(data.get('labValueUnit')).text
        )
        return sugg
