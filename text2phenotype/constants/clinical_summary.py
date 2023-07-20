from enum import Enum

# TODO Remove after migrations merge
class AnnotationLabel_DEPRECATED(Enum):
    ALLERGY = 1
    PROBLEM = 2
    MEDICATION = 3
    LAB = 4
    PHI = 5

# TODO Remove after migrations merge
LABEL_TO_COLOR = {
    1: '#663560',
    2: '#4374e9',
    3: '#fb6a02',
    4: '#109c99',
    5: '#000',
}


class AnnotationLabelEnum(Enum):
    PHI = 'PHI'
    ALLERGY = 'Allergy'
    PROBLEM = 'DiseaseDisorder'
    MEDICATION = 'Medication'
    LAB = 'Lab'


class AnnotationMsgType(Enum):
    PHI = 1
    ANN = 2
