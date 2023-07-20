import unittest
from text2phenotype.constants.deid import DeidGroupings
from text2phenotype.constants.features import PHILabel


class TestDEIDGroupings(unittest.TestCase):
    def test_safe_harbor(self):
        self.assertEqual(DeidGroupings.SAFE_HARBOR.value, {phi for phi in PHILabel if phi != PHILabel.na})
        self.assertEqual(
            {phi.value.persistent_label for phi in DeidGroupings.SAFE_HARBOR.value},
            {'hospital', 'url', 'idnum', 'username', 'zip', 'country', 'organization', 'device', 'bioid', 'email',
             'city', 'profession', 'doctor', 'patient', 'medicalrecord', 'phone', 'state', 'street', 'fax', 'age',
             'healthplan', 'location_other', 'date'})

    def test_lds_with_dates(self):
        self.assertEqual(
            DeidGroupings.LDS_DATE.value,
            {phi for phi in PHILabel if phi not in {PHILabel.na, PHILabel.date}})
        self.assertEqual(
            {phi.value.persistent_label for phi in DeidGroupings.LDS_DATE.value},
            {'hospital', 'url', 'idnum', 'username', 'zip', 'country', 'organization', 'device', 'bioid', 'email',
             'city', 'profession', 'doctor', 'patient', 'medicalrecord', 'phone', 'state', 'street', 'fax', 'age',
             'healthplan', 'location_other'})

    def test_lds_date_provider(self):
        self.assertEqual(
            DeidGroupings.LDS_DATE_PROVIDER.value,
            {phi for phi in PHILabel if phi not in {PHILabel.na, PHILabel.date, PHILabel.doctor, PHILabel.hospital}})
        self.assertEqual(
            {phi.value.persistent_label for phi in DeidGroupings.LDS_DATE_PROVIDER.value},
            {'url', 'idnum', 'username', 'zip', 'country', 'organization', 'device', 'bioid', 'email',
             'city', 'profession', 'patient', 'medicalrecord', 'phone', 'state', 'street', 'fax', 'age',
             'healthplan', 'location_other'})