import logging
import sys

from text2phenotype.common.log_data import (
    ExtraKeys,
    HIPAALogData,
)
from text2phenotype.common.log_formatters import (
    HIPAAFormatter,
    HumanReadableFormatter,
    OperationsFormatter,
)
from text2phenotype.constants.environment import Environment


# Define Adapter classes
class OperationsAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        tid = kwargs.pop("tid", None)
        extra = kwargs.setdefault("extra", {})
        extra.update({ExtraKeys.TRANSACTION_ID.value: tid})
        return msg, kwargs


class HIPAAAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        hipaa_data = kwargs.pop('hipaa_data', HIPAALogData())
        extra = kwargs.setdefault("extra", {})
        extra.update({ExtraKeys.HIPAA_LOG_DATA.value: hipaa_data})
        return msg, kwargs


LOGLEVEL = Environment.LOGLEVEL.value
LOGFILE = Environment.LOGFILE.value
HIPAA_LOGFILE = Environment.HIPAA_LOGFILE.value
HUMAN_READABLE = Environment.HUMAN_READABLE_LOGS.value
LOG_TO_FILE = Environment.LOG_TO_FILE.value


# Define and Configure Loggers
##########################################################################
# Log to console

ops_formatter = HumanReadableFormatter() if HUMAN_READABLE else OperationsFormatter()
ops_console_handler = logging.StreamHandler(sys.stdout)
ops_console_handler.setLevel(LOGLEVEL)
ops_console_handler.setFormatter(ops_formatter)

ops_stderr_handler = logging.StreamHandler(sys.stderr)
ops_stderr_handler.setLevel(LOGLEVEL)
ops_stderr_handler.setFormatter(ops_formatter)

hipaa_formatter = HumanReadableFormatter() if HUMAN_READABLE else HIPAAFormatter()
hipaa_console_handler = logging.StreamHandler(sys.stdout)
hipaa_console_handler.setLevel(LOGLEVEL)
hipaa_console_handler.setFormatter(hipaa_formatter)


##########################################################################
# Log to file
if LOG_TO_FILE:
    ops_file_handler = logging.FileHandler(LOGFILE)
    ops_file_handler.setLevel(LOGLEVEL)
    ops_file_handler.setFormatter(OperationsFormatter())

    hipaa_file_handler = logging.FileHandler(HIPAA_LOGFILE)
    hipaa_file_handler.setLevel(LOGLEVEL)
    hipaa_file_handler.setFormatter(HIPAAFormatter())


##########################################################################
# Log for operations debugging

# operations_logger = OperationsLogger('operations')
_operations_logger = logging.getLogger('operations')
_operations_logger.setLevel(LOGLEVEL)
_operations_logger.addHandler(ops_console_handler)

if LOG_TO_FILE:
    _operations_logger.addHandler(ops_file_handler)

operations_logger = OperationsAdapter(_operations_logger, {})


##########################################################################
# Log for unhandled exceptions

_exceptions_logger = logging.getLogger('errors')
_exceptions_logger.setLevel(LOGLEVEL)
_exceptions_logger.addHandler(ops_stderr_handler)

if LOG_TO_FILE:
    _exceptions_logger.addHandler(ops_file_handler)

exceptions_logger = OperationsAdapter(_exceptions_logger, {})


def exception_hook(exc_type, exc_info, exc_traceback):
    """Unhandled exceptions will be logged using operations_logger format"""

    exceptions_logger.exception('An unhandled exception occurred',
                                exc_info=exc_info)


# https://docs.python.org/3/library/sys.html#sys.excepthook
sys.excepthook = exception_hook


##########################################################################
# Log for HIPAA auditing

# hipaa_logger = HIPAALogger('hipaa')
_hipaa_logger = logging.getLogger('hipaa')
_hipaa_logger.setLevel(LOGLEVEL)
_hipaa_logger.addHandler(hipaa_console_handler)

if LOG_TO_FILE:
    _hipaa_logger.addHandler(hipaa_file_handler)

hipaa_logger = HIPAAAdapter(_hipaa_logger, {})

##########################################################################
# Log for text2phenotype-py library

logger = logging.getLogger('text2phenotype_py')
logger.setLevel(LOGLEVEL)
logger.addHandler(ops_console_handler)

if LOG_TO_FILE:
    logger.addHandler(ops_file_handler)
