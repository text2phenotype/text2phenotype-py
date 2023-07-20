import unittest
from text2phenotype.common import sftpclient
from unittest.mock import patch


class TestSFTPClient(unittest.TestCase):

    def test_upload(self):
        with patch('paramiko.Transport', autospec=True), patch('paramiko.SFTPClient', autospec=True):
            actual_result = sftpclient.upload({'test_file_A', 'test_file_B', 'test_file_C'})
            self.assertEquals(len(actual_result), 3)
