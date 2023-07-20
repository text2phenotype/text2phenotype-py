from enum import Enum
from typing import List

from text2phenotype.ccda.vocab import Vocab


class Aspect(Enum):
    allergy = 0  # ingredients,chemicals,and medications in allergies section
    immunization = 1  # flu shot vaccinations, etc (sometimes oral like polio)
    lab = 2  # pipeline: lab_value LOINC concept name value units datetime
    medication = 3  # pipeline: drug_ner RXNORM concept name dosage units frequency datetime
    procedure = 4  # total hip replacement, ultrasound (surgical or done using "machine", like ultrasound, including
    # CT/MRI and even XRAY, echocardiogram)
    diagnosis = 5  # diseases,injury
    problem = 6  # diseases,problems,some signs and symptoms
    demographics = 7  # PHI section: demographics and patient identifiers,
    # @db "care descriptors, such as Admit Date. Encounter metadata about the appointment or visit the patient had"
    encounter = 8  # PHI section: patient encounters with physician and healthcare settings
    physical_exam = 9  # often heavily negated list of diagnosis, vital signs, and signs and symptoms (done by HUMAN)
    treatment = 10  # @db "instructions"
    social = 11  # social factors section: smoking status, diet, other personal history
    device = 12  # not supported
    other = 13  # section is multiclass or unknown

    @classmethod
    def get_active_aspects(cls) -> List['Aspect']:
        return [a for a in cls if a not in [cls.other, cls.device]]


class RelTime(Enum):
    history = 0
    present = 1
    plan = 2
    admit = 3
    discharge = 4
    transfer = 5


class Person(Enum):
    family = 0
    patient = 1
    provider = 2


class Template:
    def __init__(self,
                 section: str,
                 vocab: Vocab,
                 aspect: Aspect,
                 rel_time: RelTime = None,
                 narrative: bool = None,
                 person: Person = Person.patient):
        self.section: str = section
        self.vocab: Vocab = vocab
        self.aspect: Aspect = aspect
        self.narrative: bool = narrative
        self.rel_time: RelTime = rel_time
        self.person: Person = person


class Narrative(Template):
    def __init__(self, section: str, vocab: Vocab, aspect: Aspect, rel_time: RelTime = None):
        super().__init__(section, vocab, aspect, rel_time, True)


class Section(Enum):
    addendum = Template('55107-7', Vocab.other, Aspect.other)

    # @db: legal document, allows patient to give permission to health care proxies
    advanced_directives = Template('42348-3', Vocab.SNOMED_CT, Aspect.social, RelTime.plan)

    # @db : high level diagnosis when someone comes to hospital -- your best guess (might be wrong)
    admission_diagnosis = Template('42347-5', Vocab.SNOMED_CT, Aspect.diagnosis, RelTime.admit)

    allergies_and_adverse_reactions_document = Template('48765-2', Vocab.RXNORM, Aspect.allergy, RelTime.present)

    chief_complaint_narrative_reported = Narrative('10154-3', Vocab.SNOMED_CT, Aspect.problem, RelTime.present)

    chief_complaint_reason_for_visit_narrative = Narrative('46239-0', Vocab.SNOMED_CT, Aspect.problem, RelTime.present)

    clinical_presentations_document = Narrative('55108-5', Vocab.other, Aspect.other, RelTime.admit)

    complications_document = Narrative('55109-3', Vocab.other, Aspect.problem, RelTime.present)

    # @db: conclusion of mammogram could be "normal" ( positive / negative )
    conclusions_interpretation_document = Template('55110-1', Vocab.SNOMED_CT, Aspect.diagnosis, RelTime.present)

    current_imaging_procedure_descriptions_document = Template('55111-9', Vocab.CPT, Aspect.procedure, RelTime.present)

    # @db: probably only on discharge
    diet_and_nutrition_narrative = Narrative('61144-2', Vocab.SNOMED_CT, Aspect.treatment)

    discharge_diet_narrative = Narrative('42344-2', Vocab.SNOMED_CT, Aspect.treatment, RelTime.discharge)

    discharge_diagnosis_narrative = Narrative('78375-3', Vocab.SNOMED_CT, Aspect.diagnosis, RelTime.discharge)

    discharge_medications_narrative = Narrative('75311-1', Vocab.RXNORM, Aspect.medication, RelTime.discharge)

    document_summary = Template('55112-7', Vocab.other, Aspect.other)

    # @db: "uber category" can be any or all of the Aspects
    evaluation_and_plan = Narrative('51847-2', Vocab.SNOMED_CT, Aspect.diagnosis, RelTime.present)

    evaluation_note = Narrative('51848-0', Vocab.SNOMED_CT, Aspect.diagnosis, RelTime.present)

    # @db: social
    functional_status_assessment_note = Narrative('47420-5', Vocab.SNOMED_CT, Aspect.social, RelTime.present)

    # @db: (s)oap subjective
    history_general_narrative = Narrative('11329-0', Vocab.SNOMED_CT, Aspect.other, RelTime.history)

    history_of_family_member_diseases_narrative = Template('10157-6',
                                                           Vocab.SNOMED_CT,
                                                           Aspect.diagnosis,
                                                           RelTime.history,
                                                           True,
                                                           Person.family)

    # @db: subset of general history (11329-0)
    history_of_hospitalizations_and_outpatient_visits_narrative = Narrative('46240-8',
                                                                            Vocab.SNOMED_CT,
                                                                            Aspect.other,
                                                                            RelTime.history)

    history_of_immunization_narrative = Narrative('11369-6', Vocab.CVX, Aspect.immunization, RelTime.history)

    history_of_medication_use_narrative = Narrative('10160-0', Vocab.RXNORM, Aspect.medication, RelTime.history)

    # @db: doesn't hurt to include devices. Implantation of pacemaker = Procedure, whereas "fitbit" is more like social
    history_of_medical_device_use = Template('46264-8', Vocab.other, Aspect.other, RelTime.history)

    # @db: really problem, not diagnosis
    history_of_past_illness_narrative = Narrative('11348-0', Vocab.SNOMED_CT, Aspect.problem, RelTime.history)

    # @db: really problem, not diagnosis
    history_of_present_illness_narrative = Narrative('10164-2', Vocab.SNOMED_CT, Aspect.problem, RelTime.present)

    history_of_procedures_document = Template('47519-4', Vocab.CPT, Aspect.procedure, RelTime.history)

    hospital_admission_diagnosis_narrative = Narrative('46241-6', Vocab.SNOMED_CT, Aspect.diagnosis, RelTime.admit)

    # @db: detailed history over time, some diagnostic procedure which had an impact
    # Disease progression throughout patient visit sequence always in discharge summary
    hospital_course_narrative = Narrative('8648-8', Vocab.SNOMED_CT, Aspect.other, RelTime.discharge)

    # @db: same as admission history and physical
    hospital_consultations_document = Narrative('18841-7', Vocab.SNOMED_CT, Aspect.problem, RelTime.present)

    hospital_discharge_dx = Template('11535-2', Vocab.SNOMED_CT, Aspect.diagnosis, RelTime.discharge)

    # @db: plan
    hospital_discharge_instructions = Narrative('8653-8', Vocab.SNOMED_CT, Aspect.treatment, RelTime.plan)

    hospital_discharge_medications = Template('10183-2', Vocab.RXNORM, Aspect.medication, RelTime.discharge)

    # @db: problem
    hospital_discharge_physical_findings_narrative = Narrative('10184-0',
                                                               Vocab.SNOMED_CT,
                                                               Aspect.physical_exam,
                                                               RelTime.discharge)

    # @db: studies in procedures TODO: look into the examples -- procedures may be better heading here
    hospital_discharge_studies_summary_narrative = Narrative('11493-4', Vocab.LOINC, Aspect.other, RelTime.discharge)

    instructions = Narrative('69730-0', Vocab.other, Aspect.treatment, RelTime.present)

    interventions_narrative = Narrative('62387-6', Vocab.other, Aspect.treatment, RelTime.present)

    key_images_document_radiology = Template('55113-5', Vocab.SNOMED_CT, Aspect.other)

    medications_on_admission_narrative = Narrative('42346-7', Vocab.RXNORM, Aspect.medication, RelTime.admit)

    medication_administered_narrative = Narrative('29549-3', Vocab.RXNORM, Aspect.medication, RelTime.present)

    mental_status_narrative = Narrative('10190-7', Vocab.other, Aspect.physical_exam, RelTime.present)

    # @db : can include Aspect.problem: TODO
    objective_narrative = Narrative('61149-1', Vocab.SNOMED_CT, Aspect.other, RelTime.present)

    payment_sources_document = Narrative('48768-6', Vocab.other, Aspect.demographics, RelTime.present)

    physical_findings_narrative = Narrative('29545-1', Vocab.other, Aspect.physical_exam, RelTime.present)

    physical_findings_of_general_status_narrative = Narrative('10210-3',
                                                              Vocab.other,
                                                              Aspect.physical_exam,
                                                              RelTime.present)

    # @db: Aspect.procedure, Aspect.medication, Aspect.lab, Aspect.social (diet and excercise)
    plan_of_care = Narrative('18776-5', Vocab.SNOMED_CT, Aspect.treatment, RelTime.plan)

    planned_procedure_narrative = Narrative('59772-4', Vocab.CPT, Aspect.procedure, RelTime.plan)

    prior_procedure_descriptions = Template('55114-3', Vocab.CPT, Aspect.procedure, RelTime.history)

    problem_list_reported = Template('11450-4', Vocab.SNOMED_CT, Aspect.problem, RelTime.present)

    procedure_anesthesia_narrative = Narrative('59774-0', Vocab.CPT, Aspect.problem, RelTime.present)

    procedure_disposition_narrative = Narrative('59775-7', Vocab.CPT, Aspect.other, RelTime.present)

    procedure_estimated_blood_loss_narrative = Narrative('59770-8', Vocab.SNOMED_CT, Aspect.procedure)

    procedure_findings_narrative = Narrative('59776-5', Vocab.CPT, Aspect.procedure, RelTime.present)

    procedure_implants_narrative = Narrative('59771-6', Vocab.CPT, Aspect.procedure, RelTime.present)

    procedure_indications_interpretation_narrative = Narrative('59768-2', Vocab.SNOMED_CT, Aspect.other,
                                                               RelTime.present)

    procedure_narrative = Narrative('29554-3', Vocab.CPT, Aspect.procedure, RelTime.present)

    postprocedure_diagnosis_narrative = Narrative('59769-0', Vocab.SNOMED_CT, Aspect.diagnosis, RelTime.present)

    procedure_specimens_taken_narrative = Narrative('59773-2', Vocab.SNOMED_CT, Aspect.procedure, RelTime.present)

    # @db: YES is diagnosis
    radiology_reason_for_study_narrative = Narrative('18785-6', Vocab.SNOMED_CT, Aspect.problem, RelTime.present)

    radiology_study_recommendation_narrative = Narrative('18783-1', Vocab.SNOMED_CT, Aspect.problem, RelTime.present)

    radiology_comparison_study_observation_narrative = Narrative('18834-2',
                                                                 Vocab.SNOMED_CT,
                                                                 Aspect.problem,
                                                                 RelTime.present)

    radiology_study_observation_findings_narrative = Narrative('18782-3',
                                                               Vocab.SNOMED_CT,
                                                               Aspect.problem,
                                                               RelTime.present)

    radiology_imaging_study_impression_narrative = Narrative('19005-8',
                                                             Vocab.SNOMED_CT,
                                                             Aspect.problem,
                                                             RelTime.present)

    reason_for_visit_narrative = Narrative('29299-5', Vocab.SNOMED_CT, Aspect.problem, RelTime.present)

    reason_for_referral_narrative = Narrative('42349-1', Vocab.SNOMED_CT, Aspect.problem, RelTime.transfer)

    relevant_diagnostic_tests_laboratory_data_narrative = Narrative('30954-2', Vocab.LOINC, Aspect.lab, RelTime.present)

    requested_imaging_studies_information_document = Template('55115-0', Vocab.CPT, Aspect.procedure, RelTime.present)

    review_of_systems_narrative_reported = Narrative('10187-3', Vocab.SNOMED_CT, Aspect.other, RelTime.present)

    social_history_narrative = Narrative('29762-2', None, Aspect.social, RelTime.history)

    # @db: like a chief complaint
    subjective_narrative = Narrative('61150-9', Vocab.other, Aspect.problem, RelTime.present)

    surgical_drains_narrative = Narrative('11537-8', Vocab.other, Aspect.procedure, RelTime.present)

    surgical_operation_note_fluids_narrative = Narrative('10216-0', Vocab.CPT, Aspect.procedure, RelTime.present)

    surgical_operation_note_preoperative_diagnosis_narrative = Narrative('10219-4',
                                                                         Vocab.SNOMED_CT,
                                                                         Aspect.diagnosis,
                                                                         RelTime.present)
    surgical_operation_note_postoperative_diagnosis_narrative = Narrative('10218-6',
                                                                          Vocab.SNOMED_CT,
                                                                          Aspect.diagnosis,
                                                                          RelTime.present)

    surgical_operation_note_surgical_procedure_narrative = Narrative('10223-6',
                                                                     Vocab.CPT,
                                                                     Aspect.procedure,
                                                                     RelTime.present)

    vital_signs = Narrative('8716-3', Vocab.SNOMED_CT, Aspect.physical_exam, RelTime.present)
