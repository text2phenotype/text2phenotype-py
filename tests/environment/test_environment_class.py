import os
from unittest import TestCase, mock

from text2phenotype.constants.environment import Environment, EnvironmentVariable


class TestEnvironmentClass(TestCase):
    EXAMPLE_STR = 'Example Value'
    EXAMPLE_STR_LEGACY = 'Example Value from Legacy'
    EXAMPLE_INT = '42'
    EXAMPLE_BOOLS_TRUE = ['on', 'true', '1', 'enabled']
    EXAMPLE_BOOLS_FALSE = ['off', 'false', '0', 'tomato']

    TEST_VAR = Environment.HIPAA_LOGFILE
    TEST_VAR_INT = Environment.RMQ_MAX_RECEIVE_COUNT
    TEST_VAR_BOOL = Environment.LOG_TO_FILE

    def setUp(self) -> None:
        Environment.refresh()

    def tearDown(self) -> None:
        self.TEST_VAR.required = False

    @mock.patch.dict(os.environ, {'NEW_VAR': '8'})
    def test_environment_subclass(self):
        class SubEnviron(Environment):
            HIPAA_LOGFILE = Environment.HIPAA_LOGFILE
            HIPAA_LOGFILE.required = True
            HIPAA_LOGFILE.value = 'temp value'

            NEW_VAR = EnvironmentVariable(name='NEW_VAR', value=7)

        self.assertEqual(SubEnviron.HIPAA_LOGFILE.value, 'temp value')
        self.assertEqual(Environment.HIPAA_LOGFILE.value, 'temp value')

        self.assertTrue(SubEnviron.HIPAA_LOGFILE.required)
        self.assertTrue(Environment.HIPAA_LOGFILE.required)

        self.assertEqual(SubEnviron.NEW_VAR.value, 8)

    @mock.patch.dict(os.environ, {TEST_VAR.name: EXAMPLE_STR})
    def test_environment_loading(self):
        self.assertEqual(self.TEST_VAR.value, self.EXAMPLE_STR)

    @mock.patch.dict(os.environ, {TEST_VAR.legacy_name: EXAMPLE_STR_LEGACY})
    def test_environment_loading_legacy(self):
        self.assertEqual(self.TEST_VAR.value, self.EXAMPLE_STR_LEGACY)

    @mock.patch.dict(os.environ, clear=True)
    def test_environment_loading_missing_reqs(self):
        class SubEnvironment(Environment):
            REQUIRED_VAR = EnvironmentVariable(name='REQUIRED_VAR_WITHOUT_DEFAULT_VALUE',
                                               required=True)

        with self.assertRaises(EnvironmentError):
            SubEnvironment.REQUIRED_VAR.refresh()

        with self.assertRaises(EnvironmentError):
            SubEnvironment.refresh()

    @mock.patch.dict(os.environ, clear=True)
    def test_environment_loading_no_legacy(self):
        self.TEST_VAR.required = False
        self.TEST_VAR.legacy_name = None
        self.TEST_VAR.value = self.EXAMPLE_STR

        self.assertEqual(self.TEST_VAR.value, self.EXAMPLE_STR)

    @mock.patch.dict(os.environ, {TEST_VAR_INT.name: EXAMPLE_INT})
    def test_environment_loading_default_int(self):
        self.assertTrue(isinstance(self.TEST_VAR_INT.value, int))
        self.assertEqual(self.TEST_VAR_INT.value, int(self.EXAMPLE_INT))

    @mock.patch.dict(os.environ, {TEST_VAR_INT.name: EXAMPLE_STR})
    def test_environment_loading_default_int_invalid(self):
        with self.assertRaises(ValueError):
            self.TEST_VAR_INT.value

    @mock.patch.dict(os.environ, clear=True)
    def test_environment_loading_default_bool(self):
        for val in self.EXAMPLE_BOOLS_TRUE:
            os.environ[self.TEST_VAR_BOOL.name] = val
            self.TEST_VAR_BOOL.refresh()
            self.assertTrue(self.TEST_VAR_BOOL.value)

        for val in self.EXAMPLE_BOOLS_FALSE:
            os.environ[self.TEST_VAR_BOOL.name] = val
            self.TEST_VAR_BOOL.refresh()
            self.assertFalse(self.TEST_VAR_BOOL.value)
