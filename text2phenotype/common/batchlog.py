import datetime
from collections import OrderedDict

from text2phenotype.common import common
from text2phenotype.common.log import logger


class BatchLog:
    """
    Collects the timed logging information for a named batch of items and exports the results to JSON
    """

    def __init__(self, name: str='DefaultBatch'):
        """
        :param name: The name of the batch
        """
        self.name = name
        self._start_time = None
        self._stop_time = None
        self.passed = OrderedDict()
        self.failed = OrderedDict()
        self.restart()

    def restart(self) -> None:
        """
        Restarts the logging timer
        """
        self._start_time = datetime.datetime.now()
        self._stop_time = None
        logger.debug('batch %s' % self.name)

    def log_passed(self, item: str, result: str=None) -> None:
        """
        :param item: The item to logged as passed
        :param result: The result, if any, of the operation being logged for the given item
        """
        self.passed[item] = result
        logger.debug(str(item) + ' ' + (str(result) if result else ''))

    def log_failed(self, item: str, error: Exception=None) -> None:
        """
        :param item: The item to logged as failed
        :param error: The error related to the failure
        """
        self.failed[item] = error
        logger.error(str(item) + ' ' + (str(error) if error else ''))

    def elapsed(self) -> int:
        """
        :return: The current elapsed amount of time the batch has been processing
        """
        self._stop_time = datetime.datetime.now()
        return self._stop_time - self._start_time

    def summary(self) -> str:
        """
        :return: The name, elapsed time, and number of successes and failures for the batch
        """
        diff = self.elapsed()
        num_passed = len(self.passed.keys())
        num_failed = len(self.failed.keys())

        text = '[batch %s]\t [elapsed %s] \t [passed %s]\t [failed %s]' % (self.name, str(diff), num_passed, num_failed)

        logger.info(text)

        return text

    def to_file(self, json_file=None) -> None:
        """
        Writes the results of the batch to the provided file path
        :param json_file: Absolute file path for output
        """
        if json_file is None:
            json_file = f'usage.{self._start_time}.json'
            json_file = json_file.replace(' ', '-').replace(':', '.')

        common.write_json(self.__dict__, json_file)
