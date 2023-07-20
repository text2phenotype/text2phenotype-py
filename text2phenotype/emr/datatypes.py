#################################################################################
# The data types package refers to an intermediate format for variables
# extracted from an EMR. The destination format is FHIR, the use
# of these data types is only intended to be an intermediary.
#
################################################################################

VOCAB_ICD9 = 'http://hl7.org/fhir/sid/icd-9-cm'
VOCAB_ICD10 = 'http://hl7.org/fhir/sid/icd-10'
VOCAB_CPT = 'http://www.ama-assn.org/go/cpt'
VOCAB_RXNORM = 'http://www.nlm.nih.gov/research/umls/rxnorm'
VOCAB_SNOMEDCT_US = 'http://snomed.info/sct'

__vocabulary__ = {
    'CPT': VOCAB_CPT,
    'ICD9CM': VOCAB_ICD9,
    'ICD10CM': VOCAB_ICD10,
    'RXNORM': VOCAB_RXNORM,
    'SNOMEDCT_US': VOCAB_SNOMEDCT_US
}


################################################################################
class Diagnosis:
    def __init__(self, code, display, system='http://hl7.org/fhir/sid/icd-10'):
        """
        https://www.cob.cms.hhs.gov/Section111/help/ICD10_DX_Codes.txt
        """
        self.code = code
        self.display = display
        self.system = system

    def __str__(self):
        return str(self.__dict__)


################################################################################
class CodedMention:
    def __init__(self, code, display, system, polarity=None, status=None, cui=None):
        """
        DataType for NLP Autocoder response in the form:
         {
          code': 'R23.0',
         'cui': 'C0010520',
         'polarity': 'negated',
         'status': 'current status',
         'text': 'cyanosis',
         'vocab': 'ICD10CM'
        }

        Note that param names map to how FHIR refers to this datatype, not how UMLS internally references.

        :param code: knowledge source system that the code references, such as 'I.10' for hypertension
        :param display: text that is preferred, returned by NLP autocoding
        :param system: AKA 'dictionary' AKA 'knowledge source' ... 'source vocabulary'
        :param polarity: negated or not -- if negated, probably don't want to output it (no evidence of hypertension)
        :param status: current status, history status, etc. (if known)
        :param cui: UMLS unique concept identifier
        :return:
        """
        self.code = code
        self.display = display
        self.system = system
        self.polarity = polarity
        self.status = status
        self.cui = cui

        # TODO: resolve naming conventions for vocabularies
        # if self.system not in __vocabulary__.values():
        #     self.system = __vocabulary__.get(self.system)

    def __str__(self):
        return str(self.__dict__)
