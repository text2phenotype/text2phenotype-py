import unittest

from text2phenotype.apiclients.biomed import (aggregate_redact, aggregate_summary, aggregate_phi_tokens, aggregate_demographics)
from text2phenotype.common.version_info import VersionInfo


class TestRedact(unittest.TestCase):
    def test_None_aggregate(self):
        response = "Some redacted ****."

        self.assertEqual(response, aggregate_redact(None, response, "", 1))

    def test_None_response(self):
        aggregate = "Some previously *** redacted ****."

        self.assertEqual(aggregate, aggregate_redact(aggregate, None, "", 1))

    def test_first_response(self):
        response = "Some redacted ****."

        self.assertEqual(response, aggregate_redact("", response, "", 1))

    def test_multiple_responses(self):
        responses = ["Some text.", "Patient name: **** *****", "Some more text"]
        aggregate = ""

        for response in responses:
            aggregate = aggregate_redact(aggregate, response, "", 1)

        self.assertEqual(''.join(responses), aggregate)


class TestSummary(unittest.TestCase):
    __TEXT = """Patient: Mike B.
Pt taking Aspirin 500 mg/day."""

    def test_None_aggregate(self):
        response = {'aspect': [{'text': 'Mike', 'range': [9, 13]}]}

        self.assertDictEqual(response, aggregate_summary(None, response, self.__TEXT, 0))

    def test_empty_response(self):
        aggregate = {'aspect': [{'text': 'Mike', 'range': [9, 13]}]}

        self.assertDictEqual(aggregate, aggregate_summary(aggregate, {}, self.__TEXT, 0))

    def test_first_response(self):
        response = {'aspect': [{'text': 'Mike', 'range': [9, 13]}]}

        self.assertDictEqual(response, aggregate_summary({}, response, self.__TEXT, 0))

    def test_multiple_responses(self):
        aggregate = {'Demographics': [{'text': 'Mike', 'range': [9, 13]}]}
        response = {'Demographics': [{'text': 'B.', 'range': [1, 3]}],
                    'Medication': [{'text': 'Aspirin', 'range': [14, 21],
                                    'medStrengthNum': ['500', 22, 25], 'medStrengthUnit': ['mg', 26, 28]}]
                    }

        aggregate = aggregate_summary(aggregate, response, self.__TEXT, 13)

        expected = {'Demographics': [{'text': 'Mike', 'range': [9, 13]}, {'text': 'B.', 'range': [14, 16]}],
                    'Medication': [{'text': 'Aspirin', 'range': [27, 34],
                                    'medStrengthNum': ['500', 35, 38], 'medStrengthUnit': ['mg', 39, 41]}]
                    }

        self.assertDictEqual(expected, aggregate)


class TestPHI(unittest.TestCase):
    __TEXT = """Patient: Mike B.
Pt taking Aspirin 500 mg/day, 
and is alive and well in Longmont, CO."""

    def test_empty_response(self):
        aggregate = [{'text': 'Mike', 'range': [9, 13]}, {'text': 'B.', 'range': [14, 16]}]

        self.assertListEqual(aggregate, aggregate_phi_tokens(aggregate, [], self.__TEXT, 1))

    def test_first_response(self):
        response = [{'text': 'Mike', 'range': [9, 13]}, {'text': 'B.', 'range': [14, 16]}]

        self.assertListEqual(response, aggregate_phi_tokens([], response, self.__TEXT, 0))

    def test_aggregate_to_existing(self):
        aggregate = [{'text': 'Mike', 'range': [9, 13]}, {'text': 'B.', 'range': [14, 16]}]
        response = [{'text': 'Longmont', 'range': [57, 65]}, {'text': 'CO', 'range': [67, 69]}]

        expected = [{'text': 'Mike', 'range': [9, 13]}, {'text': 'B.', 'range': [14, 16]},
                    {'text': 'Longmont', 'range': [73, 81]}, {'text': 'CO', 'range': [83, 85]}]

        self.assertListEqual(expected, aggregate_phi_tokens(aggregate, response, self.__TEXT, 16))


class TestDemographics(unittest.TestCase):
    def test_empty_response(self):
        aggregate = {'demographics':{'dob': [['08/01/45', 0.999]]},
                     'VersionInfo': {'nam': '0.00'}}

        self.assertDictEqual(aggregate, aggregate_demographics(aggregate, {}, "", 1))

    def test_first_response(self):
        response = {'demographics': {'dob': [['08/01/45', 0.999]]},
                     'VersionInfo': VersionInfo(product_id='biomed', product_version='0.00').to_dict()}

        self.assertDictEqual(response, aggregate_demographics({}, response, "", 1))

    def test_aggregate_to_existing(self):
        aggregate = {'demographics':{'dob': [['08/01/45', 0.999]],
                                     'pat_first': [['Mike', .987]]},
                     'VersionInfo':  VersionInfo(product_id='biomed', product_version='0.00').to_dict()}
        response = {'demographics': {'dob': [['08/01/45', 1.0]],
                                     'pat_first': [['Michael', .902]],
                                     'pat_city': [['Longmont', .963]]},
                     'VersionInfo':  VersionInfo(product_id='biomed', product_version='0.00').to_dict()}

        expected = {'demographics': {'dob': [['08/01/45', 0.999], ['08/01/45', 1.0]],
                    'pat_first': [['Mike', .987], ['Michael', .902]],
                    'pat_city': [['Longmont', .963]]
                    },
                     'VersionInfo':  VersionInfo(product_id='biomed', product_version='0.00').to_dict()}

        self.assertDictEqual(expected, aggregate_demographics(aggregate, response, "", 1))


if __name__ == '__main__':
    unittest.main()
