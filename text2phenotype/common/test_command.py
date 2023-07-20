import sys
import unittest

from setuptools.command.test import (
    ScanningLoader,
    test
)


class ExcludeScanningLoader(ScanningLoader):

    def loadTestsFromModule(self, module, pattern=None):
        if 'text2phenotype_auth' in module.__name__:
            # this module is tested in sands. Adding it to native loader ruins process
            return unittest.TestSuite()
        return super().loadTestsFromModule(module, pattern)


class TestCommand(test):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        super().initialize_options()
        self.pytest_args = ""

    def run_tests(self):
        import shlex
        import pytest

        pytest_args = shlex.split(self.pytest_args)
        
        if '--continue-on-collection-errors' not in pytest_args:
            pytest_args.append('--continue-on-collection-errors')

        ret = pytest.main(pytest_args)
        sys.exit(ret)
