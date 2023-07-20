import unittest
from text2phenotype.ccda import empi


class TestEmpi(unittest.TestCase):

    @unittest.skip("Review and refactor required")
    def test_missing_data(self):
        dem = empi.get_demographics(mock_xml_empty)

        self.assertEqual('', dem.id)
        self.assertEqual('', dem.ssn)
        self.assertIsNone(dem.dob)
        self.assertIsNone(dem.fname)
        self.assertIsNone(dem.lname)
        self.assertIsNone(dem.ph_home)
        self.assertIsNone(dem.addr1)
        self.assertIsNone(dem.city)
        self.assertIsNone(dem.state)
        self.assertIsNone(dem.zip5)
        self.assertEqual('', dem.sex)
        self.assertTrue(len(dem.race) == 0)

    def test_get_patient_id(self):
        self.assertEqual('111-00-1234', empi.get_patient_id(mock_xml_multiple_ids, '111-00-1234'))

    @unittest.skip("Review and refactor required")
    # FutureWarning generated in empi.py:100
    def test_get_address(self):
        self.assertEqual('123 MONTGOMERY BLVD NE', empi.get_address(mock_xml).get('addr1'))
        self.assertEqual('Las Cruces', empi.get_address(mock_xml).get('city'))
        self.assertEqual('NM', empi.get_address(mock_xml).get('state'))
        self.assertEqual('88007', empi.get_address(mock_xml).get('zip5'))

    @unittest.skip("Review and refactor required")
    # FutureWarning generated in empi.py:85
    def test_get_telecom(self):
        self.assertEqual('tel:(575) 123-4567', empi.get_telecom(mock_xml))

    @unittest.skip("Review and refactor required")
    # name not returned by Demographics object
    def test_get_demographics(self):
        """
        SANDS-222 Test for telecom, address and patient id in demographics
        """
        dem = empi.get_demographics(mock_xml)
        self.assertEqual('123456789', dem.id)
        self.assertEqual('111-00-1234', dem.ssn)
        self.assertEqual('1963-01-02', dem.dob)
        self.assertEqual('111-00-1234', dem.ssn)
        self.assertEqual('Ricardo', dem.first_name)
        self.assertEqual('Campos', dem.last_name)
        self.assertEqual('tel:(575) 123-4567', dem.ph_home)
        self.assertEqual('123 MONTGOMERY BLVD NE', dem.addr1)
        self.assertEqual('Las Cruces', dem.city)
        self.assertEqual('NM', dem.state)
        self.assertEqual('88007', dem.zip5)
        self.assertEqual('M', dem.sex)
        self.assertIn('Other Race', dem.race)


mock_xml = """  <recordTarget typeCode="RCT" contextControlCode="OP">
    <patientRole classCode="PAT">

      <!-- @@@ PAT Patient id (123-456-789) and demographics  -->
      <id root="2.16.840.1.113883.1.13.99999.1" extension="123456789" assigningAuthorityName="LCH MRN"/>
      <id extension="111-00-1234" root="2.16.840.1.113883.4.1"/>
      <addr use="WP">
        <streetAddressLine>1 BLAH BLAH BLAH</streetAddressLine>
        <city>Blah</city>
        <state>BL</state>
        <postalCode>00000</postalCode>
        <country>US</country>
      </addr>
      <addr use="HP">
        <streetAddressLine>123 MONTGOMERY BLVD NE</streetAddressLine>
        <city>Las Cruces</city>
        <state>NM</state>
        <postalCode>88007</postalCode>
        <country>US</country>
      </addr>
      <telecom use="HP" value="tel:(575) 123-4567"/>
      <telecom use="WP" value="tel:(101) 010-1010"/>
      <patient classCode="PSN" determinerCode="INSTANCE">
        <name use="L">
          <given>Ricardo</given>
          <family>Campos</family>
        </name>
        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1" codeSystemName="administrativeGender" displayName="Male">
          <originalText>Male</originalText>
        </administrativeGenderCode>
        <birthTime value="19630102"/>
        <raceCode code="2131-1" codeSystem="2.16.840.1.113883.6.238" codeSystemName="Race and Ethnicity - CDC" displayName="Other Race">
          <originalText>Other Race</originalText>
        </raceCode>
        <ethnicGroupCode code="2135-2" codeSystem="2.16.840.1.113883.6.238" codeSystemName="Race and Ethnicity - CDC" displayName="Hispanic or Latino">
          <originalText>Hispanic or Latino</originalText>
        </ethnicGroupCode>
        <languageCommunication>
          <languageCode code="eng"/>
        </languageCommunication>
      </patient>
        </patientRole>
        </recordTarget>
        """

mock_xml_multiple_ids = """  <recordTarget typeCode="RCT" contextControlCode="OP">
        <patientRole classCode="PAT">

          <!-- @@@ PAT Patient id (123-456-789) and demographics  -->
          <id root="2.16.840.1.113883.1.13.99999.1" extension="123456789" assigningAuthorityName="LCH MRN"/>
          <id root="2.16.840.1.113883.1.13.99999.1" extension="111111111" assigningAuthorityName="LCH MRN"/>
          <id root="2.16.840.1.113883.1.13.99999.1" extension="121212121" assigningAuthorityName="LCH MRN"/>
          <id extension="111-00-1234" root="2.16.840.1.113883.4.1"/>
          <addr use="WP">
            <streetAddressLine>1 BLAH BLAH BLAH</streetAddressLine>
            <city>Blah</city>
            <state>BL</state>
            <postalCode>00000</postalCode>
            <country>US</country>
          </addr>
          <addr use="HP">
            <streetAddressLine>123 MONTGOMERY BLVD NE</streetAddressLine>
            <city>Las Cruces</city>
            <state>NM</state>
            <postalCode>88007</postalCode>
            <country>US</country>
          </addr>
          <telecom use="HP" value="tel:(575) 123-4567"/>
          <telecom use="WP" value="tel:(101) 010-1010"/>
          <patient classCode="PSN" determinerCode="INSTANCE">
            <name use="L">
              <given>Ricardo</given>
              <family>Campos</family>
            </name>
            <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1" codeSystemName="administrativeGender" displayName="Male">
              <originalText>Male</originalText>
            </administrativeGenderCode>
            <birthTime value="19630102"/>
            <raceCode code="2131-1" codeSystem="2.16.840.1.113883.6.238" codeSystemName="Race and Ethnicity - CDC" displayName="Other Race">
              <originalText>Other Race</originalText>
            </raceCode>
            <ethnicGroupCode code="2135-2" codeSystem="2.16.840.1.113883.6.238" codeSystemName="Race and Ethnicity - CDC" displayName="Hispanic or Latino">
              <originalText>Hispanic or Latino</originalText>
            </ethnicGroupCode>
            <languageCommunication>
              <languageCode code="eng"/>
            </languageCommunication>
          </patient>
            </patientRole>
            </recordTarget>
            """

mock_xml_empty = """<recordTarget typeCode="RCT" contextControlCode="OP">
    <patientRole classCode="PAT">
      <patient classCode="PSN" determinerCode="INSTANCE">
      </patient>
        </patientRole>
        </recordTarget>
        """