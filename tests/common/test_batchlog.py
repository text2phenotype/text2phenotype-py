import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from text2phenotype.common.batchlog import BatchLog


class TestBatchLog(unittest.TestCase):

    test_batch_name = "Unit Tests"

    def test_restart(self):
        now = datetime.now()
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now = MagicMock(return_value=now)
            test_target = BatchLog(self.test_batch_name)
            test_target.restart()
            self.assertEquals(now, test_target._start_time)
            self.assertEquals(None, test_target._stop_time)

    def test_log_passed(self):
        key = "Passed Item"
        value = "Passed"
        test_target = BatchLog(self.test_batch_name)
        test_target.log_passed(key, value)
        self.assertDictEqual({key: value}, test_target.passed)

    def test_log_failed(self):
        key = "Failed Item"
        value = "Failed"
        test_target = BatchLog(self.test_batch_name)
        test_target.log_failed(key, value)
        self.assertDictEqual({key: value}, test_target.failed)

    def test_elapsed(self):
        now = datetime.now()
        later = now + timedelta(days=1)
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now = MagicMock()
            mock_datetime.now.side_effect = (now, later)
            test_target = BatchLog(self.test_batch_name)
            self.assertEquals(later - now, test_target.elapsed())

    def test_summary(self):
        now = datetime.now()
        later = now + timedelta(days=1)
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now = MagicMock()
            mock_datetime.now.side_effect = (now, later)
            test_target = BatchLog(self.test_batch_name)
            test_target.log_passed("Passed Item", "Passed")
            test_target.log_failed("Failed Item", "Failed")
            expected =\
                '[batch %s]\t [elapsed %s] \t [passed %s]\t [failed %s]' % (self.test_batch_name, later - now, 1, 1)
            self.assertEquals(expected, test_target.summary())
