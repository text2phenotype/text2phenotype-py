from pathlib import Path

from text2phenotype.constants.environment import (
    Environment,
    EnvironmentVariable,
)


class TestsEnvironment(Environment):
    config_file_dir = Path(__file__).parent

    INTEGRATION_TESTS_ENABLED = EnvironmentVariable('MDL_TEST_INTEGRATION_TESTS_ENABLED',
                                                    value=False, expected_type=bool)

    DEFAULT_WAITING_TIMEOUT = EnvironmentVariable('MDL_TEST_DEFAULT_WAITING_TIMEOUT', value=120)

    CORPUS_SOURCE_BUCKET = EnvironmentVariable('MDL_TEST_CORPUS_SOURCE_BUCKET', value='')
    CORPUS_SOURCE_DIRECTORY = EnvironmentVariable('MDL_TEST_CORPUS_SOURCE_DIRECTORY', value='')
    CORPUS_DESTINATION_DIRECTORY = EnvironmentVariable('MDL_TEST_CORPUS_DESTINATION_DIRECTORY',
                                                       value='')
