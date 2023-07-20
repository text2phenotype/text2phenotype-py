import logging
import os
import sys
from pathlib import Path
from typing import (
    Any,
    List,
    Optional,
    Set,
)

from text2phenotype.environment.load import load_config_file


# Create temporary logger
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('{levelname:>8} {asctime} {funcName} in {module} ({pathname}, line: {lineno})\n\t {message}',
                                               style='{',
                                               datefmt='%Y-%m-%d %H:%M:%S TZ%z'))

temp_logger = logging.getLogger('environment-sands')
temp_logger.addHandler(console_handler)
temp_logger.setLevel(logging.INFO)


def _find_root_dir(module_name: Optional[str]) -> Optional[Path]:
    """Find project-root by a module"""

    if not module_name:
        return None

    # eg: text2phenotype.constants.environment -> text2phenotype
    root_module_name = module_name.split('.')[0]
    root_module = sys.modules.get(root_module_name)

    # /path/to/project/text2phenotype/ -> /path/to/project
    if root_module:
        return Path(root_module.__path__[0]).parent

    return None


# Specific object to mark EnvironmentVariables as "not loaded".
# We can't use "None" for that because it's also an appropriate value.
class _NotLoadedMarker:
    def __repr__(self):
        return "'<NOT LOADED>'"


class Declarator(type):
    """ Declarator creates an attribute of instance `declared_variables`
    which contains all attributes of the class of EnvironmentVariable type
    """
    def __new__(mcs, name, bases, attrs):
        # Fill APPLICATION_ROOT_DIR attribute
        cls_module_name = attrs.get('__module__')
        root_dir = _find_root_dir(cls_module_name)
        attrs['root_dir'] = root_dir

        # Update runtime environment (os.environ) with values from the config file (config.yaml)
        config_dir = attrs.get('config_file_dir')
        if config_dir is None:
            config_dir = root_dir

        if config_dir:
            load_config_file(config_dir)

        # Fill variables declared in the Environment class
        declared_variables = []
        for key, value in attrs.items():
            if isinstance(value, EnvironmentVariable):
                declared_variables.append(value)
        attrs['declared_variables'] = declared_variables

        return super().__new__(mcs, name, bases, attrs)


class EnvironmentVariable:
    """ The class for defining the variable which will be expected from the environment """

    TRUTHY_STRINGS: Set[str] = {'TRUE', 'ON', '1', 'ENABLED'}
    NOT_LOADED: _NotLoadedMarker = _NotLoadedMarker()

    def __init__(self,
                 name: str,
                 legacy_name: str = None,
                 value: Optional[Any] = None,
                 required: bool = False,
                 expected_type: Optional[type] = None):
        """
        :param name:            The name of the variable to be expected from the environment
        :param legacy_name:     The LEGACY name of the variable to be expected from the environment.
        :param value:           Default value if the variable is not defined in the environment
        :param required:        Bool value. Is the variable required or not?
        :param expected_type:   The type which is expected from the variable
        """

        self.name = name
        self.legacy_name = legacy_name or name
        self.required = required

        self.default_value = value
        self.__value = self.NOT_LOADED

        if not expected_type and value is None:
            self.expected_type = str
        elif not expected_type:
            self.expected_type = type(value)
        else:
            self.expected_type = expected_type

    def __set_name__(self, owner, name):
        self.instance_name = name

    @property
    def value(self) -> Any:
        """Lazzy loading of variable value on demand"""

        if self.__value is self.NOT_LOADED:
            self.load_value()
        return self.__value

    @value.setter
    def value(self, val) -> None:
        self.set_value(val)

    def load_value(self):
        val = os.environ.get(self.name)

        if val is None and self.legacy_name and self.legacy_name in os.environ:
            val = os.environ.get(self.legacy_name)

            temp_logger.warning(
                f'** Deprecation Warning ** `{self.name}` not found in the environment! Using legacy '
                f'`{self.legacy_name}` instead.')

        if val is None:
            val = self.default_value

        self.set_value(val)

    def refresh(self):
        """Mark variable as "not loaded" to force reload the value on demand.

        If variable is "required" value will be loaded immediately.
        """

        self.__value = self.NOT_LOADED

        if self.required:
            self.load_value()

    def set_value(self, val):
        """Validate and cast to type"""

        self.validate(val)
        self.__value = self.clean(val)

    def validate(self, value: Optional[Any]):
        """Check of `required` flag.

        :raise: ValueError If the value is required and does not get from the environment and
                default value if undefined, ValueError will be raised.
        """
        if self.required and value is None:
            raise EnvironmentError(f'{self.name} value is required')

    def clean(self, val: Optional[Any]) -> Any:
        """Conversion to the type that is expected.

        :returns value casted to expected type
        :raise ValueError If the type of value is not conformance with the type which was expected
        """

        if val is None:
            return val

        if not self.expected_type:
            return val

        if isinstance(val, self.expected_type):
            return val

        if issubclass(self.expected_type, bool) and isinstance(val, str):
            return val.upper() in self.TRUTHY_STRINGS

        try:
            return self.expected_type(val)
        except ValueError:
            raise ValueError(f'{self.name} variable expects a value of another type. '
                             f'Expected {self.expected_type}, Received {type(val)}')

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(' \
               f'name={repr(self.name)}, ' \
               f'value={repr(self.__value)}, ' \
               f'required={repr(self.required)}'\
               f')'


class AbstractEnvironment(metaclass=Declarator):
    """Abstract class for parse of predefined environment variables.

    For defining your Environment you should use inheritance from AbstractEnvironment class and
    define your variables as attributes of the class (by instances of EnvironmentVariable) something like that:

    class Environment(AbstractEnvironment):
        EHR_LAUNCH = EnvironmentVariable(name='MDL_SANDS_EHR_LAUNCH', legacy_name='EHR_LAUNCH', expected_type=bool)
        DJANGO_SECRET_KEY = EnvironmentVariable(name='MDL_COMN_DJANGO_SECRET_KEY')
        AUTH_ALLOWED_SSO_PROVIDERS = EnvironmentVariable(name='MDL_SANDS_AUTH_ALLOWED_SSO_PROVIDERS',
                                                         legacy_name='AUTH_ALLOWED_SSO_PROVIDERS', default=[],
                                                         expected_type=list)
    """

    # Path to project root dir
    # Value will be updated automatically on the load of module
    root_dir: Optional[Path] = None

    # If defined - config file will be loaded from this path
    # else from the "root_dir"
    config_file_dir: Optional[Path] = None

    # List of declared Environment Variables
    declared_variables: List['EnvironmentVariable'] = []

    # Set attributes corresponding to expected Environment Variables equal to instances of `EnvironmentVariable`

    def get_temp_logger(level: str = 'INFO'):
        """
        We sometimes need to use a temporary logger so that our main loggers
        don't get imported before the relevant environment variables are set
        (LOGLEVEL, HUMAN_READABLE_LOGS, etc.) because that prevents the
        desired settings from taking effect in Development.
        """
        temp_logger.setLevel(level)
        console_handler.setLevel(level)

        return temp_logger

    @classmethod
    def refresh(cls) -> None:
        """The method force refresh all declared EnvironmentVariables.

        The `declared_variables` attribute must contain the attributes of your Environment class,
        which was parsed by Declarator metaclass.

        :raise EnvironmentError When `EnvironmentVariable` raises `ValueError` exception.
        """
        for var in cls.declared_variables:
            var.refresh()

    @classmethod
    def load(cls, logger: logging.Logger = None) -> None:
        """Deprecated. Use "Environment.refresh()" method instead.

        This "load()" method saved as alias to "refresh()" for backwards compatibility.
        """
        cls.refresh()


class Environment(AbstractEnvironment):
    """
    Class for defining a Text2phenotype Environment in Python so we can avoid polling
    the environment using raw strings.  Can be sub-classed in other contexts
    and the default `value` and `required` settings can be overridden.

    Example sub-class usage with override:
    class SubEnviron(Environment):
        NLP_HOST = Environment.NLP_HOST
        NLP_HOST.required = True
        NLP_HOST.value = 'temp value'

        NEW_VAR = EnvironmentVariable(name='NEW_VAR', value=7)
    """
    # Set attributes corresponding to expected Environment Variables
    # equal to instances of `EnvironmentVariable`

    # Logging
    APPLICATION_NAME = EnvironmentVariable(name='MDL_COMN_APPLICATION_NAME', legacy_name='APPLICATION_NAME', value='Not Set')
    HUMAN_READABLE_LOGS = EnvironmentVariable(name='MDL_COMN_HUMAN_READABLE_LOGS', legacy_name='HUMAN_READABLE_LOGS', value=False)
    LOGLEVEL = EnvironmentVariable(name='MDL_COMN_LOGLEVEL', legacy_name='LOGLEVEL', value='INFO')
    LOG_TIMESTAMP_FORMAT = EnvironmentVariable(name='MDL_COMN_LOG_TIMESTAMP_FORMAT', legacy_name='LOG_TIMESTAMP_FORMAT', value='%Y-%m-%d %H:%M:%S TZ%z')

    # COLORED_LOGS has effect only if HUMMAN_READABLE_LOGS flag is True
    COLORED_LOGS = EnvironmentVariable(name='MDL_COMN_COLORED_LOGS', expected_type=bool, value=False)

    LOG_TO_FILE = EnvironmentVariable(name='MDL_COMN_LOG_TO_FILE', legacy_name='LOG_TO_FILE', value=True)
    LOGFILE = EnvironmentVariable(name='MDL_COMN_LOGFILE', legacy_name='LOGFILE', value='text2phenotype.log')
    HIPAA_LOGFILE = EnvironmentVariable(name='MDL_COMN_HIPAA_LOGFILE', legacy_name='HIPAA_LOGFILE', value='text2phenotype_hipaa.log')

    # text2phenotype Samples
    text2phenotype_SAMPLES_PATH = EnvironmentVariable(name='MDL_COMN_text2phenotype_SAMPLES_PATH', legacy_name='text2phenotype_SAMPLES_PATH')

    # Services
    DEFAULT_QUEUE_SERVICE = EnvironmentVariable(name='MDL_COMN_DEFAULT_QUEUE_SERVICE', legacy_name='DEFAULT_QUEUE_SERVICE', value='SQS')
    DEFAULT_STORAGE_SERVICE = EnvironmentVariable(name='MDL_COMN_DEFAULT_STORAGE_SERVICE', legacy_name='DEFAULT_STORAGE_SERVICE', value='S3')
    STORAGE_CONTAINER_NAME = EnvironmentVariable(name='MDL_COMN_STORAGE_CONTAINER_NAME', legacy_name='STORAGE_CONTAINER_NAME')
    STORAGE_BASE_URL = EnvironmentVariable(name='MDL_COMN_STORAGE_BASE_URL', legacy_name='STORAGE_BASE_URL')

    # AWS
    AWS_ACCESS_ID = EnvironmentVariable(name='MDL_COMN_AWS_ACCESS_ID', legacy_name='AWS_ACCESS_ID')
    AWS_ACCESS_KEY = EnvironmentVariable(name='MDL_COMN_AWS_ACCESS_KEY', legacy_name='AWS_ACCESS_KEY')
    AWS_ENDPOINT_S3 = EnvironmentVariable(name='MDL_COMN_AWS_ENDPOINT_S3', legacy_name='AWS_ENDPOINT_S3')
    AWS_REGION_NAME = EnvironmentVariable(name='MDL_COMN_AWS_REGION_NAME', legacy_name='AWS_REGION_NAME', value='us-west-2')
    AWS_ENDPOINT_URL = EnvironmentVariable(name='MDL_COMN_AWS_ENDPOINT_URL', expected_type=str, value=None)

    # Azure
    AZURE_OCR_ENDPOINT = EnvironmentVariable(name='MDL_TASK_OCR_AZURE_ENDPOINT', legacy_name='AZURE_ENDPOINT')
    AZURE_OCR_SUBSCRIPTION_KEY = EnvironmentVariable(name='MDL_TASK_OCR_AZURE_SUBSCRIPTION_KEY', legacy_name='AZURE_SUBSCRIPTION_KEY')
    AZURE_MAX_CONCURRENT_REQUESTS = EnvironmentVariable(name='MDL_TASK_OCR_AZURE_MAX_CONCURRENT_REQUESTS', value=10)
    AZURE_RESULT_WAITING_TIMEOUT = EnvironmentVariable(name='MDL_TASK_OCR_AZURE_RESULT_WAITING_TIMEOUT', value=60)

    # RabbitMQ
    RMQ_HOST = EnvironmentVariable(name='MDL_COMN_RMQ_HOST', legacy_name='RMQ_HOST')
    RMQ_PORT = EnvironmentVariable(name='MDL_COMN_RMQ_PORT', legacy_name='RMQ_PORT')
    RMQ_USERNAME = EnvironmentVariable(name='MDL_COMN_RMQ_USERNAME', legacy_name='RMQ_USERNAME')
    RMQ_PASSWORD = EnvironmentVariable(name='MDL_COMN_RMQ_PASSWORD', legacy_name='RMQ_PASSWORD')
    RMQ_MAX_RECEIVE_COUNT = EnvironmentVariable(name='MDL_COMN_RMQ_MAX_RECEIVE_COUNT', legacy_name='RMQ_MAX_RECEIVE_COUNT', value=0)
    RMQ_DEFAULT_EXCHANGE = EnvironmentVariable(name='MDL_COMN_RMQ_DEFAULT_EXCHANGE', legacy_name='RMQ_DEFAULT_EXCHANGE', value='text2phenotype-default-exchange')
    RMQ_DEFAULT_EXCHANGE_TYPE = EnvironmentVariable(name='MDL_COMN_RMQ_DEFAULT_EXCHANGE_TYPE', value='x-delayed-message')
    RMQ_HEARTBEAT = EnvironmentVariable(name='MDL_COMN_RMQ_HEARTBEAT', value=60)
    RMQ_CONNECTION_ATTEMPTS = EnvironmentVariable(name='MDL_COMN_RMQ_CONNECTION_ATTEMPTS', value=3)
    RMQ_CONNECTION_RETRY_DELAY = EnvironmentVariable(name='MDL_COMN_RMQ_CONNECTION_RETRY_DELAY', value=2)  # seconds

    # KubeMQ
    KUBEMQ_HOST = EnvironmentVariable(name='MDL_COMN_KUBEMQ_HOST')
    KUBEMQ_PORT = EnvironmentVariable(name='MDL_COMN_KUBEMQ_PORT')
    KUBEMQ_MAX_RECEIVE_COUNT = EnvironmentVariable(name='MDL_COMN_KUBEMQ_MAX_RECEIVE_COUNT', value=3)
    KUBEMQ_MESSAGE_VISIBILITY_SECONDS = EnvironmentVariable(name='MDL_COMN_KUBEMQ_MESSAGE_VISIBILITY_SECONDS', value=30)  # 30 seconds
    KUBEMQ_MESSAGE_EXPIRATION_SECONDS = EnvironmentVariable(name='MDL_COMN_KUBEMQ_MESSAGE_EXPIRATION_SECONDS', value=43200)  # 12 hours

    # Addresses
    ADDRESS_HOST = EnvironmentVariable(name='MDL_COMN_ADDRESS_HOST', legacy_name='ADDRESS_HOST')

    # Biomed
    BIOMED_API_BASE = EnvironmentVariable(name='MDL_COMN_BIOMED_API_BASE', legacy_name='BIOMED_API_BASE', value='http://0.0.0.0:8080')
    BIOMED_MODELS = EnvironmentVariable(name='MDL_COMN_BIOMED_MODELS', legacy_name='BIOMED_MODELS')
    BIOMED_MAX_DOC_WORD_COUNT = EnvironmentVariable(name="MDL_COMN_BIOMED_MAX_DOC_WORD_COUNT", value=10000)

    # Biomed Models Metadata Service
    METADATA_SERVICE_API_BASE = EnvironmentVariable(name="MDL_COMN_METADATA_SERVICE_API_BASE", value='http://0.0.0.0:8080')

    # Intake
    INTAKE_URL = EnvironmentVariable(name='MDL_COMN_INTAKE_URL', legacy_name='INTAKE_URL', value='http://0.0.0.0:5000')

    # DISCHARGE
    DISCHARGE_URL = EnvironmentVariable(name='MDL_COMN_DISCHARGE_URL', value='http://0.0.0.0:5001')

    # APM
    APM_ENABLED = EnvironmentVariable(name='MDL_COMN_APM_ENABLED', legacy_name='APM_ENABLED', value=False)
    APM_SERVER_URL = EnvironmentVariable(name='MDL_COMN_APM_SERVER_URL', legacy_name='APM_SERVER_URL', value='http://localhost:8200')
    APM_SECRET_TOKEN = EnvironmentVariable(name='MDL_COMN_APM_SECRET_TOKEN', legacy_name='APM_SECRET_TOKEN')

    # NeuroNER
    NEURONER_API_BASE = EnvironmentVariable(name='MDL_COMN_NEURONER_API_BASE', legacy_name='NEURONER_HOST', value='https://0.0.0.0:8082')

    # MIPS
    MIPS_API_BASE = EnvironmentVariable(name='MDL_COMN_MIPS_API_BASE', value='http://0.0.0.0:8002')

    # SANDS
    SANDS_API_BASE = EnvironmentVariable(name='MDL_COMN_SANDS_API_BASE', value='http://0.0.0.0:8001')

    # text2phenotype API
    TEXT2PHENOTYPE_API_BASE = EnvironmentVariable(name='MDL_COMN_TEXT2PHENOTYPE_API_BASE',
                                         legacy_name='TEXT2PHENOTYPE_API_BASE',
                                         value='http://0.0.0.0:8082')

    TEXT2PHENOTYPE_API_SECRET_KEY = EnvironmentVariable(name='MDL_COMN_TEXT2PHENOTYPE_API_SECRET_KEY',
                                               legacy_name='TEXT2PHENOTYPE_SECRET_KEY',
                                               value='')
    # Tasks Framework
    WORKER_MEMORY_LIMIT = EnvironmentVariable(name='MDL_COMN_CONTAINER_MEMORY_LIMIT_IN_BYTES', expected_type=int, value=None)
    MEMORY_WATCHER_ENABLED = EnvironmentVariable(name='MDL_COMN_MEMORY_WATCHER_ENABLED', expected_type=bool, value=False)

    INTAKE_QUEUE = EnvironmentVariable(name='MDL_COMN_INTAKE_SINGLE_DOCUMENT_QUEUE', value='document-intake-single')
    BULK_INTAKE_QUEUE = EnvironmentVariable(name='MDL_COMN_INTAKE_BULK_DOCUMENT_QUEUE', value='document-intake-bulk')

    SEQUENCER_QUEUE = EnvironmentVariable(name='MDL_COMN_SEQUENCER_TASK_QUEUE', value='task-sequencer')
    DISCHARGE_QUEUE = EnvironmentVariable(name='MDL_COMN_DISCHARGE_TASK_QUEUE', value='task-discharge')

    PURGE_QUEUE = EnvironmentVariable(name='MDL_COMN_PURGE_QUEUE', value='task-purge')

    # Task queue name for workers
    APP_REPROCESS_TASK_QUEUE = EnvironmentVariable(name='MDL_COMN_APP_REPROCESS_TASK_QUEUE', value='task-app-reprocess')
    APP_INGEST_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_APP_INGEST_TASK_QUEUE', value='task-app-ingest')
    APP_PURGE_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_APP_PURGE_TASK_QUEUE', value='task-app-purge')
    OCR_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_OCR_TASK_QUEUE', value='task-ocr')
    OCR_PROCESS_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_OCR_PROCESS_TASK_QUEUE', value='task-ocr-process')
    OCR_REASSEMBLE_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_OCR_REASSEMBLE_TASK_QUEUE', value='task-ocr-reassemble')

    FDL_TASK_QUEUE = EnvironmentVariable(name='MDL_COMN_FDL_TASK_QUEUE', value='task-fdl')
    ANNOTATE_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_ANNOTATE_TASK_QUEUE', value='task-annotate')
    VECTORIZE_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_VECTORIZE_TASK_QUEUE', value='task-vectorize')
    TRAIN_TEST_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_TRAIN_TEST_TASK_QUEUE', value='task-train-test')
    LABEL_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_LABEL_TASK_QUEUE', value='task-label')
    DISASSEMBLE_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_DISASSEMBLE_TASK_QUEUE', value='task-disassemble')
    REASSEMBLE_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_REASSEMBLE_TASK_QUEUE', value='task-reassemble')
    DEDUPLICATOR_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_DEDUP_TASK_QUEUE', value='task-deduplicator')

    # biomed summary (post-reasembler queues)
    SUMMARY_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_SUMMARY_TASK_QUEUE', value='task-summary')
    DEID_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_DEID_QUEUE', value='task-deid')
    PDF_EMBEDDER_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_PDF_EMBED_QUEUE', value='task-pdf-embedder')
    ICD10_DIAGNOSIS_QUEUE = EnvironmentVariable(name='MDL_COMN_ICD10_DIAGNOSIS_QUEUE', value='model-icd10-diagnosis')

    # single model queues
    PHI_TOKEN_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_PHI_QUEUE', value='model-phi')
    DRUG_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_DRUG_QUEUE', value='model-drug')
    LAB_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_LAB_QUEUE', value='model-lab')
    DISEASE_SIGN_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_DISEASE_SIGN_QUEUE', value='model-disease-sign')
    FAMILY_HISTORY_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_FAMILY_HISTORY_QUEUE', value='model-family-history')
    COVID_LAB_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_COVID_LAB_QUEUE', value='model-covid-lab')
    DEVICE_PROCEDURE_TASKS_QUEUE = EnvironmentVariable(
        name='MDL_COMN_DEVICE_PROCEDURE_QUEUE', value='model-device-procedure')
    IMAGING_FINDING_TASKS_QUEUE = EnvironmentVariable( name='MDL_COMN_IMAGE_FINDING_QUEUE', value='model-image-finding')
    SMOKING_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_SMOKING_QUEUE', value='model-smoking')
    VITAL_SIGN_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_VITAL_QUEUE', value='model-vital')
    DOC_TYPE_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_DOC_TYPE_QUEUE', value='model-doctype')
    DOS_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_DOS_QUEUE', value='model-date-of-service')
    DEMOGRAPHICS_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_DEMOGRAPHIC_QUEUE', value='model-demographic')
    SDOH_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_SDOH_QUEUE', value='model-sdoh')

    ONCOLOGY_ONLY_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_ONCOLOGY_QUEUE', value='model-oncology')
    GENETICS_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_GENETICS_QUEUE', value='model-genetics')
    BLADDER_RISK_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_BLADDER_RISK_QUEUE', value='model-bladder-risk')
    BLADDER_SUMMARY_TASKS_QUEUE = EnvironmentVariable(name='MDL_COMN_SUMMARY_BLADDER_QUEUE', value='summary-bladder')

    FDL_ENABLED = EnvironmentVariable(name='MDL_COMN_FDL_ENABLED', value=False, expected_type=bool)

    REDIS_HOST = EnvironmentVariable(name='MDL_COMN_REDIS_HOST', value='localhost')
    REDIS_PORT = EnvironmentVariable(name='MDL_COMN_REDIS_PORT', value='6379')
    REDIS_DB = EnvironmentVariable(name='MDL_COMN_REDIS_DB', value=0)
    REDIS_HA_MODE = EnvironmentVariable(name='MDL_COMN_REDIS_HA_MODE', value=True)
    REDIS_HA_SENTINEL_PORT = EnvironmentVariable(name='MDL_COMN_REDIS_HA_SENTINEL_PORT', value=26379)
    REDIS_HA_MASTER_NAME = EnvironmentVariable(name='MDL_COMN_REDIS_HA_MASTER_NAME', value='mymaster')
    REDIS_SOCKET_TIMEOUT = EnvironmentVariable(name='MDL_COMN_REDIS_SOCKET_TIMEOUT', value=0.5)
    REDIS_AUTH_REQUIRED = EnvironmentVariable(name='MDL_COMN_REDIS_AUTH_REQUIRED', value=False, expected_type=bool)
    REDIS_AUTH_PASSWORD = EnvironmentVariable(name='MDL_COMN_REDIS_AUTH_PASSWORD')

    OKTA_API_TOKEN = EnvironmentVariable(name='MDL_COMN_OKTA_API_TOKEN')
    OKTA_CUSTOMER_GROUP_ID = EnvironmentVariable(name='MDL_COMN_OKTA_CUSTOMER_GROUP_ID')
    OKTA_OAUTH_PATH = EnvironmentVariable(name='MDL_COMN_OKTA_OAUTH_PATH')
    OKTA_ROLE_PREFIX = EnvironmentVariable(name='MDL_COMN_OKTA_ROLE_PREFIX', value='dev')
    OKTA_TENANT_URL = EnvironmentVariable(name='MDL_COMN_OKTA_TENANT_URL')

    INGEST_COPY_TO_TRAIN = EnvironmentVariable(name='MDL_INGEST_COPY_TO_TRAIN', value=False)
    INGEST_TRAIN_BUCKET = EnvironmentVariable(name='MDL_INGEST_TRAIN_BUCKET', value='')

    DATA_ROOT = EnvironmentVariable(name='MDL_COMN_DATA_ROOT', legacy_name='DATA_ROOT', value='/tmp')
    USE_STORAGE_SERVICE = EnvironmentVariable(name='MDL_COMN_USE_STORAGE_SVC',
                                              legacy_name='USE_STORAGE_SERVICE',
                                              value=True)

    FEAT_API_BASE = EnvironmentVariable(name='MDL_COMN_FEAT_API_BASE',
                                        legacy_name='FEATURE_API_BASE',
                                        value='http://0.0.0.0:8081')

    OCR_PDF_PARALLEL_JOBS = EnvironmentVariable(name='MDL_COMN_OCR_PDF_PARALLEL_JOBS', value=10)
    GVC_MAX_CONCURRENT_REQUESTS = EnvironmentVariable(name='MDL_COMN_OCR_GCV_MAX_REQUESTS', value=10)
    GVC_REQUEST_TIMEOUT = EnvironmentVariable(name='MDL_COMN_OCR_GVC_REQUEST_TIMEOUT', value=300)

    DJANGO_SECRET_KEY = EnvironmentVariable(name='MDL_COMN_DJANGO_SECRET_KEY')
    # All Django apps share a common database, including session storage, so need access to the same Secret Key

    # DB users will be separate by application and grant only permission to the tables that app needs.
    DB_HOSTNAME = EnvironmentVariable(name='MDL_COMN_DB_HOSTNAME', legacy_name='DB_HOSTNAME', value='0.0.0.0')
    DB_PORT = EnvironmentVariable(name='MDL_COMN_DB_PORT', legacy_name='DB_PORT', value=3306)
    DB_NAME = EnvironmentVariable(name='MDL_COMN_DB_NAME', legacy_name='DB_NAME', value='text2phenotype')

    RETRY_TASK_COUNT_MAX = EnvironmentVariable(name='MDL_COMN_RETRY_TASK_COUNT_MAX',
                                               legacy_name='MDL_TASKS_RETRY_TASK_COUNT_MAX',
                                               value=3)

    # Text2phenotype API features flags
    OCR_OPERATION_ENABLED = EnvironmentVariable('MDL_API_OPERATION_OCR_ENABLED', value=True, expected_type=bool)

    DEID_OPERATION_ENABLED = EnvironmentVariable('MDL_API_OPERATION_DEID_ENABLED', value=True, expected_type=bool)

    DEMOGRAPHICS_OPERATION_ENABLED = EnvironmentVariable('MDL_API_OPERATION_DEMOGRAPHICS_ENABLED',
                                                         value=True, expected_type=bool)

    CLINICAL_SUMMARY_OPERATION_ENABLED = EnvironmentVariable('MDL_API_OPERATION_SUMMARY_CLINICAL_ENABLED',
                                                             value=True, expected_type=bool)

    ONCOLOGY_SUMMARY_OPERATION_ENABLED = EnvironmentVariable('MDL_API_OPERATION_SUMMARY_ONCOLOGY_ENABLED',
                                                             value=True, expected_type=bool)

    ONCOLOGY_ONLY_OPERATION_ENABLED = EnvironmentVariable('MDL_API_OPERATION_ONCOLOGY_ONLY_ENABLED',
                                                          value=True, expected_type=bool)

    APP_INGEST_OPERATION_ENABLED = EnvironmentVariable('MDL_API_OPERATION_APP_INGEST_ENABLED',
                                                       value=True, expected_type=bool)

    ANNOTATE_OPERATION_ENABLED = EnvironmentVariable('MDL_API_OPERATION_ANNOTATE_ENABLED',
                                                     value=False, expected_type=bool)

    DOCUMENT_PROCESSING_CORPUS_ENABLED = EnvironmentVariable('MDL_API_DOCUMENT_PROCESSING_CORPUS_ENABLED',
                                                             value=True, expected_type=bool)

    DOCUMENT_PROCESSING_TEXT_ENABLED = EnvironmentVariable('MDL_API_DOCUMENT_PROCESSING_TEXT_ENABLED',
                                                           value=True, expected_type=bool)

    DOCUMENT_PROCESSING_FILE_ENABLED = EnvironmentVariable('MDL_API_DOCUMENT_PROCESSING_FILE_ENABLED', value=True,
                                                           expected_type=bool)

    WORKER_HEALTHCHECK_FILE = EnvironmentVariable(name='MDL_COMN_WORKER_HEALTHCHECK_FILE',
                                                  value='/tmp/text2phenotype-worker-healthcheck')

    WORKER_HEALTHCHECK_MAX_AGE = EnvironmentVariable(name='MDL_COMN_WORKER_HEALTHCHECK_MAX_AGE',
                                                     value=600, expected_type=int)

    WORKER_HEALTHCHECK_VERBOSE = EnvironmentVariable('MDL_COMN_WORKER_HEALTHCHECK_VERBOSE',
                                                     value=False, expected_type=bool)

    # This feature flag used in SANDS. If enabled - the "/api/biomed_training/*" endpoints will be available
    BIOMED_TRAINING_ENABLED = EnvironmentVariable(name='MDL_COMN_BIOMED_TRAINING_ENABLED',
                                                  value=False,
                                                  expected_type=bool)

    # This "Api Key" is used for authorization in the Biomed Training APIs in SANDS.
    # Api-Key should be passed in the "X-Api-Key" HTTP header. The same environment variable
    # should be defined in the SANDS config.

    # TODO: This is a custom simplest approach for the first attempt but maybe not good for security reasons.
    #       We should think about Django's native auth scehemes. Maybe JWT or TokeAuthentication.
    #       https://www.django-rest-framework.org/api-guide/authentication/#api-reference
    BIOMED_TRAINING_API_KEY = EnvironmentVariable(name='MDL_COMN_BIOMED_TRAINING_API_KEY', value='')

    BIOMED_TRAINING_SANDS_URL = EnvironmentVariable(name='MDL_COMN_BIOMED_TRAINING_SANDS_URL',
                                                    value='http://localhost:8000')

    INTERNAL_COMMUNICATION_API_KEY = EnvironmentVariable(name='MDL_COMN_INTERNAL_COMMUNICATION_API_KEY',
                                                         value=None,
                                                         expected_type=str)

    # Default expiration time for redis_lock in seconds
    REDIS_LOCK_EXPIRATION = EnvironmentVariable(name='MDL_COMN_REDIS_LOCK_EXPIRATION',
                                                value=3,
                                                expected_type=int)

    # minimum length of segment (in characters of text) considered for duplication
    MIN_DUPLICATE_SEGMENT_LEN = EnvironmentVariable(name='MDL_COMN_DEDUP_MIN_SEGMENT_LEN', value=800)

    TASK_WORKER_VERSION = '1'

    TAG_TOG_API = EnvironmentVariable(name='MDL_COMN_TAGTOGAPI', value="https://datascience-training.text2phenotype.com/-api")
    TAG_TOG_USER = EnvironmentVariable(name='MDL_COMN_TAGTOGUSER')
    TAG_TOG_PWD = EnvironmentVariable(name='MDL_COMN_TAGTOGPWD')

    EKS_CLUSTER_NAME = EnvironmentVariable(name='MDL_TF_awsEksClusterName', expected_type=str, value='')

    # Webhook url for slack client
    SLACK_WEBHOOK_URL = EnvironmentVariable(name='MDL_COMN_SLACK_WEBHOOK_URL', expected_type=str)

    @classmethod
    def to_pretty_table(cls):
        """Generate table with all environment variables"""

        header = [('Name', 'Env variable', 'Value')]
        variables = []

        for attr_name in dir(cls):
            variable = getattr(cls, attr_name, None)
            if not isinstance(variable, EnvironmentVariable):
                continue

            variables.append((attr_name, variable.name, variable.value))

        # Columns width
        col_width = [0] * len(variables[0])

        for var in header + variables:
            for i in range(len(var)):
                col_width[i] = max(col_width[i], len(str(var[i])))

        templates = [f'{{:<{width}}}' for width in col_width]

        row = ['-' * width for width in col_width]
        table_border = '+-' + '-+-'.join(row) + '-+\n'

        def _create_row(values):
            row = []
            for i, x in enumerate(values):
                row.append(templates[i].format(str(x)))
            return '| ' + ' | '.join(row) + ' |\n'

        table = table_border
        table += _create_row(header[0])
        table += table_border
        table += ''.join(map(_create_row, variables))
        table += table_border
        return table
