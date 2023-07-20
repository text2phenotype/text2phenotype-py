import json
import logging
import socket

from datetime import datetime
from typing import Dict

import coloredlogs

from django.utils.functional import cached_property

from text2phenotype.constants.environment import Environment


class JSONFormatter(logging.Formatter):

    TYPE = 'Base'

    def format(self, record: 'logging.LogRecord') -> str:
        json_record = self.prepare_dictionary(record)

        return json.dumps(json_record)

    @cached_property
    def fqdn(self):
        return socket.getfqdn()

    def prepare_dictionary(self, record: 'logging.LogRecord') -> Dict:
        result = dict()
        result['fqdn'] = self.fqdn
        result['timestamp'] = datetime.now().strftime(Environment.LOG_TIMESTAMP_FORMAT.value)
        result['level_name'] = record.levelname
        result['message'] = record.getMessage()
        result['module'] = record.module
        result['function_name'] = record.funcName
        result['application'] = Environment.APPLICATION_NAME.value
        result['type'] = self.TYPE

        return result


class HIPAAFormatter(JSONFormatter):

    TYPE = 'HIPAA'

    def prepare_dictionary(self, record: 'logging.LogRecord') -> Dict:
        hipaa_data = record.hipaa_log_data

        if hipaa_data.module is None or hipaa_data.function_name is None:
            # use default data if it is not completely or correctly overridden
            hipaa_data.module = record.module
            hipaa_data.function_name = record.funcName

        if hipaa_data.message is None:
            hipaa_data.message = record.getMessage()

        new_data = hipaa_data.to_dict()

        result = super().prepare_dictionary(record)
        result.update(new_data)

        return result


class OperationsFormatter(JSONFormatter):

    TYPE = 'Operations'

    def prepare_dictionary(self, record: 'logging.LogRecord') -> Dict:
        result = super().prepare_dictionary(record)
        result['transaction_id'] = record.transaction_id
        result['line_number'] = record.lineno

        if record.exc_info:
            result['exc_info'] = self.formatException(record.exc_info)
        else:
            result['exc_info'] = None

        return result


class CommonFormattersMixin:
    def add_indent(self, text, indent):
        if not isinstance(text, str):
            text = str(text)

        lines = text.splitlines(True)
        spaces = ' ' * indent
        return ''.join(spaces + line for line in lines)

    def formatException(self, exc_info):
        text = super().formatException(exc_info)
        return self.add_indent(text, indent=9)

    def formatStack(self, stack_info):
        text = super().formatStack(stack_info)
        return self.add_indent(text, indent=9)


class DefaultHumanReadableFormatter(CommonFormattersMixin, logging.Formatter):
    HUMAN_READABLE_DEFAULT_FORMAT = '{levelname:>8} {asctime} {funcName} in {module} ({pathname}, line: {lineno})\n{message}\n'

    def __init__(self):
        super().__init__(fmt=self.HUMAN_READABLE_DEFAULT_FORMAT,
                         style='{',
                         datefmt=Environment.LOG_TIMESTAMP_FORMAT.value)

    def format(self, record):
        record.msg = self.add_indent(record.msg, indent=9)
        return super().format(record)


class ColoredHumanReadableFormatter(CommonFormattersMixin, coloredlogs.ColoredFormatter):
    CUSTOM_FIELD_STYLES = {
        'asctime': {'color': 'cyan'},
        'levelname': {'color': 'white'},
        'module': {'color': 'blue'},
        'funcName': {'color': 'magenta'},
        'lineno': {'color': 'yellow'},
        'filename': {'color': 'yellow'},
        'pathname': {'color': 'yellow'},
    }

    def __init__(self):
        field_styles = coloredlogs.DEFAULT_FIELD_STYLES.copy()
        field_styles.update(self.CUSTOM_FIELD_STYLES)

        super().__init__(fmt=DefaultHumanReadableFormatter.HUMAN_READABLE_DEFAULT_FORMAT,
                         style='{',
                         datefmt=Environment.LOG_TIMESTAMP_FORMAT.value,
                         field_styles=field_styles)

    def format(self, record):
        msg = self.add_indent(record.msg, indent=9)
        record.msg = coloredlogs.ansi_wrap(msg, bold=True)

        formatted_text = super().format(record)
        level_style = self.level_styles.get(record.levelname.lower())

        if level_style:
            colored_level = coloredlogs.ansi_wrap(record.levelname, **level_style)
            formatted_text = formatted_text.replace(record.levelname, colored_level, 1)

        return formatted_text

    def formatException(self, exc_info):
        text = super().formatException(exc_info)
        return coloredlogs.ansi_wrap(text, color='red', bold=True)

    def formatStack(self, stack_info):
        text = super().formatStack(stack_info)
        return coloredlogs.ansi_wrap(text, color='red', bold=True)


HumanReadableFormatter = (ColoredHumanReadableFormatter if Environment.COLORED_LOGS.value
                          else DefaultHumanReadableFormatter)


class WorkerFormatter(OperationsFormatter):

    def __init__(self, worker_name, document_id=None, chunk_number=None, job_id=None):
        super().__init__()
        self.worker_name = worker_name
        self.document_id = document_id
        self.chunk_number = chunk_number
        self.job_id = job_id

    def prepare_dictionary(self, record: 'logging.LogRecord') -> Dict:
        result = super().prepare_dictionary(record)
        result['worker_name'] = self.worker_name
        result['document_id'] = self.document_id
        if self.chunk_number:
            result['chunk_number'] = self.chunk_number
        if self.job_id:
            result['job_id'] = self.job_id
        return result
