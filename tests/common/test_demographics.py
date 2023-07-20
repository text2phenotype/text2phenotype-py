import unittest

from text2phenotype.common.demographics import Demographics


class TestDemographics(unittest.TestCase):

    EXAMPLE_GOOD = "Right Answer"
    EXAMPLE_BAD = "Wrong Answer"

    def test_demographics_use_preferred_first_name(self):
        """
        Test that Demographics will return the preferred term if one is provided
        in on initialization.
        """
        kwargs = {
            'pat_first': [(self.EXAMPLE_BAD, 0.8), (self.EXAMPLE_GOOD, 0.9)]
        }
        demo = Demographics(**kwargs)

        self.assertEqual(demo.first_name, self.EXAMPLE_GOOD)

    def test_demographics_use_preferred_last_name(self):
        """
        Test that Demographics will return the preferred term if one is provided
        in on initialization.
        """
        kwargs = {
            'pat_last': [(self.EXAMPLE_BAD, 0.8), (self.EXAMPLE_GOOD, 0.9)]
        }
        demo = Demographics(**kwargs)

        self.assertEqual(demo.last_name, self.EXAMPLE_GOOD)

    def test_demographics_use_preferred_dob(self):
        """
        Test that Demographics will return the preferred term if one is provided
        in on initialization.
        """
        kwargs = {
            'dob': [(self.EXAMPLE_BAD, 0.8), (self.EXAMPLE_GOOD, 0.9)]
        }
        demo = Demographics(**kwargs)

        self.assertEqual(demo.date_of_birth, self.EXAMPLE_GOOD)

    def test_demographics_missing_kwargs(self):
        """
        Test that Demographics can handle missing kwargs and sets appropriate
        defaults.
        """
        kwargs = dict()

        demo = Demographics(**kwargs)

        self.assertListEqual(demo.mrn, [])

    def test_demographics_add_entry(self):
        """
        Test that setting expected attributes normally on Demographics works.
        """
        demo = Demographics()

        demo.add_entry("dr_city", self.EXAMPLE_GOOD, score=0.90)

        self.assertListEqual(demo.dr_city, [(self.EXAMPLE_GOOD, 0.9)])
