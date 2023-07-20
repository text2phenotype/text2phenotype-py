from typing import List, Dict

from text2phenotype.entity.attributes import Serializable

###############################################################################
#
# ['result'][index]['umlsConcept'][index]
#
###############################################################################
class Concept(Serializable):

    def __init__(self, source=None):
        self.code = None
        self.cui = None
        self.tui = None
        self.tty = None
        self.preferredText = None
        self.codingScheme = None

        if source:
            self.from_json(source)

    def to_bsv(self):
        """
        :return: README.concept_ctakes = 'cui|tui|tty|code|vocab|text|preferred_text'
        """
        return [f'{self.cui}|{self.tui}|{self.tty}|{self.code}|{self.codingScheme}|{self.preferredText}']

    def to_table(self, tab='\t'):
        """
        :return: README.concept_ctakes = 'cui|tui|code|vocab|text|preferred_text'
        """
        out = [f"cui{tab}{self.cui}"]

        out.append(f"tui{tab}{self.tui}")
        out.append(f"tty{tab}{self.tty}")
        out.append(f"code{tab}{self.code}")
        out.append(f"vocab{tab}{self.codingScheme}")
        out.append(f"pref{tab}{self.preferredText}")

        return out

    def from_json(self, source: Dict) -> None:
        self.code = source.get('code')
        self.cui = source.get('cui')
        self.tui = source.get('tui')
        self.tty = source.get('tty')
        self.preferredText = source.get('preferredText')
        self.codingScheme = source.get('codingScheme')

        if not self.codingScheme:
            self.codingScheme = source.get('vocab')

###############################################################################
#
# ['result'][index]['umlsConcept']
#
###############################################################################

class ConceptList(Serializable):

    def __init__(self, source=None):
        self.items = list()
        if source:
            self.from_json(source)

    def __getitem__(self, index):
        return self.items[index]

    def __iter__(self):
        return iter(self.items)

    def from_json(self, source:List):
        for concept in source:
            self.items.append(Concept(concept))

    def to_json(self) -> List[Concept]:
        return [c.to_json() for c in self.items]

    def __eq__(self, other: Serializable):
        return self.to_json() == other.to_json()

