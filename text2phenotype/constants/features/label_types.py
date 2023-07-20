import enum
import sys
from typing import List

from text2phenotype.common.annotations import AnnotationLabelConfig, AnnotationCategoryConfig
from text2phenotype.common.log import operations_logger


class LabelEnum(enum.Enum):
    @classmethod
    def quick_check_ann(cls, ann_txt: str):
        for category_name in cls.__members__:
            if category_name.lower() != 'na' and category_name.lower() in ann_txt.lower():
                return True
        return False

    @classmethod
    def from_brat(cls, brat_value: str):
        from_persistent_label = cls.get_from_persistent_label(brat_value)
        if from_persistent_label:
            return from_persistent_label
        if brat_value is not None and brat_value.lower() in cls.__members__:
            return cls[brat_value.lower()]
        from_alternative_text_labels = cls.get_from_alternative_text_labels(brat_value)
        if from_alternative_text_labels:
            return from_alternative_text_labels
        operations_logger.debug(f'{brat_value} not found to match any label in in {cls}')

        return cls.get_default_label()

    @classmethod
    def get_default_label(cls):
        return cls['na']

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        # Needs to be implemented on all sub classes.  Contains the category-
        # specific label values.
        raise NotImplementedError

    @classmethod
    def to_dict(cls) -> dict:
        # Get JSON-compatible dictionary for HTTP response
        res_cat = AnnotationCategoryConfig(category_label=cls.get_category_label(),
                                           label_enum=cls)
        return res_cat.to_dict()

    @classmethod
    def category_name(cls) -> str:
        return cls.__name__

    @classmethod
    def get_from_int(cls, item):
        item = int(item)

        for member in cls:
            if member.value.column_index == item:
                return member

    @classmethod
    def get_from_persistent_label(cls, item: str):
        for member in cls:
            if member.value.persistent_label == item:
                return member

    @classmethod
    def get_from_alternative_text_labels(cls, item: str):
        for member in cls:
            if item in member.value.alternative_text_labels:
                return member

    @classmethod
    def get_column_indices(cls):
        return sorted([member.value.column_index for member in cls])


class PHILabel(LabelEnum):
    # Label-level visibility affects behavior of SANDS in "Annotator" mode.'
    # colors are not from brat or defined by sands, they are a random rainbow and probably will need to be changes
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False, column_index=0, order=999,
                               persistent_label='na')
    date = AnnotationLabelConfig(label='Date', color='#800080', visibility=True, column_index=1, order=1,
                                 persistent_label='date')
    hospital = AnnotationLabelConfig(label='Hospital', color='#f7d89e', visibility=True, column_index=2, order=2,
                                     persistent_label='hospital')
    age = AnnotationLabelConfig(label='Age', color='#f4f79e', visibility=True, column_index=3, order=3,
                                persistent_label='age')
    street = AnnotationLabelConfig(label='Street', color='#cbf79e', visibility=True, column_index=4, order=4,
                                   persistent_label='street', alternative_text_labels={'location'})
    zip = AnnotationLabelConfig(label='Zip Code', color='#65b514', visibility=True, column_index=5, order=5,
                                persistent_label='zip')
    city = AnnotationLabelConfig(label='City', color='#14b52c', visibility=True, column_index=6, order=6,
                                 persistent_label='city')
    state = AnnotationLabelConfig(label='State', color='#14b587', visibility=True, column_index=7, order=7,
                                  persistent_label='state')
    country = AnnotationLabelConfig(label='Country', color='#14b2b5', visibility=True, column_index=8, order=8,
                                    persistent_label='country')
    location_other = AnnotationLabelConfig(label='Other Location', color='#14a8b5', visibility=False, column_index=9,
                                           order=9, persistent_label='location_other')
    phone = AnnotationLabelConfig(label='Phone #', color='#148fb5', visibility=True, column_index=10, order=10,
                                  persistent_label='phone')
    url = AnnotationLabelConfig(label='URL', color='#1482b5', visibility=True, column_index=11, order=11,
                                persistent_label='url')
    fax = AnnotationLabelConfig(label='Fax #', color='#144fb5', visibility=True, column_index=12, order=10,
                                persistent_label='fax')
    email = AnnotationLabelConfig(label='Email', color='#143ab5', visibility=True, column_index=13, order=12,
                                  persistent_label='email')
    idnum = AnnotationLabelConfig(label='ID #', color='#1414b5', visibility=True, column_index=14, order=13,
                                  persistent_label='idnum')
    bioid = AnnotationLabelConfig(label='BioID', color='#4414b5', visibility=False, column_index=15, order=13,
                                  persistent_label='bioid')
    organization = AnnotationLabelConfig(label='Organization Name', color='#6a14b5', visibility=False, column_index=16,
                                         order=14, persistent_label='organization')
    profession = AnnotationLabelConfig(label='Profession', color='#ffff99', visibility=False, column_index=17, order=14,
                                       persistent_label='profession')
    patient = AnnotationLabelConfig(label='Patient Name', color='#8714b5', visibility=True, column_index=18, order=1,
                                    persistent_label='patient')
    doctor = AnnotationLabelConfig(label='Doctor Name', color='#a514b5', visibility=True, column_index=19, order=2,
                                   persistent_label='doctor')
    medicalrecord = AnnotationLabelConfig(label='Medical Record Number', color='#b514b5', visibility=False,
                                          column_index=20, order=13, persistent_label='medicalrecord')
    username = AnnotationLabelConfig(label='Username', color='#b514a0', visibility=True, column_index=21, order=12,
                                     persistent_label='username')
    device = AnnotationLabelConfig(label='Device ID', color='#b5148f', visibility=True, column_index=22, order=13,
                                   persistent_label='device')
    healthplan = AnnotationLabelConfig(label='Insurance Identifiers', color='#b51465', visibility=False,
                                       column_index=23, order=13, persistent_label='healthplan')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='PHI',
                                     color='#000000',  # Black - current SANDS value, please maintain
                                     visibility=True,  # Will show in Annotator mode AND in Regular mode BY DEFAULT.
                                     # Category-level visibility affects only the behavior of SANDS in "Regular" mode.
                                     column_index=None, order=8,
                                     persistent_label='PHI')  # IMMUTABLE, can be any string,
        # but once set cannot be changed
        # without coordination with SANDS


class AllergyLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False, column_index=0, persistent_label='na',
                               order=999)
    allergy = AnnotationLabelConfig(label='Allergy', color='#ffccaa', visibility=True, column_index=1, order=1,
                                    persistent_label='allergy')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Allergy',
                                     color='#663560',  # Purple - current SANDS value, please maintain
                                     visibility=True,  # Will show in Annotator mode AND in Regular mode BY DEFAULT.
                                     column_index=None,
                                     order=1, persistent_label='Allergy')


class MedLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False, column_index=0, order=800,
                               persistent_label='na')
    # Label-level visibility affects behavior of SANDS in "Annotator" mode.
    med = AnnotationLabelConfig(label='Medication Name', color='#6fffdf', visibility=True, column_index=1, order=1,
                                persistent_label='med', alternative_text_labels={'medication'})

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Medication',
                                     color='#fb6a02',  # Orange - current SANDS value, please maintain
                                     visibility=True,  # Will show in Annotator mode AND in Regular mode BY DEFAULT.
                                     column_index=None,
                                     order=2, persistent_label='Medication')


class LabLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    lab = AnnotationLabelConfig(label='Lab Name', color='#7fe2ff', visibility=True, column_index=1, order=1,
                                persistent_label='lab', alternative_text_labels={'covid_lab'})
    lab_value = AnnotationLabelConfig(label='Lab Value', color='#47bcde', visibility=False, column_index=2, order=2,
                                      persistent_label='lab_value')
    lab_unit = AnnotationLabelConfig(label='Lab Unit', color='#2b8aa6', visibility=False, column_index=3, order=3,
                                     persistent_label='lab_unit')
    lab_interp = AnnotationLabelConfig(label='Lab Interpretation', color='#2b8aa6', visibility=False, column_index=4,
                                       order=4, persistent_label='lab_interp')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Lab',
                                     color='#12b5b3',  # Teal - current SANDS value, please maintain
                                     visibility=True,  # Will show in Annotator mode AND in Regular mode BY DEFAULT.
                                     column_index=None,
                                     order=5, persistent_label='Lab')


class ProblemLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, persistent_label='na',
                               order=0)  # Label-level visibility affects behavior of SANDS in "Annotator" mode.
    diagnosis = AnnotationLabelConfig(label='Diagnosis', color='#ccccee', visibility=True, column_index=1, order=1,
                                      persistent_label='diagnosis')
    problem = AnnotationLabelConfig(label='Problem', color='#565e61', visibility=False, column_index=2, order=2,
                                    persistent_label='problem')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Problem',
                                     color='#4374e9',  # Blue - current SANDS value, please maintain
                                     visibility=True,  # Will show in Annotator mode AND in Regular mode BY DEFAULT.
                                     column_index=None,
                                     order=3, persistent_label='DiseaseDisorder')


class SignSymptomLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=800,
                               persistent_label='na')
    signsymptom = AnnotationLabelConfig(label='SignSymptom', color='#007088', visibility=True, column_index=1, order=1,
                                        persistent_label='signsymptom')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Sign/Symptom',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=4, persistent_label='SignSymptom')


class TemporalLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=800,
                               persistent_label='na')
    # Label-level visibility affects behavior of SANDS in "Annotator" mode.
    event_date = AnnotationLabelConfig(label='EventDate', color='#007088', visibility=False, column_index=1, order=1,
                                       persistent_label='eventdate')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Temporal',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=4, persistent_label='Temporal')


class ReportType(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=800,
                               persistent_label='na')
    # Label-level visibility affects behavior of SANDS in "Annotator" mode.
    pathology_report = AnnotationLabelConfig(label='Pathology Report', color='#007088', visibility=False,
                                             column_index=1,
                                             order=1, persistent_label='pathology_report')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Report Type',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=4, persistent_label='ReportType')


class DemographicEncounterLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    # Label-level visibility affects behavior of SANDS in "Annotator" mode.
    ssn = AnnotationLabelConfig(label='Social Security Number', color='#ffff00', visibility=True, column_index=1,
                                order=1, persistent_label='ssn')
    mrn = AnnotationLabelConfig(label='Medical Record #', color='#ffffe0', visibility=True, column_index=2, order=2,
                                persistent_label='mrn')
    pat_first = AnnotationLabelConfig(label='Patient First Name', color='#fafad2', visibility=True, column_index=3,
                                      order=5, persistent_label='pat_first')
    pat_middle = AnnotationLabelConfig(label='Patient Middle Name', color='#ffefd5', visibility=True, column_index=4,
                                       order=6, persistent_label='pat_middle')
    pat_last = AnnotationLabelConfig(label='Patient Last Name', color='#ffe4b5', visibility=True, column_index=5,
                                     order=7, persistent_label='pat_last')
    pat_initials = AnnotationLabelConfig(label='Patient Initials', color='#ffe4b5', visibility=False, column_index=6,
                                         order=800, persistent_label='pat_initials')
    pat_age = AnnotationLabelConfig(label='Patient Age', color='#ffdab9', visibility=True, column_index=7, order=8,
                                    persistent_label='pat_age')
    pat_street = AnnotationLabelConfig(label='Patient Street Address', color='#eee8aa', visibility=True, column_index=8,
                                       order=9, persistent_label='pat_street')
    pat_zip = AnnotationLabelConfig(label='Patient Zip Code', color='#f0e68c', visibility=True, column_index=9,
                                    order=12, persistent_label='pat_zip')
    pat_city = AnnotationLabelConfig(label='Patient City', color='#eee8aa', visibility=True, column_index=10, order=10,
                                     persistent_label='pat_city')
    pat_state = AnnotationLabelConfig(label='Patient State', color='#daa520', visibility=True, column_index=11,
                                      order=11, persistent_label='pat_state')
    pat_phone = AnnotationLabelConfig(label='Patient Phone #', color='#f5deb3', visibility=True, column_index=12,
                                      order=12, persistent_label='pat_phone')
    pat_email = AnnotationLabelConfig(label='Patient Email', color='#fffacd', visibility=True, column_index=13,
                                      order=13, persistent_label='pat_email')
    insurance = AnnotationLabelConfig(label='Insurancee #', color='#fffacd', visibility=True, column_index=14,
                                      order=700, persistent_label='insurance')
    facility_name = AnnotationLabelConfig(label='Medical Facility Name', color='#00ffff', visibility=True,
                                          column_index=15, order=14, persistent_label='facility_name')
    dr_first = AnnotationLabelConfig(label='Dr First Name', color='#e0ffff', visibility=True, column_index=16, order=15,
                                     persistent_label='dr_first')
    dr_middle = AnnotationLabelConfig(label='Dr Middle Name', color='#afeeee', visibility=True, column_index=17,
                                      order=16, persistent_label='dr_middle')
    dr_last = AnnotationLabelConfig(label='Dr Last Name', color='#7fffd4', visibility=True, column_index=18, order=17,
                                    persistent_label='dr_last')
    dr_initials = AnnotationLabelConfig(label='Dr Initials', color='#7fffd4', visibility=False, column_index=19,
                                        order=700, persistent_label='dr_initials')
    dr_street = AnnotationLabelConfig(label='Dr/Facility Street Address', color='#40e0d0', visibility=True,
                                      column_index=20, order=18, persistent_label='dr_street')
    dr_zip = AnnotationLabelConfig(label='Dr/Facility Zip Code', color='#48d1cc', visibility=True, column_index=21,
                                   order=21, persistent_label='dr_zip')
    dr_city = AnnotationLabelConfig(label='Dr/Facility City', color='#00ced1', visibility=True, column_index=22,
                                    order=19, persistent_label='dr_city')
    dr_state = AnnotationLabelConfig(label='Dr/Facility State', color='#5f9ea0', visibility=True, column_index=23,
                                     order=20, persistent_label='dr_state')
    dr_phone = AnnotationLabelConfig(label='Dr/Facility Phone #', color='#4682b4', visibility=True, column_index=24,
                                     order=22, persistent_label='dr_phone')
    dr_fax = AnnotationLabelConfig(label='Dr/Facility Fax #', color='#b0c4de', visibility=True, column_index=25,
                                   order=23, persistent_label='dr_fax')
    dr_email = AnnotationLabelConfig(label='Dr Email', color='#b0e0e6', visibility=True, column_index=26, order=24,
                                     persistent_label='dr_email')
    dr_id = AnnotationLabelConfig(label='Dr ID #', color='#add8e6', visibility=True, column_index=27, order=28,
                                  persistent_label='dr_id')
    dr_org = AnnotationLabelConfig(label='Dr Org', color='#87ceeb', visibility=True, column_index=28, order=28,
                                   persistent_label='dr_org')
    sex = AnnotationLabelConfig(label='Patient Sex', color='#ffff4d', visibility=True, column_index=29, order=4,
                                persistent_label='sex')
    dob = AnnotationLabelConfig(label='Patient Date of Birth', color='#148fb5', visibility=True, column_index=30,
                                order=3, persistent_label='dob')
    race = AnnotationLabelConfig(label='Patient Race', color='#ffff4d', visibility=True, column_index=31, order=8,
                                 persistent_label='race')
    ethnicity = AnnotationLabelConfig(label='Patient Ethnicity', color='#ffff4d', visibility=True, column_index=32,
                                      order=8, persistent_label='ethnicity')
    language = AnnotationLabelConfig(label='Patient Preferred Language', color='#ffff4d', visibility=True,
                                     column_index=33, order=9, persistent_label='language')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Demographics',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=9,
                                     persistent_label='Demographic')


class DisabilityLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    # Label-level visibility affects behavior of SANDS in "Annotator" mode.
    diagnosis = AnnotationLabelConfig(label='Diagnosis', color='#ccccee', visibility=False, column_index=1, order=1,
                                      persistent_label='diagnosis')
    procedure = AnnotationLabelConfig(label='Procedure', color='#ccccee', visibility=False, column_index=2, order=2,
                                      persistent_label='procedure')
    finding = AnnotationLabelConfig(label='Relevant Medical Finding', color='#ccccee', visibility=False, column_index=3,
                                    order=3, persistent_label='finding')
    physical_exam = AnnotationLabelConfig(label='Physical Exam Finding', color='#ccccee', visibility=False,
                                          column_index=4, order=4, persistent_label='physical_exam')
    device = AnnotationLabelConfig(label='Device', color='#ccccee', visibility=False, column_index=5, order=5,
                                   persistent_label='device')
    signsymptom = AnnotationLabelConfig(label='SignSymptom', color='#007088', visibility=False, column_index=6, order=6,
                                        persistent_label='signsymptom')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Disability',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=6,
                                     persistent_label='Disability')


class CancerLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    # Label-level visibility affects behavior of SANDS in "Annotator" mode.
    topography_primary = AnnotationLabelConfig(label='Cancer Topography (Pri)', color='#ccccee', visibility=False,
                                               column_index=1, order=1, persistent_label='topography_primary')
    topography_metastatic = AnnotationLabelConfig(label='Cancer Topography (Met)', color='#ccccee', visibility=False,
                                                  column_index=2, order=2, persistent_label='topography_metastatic')
    morphology = AnnotationLabelConfig(label='Cancer Morphology', color='#ccccee', visibility=False, column_index=3,
                                       order=3, persistent_label='morphology')
    behavior = AnnotationLabelConfig(label='Cancer Behavior', color='#ccccee', visibility=False, column_index=4,
                                     order=4, persistent_label='behavior',
                                     alternative_text_labels={'b0_benign', 'b1_uncertain', 'b2_in_situ',
                                                              'b3_mal_primary', 'b6_mal_metastatic',
                                                              'b9_mal_uncertain'})
    grade = AnnotationLabelConfig(label='Cancer Grade', color='#ccccee', visibility=False, column_index=5, order=5,
                                  persistent_label='grade')
    stage = AnnotationLabelConfig(label='Cancer TNM Stage', color='#ccccee', visibility=False, column_index=6, order=6,
                                  persistent_label='stage')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Cancer',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=7, persistent_label='Cancer')


class BladderRiskLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    lvi = AnnotationLabelConfig(label='LVI', color='#ccccee', visibility=False,
                                column_index=1, order=1, persistent_label='LVI')
    multifocal = AnnotationLabelConfig(label='Multifocal', color='#ccccee', visibility=False,
                                       column_index=2, order=2, persistent_label='multifocal')
    pui = AnnotationLabelConfig(label='PUI', color='#ccccee', visibility=False,
                                column_index=3, order=3, persistent_label='PUI')
    recurrence = AnnotationLabelConfig(label='Recurrence', color='#ccccee', visibility=False,
                                       column_index=4, order=4, persistent_label='recurrence')
    tumor_size = AnnotationLabelConfig(label='Tumor Size', color='#ccccee', visibility=False,
                                       column_index=5, order=5, persistent_label='tumor_size')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='BladderRisk',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     column_index=None,
                                     order=7, persistent_label='BladderRisk')


# TODO: this is to support the data Sequoia is trying to collect outside of the standard risk criteria for NMIBC
#  and should be transient
class SequoiaBladderLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    bcg = AnnotationLabelConfig(label='BCG', color='#ccccee', visibility=False,  # TODO: incorporate into drug?
                                column_index=1, order=1, persistent_label='BCG')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='SequoiaBladder',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     column_index=None,
                                     order=7, persistent_label='SequoiaBladder')


class GeneticsLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff',
                               visibility=False, column_index=0, order=999, persistent_label='na')
    gene = AnnotationLabelConfig(label='Gene', color='#ffffff',
                                 visibility=False, column_index=1, order=1, persistent_label='gene_names')
    gene_interpretation = AnnotationLabelConfig(label='Gene Clinical Interpretation', color='#ffffff',
                                                visibility=False, column_index=2, order=2,
                                                persistent_label='gene_interpretation')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Genetics',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=7, persistent_label='Genetics')


class HeartDiseaseLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    cad = AnnotationLabelConfig(label='Coronary Artery Disease', color='#ccccee', visibility=False, column_index=1,
                                order=1, persistent_label='cad')
    diabetes = AnnotationLabelConfig(label='Diabetes', color='#ccccee', visibility=False, column_index=2, order=2,
                                     persistent_label='diabetes')
    hyperlipidemia = AnnotationLabelConfig(label='Hyperlipidemia', color='#ccccee', visibility=False, column_index=3,
                                           order=3, persistent_label='hyprelipideemia')
    hypertension = AnnotationLabelConfig(label='Hypertension', color='#ccccee', visibility=False, column_index=4,
                                         order=4, persistent_label='hypertension')
    medication = AnnotationLabelConfig(label='Medications HDRF', color='#ccccee', visibility=False, column_index=5,
                                       order=5, persistent_label='medication')
    obese = AnnotationLabelConfig(label='Obesity', color='#ccccee', visibility=False, column_index=6, order=6,
                                  persistent_label='obese')
    family_hist = AnnotationLabelConfig(label='Family History HDRF', color='#ccccee', visibility=False, column_index=7,
                                        order=7, persistent_label='family_hist')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Heart Disease Risk Factor',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=8,
                                     persistent_label='HeartDisease')


class DocumentTypeLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A non-clinical', color='#BE33FF', visibility=True,
                               column_index=0, order=999, persistent_label='na')
    other_clinical_doc = AnnotationLabelConfig(label='Other', color='#BE33FF', visibility=True,
                                               column_index=1, order=1, persistent_label='other_clinical_doc')
    discharge_summary = AnnotationLabelConfig(label='DischargeSummary', color='#BE33FF', visibility=True,
                                              column_index=2, order=2, persistent_label='discharge_summary')
    history_and_physical = AnnotationLabelConfig(label='HistoryAndPhysical', color='#BE33FF', visibility=True,
                                                 column_index=3, order=3, persistent_label='history_and_physical')
    progress_notes = AnnotationLabelConfig(label='ProgressNote', color='#BE33FF', visibility=True,
                                           column_index=4, order=4, persistent_label='progress_notes')
    consult_note = AnnotationLabelConfig(label='ConsultNote', color='#BE33FF', visibility=True,
                                         column_index=5, order=5, persistent_label='consult_note')
    diagnostic_imaging_study = AnnotationLabelConfig(label='DiagnosticImagingStudy', color='#BE33FF', visibility=True,
                                                     column_index=6, order=6,
                                                     persistent_label='diagnostic_imaging_study')
    surgical_operation_note = AnnotationLabelConfig(label='SurgicalOperationNote', color='#BE33FF', visibility=True,
                                                    column_index=7, order=7, persistent_label='surgical_operation_note')
    procedure_note = AnnotationLabelConfig(label='ProcedureNote', color='#BE33FF', visibility=True,
                                           column_index=8, order=8, persistent_label='procedure_note')
    nursing = AnnotationLabelConfig(label='Nursing', color='#BE33FF', visibility=True,
                                    column_index=9, order=9, persistent_label='nursing')
    pathology = AnnotationLabelConfig(label='Pathology', color='#BE33FF', visibility=True,
                                      column_index=10, order=10, persistent_label='pathology')
    laboratory = AnnotationLabelConfig(label='Laboratory', color='#BE33FF', visibility=True,
                                       column_index=11, order=11, persistent_label='laboratory')
    non_clinical = AnnotationLabelConfig(label='Laboratory', color='#BE33FF', visibility=True,
                                         column_index=12, order=12, persistent_label='non_clinical')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='DocumentType',
                                     color='#000000',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=11,
                                     persistent_label='DocumentType')


class BinaryEnum(LabelEnum):
    na = AnnotationLabelConfig(column_index=0, color='red', order=0, persistent_label='na', visibility=True, label='na')
    phi = AnnotationLabelConfig(column_index=1, color='red', order=0, persistent_label='non-na', visibility=True,
                                label='non-na')


class GeneticTestLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False, column_index=0,
                               order=999, persistent_label='na')
    gene = AnnotationLabelConfig(label='Gene', color='#ccccee', visibility=False, column_index=1,
                                 order=1, persistent_label='gene')
    locus = AnnotationLabelConfig(label='Locus', color='#add8e6', visibility=False, column_index=2,
                                  order=2, persistent_label='locus')
    variant = AnnotationLabelConfig(label='Variant', color='#87ceeb', visibility=False, column_index=3,
                                    order=3, persistent_label='variant')
    result = AnnotationLabelConfig(label='Test Result', color='#ffff4d', visibility=False, column_index=4,
                                   order=4, persistent_label='result')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Genetic Test',
                                     color='#007088',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=9, persistent_label='GeneticTest')


class SmokingLabel(LabelEnum):
    unknown = AnnotationLabelConfig(label='Unknown', color='#ffffff', visibility=False,
                                    column_index=0, order=1, persistent_label='unknown')
    past = AnnotationLabelConfig(label='Past', color='#ccccee', visibility=False,
                                 column_index=1, order=2, persistent_label='past')
    current = AnnotationLabelConfig(label='Current', color='#add8e6', visibility=False,
                                    column_index=2, order=3, persistent_label='current')
    never = AnnotationLabelConfig(label='Non-smoker', color='#ffff4d', visibility=False,
                                  column_index=3, order=4, persistent_label='never')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Smoking', color='#007088', visibility=False,
                                     column_index=None, order=9, persistent_label='Smoking')

    @classmethod
    def get_default_label(cls):
        return cls.unknown


class VitalSignsLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False, column_index=0,
                               order=999, persistent_label='na')
    temperature = AnnotationLabelConfig(label='Temperature', color='#ccccee', visibility=True, column_index=1,
                                        order=1, persistent_label='temperature')
    pulse_ox = AnnotationLabelConfig(label='Pulse Ox', color='#add8e6', visibility=True, column_index=2,
                                     order=2, persistent_label='pulse_ox')
    heart_rate = AnnotationLabelConfig(label='Heart Rate', color='#87ceeb', visibility=True, column_index=3,
                                       order=3, persistent_label='heart_rate')
    respiratory_rate = AnnotationLabelConfig(label='Respiratory Rate', color='#ffff4d', visibility=True, column_index=4,
                                             order=4, persistent_label='respiratory_rate')
    blood_pressure = AnnotationLabelConfig(label='Blood Pressure', color='#148fb5', visibility=True, column_index=5,
                                           order=5, persistent_label='blood_pressure')
    height = AnnotationLabelConfig(label='Height', color='#148fb5', visibility=True, column_index=6,
                                   order=5, persistent_label='height')
    weight = AnnotationLabelConfig(label='Weight', color='#148fb5', visibility=True, column_index=7,
                                   order=5, persistent_label='weight')
    bmi = AnnotationLabelConfig(label='BMI', color='#148fb5', visibility=True, column_index=8,
                                order=5, persistent_label='BMI')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Vital Signs', color='#007088', visibility=False,
                                     column_index=None, order=9, persistent_label='VitalSigns')


class DiagnosticImagingLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False, column_index=0,
                               order=999, persistent_label='na')
    mri = AnnotationLabelConfig(label='MRI', color='#ccccee', visibility=True, column_index=1,
                                order=1, persistent_label='mri')
    ecg = AnnotationLabelConfig(label='ECG', color='#add8e6', visibility=True, column_index=2,
                                order=2, persistent_label='ecg')
    echo = AnnotationLabelConfig(label='ECHO', color='#87ceeb', visibility=True, column_index=3,
                                 order=3, persistent_label='echo')
    xray = AnnotationLabelConfig(label='X-Ray', color='#F0FF33', visibility=True, column_index=4,
                                 order=4, persistent_label='xr')
    ct = AnnotationLabelConfig(label='CT', color='#80FF33', visibility=True, column_index=5,
                               order=5, persistent_label='ct')
    us = AnnotationLabelConfig(label='Ultrasound', color='#ffff4d', visibility=True, column_index=6,
                               order=6, persistent_label='us')
    other = AnnotationLabelConfig(label='Other', color='#148fb5', visibility=True, column_index=7,
                                  order=7, persistent_label='other')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Diagnostic Imaging', color='#007088', visibility=False,
                                     column_index=None, order=9, persistent_label='DiagnosticImaging')


class SocialRiskFactorLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False, column_index=0,
                               order=999, persistent_label='na')
    social_risk_factor = AnnotationLabelConfig(
        label='OTHER_SDOH', color='#ccccee', visibility=True,
        column_index=1, order=1, persistent_label='social_risk_factor',
        alternative_text_labels={'other_sdoh'})
    living_status = AnnotationLabelConfig(
        label='Living Status', color='#ccccee', visibility=True,
        column_index=2, order=1, persistent_label='living_status')

    social_status = AnnotationLabelConfig(
        label='Social Status', color='#ccccee', visibility=True,
        column_index=3, order=1, persistent_label='social_status',

        alternative_text_labels={'social'})
    insurance_status = AnnotationLabelConfig(
        label='Insurance', color='#ccccee', visibility=True,
        column_index=4, order=1, persistent_label='insurance')
    mental_health = AnnotationLabelConfig(
        label='Mental Health', color='#ccccee', visibility=True,
        column_index=5, order=1, persistent_label='metnal_health')
    occupation = AnnotationLabelConfig(
        label='Occupation', color='#ccccee', visibility=True,
        column_index=6, order=1, persistent_label='occupation')
    physical_activity = AnnotationLabelConfig(
        label='Physical Activity', color='#ccccee', visibility=True,
        column_index=7, order=1, persistent_label='physical_activity')
    travel = AnnotationLabelConfig(
        label='Travel', color='#ccccee', visibility=True,
        column_index=8, order=1, persistent_label='travel')
    drug_alcohol = AnnotationLabelConfig(
        label='Drugs And Alcohol', color='#ccccee', visibility=True,
        column_index=9, order=1, persistent_label='drug_alcohol')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Social', color='#007088', visibility=False,
                                     column_index=None, order=9, persistent_label='SocialRiskFactors')


class DuplicateDocumentLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False, column_index=0,
                               order=999, persistent_label='na')
    duplicate = AnnotationLabelConfig(label='Duplicate', color='#555555', visibility=True, column_index=1,
                                      order=1, persistent_label='dup')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Duplicate Document', color='#555555', visibility=False,
                                     column_index=None, order=9, persistent_label='DuplicateDocument')


class DeviceProcedureLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    device = AnnotationLabelConfig(label='Device', color='#ccccee', visibility=False, column_index=1, order=1,
                                   persistent_label='device')

    # procedure = AnnotationLabelConfig(label='Procedure', color='#ccccee', visibility=False, column_index=2, order=2,
    #                                   persistent_label='procedure')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Device/Procedure',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=6,
                                     persistent_label='Device/Procedure')


class ProcedureLabel(LabelEnum):
    na = AnnotationLabelConfig(
        label='N/A', color='#ffffff', visibility=False, column_index=0, order=999, persistent_label='na')
    procedure = AnnotationLabelConfig(
        label='procedure', color='#ccccee', visibility=False, column_index=1, order=1, persistent_label='procedure')
    anatomical_site = AnnotationLabelConfig(
        label='anatomical_site', color='#ccccee', visibility=False, column_index=2, order=2,
        persistent_label='anatomical_site')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Procedure',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=6,
                                     persistent_label='Procedure')


class EventDateLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False, column_index=0, order=999,
                               persistent_label='na')
    encounter_date = AnnotationLabelConfig(label='Encounter Date', color='#ccccee', visibility=False, column_index=1,
                                           order=1,
                                           persistent_label='encounter_date')
    admission_date = AnnotationLabelConfig(label='Admisssion Date', color='#ccccee', visibility=False, column_index=2,
                                           order=2, persistent_label='admission_date')
    discharge_date = AnnotationLabelConfig(label='Discharge Date', color='#ccccee', visibility=False, column_index=3,
                                           order=3, persistent_label='discharge_date')
    death_date = AnnotationLabelConfig(label='Death Date', color='#ccccee', visibility=False, column_index=4,
                                       order=4, persistent_label='death_date')
    transfer_date = AnnotationLabelConfig(label='Transfer Date', color='#ccccee', visibility=False, column_index=5,
                                          order=5, persistent_label='transfer_date')
    procedure_date = AnnotationLabelConfig(label='Procedure Date', color='#ccccee', visibility=False, column_index=6,
                                           order=6, persistent_label='procedure_date')
    report_date = AnnotationLabelConfig(label='Report Date', color='#ccccee', visibility=False, column_index=7,
                                        order=7, persistent_label='report_date')
    collection_date = AnnotationLabelConfig(label='Specimen Collection Date', color='#ccccee', visibility=False,
                                            column_index=8,
                                            order=8, persistent_label='collection_date')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Event Date',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=6,
                                     persistent_label='EventDate')


class CovidLabLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    lab = AnnotationLabelConfig(label='Covid Lab Name', color='#7fe2ff', visibility=True, column_index=1, order=1,
                                persistent_label='covid_lab')
    lab_value = AnnotationLabelConfig(label='Lab Value', color='#47bcde', visibility=False, column_index=2, order=2,
                                      persistent_label='lab_value')
    lab_unit = AnnotationLabelConfig(label='Lab Unit', color='#2b8aa6', visibility=False, column_index=3, order=3,
                                     persistent_label='lab_unit')
    lab_interp = AnnotationLabelConfig(label='Covid Lab Interpretation', color='#2b8aa6', visibility=True,
                                       column_index=4,
                                       order=4, persistent_label='lab_interp')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Covid Lab',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=6,
                                     persistent_label='CovidLabs')


class FindingLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    finding = AnnotationLabelConfig(label='Relevant Medical Finding', color='#ccccee', visibility=False, column_index=3,
                                    order=3, persistent_label='finding')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Findings',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=6,
                                     persistent_label='Findings')


class FamilyHistoryLabel(LabelEnum):
    na = AnnotationLabelConfig(label='N/A', color='#ffffff', visibility=False,
                               column_index=0, order=999,
                               persistent_label='na')
    family_history = AnnotationLabelConfig(label='Family History', color='#ccccee', visibility=False, column_index=1,
                                           order=1, persistent_label='family_history')

    @classmethod
    def get_category_label(cls) -> AnnotationLabelConfig:
        return AnnotationLabelConfig(label='Family History',
                                     color='#ffffff',  # Not set in SANDS
                                     visibility=False,
                                     # Will show in Annotator mode, but NOT in Regular mode BY DEFAULT
                                     column_index=None,
                                     order=6,
                                     persistent_label='Family_History')


LabelList = {
    PHILabel, DemographicEncounterLabel, ProblemLabel, CancerLabel, DisabilityLabel, AllergyLabel, MedLabel,
    LabLabel, SignSymptomLabel, HeartDiseaseLabel, ReportType, TemporalLabel, GeneticTestLabel, SmokingLabel,
    VitalSignsLabel, DiagnosticImagingLabel, DocumentTypeLabel, SocialRiskFactorLabel, DuplicateDocumentLabel,
    DeviceProcedureLabel, EventDateLabel, CovidLabLabel, FindingLabel, FamilyHistoryLabel, BladderRiskLabel,
    SequoiaBladderLabel, ProcedureLabel}


def list_annotation_labels() -> List[dict]:
    return [label_type.to_dict() for label_type in LabelList]


def deserialize_label_type(label_type_str: str):
    """Given a string that matches a class in the label_types.py module, return the associated class"""
    return getattr(sys.modules[__name__], label_type_str)
