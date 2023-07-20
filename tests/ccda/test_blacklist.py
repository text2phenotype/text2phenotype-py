import unittest
from text2phenotype.ccda import blacklist
from text2phenotype.ccda.vocab import Vocab


class TestBlacklist(unittest.TestCase):
    def test__contains(self):
        # Contrived source of codes
        source = {
            Vocab.SNOMED_CT: [
                'valid_code'
            ]
        }

        # Valid vocab and valid code
        self.assertTrue(blacklist._contains(Vocab.SNOMED_CT, 'valid_code', source))

        # Valid vocab (but as string which is a nono) and valid code
        # Vocabs should be referenced with their enum type, not a string!
        self.assertFalse(blacklist._contains('2.16.840.1.113883.6.96', 'valid_code', source))

        # Valid vocab but invalid code
        self.assertFalse(blacklist._contains(Vocab.SNOMED_CT, 'invalid_code', source))

        # Invalid vocab and invalid code
        self.assertFalse(blacklist._contains(Vocab.CPT, 'invalid_code', source))

    def test_skip_code(self):
        # Code 29308 or "Diagnosis" is blacklisted, so skip it
        self.assertTrue(blacklist.skip_code(Vocab.SNOMED_CT, '29308'))

        # Code 99999999 is made-up, so it can't be found in the blacklisted code, so DON'T skip it
        self.assertFalse(blacklist.skip_code(Vocab.SNOMED_CT, '99999999'))

        # Valid vocab (but as string which is not correct),
        # meaning we won't match a blacklisted code, so DON'T skip it
        self.assertFalse(blacklist.skip_code('2.16.840.1.113883.6.96', '29308'))

    def test_skip_section(self):
        # Section "UNKNOWN" is blacklisted, so skip it
        self.assertTrue(blacklist.skip_section('UNKNOWN'))

        # Section 99999999 is made-up, so it can't be found in the blacklisted sections,
        # so DON'T skip it
        self.assertFalse(blacklist.skip_section('99999999'))
