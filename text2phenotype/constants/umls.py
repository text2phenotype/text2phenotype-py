from enum import Enum

###############################################################################
#
# TUI (Type Unique Identifier) defines UMLS Semantic Types
# https://metamap.nlm.nih.gov/SemanticTypesAndGroups.shtml
#
###############################################################################


class TUI(Enum):
    T019 = 'Congenital Abnormality'
    T020 = 'Acquired Abnormality'
    T023 = 'Body Part, Organ, or Organ Component'
    T033 = 'Finding'
    T037 = 'Injury or Poisoning'
    T046 = 'Pathologic Function'
    T047 = 'Disease or Syndrome'
    T048 = 'Mental or Behavioral Dysfunction'
    T059 = 'Laboratory Procedure'
    T060 = 'Diagnostic Procedure'
    T061 = 'Therapeutic or Preventive Procedure'
    T109 = 'Organic Chemical'
    T114 = 'Nucleic Acid, Nucleoside, or Nucleotide'
    T116 = 'Amino Acid, Peptide, or Protein'
    T121 = 'Pharmacologic Substance'
    T122 = 'Biomedical or Dental Material'
    T123 = 'Biologically Active Substance'
    T125 = 'Hormone'
    T127 = 'Vitamin'
    T129 = 'Immunologic Factor'
    T130 = 'Indicator, Reagent, or Diagnostic Aid'  # bsv_minus
    T131 = 'Hazardous or Poisonous Substance'
    T184 = 'Sign or Symptom'
    T190 = 'Anatomical Abnormality'
    T191 = 'Neoplastic Process'
    T195 = 'Antibiotic'  # # bsv_minus
    T197 = 'Inorganic Chemical'
    T201 = 'Clinical Attribute'
    T200 = 'Clinical Drug'
    T203 = 'Drug Delivery Device'

PROBLEM_TUI = [TUI.T019,
               TUI.T020,
               TUI.T033,
               TUI.T037,
               TUI.T046,
               TUI.T047,
               TUI.T048,
               TUI.T184,
               TUI.T190,
               TUI.T191]

DRUG_TUI = [TUI.T109,
            # TUI.T114, (-) Nucleic Acid, Nucleoside, or Nucleotide
            TUI.T116,
            TUI.T121,
            # TUI.T122, (-) Biomedical or Dental Material "capsule, latex, etc"
            TUI.T123,
            TUI.T125,
            TUI.T127,
            TUI.T129,
            TUI.T131, # (+) Hazardous or Poisonous Substance
            TUI.T195, # (+) Antibiotic
            TUI.T197,
            TUI.T200,
            TUI.T203]

BODYSITE_TUI = [TUI.T023]

LAB_TUI = [TUI.T201]

PROCEDURE_TUI = [TUI.T060, TUI.T061]

class SemTypeCtakesAsserted(Enum):
    AnatomicalSite = 0
    Antibiotic = 1
    Bacterium = 2
    DiseaseDisorder = 3
    Entity = 4
    Lab = 5
    MedicalDevice = 6
    Medication = 7
    Procedure = 8
    SignSymptom = 9


class DRUG_TTY(Enum):
    """
    https://www.nlm.nih.gov/research/umls/rxnorm/docs/appendix5.html
    """
    PSN = ['Prescribable Name',
           'Synonym of another TTY, given for clarity and for display purposes in electronic prescribing applications. Only one PSN per concept',
           'Leena 28 Day Pack']
    SY = ['Synonym', 'Prozac 4 MG/ML Oral Solution']
    SCD = ['Semantic Clinical Drug', 'Ingredient + Strength + Dose Form', 'Fluoxetine 4 MG/ML Oral Solution']
    SCDC = ['Semantic Clinical Drug Component', 'Ingredient + Strength', 'Fluoxetine 4 MG/ML']
    BN = ['Brand Name', 'proprietary name for a family of products containing a specific active ingredient', 'Prozac']
    IN = ['Ingredient',
          'compound or moiety that gives the drug its distinctive clinical properties. Ingredients generally use the US Adopted Name',
          'Fluoxetine']
    SBDG = ['Semantic Branded Dose Form Group', 'Brand Name + Dose Form Group', 'Prozac Pill']
    SBD = ['Semantic Branded Drug', 'Ingredient + Strength + Dose Form + Brand Name',
           'Fluoxetine 4 MG/ML Oral Solution [Prozac])']
    SBDC = ['Semantic Branded Drug Component', 'Ingredient + Strength + Brand Name', 'Fluoxetine 4 MG/ML [Prozac]']
    SCDG = ['Semantic Clinical Dose Form Group', 'Ingredient + Dose Form Group', 'Fluoxetine Oral Product']
    SCDF = ['Semantic Clinical Drug Form', 'Ingredient + Dose Form', 'Fluoxetine Oral Solution']
    SBDF = ['Semantic Branded Drug Form', 'Ingredient + Dose Form + Brand Name', 'Fluoxetine Oral Solution [Prozac]']
    PIN = ['Precise Ingredient',
           'specified form of the ingredient that may or may not be clinically active. Most precise ingredients are salt or isomer forms',
           'Fluoxetine Hydrochloride']
    DF = ['Dose Form', 'any ingredient', 'Oral Solution']
    DFG = ['Dose Form Group', 'any ingredient', 'Oral Liquid)']
    ET = ['Dose Form Entry Term', 'any ingredient', 'Nasal Drops']


class LAB_TTY(Enum):
    COMP = ['Component', 'Tyrosine crystals']
    OSN = ['Official short name', 'Glucose']
    LC = ['Long common name', 'red cell adenosine deaminase activity']
    LN = ['Official fully-specified name', 'Anti-ganglioside GM1 IgM antibody']


class DIAGNOSIS_TTY(Enum):
    """
    https://www.nlm.nih.gov/research/umls/sourcereleasedocs/current/ICD10CM/sourcerepresentation.html
    """
    PT = ['preferred term', 'Fracture of one rib, left side, initial encounter for open fracture']
    AB = ['Abbreviation in any source vocabulary', 'Adv eff antithyroid agnt']
    HT = ['Hierarchical Term', 'Other metabolic disorders']
    ET = ['Entry Term', 'Hypertensive chronic kidney disease NOS']
    SY = ['Synonym', 'Hairy Cell Leukemia']
    PN = ['Preferred Name', 'Embolism due to cardiac prosthetic devices, implants and grafts, initial encounter']
    LLT = ['Lower Level Term', 'Inflammation gallbladder']
    PM = ['Machine permutation', 'Papillitis, Optic Nerve']


class PROBLEM_TTY(Enum):
    """
    https://www.nlm.nih.gov/research/umls/sourcereleasedocs/current/SNOMEDCT_US/stats.html
    """
    PT = ['preferred term', 'Tumor of submandibular gland']
    SY = ['Synonym', 'Protein S deficiency']
    FN = ['Full form of descriptor', 'Manic bipolar I disorder in full remission']
    IS = ['Obsolete Synonym', 'Disease of skin, NOS']


class PROCEDURE_TTY(Enum):  # TODO: better human readable names
    HX = ['Expanded version of short hierarchical term',
          'Medical and Surgical @ Upper Joints @ Reposition @ Acromioclavicular Joint, Left @ Percutaneous Endoscopic @ No Device']
    AB = ['Abbreviation in any source vocabulary', 'Drainage of Right Saphenous Vein, Percutaneous Approach']
    PT = ['preferred term', 'Occlusion of Left Vertebral Vein with Extraluminal Device, Open Approach']
    PX = ['Expanded preferred terms',
          'Medical and Surgical @ Lower Bones @ Insertion @ Tibia, Left @ Percutaneous @ External Fixation Device, Limb Lengthening @ No Qualifier']
    ETCLIN = ['Entry term, clinician description',
              'Repair of high imperforate anus with rectourethral fistula by perineal approach']
    ETCF = ['Entry term, consumer friendly description', 'Reconstruction of midface bones with bone graft']
    SY = ['Synonym', 'Computed tomography of thorax with contrast']


TTY = list(set([drug.name for drug in DRUG_TTY] +
               [lab.name for lab in LAB_TTY] +
               [dx.name for dx in DIAGNOSIS_TTY] +
               [core.name for core in PROBLEM_TTY]))
TTY.sort()


def url_umls(sab_source_abbreviation: str):
    """
    https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/abbreviations.html

    :param sab_source_abbreviation: UMLS Source name abbreviation
    :return:
    """
    return f"https://www.nlm.nih.gov/research/umls/sourcereleasedocs/current/{sab_source_abbreviation}"


class Vocab(Enum):
    """
    UMLS Meta-thesaurus list

    https://www.hl7.org/fhir/terminologies-systems.html
    https://www.nlm.nih.gov/research/umls/sourcereleasedocs/index.html
    """
    AOD = 'Alcohol and Other Drug Thesaurus'
    ATC = 'Anatomical Therapeutic Chemical'
    BI = 'Beth Israel Problem List'
    CCPSS = 'Clinical Problem Statements'
    CCS = 'Clinical Classifications Software ICD-9'
    CCS_10 = 'Clinical Classifications Software ICD-10'
    CPT = 'Current Procedure Terminology'
    CST = 'Adverse Reaction Terms'
    CHV = 'Consumer Health Vocabulary'
    DRUGBANK = 'DRUGBANK'
    DXP = 'DXplain'
    GS = 'Gold Standard Drug Database'
    HCPCS = 'Healthcare Common Procedure Coding System'
    HCPT = 'CPT in HCPCS'
    HPO = 'Human Phenotype Ontology'
    ICD9CM = 'ICD-9 Clinical Modification'
    ICD10 = 'ICD10 ( standalone )'
    ICD10AE = 'ICD-10 American English Equiv'
    ICD10CM = 'ICD-10 Clinical Modification'
    ICD10PCS = 'ICD-10 Procedure Coding System'
    ICPC2ICD10ENG = 'ICPC2-ICD10 Thesaurus'
    ICPC2P = 'International Classification of Primary Care'
    LNC = 'LNC', 'https://www.hl7.org/fhir/loinc.html'
    LNC2000 = 'https://loinc.org/usage/obs/'
    LNC2HPO = 'https://gettext2phenotype.atlassian.net/browse/BIOMED-790'
    LNCICU = 'https://mimic.physionet.org/mimictables/d_labitems/'
    MDR = 'Regulatory Activities'
    MEDCIN = 'point-of-care tools for EMR'
    MEDLINEPLUS = 'Health Topics'
    MMSL = 'Multum (Drug patient safety)'
    MMX = 'Micromedex'
    MSH = 'Medical Subject Headings'
    MTH = 'UMLS Metathesaurus Names'
    MTHICD9 = 'UMLS Additional Entry Terms for ICD-9-CM'
    MTHSPL = 'FDA Structured Product labels'
    NCI = 'NCI Thesaurus'
    NCI_FDA = 'FDA Structued Product Labeling'
    NCI_CTCAE = 'Common Terminology Criteria for Adverse Events'
    NDDF = 'FDB MedKnowledge'
    NDFRT = 'National Drug File - Reference Terminology'
    RCD = 'Read Codes, became SNOMED Clinical Terms'
    RCDAE = 'Read Codes American English'
    RCDSY = 'Read Codes Synthesized'
    RXNORM = 'https://www.hl7.org/fhir/rxnorm.html'
    SNOMEDCT_US = 'https://www.hl7.org/fhir/snomedct.html'
    SNOMEDCT_CORE = 'https://www.nlm.nih.gov/research/umls/Snomed/core_subset.html'
    VANDF = 'VA National Drug File'


LAB_VOCAB = [Vocab.LNC,
             Vocab.LNC2000,
             Vocab.LNC2HPO,
             Vocab.LNCICU]
DRUG_VOCAB = [Vocab.RXNORM,  # SYN listed in order of usage frequency
              Vocab.MTHSPL,
              Vocab.SNOMEDCT_US,
              Vocab.NDFRT,
              Vocab.MMSL,
              Vocab.GS,
              Vocab.NDDF,
              Vocab.MMX,
              Vocab.VANDF,
              Vocab.MSH,
              Vocab.DRUGBANK,
              Vocab.NCI_FDA]
DIAGNOSIS_VOCAB = [Vocab.ICD10CM,  # Preferred Terms
                   Vocab.ICD9CM,  # Preferred Terms
                   Vocab.ICD10,  # Preferred Terms
                   Vocab.ICD10AE,  # Preferred Terms
                   Vocab.MTH,
                   Vocab.MEDCIN,
                   Vocab.MDR,
                   Vocab.MSH,
                   Vocab.CHV,
                   Vocab.ICPC2ICD10ENG,
                   Vocab.NDFRT,
                   Vocab.MTHICD9,
                   Vocab.NCI,
                   Vocab.ICPC2P,
                   Vocab.DXP,
                   Vocab.HPO,
                   Vocab.NCI_FDA,
                   Vocab.CCS,
                   Vocab.CCS_10,
                   Vocab.NCI_CTCAE]
PROBLEM_VOCAB = [Vocab.SNOMEDCT_CORE,  # Preferred Terms
                 # SYN listed in order of usage frequency (roughly, some expect curation)
                 Vocab.CHV,
                 Vocab.MSH,
                 Vocab.RCD,
                 Vocab.MDR,
                 Vocab.MEDCIN,
                 Vocab.NCI,
                 Vocab.ICPC2P,
                 Vocab.MTH,
                 Vocab.HPO,
                 Vocab.DXP,
                 Vocab.CST,
                 Vocab.CCPSS,
                 Vocab.LNC2HPO,
                 Vocab.RCDAE,
                 Vocab.MEDLINEPLUS,
                 Vocab.BI]
PROCEDURE_VOCAB = [Vocab.ICD10PCS,  # Preferred Terms
                   Vocab.CPT,  # Preferred Terms
                   Vocab.SNOMEDCT_US,  # Preferred Terms
                   Vocab.HCPT,  # Preferred Terms
                   Vocab.HCPCS]  # Preferred Terms
