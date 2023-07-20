from __future__ import absolute_import, division, print_function, unicode_literals

from text2phenotype.ccda.vocab import Vocab

###############################################################################
#
# XPATH Ignore sections
#
###############################################################################

__codes__ = {
    Vocab.SNOMED_CT: [
        '55561003',  # Active
        '413322009',  # Resolved
        '409586006',  # Complaint
        '55561003',  # Treatment Status
        '397659008',  # Age (observeable entity)
        '64572001',  # Condition
        '29308',  # Diagnosis
    ]}

__sections__ = {
    Vocab.LOINC: [
        '26436-6',  # Laboratory Studies
        '13362-9',  # Collection duration of Urine
        '30973-2',  # DOSE NUMBER -- VACCIN/Clinical

        '34552-0',  # 2D echocardiogram panel

        '1742-6',  # Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma]

        '1751-7',  # Albumin [Mass/volume] in Serum or Plasma]
        '1754-1',  # Albumin Ur-mCnc (Albumin [Mass/​volume] in Urine)

        '18041-4',  # Aortic valve Ejection [Time] by US.doppler

        '12805-8',  # Alkaline Phosphatase, Serum
        '6768-6',  # Alkaline phosphatase [Enzymatic activity/volume] in Serum or Plasma]

        '10466-1',  # Anion gap 3 in Serum or Plasma
        '1920-8',  # Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma]

        '18089-3',  # AV Orifice Area US

        '706-2',  # Basos -- Basophils/​100 leukocytes in Blood by Automated count
        '704-7',  # Baso(Absolute) -- Basophils [#/​volume] in Blood by Automated count

        '24321-2',  # BMP
        '51990-0',  # Basic Metabolic Panel (Blood)

        '14627-4',  # Bicarbonate [Moles/volume] in Venous blood

        '15152-2',  # Bilirubin, Direct
        '1975-2',  # Bilirubin.total [Mass/volume] in Serum or Plasma]

        '6299-2',  # BUN (Urea nitrogen [Mass/​volume] in Blood)
        '3094-0',  # Blood Urea Nitrogen, Serum

        '17861-6',  # Calcium, Total Serum

        '1002',  # Complete CBC

        '2028-9',  # Carbon Dioxide
        '20565-8',  # CO2, Whole Blood

        '2069-3',  # Cl -- Chloride [Moles/​volume] in Blood
        '2075-0',  # Chloride [Moles/volume] in Serum or Plasma

        '38483-4',  # Cr -- Creatinine [Mass/​volume] in Blood)
        '35674-1',  # Creatinine [Mass/volume] in unspecified time Urine
        '2160-0',  # Creatinine [Mass/volume] in Serum or Plasma

        '34534-8',  # EKG 12 channel panel
        '18844-1',  # EKG impression Narrative

        '713-8',  # Eos -- Eosinophils/​100 leukocytes in Blood by Automated count)
        '711-2',  # Eos (Absolute Value) -- Eosinophils [#/​volume] in Blood by Automated count

        '789-8',  # Erythrocytes [#/volume] in Blood by Automated count
        '787-2',  # Erythrocyte mean corpuscular volume [Entitic volume] by Automated count]
        '785-6',  # Erythrocyte mean corpuscular hemoglobin [Entitic mass] by Automated count]
        '786-4',  # Erythrocyte mean corpuscular hemoglobin concentration [Mass/volume] by Automated count]
        '788-0',  # Erythrocyte distribution width [Ratio] by Automated count]
        '30392-5',  # Nucleated erythrocytes [#/volume] in Blood]
        '26461-4',  # Nucleated erythrocytes/100 erythrocytes in Blood

        '2324-2',  # GGT -- Gamma glutamyl transferase [Enzymatic activity/​volume] in Serum or Plasma

        '2339-0',  # Glu (Glucose [Mass/​volume] in Blood)
        '2345-7',  # Glucose, Serum
        '6777-7',  # Deprecated Glucose [Mass/volume] in Serum or Plasma

        '2336-6',  # Globulin [Mass/volume] in Serum
        '33914-3',  # Glomerular filtration rate/1.73 sq M.predicted by Creatinine-based formula (MDRD)

        '30313-1',  # HGB
        '718-7',  # HGB (HEMOGLOBIN) -- Hemoglobin [Mass/​volume] in Blood
        '4548-4',  # Hgb A1c MFr Bld
        '2335-8',  # Hemoccult Stl Ql -- Hemoglobin.gastrointestinal [Presence] in Stool

        '20570-8',  # HCT -- Hematocrit [Volume Fraction] of Blood)
        '4544-3',  # HCT (HEMATOCRIT) -- Hematocrit [Volume Fraction] of Blood by Automated count

        '6301-6',  # INR in Platelet poor plasma by Coagulation assay

        '2532-0',  # LDH -- Lactate dehydrogenase [Enzymatic activity/​volume] in Serum or Plasma

        '736-9',  # Lymphs -- Lymphocytes/​100 leukocytes in Blood by Automated count
        '731-0',  # Lymphs -- Absolute

        '6298-4',  # K (Potassium [Moles/​volume] in Blood)
        '22760-3',  # Potassium, Serum (Potassium [Mass/​volume] in Serum or Plasma)
        '2823-3',  # Potassium [Moles/volume] in Serum or Plasma

        '26515-7',  # PLT (Platelets [#/​volume] in Blood)
        '2777-1',  # Phosphate [Mass/volume] in Serum or Plasma]
        '2885-2',  # Protein [Mass/volume] in Serum or Plasma

        '5905-5',  # Monocytes -- Monocytes/​100 leukocytes in Blood by Automated count
        '742-7',  # Monocytes(Absolute)

        '14957-5',  # Microalbumin [Mass/volume] in Urine
        '14959-1',  # Microalbumin/Creatinine [Mass Ratio] in Urine]

        '2947-0',  # Na -- Sodium [Moles/​volume] in Blood
        '2951-2',  # Sodium, Serum -- Sodium [Moles/​volume] in Serum or Plasma

        '770-8',  # Polys -- Neutrophils/​100 leukocytes in Blood by Automated count
        '751-8',  # Polys (Absolute)

        '6460-0',  # Sputum Culture (Bacteria identified in Sputum by Culture	)
        '6598-7',  # Troponin T (Troponin T.cardiac [Mass/​volume] in Serum or Plasma)

        '39156-5',  # Body Mass Index Calculated
        '3140-1',  # Body Surface Area Calculated
        '3141-9',  # Patient Body Weight - Measured
        '29463-7',  # Body weight
        '41909-3',  # Body Mass Index
        '8310-5',  # Body Temperature
        '8287-5',  # Head Circumference
        '8867-4',  # Heart Rate
        '8302-2',  # Height
        '8306-3',  # Height (Lying)
        '9279-1',  # Respiratory Rate

        '14646-4',  # HDLc SerPl-sCnc -- Cholesterol in HDL [Moles/​volume] in Serum or Plasma

        '2089-1',  # LDLc SerPl-mCnc
        '2093-3',  # Cholest SerPl-mCnc
        '2085-9',  # HDLc SerPl-mCnc -- Cholesterol in HDL [Mass/​volume] in Serum or Plasma
        '12951-0',  # Trigl SerPl Calc-mCnc -- Triglyceride [Mass/​volume] in Serum or Plasma by calculation
        '2571-8',  # Trigl SerPl-mCnc -- Triglyceride [Mass/​volume] in Serum or Plasma

        '33765-9',  # WBC
        '26464-8',  # WBC Count -- Leukocytes [#/​volume] in Blood
        '6690-2',  # WBC -- Leukocytes [#/​volume] in Blood by Automated count

        '8462-4',  # BP Diastolic
        '8480-6',  # Systolic blood pressure

        '30522-7',
        # CRP SerPl High Sens-mCnc -- C reactive protein [Mass/​volume] in Serum or Plasma by High sensitivity method
        '10524-7',  # Cyto Cervix -- Microscopic observation [Identifier] in Cervix by Cyto stain

        '31777-6',  # C trach Ag XXX Ql -- Chlamydia trachomatis Ag [Presence] in Unspecified specimen
        '50561-0',  # Prot Ur Strip.auto-mCnc
        '2119-6',  # HCG SerPl-sCnc -- Choriogonadotropin [Moles/​volume] in Serum or Plasma
        '73906-0',  # HIV1+2 IgG Bld Ql EIA.rapid -- HIV 1+​2 IgG Ab [Presence] in Blood by Rapid immunoassay
        '1314-4',  # Rh Ig Scn Bld-Imp -- Rh immune globulin screen [interpretation]

        '35266-6',  # Gleason Score Spec Ql
        '777-3',  # Platelet # Bld Auto -- Platelets [#/​volume] in Blood by Automated count
        '2575-9',  # PreB-LP SerPl-mCnc -- Lipoprotein.pre-beta [Mass/​volume] in Serum or Plasma
        '19195-7',  # PSA SerPl-aCnc
        '31971-5',  # S pyo Ag XXX Ql -- Streptococcus pyogenes Ag [Presence] in Unspecified specimen

        '5292-8',  # RPR -- Reagin Ab [Presence] in Serum by VDRL

        '3050-2',  # T3 Uptake -- Triiodothyronine resin uptake (T3RU) in Serum or Plasma

        '3026-2',  # Thyroxine (T4)
        '3022-1',  # Free Thyroxine Index -- Deprecated Thyroxine free index in Serum or Plasma

        '11579-0',  # Thyrotropin [Units/volume] in Serum or Plasma by Detection limit less than or equal to 0.05 mIU/L
        '3016-3',  # Thyrotropin [Units/volume] in Serum or Plasma

        '48767-8',  # Annotation Comment
        '18314-5',  # Hematology Comments:

        '29308-4',  # Encounter Diagnosis (TODO: investigate)
        '11323-3',  # Health status
        '48766-0',
        # Information source (PHVS_ReportingSourceType_NND / Codes specifying the type of facility or provider
        # associated with the source of information sent to Public Health.)
        '33999-4',  # Status

        'CONSP-X',  # Consent for Surgical Procedure
        'UNKNOWN',  # Urobilinogen -- found in Vitera_CCDA_SMART_Sample.xml
    ]}


def _contains(vocab: Vocab, code, source):
    if vocab in source.keys():
        return code in source.get(vocab)
    else:
        return False


def skip_code(vocab: Vocab, code):
    """
    Check if a code in a vocabulary should be skipped, such as a general code like "Diagnosis"
    :param vocab:
    :param code:
    :return: bool if vocabulary:code should be skipped
    """
    return _contains(vocab, code, __codes__)


def skip_section(code):
    """
    Check of a section should be skipped, most likely because it isn't really a coded concept but rather a LOINC code
    section header.
    :param code: LOINC code
    :return: bool if code should not be considered a section header
    """
    return _contains(Vocab.LOINC, code, __sections__)
