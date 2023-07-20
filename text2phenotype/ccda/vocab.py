from enum import Enum


###############################################################################
#
# Vocabularies
#
###############################################################################
class Vocab(Enum):
    SNOMED_CT = '2.16.840.1.113883.6.96'  # Clinical Terms (such as problems, Diagnosis, Procedures)
    LOINC = '2.16.840.1.113883.6.1'  # Logical Observation Identifiers Names and Codes
    RXNORM = '2.16.840.1.113883.6.88'  # Medications, Allergies
    CPT = '2.16.840.1.113883.6.12'  # Current Procedure Terminology
    CVX_UNKNOWN = '2.16.840.1.113883.6.59'  # CVX  Vaccine (codes)
    CVX = '2.16.840.1.113883.12.292'  # CVX  Vaccine (section?)
    UNII = '2.16.840.1.113883.4.9'  # Unique Ingredient Identifier ( allergies)
    NDFRT = '2.16.840.1.113883.3.26.1.5'  # National Drug File (allergies / medications)
    SSN = '2.16.840.1.113883.4.1'  # SS Number, if needed to PatientID
    other = '???'
    RaceEthnicity = '2.16.840.1.113883.6.238'
    Gender = '2.16.840.1.113883.5.1'

    # Moved from Feature Service
    original = 'original'  # ctakes original SNOMEDCT+RXNORM
    general = 'general'  # ctakes (supports pos_tagger smoking_status lab_value)
    snomedct = 'snomedct'  # Clinical Terms (many Aspect types)
    problem = 'problem-master'
    diagnosis = 'icd-syn'
    hepc = 'hepc'  # Hepatitis-C
    icd9 = 'icd9'  # Aspect.diagnosis
    icd10 = 'icd10'  # Aspect.diagnosis
    rxnorm = 'rxnorm'  # Aspect.medication
    rxnorm_syn = 'rxnorm-syn'  # Aspect.medication
    loinc = 'loinc'  # Aspect.Lab
    loinc_common = 'loinc-common'
    loinc_mimic = 'loinc-mimic'
    loinc2hpo = 'loinc2hpo'
    shrine_icd9 = 'shrine-icd9'  # Aspect.diagnosis (subset, Harvard shrine)
    shrine_icd10 = 'shrine-icd10'  # Aspect.diagnosis (subset, Harvard shrine)
    shrine_loinc = 'shrine-loinc'  # Aspect.lab (subset, Harvard shrine)
    shrine_rxnorm = 'rxnorm-shrine'  # Aspect.drug (subset, Harvard shrine)
    npi = 'npi'
    healthcare = 'healthcare'
    medgen = 'medgen'  # Medical Genetics
    topography = 'cancer-topography'
    morphology = 'cancer-morphology'
    loinc_section = 'loinc-section'
    loinc_title = 'loinc-title'
    covid = 'covid'     # TODO: remove once new UMLS is in the wild (2020-09-23)


def readme_loinc(loinc_code='18842-5'):
    """
    LOINC code, default is example for discharge summary
    :param loinc_code: name of the template type
    :return: URL readme containing the list of sections
    """
    return 'http://s.details.loinc.org/LOINC/%s.html' % loinc_code
