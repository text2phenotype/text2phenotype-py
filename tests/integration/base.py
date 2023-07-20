import unittest

from .environment import TestsEnvironment


class IntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not TestsEnvironment.INTEGRATION_TESTS_ENABLED.value:
            raise unittest.SkipTest(
                f'Integration tests are disabled in this environment. '
                f'{TestsEnvironment.INTEGRATION_TESTS_ENABLED.name} = '
                f'{TestsEnvironment.INTEGRATION_TESTS_ENABLED.value}')
