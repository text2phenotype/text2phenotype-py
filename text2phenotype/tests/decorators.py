import os
import unittest


SKIP_VARIABLE_NAME = 'SKIP_SLOW_TESTS_ON_DOCKER_BUILD'


skip_on_docker_build = unittest.skipIf(
    condition=os.getenv(SKIP_VARIABLE_NAME, False),
    reason=f'The "{SKIP_VARIABLE_NAME}" environment variable is defined. '
           f'This test is not required during the build of Docker image.'
)
