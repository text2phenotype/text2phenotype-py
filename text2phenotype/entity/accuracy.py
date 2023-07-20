from text2phenotype.entity.attributes import Serializable


class Accuracy(Serializable):

    def __init__(self):
        """
        The number of instances in each prediction: TP, FP, FN, TN.
        If object is the type List, then the direct List is used.
        """
        self.truepos = None
        self.falsepos = None
        self.falseneg = None
        self.trueneg = None

    def compare_sets(self, expected: set, actual: set):
        expected = set(expected)
        actual = set(actual)

        self.truepos = expected.intersection(actual)  # True  Positive
        self.falseneg = expected.difference(actual)  # False Positive
        self.falsepos = actual.difference(expected)  # False Negative
        self.trueneg = set()

        return self

    def num_instances(self) -> int:
        """
        :return: TP + FP + FN + TN
        """
        return self.number(self.truepos) + self.number(self.falsepos) + self.number(self.falseneg) + self.number(
            self.trueneg)

    def recall(self) -> float:
        """
        True Positive Rate
        TPR = TP / (TP + FN)
        https://en.wikipedia.org/wiki/Sensitivity_and_specificity
        """
        TP = float(self.number(self.truepos))
        FN = float(self.number(self.falseneg))

        if TP == float(0):
            return 0

        return TP / (TP + FN)

    def precision(self) -> float:
        """
        Positive Predictive Value
        PPV = TP / ( TP + FP )
        https://en.wikipedia.org/wiki/Sensitivity_and_specificity
        """
        TP = float(self.number(self.truepos))
        FP = float(self.number(self.falsepos))

        if TP == float(0):
            return 0

        return TP / (TP + FP)

    def number(self, source) -> int:
        """
        :param source: either integer or list of elements
        :return: int number defined by source
        """
        if isinstance(source, list):
            return len(source)

        if isinstance(source, set):
            return len(source)

        if source is None:
            return 0

        return int(source)

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return f"""
        #########################
        TP = {self.truepos}
        FP = {self.falsepos}
        FN = {self.falseneg}
        TN = {self.trueneg}
        #########################
        recall    = {self.recall()}
        #########################
        precision = {self.precision()}
        #########################
        """

    def to_json(self):
        return {'TP': self.truepos,
                'FP': self.falsepos,
                'FN': self.falseneg,
                'TN': self.trueneg,
                'recall': self.recall(),
                'precision': self.precision()}
