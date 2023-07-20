from botocore.exceptions import ClientError
from pika.exceptions import (
    AMQPError,
    ChannelError,
)


class QueueClientError(Exception):
    def __init__(self, exception):
        super().__init__(exception)
        self.message = ''
        self.exception = exception
        # AWS
        if isinstance(exception, ClientError):
            error = exception.response.get('Error', {})
            self.message = error.get('Message', '')
        # RabbitMQ
        elif isinstance(exception, (AMQPError, ChannelError)):
            self.message = str(self.exception)


class StorageClientError(Exception):
    pass
