import json
import logging
import os
import traceback
import yaml

from typing import Optional

from text2phenotype.constants.common import FileExtensions


# We need to use a temp logger here so that our main loggers don't get imported
# before the relevant environment variables are set (LOGLEVEL, HUMAN_READABLE_LOGS, etc.)
temp_logger = logging.getLogger()  # TODO: Use JSON-format logger here


def load_env(config_file: Optional[str] = None, **kwargs) -> None:
    if kwargs:
        call_trace = traceback.format_stack(limit=2)[-2]
        temp_logger.warning(
            f'*** DEPRECATION WARNING ***\n'
            f'Unxpected {list(kwargs.keys())} arguments were passed to the "load_env" method.\n'
            f'{call_trace}')

    if not config_file:
        return

    if config_file and not os.path.exists(config_file):
        temp_logger.warning(f'Proposed config file `{config_file}` does not'
                            f' exist! No local configuration was loaded.')
        return

    temp_logger.info(f'Loading configuration into environment from {config_file}...')

    _, ext = os.path.splitext(config_file)
    ext = ext.lower().strip('.')

    if ext in [FileExtensions.YAML.value, FileExtensions.YML.value]:
        config_dict = yaml.safe_load(open(config_file, 'r'))
    elif ext == FileExtensions.JSON.value:
        config_dict = json.load(open(config_file, 'r'))
    else:
        temp_logger.warning(f'File has unknown extension `{ext}`! '
                            f'Only YAML and JSON files accepted.')
        return

    for k, v in config_dict.items():
        if isinstance(v, str):
            os.environ[k] = v
        else:
            # Environment variable values must be strings
            os.environ[k] = json.dumps(v)

    temp_logger.info('...Done loading local config.')


def load_config_file(dir_path: str) -> None:
    """Find supported config file in the directory and load it to env."""

    # Lookup for a suitable config file in the directory
    for ext in [FileExtensions.YAML, FileExtensions.YML, FileExtensions.JSON]:
        file_name = f'config.{ext}'
        config_path = os.path.join(dir_path, file_name)

        if os.path.exists(config_path):
            return load_env(config_path)
