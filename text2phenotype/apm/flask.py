import logging

from elasticapm.contrib.flask import ElasticAPM
from elasticapm.handlers.logging import LoggingHandler

from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import Environment


def configure_apm(app, apm_service_name: str):
    if Environment.APM_ENABLED.value:
        operations_logger.info(f'Configuring APM agent ({apm_service_name}) -> {Environment.APM_SERVER_URL.value}.')

        app.config['ELASTIC_APM'] = {
            # Set required service name.
            # Allowed characters:
            # a-z, A-Z, 0-9, -, _, and space
            'SERVICE_NAME': apm_service_name,

            # Use if APM Server requires a token
            'SECRET_TOKEN': Environment.APM_SECRET_TOKEN.value,

            # Set custom APM Server URL
            # default: http://localhost:8200)
            'SERVER_URL': Environment.APM_SERVER_URL.value
        }

        apm = ElasticAPM(app)

        # Create a logging handler and attach it.
        apm_handler = LoggingHandler(client=apm.client)
        apm_handler.setLevel(logging.WARN)
        app.logger.addHandler(apm_handler)
