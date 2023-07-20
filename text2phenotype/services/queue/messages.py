import json

from text2phenotype.services.queue.constants import INTAKE_SERVICE_SOURCE_NAME


class FileUploadedMessage:
    def __init__(self, filename, **kwargs):
        self.filename = filename
        self.message = 'metadata file was added'

    def to_dict(self):
        return {'filename': self.filename, 'message': self.message}

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, queue_message):
        message = json.loads(queue_message.body)
        if isinstance(message, dict):
            return message
        else:
            return None

    @classmethod
    def get_filename(cls, queue_message):
        raise NotImplemented()

    @classmethod
    def is_test_message(cls, queue_message):
        raise NotImplemented()


class FileUploadedIntakeMessage(FileUploadedMessage):
    def to_dict(self):
        message = super().to_dict()
        message['event_source'] = INTAKE_SERVICE_SOURCE_NAME
        return message

    @classmethod
    def get_filename(cls, queue_message):
        message = cls.from_json(queue_message)

        # Check for `Intake` message format
        if message and message.get('event_source') == INTAKE_SERVICE_SOURCE_NAME:
            return message.get('filename')
        else:
            return None

    @classmethod
    def is_test_message(cls, queue_message):
        message = cls.from_json(queue_message)
        if message:
            return False
        else:
            return None


class FileUploadedSQSMessage(FileUploadedMessage):
    def to_dict(self):
        raise NotImplemented()

    @classmethod
    def get_filename(cls, queue_message):
        message = cls.from_json(queue_message)
        if not message:
            return None

        # Check for `SNS` message format
        # https://docs.aws.amazon.com/en_us/sns/latest/dg/sns-message-and-json-formats.html
        if message.get('Message'):
            # If the key 'Message' appears, the item is from SNS and has
            # a different format than a direct to SQS notification.
            message = json.loads(message['Message'])

        # Check for `S3Event` SQS message format
        # https://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
        if message.get('Records') and 's3' in message['Records'][0]:
            return message['Records'][0]['s3']['object']['key']
        else:
            return None

    @classmethod
    def is_test_message(cls, queue_message):
        message = cls.from_json(queue_message)
        if message:
            return message.get('Event') == 's3:TestEvent'
        else:
            return None
