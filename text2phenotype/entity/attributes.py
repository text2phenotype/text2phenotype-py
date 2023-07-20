from typing import Dict, List, Tuple

from text2phenotype.common.errors import Text2phenotypeError

###############################################################################
#
# Serializable
#
###############################################################################


class Serializable:
    def from_json(self, source) -> None:
        raise Text2phenotypeError('from_json() no default implementation')

    def to_json(self) -> Dict:
        return self.__dict__

    def __str__(self):
        return '\n'.join(self.to_table())

    def nice(self, value, show=''):
        if value is None: return show
        if value is False: return False
        return value

    def pretty(self, name, value, tab='\t') -> str:
        value = value if value else ''
        return f"{name}{tab}{value}"

    def to_bsv(self) -> List:
        return self.to_table('|')

    def to_table(self, tab='\t') -> List:
        out = ['']
        for key, val in self.__dict__.items():
            if not key: key = ''
            if not val: val = ''
            out.append(f'{key}{tab}{val}')
        return out


###############################################################################
#
# Document
#
###############################################################################

class DocumentAttributes(Serializable):
    """
    Conceptually derived from cTAKES
    http://ctakes.apache.org/apidocs/trunk/overview-tree.html
    http://ctakes.apache.org/apidocs/trunk/org/apache/ctakes/preprocessor/DocumentMetaData.html
    """

    def __init__(self, source=None):
        self.docid = None
        self.dob = None
        self.age = None
        self.gender = None
        self.date = None
        self.version = None
        self.jira = None
        self.user = None
        self.timestamp = None

        if source:
            self.from_json(source)

    def from_json(self, source: dict) -> None:
        self.docid = source.get('docid')
        self.dob = source.get('dob')
        self.age = source.get('age')
        self.gender = source.get('gender')
        self.date = source.get('date')
        self.version = source.get('version')
        self.jira = source.get('jira')
        self.user = source.get('user')
        self.timestamp = source.get('timestamp')

    def to_table(self, tab='\t'):
        return [self.pretty('version', self.version),
                self.pretty('timestamp', self.timestamp),
                self.pretty('jira', self.jira),
                "",
                self.pretty('docid', self.docid),
                self.pretty('dob', self.dob),
                self.pretty('age', self.age),
                self.pretty('gender', self.gender)]


###############################################################################
#
# ['result]['attributes']
#
###############################################################################
class Attributes(Serializable):
    """
    http://ctakes.apache.org/apidocs/trunk/org/apache/ctakes/assertion/attributes/features/GenericFeaturesExtractor.html
    """

    def __init__(self, source=None):
        self.polarity = None

        if source:
            self.from_json(source)

    def from_json(self, source: Dict) -> None:
        self.polarity = source.get('polarity')
        self.relTime = source.get('relTime', '')  # TODO: special case ?

    def to_table(self, tab='\t') -> List:
        return [f'polarity{tab}{self.polarity}']


###############################################################################
#
# ['labValues']['attributes']
#
###############################################################################
class LabAttributes(Serializable):

    def __init__(self, source=None):
        self.polarity = None

        self.labValue = None
        self.labValueUnit = None

        if source: self.from_json(source)

    def from_json(self, source: Dict) -> None:
        self.polarity = source.get('polarity')

        self.labValue = TextSpan(source.get('labValue'))
        self.labValueUnit = TextSpan(source.get('labValueUnit'))

    def to_json(self):
        return {'polarity': self.polarity,
                'labValue': self.labValue.to_json(),
                'labValueUnit': self.labValueUnit.to_json()}

    def to_table(self, tab='\t'):
        return [self.pretty('polarity', self.polarity, tab),
                self.pretty('labValue', self.labValue, tab),
                self.pretty('labValueUnit', self.labValueUnit, tab)]


###############################################################################
#
# ['drugEntities']['attributes']
#
###############################################################################
class DrugAttributes(Serializable):

    def __init__(self, source=None):
        self.polarity = None

        self.medDosage = None
        self.medDuration = None
        self.medForm = None
        self.medFrequencyNumber = None
        self.medFrequencyUnit = None
        self.medRoute = None
        self.medStatusChange = None
        self.medStrengthNum = None
        self.medStrengthUnit = None

        if source:
            self.from_json(source)

    def from_json(self, source: Dict):
        self.polarity = source.get('polarity')

        self.medDosage = source.get('medDosage')
        self.medDuration = source.get('medDuration')
        self.medForm = source.get('medForm')
        self.medFrequencyNumber = TextSpan(source.get('medFrequencyNumber'))
        self.medFrequencyUnit = TextSpan(source.get('medFrequencyUnit'))
        self.medRoute = source.get('medRoute')
        self.medStatusChange = source.get('medStatusChange')
        self.medStrengthNum = TextSpan(source.get('medStrengthNum'))
        self.medStrengthUnit = TextSpan(source.get('medStrengthUnit'))

    def to_json(self) -> Dict:
        return {'medDosage': self.medDosage,
                'medDuration': self.medDuration,
                'medForm': self.medForm,
                'medFrequencyNumber': self.medFrequencyNumber.to_json(),
                'medFrequencyUnit': self.medFrequencyUnit.to_json(),
                'medRoute': self.medRoute,
                'medStatusChange': self.medStatusChange,
                'medStrengthNum': self.medStrengthNum.to_json(),
                'medStrengthUnit': self.medStrengthUnit.to_json(),
                'polarity': self.polarity}

    def to_table(self, tab='\t'):
        return [self.pretty('polarity', self.polarity, tab),
                self.pretty('dosage', self.medDosage, tab),
                self.pretty('duration', self.medDuration, tab),
                self.pretty('strength', self.medStrengthNum, tab),
                self.pretty('strength_unit', self.medStrengthUnit, tab),
                self.pretty('frequency', self.medFrequencyNumber, tab),
                self.pretty('frequency_unit', self.medFrequencyUnit, tab),
                self.pretty('route', self.medRoute, tab)]


###############################################################################
#
# TextMatch
#
###############################################################################
class TextSpan(Serializable):

    def __init__(self, source=None):
        """
        http://ctakes.apache.org/apidocs/trunk/org/apache/ctakes/typesystem/type/textspan/package-tree.html
        """
        self.text = None
        self.start = None
        self.stop = None

        if source: self.from_json(source)

    def __eq__(self, other) -> bool:
        """
        literally (self == other)
        :param other: TextSpan to compare to
        :return: ture if start and stop positions are the same for self and other
        """
        self.guard_span()
        other.guard_span()

        return self.start == other.start and self.stop == other.stop

    def __gt__(self, other) -> bool:
        """
        literally (self > other )
        :param other: TextSpan to compare to
        :return: true if self.start and self.stop positions are greater than other.start and other.stop positions
        """
        self.guard_span()
        other.guard_span()

        if self.start > other.start:
            return True
        if self.start < other.start:
            return False

        return (self.start == other.start) and (self.stop > other.stop)

    def __str__(self):
        return '\n'.join(self.to_bsv())

    def __hash__(self):
        """
        https://stackoverflow.com/questions/1608842/types-that-define-eq-are-unhashable
        """
        return hash(self.__str__())

    def guard_span(self) -> None:
        """
        Guard against 5 cases:
           1. start or stop position is empty
           2. start or stop positions cannot be case to integer
           3. start and stop positions are the same ( start == stop )
           4. start or stop positions are negative
           5. start cannot be less than stop
        """
        if self.start is None:
            raise Text2phenotypeError(f"missing start position: {self.__dict__}")
        if self.stop is None:
            raise Text2phenotypeError(f"missing stop  position: {self.__dict__}")

        if int(self.start) == int(self.stop):
            raise Text2phenotypeError(f"start and stop positions are the same {self.__dict__}")

        if (int(self.start) < 0) or (int(self.stop) < 0):
            raise Text2phenotypeError(f"start or stop positions was negative {self.__dict__}")

        if int(self.start) > int(self.stop):
            raise Text2phenotypeError(f"start > stop {self.__dict__}")

    @staticmethod
    def overlap_ranges(range1: range, range2: range) -> set:
        """
        Return a set of character positions for two text spans

        Example overlap( range(0,6), range(2,4))

        :param range1: range or list [start,stop]
        :param range2: range or list [start,stop]
        :return:
        """
        r1, r2 = set(range1), set(range2)
        charmap = r1.intersection(r2)

        return charmap

    def from_json(self, source: List):
        """
        :param source: list, like ['heart', 0, 5]
        :return:
        """
        # print(f'from_json(source)= {source}')
        if isinstance(source, str):  # 'day'
            self.text = source

        elif isinstance(source, list):
            if 1 == len(source):  # ['day']
                self.text = source[0]

            elif 2 == len(source):
                self.start, self.stop = source

            elif 3 == len(source):  # ['day', 0, 5]
                self.text, self.start, self.stop = source
            else:
                raise Text2phenotypeError(f'source:list has wrong size= {len(source)}, source={source}')

        else:
            raise Text2phenotypeError(
                f' TextMatch.from_jsom(source) '
                f' unexpected type(source) = {type(source)} , '
                f' source = {source}')

    def to_range(self) -> range:
        """
        :return: range(start,stop) or None
        """
        self.guard_span()
        return range(self.start, self.stop)

    def to_tuple(self) -> Tuple:
        """
        :return: (start,stop)
        """
        self.guard_span()

        return (self.start, self.stop)

    def to_json(self) -> List:
        """
        :return: [text, start, stop] like ['mg', 11, 13] or empty list if text is None
        """
        if self.text is None:  # Required for TextMatch
            return list()

        return [self.text, self.start, self.stop]

    def to_bsv(self) -> List:
        text = self.text if self.text else ''
        start = self.start if self.start else ''
        stop = self.stop if self.stop else ''

        return [f"{text}|{start}|{stop}"]

    def to_table(self, tab='\t') -> List:
        text = self.text if self.text else ''
        start = self.start if self.start else ''
        stop = self.stop if self.stop else ''

        if tab == '\t':
            return [f"{text}    [{start},{stop}]"]
        if tab == '|':
            return self.to_bsv()


###############################################################################
#
# Polarity
#
###############################################################################
class Polarity(Serializable):
    POSITIVE = 'positive'
    NEGATIVE = 'negative'

    def __init__(self, polarity):
        self.from_json(polarity)

    def from_json(self, polarity):
        if (polarity == Polarity.POSITIVE) or (polarity == True):
            self.text = Polarity.POSITIVE
            self.polarity = True

        elif (polarity == Polarity.NEGATIVE) or (polarity == False):
            self.text = Polarity.NEGATIVE
            self.polarity = False
        else:
            if polarity is None:
                raise Text2phenotypeError(f"polarity was not specified, polarity = {polarity} ")
            else:
                raise Text2phenotypeError(f"unexpected polarity = {polarity} ")

    def is_positive(self):
        return self.polarity == True

    def is_negative(self):
        return self.polarity == False

    def to_json(self):
        return self.text

    def to_table(self, tab='\t') -> List:
        return [f"polarity{tab}{self.text}"]

    def __str__(self):
        return self.is_positive()
