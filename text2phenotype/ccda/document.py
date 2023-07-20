from __future__ import absolute_import, unicode_literals

from enum import Enum

###############################################################################
#
# CCDA Document Types "Consolidated Clinical Document Architecture"
#
###############################################################################

class DocumentType(Enum):
    """
    CCDA Document Types
    https://www.healthit.gov/sites/default/files/c-cda_and_meaningfulusecertification.pdf
    """
    ccd= '34133-9'
    consult_note='11488-4'
    history_and_physical_note='34117-2'
    discharge_summary = '18842-5'
    physician_discharge_summary='11490-0'
    progress_note='11506-3'
    diagnostic_imaging_study='18748-4'
    surgical_operation_note='11504-8'
    procedure_note= '28570-0'

###############################################################################
#
# Continuity Of Care Document (CCD)
#    (also known as summary of episode)
#
###############################################################################
class CCD(Enum):
    """
    https://details.loinc.org/LOINC/34133-9.html
    """
    __document_type__ = DocumentType.ccd

    allergies  ='48765-2'
    history_of_medication_use_narrative  ='10160-0'
    problem_list_reported  ='11450-4'
    history_of_procedures_document  ='47519-4'
    relevant_diagnostic_tests_or_laboratory_data_narrative  ='30954-2'
    social_history  ='29762-2'
    vital_signs  ='8716-3'
    advance_directives  ='42348-3'
    history_of_hospitalizations_outpatient_visits_narrative  ='46240-8'
    history_of_family_member_diseases_narrative  ='10157-6'
    functional_status_assessment_note  ='47420-5'
    history_of_immunization_narrative  ='11369-6'
    mental_status_narrative  ='10190-7'
    history_of_medical_device_use  ='46264-8'
    diet_and_nutrition_narrative  ='61144-2'
    payment_sources_document  ='48768-6'
    plan_of_care_note  ='18776-5'

    #Andy TODO: examine non-standard use found in samples (AllScripts, HL7)
    reason_for_referral ='42349-1'
    reason_for_visit='29299-5'
    reason_for_visit_and_chief_complaint  ='46239-0'
    medication_administered_narrative='29549-3'
    interventions_narrative  ='62387-6'
    instructions  ='69730-0'
    history_of_past_illness_narrative  ='11348-0'
    chief_complaint  ='10154-3'
    assessments = '51848-0'
    medications_administered_narrative='29549-3'
    hospital_admission_diagnosis_narrative ='46241-6'
    hospital_discharge_instructions  ='8653-8'
    physical_findings_narrative  ='29545-1'
    history_of_present_illness_narrative='10164-2'
    medical_general_history='11329-0'
    discharge_medication ='10183-2'
    assessment_and_plan  ='51847-2'
    review_of_systems  ='10187-3'

###############################################################################
#
# Discharge Summary
#
###############################################################################

class DischargeSummary(Enum):
    """
    https://s.details.loinc.org/LOINC/18842-5.html
    """
    __document_type__ = DocumentType.discharge_summary

    allergies ='48765-2'
    hospital_course_narrative ='8648-8'
    discharge_diagnosis_narrative ='78375-3'
    discharge_medications_narrative = '75311-1'
    hospital_discharge_dx ='11535-2'
    hospital_discharge_medications ='10183-2'
    plan_of_care ='18776-5'
    admission_diagnosis ='42347-5'
    medications_on_admission_narrative  ='42346-7'
    chief_complaint_reason_for_visit_narrative  ='46239-0'
    chief_complaint_narrative_reported  ='10154-3'
    discharge_diet_narrative  ='42344-2'
    history_of_family_member_diseases_narrative  ='10157-6'
    functional_status_assessment_note  ='47420-5'
    history_of_past_illness_narrative  ='11348-0'
    history_of_present_illness_narrative   ='10164-2'
    hospital_admission_diagnosis_narrative ='46241-6'
    hospital_consultations_document  ='18841-7'
    hospital_discharge_instructions  ='8653-8'
    hospital_discharge_physical_findings_narrative  ='10184-0'
    hospital_discharge_studies_summary_narrative  ='11493-4'
    history_of_immunization_narrative  ='11369-6'
    diet_and_nutrition_narrative  ='61144-2'
    problem_list_reported  ='11450-4'
    history_of_procedures_document  ='47519-4'
    reason_for_visit_narrative  ='29299-5'
    review_of_systems_narrative_reported  ='10187-3'
    social_history_narrative  ='29762-2'
    vital_signs  ='8716-3'

    #Andy TODO: examine non-standard use found in AllScripts sample
    history_of_medication_use_narrative  ='10160-0'
    relevant_diagnostic_tests_or_laboratory_data_narrative  ='30954-2'
    instructions  ='69730-0'
    encounters ='46240-8'
    medications_administered_narrative='29549-3'
    advance_directives  ='42348-3'


###############################################################################
#
# History and Physical
#
###############################################################################

class HistoryAndPhysical(Enum):
    """
    https://details.loinc.org/LOINC/34117-2.html
    """
    __document_type__ = DocumentType.history_and_physical_note

    alerts  ='48765-2'
    assessment  ='51848-0'
    assessment_and_plan  ='51847-2'
    chief_complaint  ='10154-3'
    family_history  ='10157-6'
    general_status  ='10210-3'
    history_of_present_illness  ='10164-2'
    history_of_immunizations  ='11369-6'
    instructions  ='69730-0'
    medications  ='10160-0'
    past_medical_history  ='11348-0'
    physical_examination  ='29545-1'
    plan_of_care  ='18776-5'
    problems  ='11450-4'
    procedures=  '47519-4'
    reason_for_visit  ='29299-5'
    reason_for_visit_and_chief_complaint  ='46239-0'
    results_diagnostic_findings  ='30954-2'
    review_of_systems  ='10187-3'
    social_history  ='29762-2'
    vital_signs  ='8716-3'

###############################################################################
#
# Progress Note
#
###############################################################################

class ProgressNote(Enum):
    """
    https://details.loinc.org/LOINC/11506-3.html
    """
    __document_type__ = DocumentType.progress_note

    assessment_and_plan  ='51847-2'
    assessment  ='51848-0'
    plan_of_care  ='18776-5'
    allergies  ='48765-2'
    chief_complaint_narrative_reported  ='10154-3'
    instructions  ='69730-0'
    interventions_narrative  ='62387-6'
    history_of_medication_use_narrative  ='10160-0'
    diet_and_nutrition_narrative  ='61144-2'
    objective_narrative  ='61149-1'
    physical_findings_narrative  ='29545-1'
    problem_list_reported  ='11450-4'
    results  ='30954-2'
    review_of_systems_narrative_reported  ='10187-3'
    subjective_narrative  ='61150-9'
    vital_signs  ='8716-3'

    #Andy TODO: examine non-standard use found in samples (AllScripts, HL7)
    reason_for_visit_and_chief_complaint='46239-0'


###############################################################################
#
# Less common CCDA Document Types
#
###############################################################################
class ConsultNote(Enum):
    """
    https://details.loinc.org/LOINC/11488-4.html
    """
    __document_type__ = DocumentType.consult_note
    assessment_and_plan = '51847-2'
    assessment = '51848-0'
    plan_of_care = '18776-5'
    past_medical_history='11348-0'
    physical_examination='29545-1'
    reason_for_referral ='42349-1'
    reason_for_visit='29299-5'
    advance_directives='42348-3'
    allergies='48765-2'
    chief_complaint_and_reason_for_visit_narrative='46239-0'
    chief_complaint_narrative_reported='10154-3'
    family_history='10157-6'
    functional_status_assessment_note='47420-5'
    general_status='10210-3'
    history_of_present_illness_narrative='10164-2'
    history_of_immunizations='11369-6'
    history_of_medical_device_use='46264-8'
    medications='10160-0'
    mental_status_Narrative='10190-7'
    diet_and_nutrition_narrative='61144-2'
    problems='11450-4'
    procedures='47519-4'
    results='30954-2'
    review_of_systems='10187-3'
    social_history='29762-2'
    vital_signs='8716-3'

class DiagnosticImagingStudy(Enum):
    """
    https://details.loinc.org/LOINC/18748-4.html
    """
    __document_type__ = DocumentType.diagnostic_imaging_study

    history_general='11329-0'
    request_radiology='55115-0'
    current_imaging_procedure_descriptions_document='55111-9'
    prior_procedure_descriptions='55114-3'
    radiology_comparison_study_observation='18834-2'
    radiology_study_observation_findings='18782-3'
    radiology_impression='19005-8'
    radiology_study_recommendation='18783-1'
    conclusions='55110-1'
    addendum='55107-7'
    radiology_reason_for_study='18785-6'
    patient_presentation='55108-5'
    complications='55109-3'
    summary='55112-7'
    key_images='55113-5'

class SurgicalOperationNote(Enum):
    """
    https://details.loinc.org/LOINC/11504-8.html
    """
    __document_type__ = DocumentType.surgical_operation_note

    procedure_anesthesia_narrative='59774-0'
    complications_Document='55109-3'
    surgical_operation_note_postoperative_diagnosis_narrative='10218-6'
    surgical_operation_note_preoperative_diagnosis_narrative='10219-4'
    procedure_estimated_blood_loss_narrative='59770-8'
    procedure_findings_narrative='59776-5'
    procedure_specimens_taken_narrative='59773-2'
    procedure_narrative='29554-3'
    procedure_implants_narrative='59771-6'
    surgical_operation_note_fluids_narrative='10216-0'
    surgical_operation_note_surgical_procedure_narrative='10223-6'
    plan_of_care_note='18776-5'
    planned_procedure_narrative='59772-4'
    procedure_disposition_narrative='59775-7'
    procedure_indications_Interpretation_narrative='59768-2'
    surgical_drains_narrative='11537-8'

class PhysicianDischargeSummary(Enum):
    """
    https://details.loinc.org/LOINC/11490-0.html
    """
    __document_type__ = DocumentType.physician_discharge_summary

    allergies= '48765-2'
    hospital_course_narrative= '8648-8'
    discharge_diagnosis_narrative= '78375-3'
    discharge_medications_narrative= '75311-1'
    plan_of_care= '18776-5'
    admission_diagnosis_narrative= '42347-5'
    medications_on_admission_narrative= '42346-7'
    chief_complaint_and_reason_for_visit_narrative = '46239-0'
    chief_complaint_narrative_reported= '10154-3'
    discharge_diet_narrative= '42344-2'
    history_of_family_member_diseases_narrative= '10157-6'
    functional_status_assessment_note= '47420-5'
    history_of_past_illness_narrative= '11348-0'
    history_of_present_illness_narrative= '10164-2'
    hospital_consultations_document= '18841-7'
    hospital_discharge_instructions= '8653-8'
    hospital_discharge_physical_findings_narrative= '10184-0'
    hospital_discharge_studies_summary_narrative= '11493-4'
    history_of_immunization_narrative= '11369-6'
    diet_and_nutrition_narrative= '61144-2'
    problem_list_reported= '11450-4'
    history_of_procedures_document= '47519-4'
    reason_for_visit_narrative= '29299-5'
    review_of_systems_narrative_reported= '10187-3'
    social_history_narrative= '29762-2'
    vital_signs= '8716-3'


class ProcedureNote(Enum):
    """
    https://details.loinc.org/LOINC/28570-0.html
    """
    __document_type__ = DocumentType.procedure_note

    assessment_and_plan='51847-2'
    assessment='51848-0'
    plan_of_care='18776-5'
    complications_document='55109-3'
    procedure_description='29554-3'
    postprocedure_diagnosis_narrative='59769-0'
    procedure_indications_interpretation_narrative='59768-2'
    allergies='48765-2'
    procedure_anesthesia_narrative='59774-0'
    chief_complaint_and_reason_for_visit_narrative='46239-0'
    chief_complaint_narrative_reported='10154-3'
    family_history='10157-6'
    history_of_past_illness_narrative='11348-0'
    history_of_present_illness_narrative='10164-2'
    past_medical_history='11348-0'
    medication_administered_narrative='29549-3'
    medications='10160-0'
    physical_examination='29545-1'
    planned_procedure_narrative='59772-4'
    procedure_disposition_narrative='59775-7'
    procedure_estimated_blood_loss_narrative='59770-8'
    procedure_findings_narrative='59776-5'
    procedure_implants_narrative='59771-6'
    procedure_specimens_taken_narrative='59773-2'
    history_of_procedures_document='47519-4'
    reason_for_visit='29299-5'
    review_of_systems_narrative_reported='10187-3'
    social_history_narrative='29762-2'

    #Andy TODO: examine non-standard use found in samples (AllScripts, HL7)
    medical_general_history='11329-0'
    postoperative_diagnosis='10218-6'
    surgical_operation_note_preoperative_dx='10219-4'
    surgical_drains_narrative='11537-8'


###############################################################################
#
# Meaningful Use 2 (MU2) Common elements.
#
###############################################################################

class MU2(object):
    """
    Meanginful Use 2 (MU2) common dataset
    https://www.healthit.gov/sites/default/files/c-cda_and_meaningfulusecertification.pdf
    """
    patient_name = 0
    sex = 1
    date_of_birth=2
    race =3
    ethnicity=4
    preferred_language=5
    care_team_members =6
    medications =7
    medication_allergies =8
    care_plan = 9
    problems =10
    laboratory_tests = 11
    laboratory_result = 12
    procedures =13
    smoking_status=14 # Andy TODO: https://s.details.loinc.org/LOINC/72166-2.html
    vital_signs=15