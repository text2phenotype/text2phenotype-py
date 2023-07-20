from enum import Enum
from typing import (
    Any,
    Dict,
    Optional,
    Union,
)

from text2phenotype.constants.environment import Environment
from .drivers import (
    KubeQueueService,
    RmqQueueService,
    SqsQueueService,
)


class QueueProvidersEnum(Enum):
    SQS = 'SQS'
    RMQ = 'RMQ'
    KUBEMQ = 'KUBEMQ'


class QueueProvider:
    """ Storage provider factory

    :arg QueueProvidersEnum queue_service: Storage service name, by default, is QueueProvidersEnum.SQS
    """

    def __init__(self, queue_service: Optional[QueueProvidersEnum] = QueueProvidersEnum.SQS, **kwargs):
        if queue_service == QueueProvidersEnum.SQS:
            self.provider = SqsQueueService
            self.options = {
                'aws_access_key_id': Environment.AWS_ACCESS_ID.value,
                'aws_secret_access_key': Environment.AWS_ACCESS_KEY.value,
                'region_name': Environment.AWS_REGION_NAME.value,
                # Place for custom options
                'options': {}
            }

        elif queue_service == QueueProvidersEnum.RMQ:
            self.provider = RmqQueueService
            self.options = {
                # RabbitMQ (pika) specific kwargs
                'host': Environment.RMQ_HOST.value,
                'port': Environment.RMQ_PORT.value,
                'username': Environment.RMQ_USERNAME.value,
                'password': Environment.RMQ_PASSWORD.value,

                # Custom options
                'options': {
                    'max_receive_count': int(Environment.RMQ_MAX_RECEIVE_COUNT.value),
                    'default_exchange': Environment.RMQ_DEFAULT_EXCHANGE.value,
                }
            }

        elif queue_service == QueueProvidersEnum.KUBEMQ:
            self.provider = KubeQueueService
            self.options = {
                'host': Environment.KUBEMQ_HOST.value,
                'port': int(Environment.KUBEMQ_PORT.value),
                'message_visibility_seconds': int(Environment.KUBEMQ_MESSAGE_VISIBILITY_SECONDS.value),
                'message_expiration_seconds': int(Environment.KUBEMQ_MESSAGE_EXPIRATION_SECONDS.value),
                'max_receive_count': int(Environment.KUBEMQ_MAX_RECEIVE_COUNT.value),
                'client_id': Environment.APPLICATION_NAME.value,
            }

        # By default use pre-defined settings, else custom settings
        self.options = kwargs or self.options


def get_queue_service(provider: Optional[QueueProvidersEnum] = None, config: Dict[str, Any] = None) -> \
        Union[SqsQueueService, RmqQueueService]:
    """ Get Queue service instance

    :param provider: Value for a queue provider, by default, will be used DEFAULT_QUEUE_SERVICE
    :param config: Dictionary with some special or additional parameters
    :return: Queue instance, one of (SqsQueueService, RmqQueueService, )
    """
    if not provider and config:
        raise AttributeError('Please define service provider')

    provider = provider or getattr(QueueProvidersEnum, Environment.DEFAULT_QUEUE_SERVICE.value)
    if not config:
        config = {}
    queue = QueueProvider(provider, **config)
    return queue.provider(queue.options)
