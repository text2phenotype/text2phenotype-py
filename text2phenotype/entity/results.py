from typing import Dict

from text2phenotype.entity.concept import ConceptList
from text2phenotype.entity.attributes import Serializable, TextSpan, Attributes, LabAttributes, DrugAttributes

###############################################################################
#
# cTAKES results
#
###############################################################################

class ResultType(object):
    clinical = 'result'  # default_clinical
    lab_value = 'labValues'
    drug_ner = 'drugEntities'
    smoking = 'smokingStatus'
    temporal = 'events'


class Result(Serializable):

    def __init__(self, source=None, type=ResultType.clinical):
        self.match = None
        self.aspect = None
        self.name = None
        self.attributes = None
        self.concepts = None

        self.id = None  # TODO: ?
        self.sectionOffset = None  # TODO: ?
        self.sectionOid = None  # TODO: ?
        self.sentence = None  # TODO: ?

        if source: self.from_json(source, type)
    
    @property
    def semantic_type(self) -> str:
        if self.name:
            return self.name.replace('Mention', '')

    def from_json(self, source: Dict, type=ResultType.clinical):
        self.match = TextSpan(source.get('text'))
        self.aspect = source.get('aspect')
        self.name = source.get('name')

        attributes = source.get('attributes', dict())

        if type == ResultType.clinical:
            self.attributes = Attributes(attributes)

        if type == ResultType.drug_ner:
            self.attributes = DrugAttributes(attributes)

        if type == ResultType.lab_value:
            self.attributes = LabAttributes(attributes)

        self.concepts = ConceptList(source.get('umlsConcept', list()))

        self.id = source.get('id')
        self.sentence = source.get('sentence')
        self.sectionOid = source.get('sectionOid')
        self.sectionOffset = source.get('sectionOffset')

    def to_json(self) -> Dict:
        return {'text': self.match.to_json(),
                'aspect': self.aspect,
                'name': self.name,
                'attributes': self.attributes.to_json(),
                'umlsConcept': self.concepts.to_json(),
                'id': self.id,
                'sentence': self.sentence,
                'sectionOid': self.sectionOid,
                'sectionOffset': self.sectionOffset}

    def to_table(self, tab='\t'):
        """
        Reader: nlp_reader.results.items[0].concepts[0].cui
        """
        res = [self.pretty('text', self.match, tab),
               self.pretty('aspect', self.aspect, tab),
               self.pretty('name', self.name, tab)]

        dep = [f"text{tab}{self.match.to_brat(tab).pop()}",
               f"aspect{tab}{self.nice(self.aspect)}",
               f"name{tab}{self.nice(self.name)}"]

        res += self.attributes.to_brat(tab)

        for c in self.concepts:
            for item in c.to_brat(tab):
                res.append(item)
        return res


class ResultList(Serializable):

    def __init__(self, source=None, type=ResultType.clinical):
        self.items = list()

        if source: self.from_json(source, type)

    def __iter__(self):
        """
        https://stackoverflow.com/questions/21665485/how-to-make-a-custom-object-iterable
        :return: list (iterable)
        """
        return iter(self.items)

    def __getitem__(self, index):
        """
        https://stackoverflow.com/questions/22463866/python-object-does-not-support-indexing
        :param index:
        :return:
        """
        return self.items[index]

    def to_table(self, tab='\t'):
        out = ['ResultList']
        for result in self.items:
            out += result.to_brat(tab)
        return out

    def from_json(self, source: Dict, result_type=ResultType.clinical):
        for concept in source.get(result_type):
            self.items.append(Result(concept, result_type))

    def to_json(self):
        return [r.to_json() for r in self.items]
