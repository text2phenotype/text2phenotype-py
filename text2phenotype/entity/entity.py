###############################################################################
#
# JSON Serializable types
#
###############################################################################
from text2phenotype.entity.attributes import Polarity
from text2phenotype.entity.attributes import DrugAttributes
from text2phenotype.entity.concept import Concept

###############################################################################
#
# Lab
#
###############################################################################
class LabEntity:
    def __init__(self, text=None, value=None, units=None, concepts=None, polarity=None):
        """
        Example: "Hemoglobin A1c is 6.4%"
        :param text: Hemoglobin A1c
        :param value: 6.4
        :param units: %
        :param concepts: HBGA1C synonyms for 'C0202054' (count 2)
        :param polarity: positive (if result was "not normal" then negative)
        """
        self.text  = text
        self.value = value
        self.units  = units
        self.concepts = concepts
        self.polarity = polarity

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


###############################################################################
#
# Drug / Medication
#
###############################################################################
class DrugEntity:

    def __init__(self, text, concept: Concept, attributes: DrugAttributes):
        """
        Example:
            nlp.drug_ner('Do not take aspirin 50 mg twice daily by mouth' )

           'attributes': {'conditional': 'false',
            'generic': 'false',
            'medDosage': None,
            'medDuration': None,
            'medForm': None,
            'medFrequencyNumber': ['2', 26, 31],
            'medFrequencyUnit': ['day'],
            'medRoute': 'Enteral_Oral',
            'medStatusChange': 'noChange',
            'medStrengthNum': ['50', 20, 22],
            'medStrengthUnit': ['mg', 23, 25],
            'modality': 'N/A',
            'polarity': 'negative',
            'uncertainty': 'false'},
        """
        self.text = text
        self.frequency = attributes.medFrequencyNumber
        self.frequency_units = attributes.medFrequencyUnit
        self.route = attributes.medRoute
        self.strength = attributes.medStrengthNum
        self.strength_units = attributes.medStrengthUnit
        self.polarity = Polarity(attributes.polarity)
































