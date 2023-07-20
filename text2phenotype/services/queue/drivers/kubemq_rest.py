from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
)

import atexit
import base64
import json
import threading
import time
import requests

from .base import (
    Message as BaseMessage,
    Queue as BaseQueue,
    QueueService as BaseQueueService,
)


DEFAULT_MESSAGE_EXPIRATION_SECONDS = 43200
DEFAULT_MESSAGE_VISIBILITY_SECONDS = 30
DEFAULT_CLIENT_ID = 'Text2phenotype'


class TransactionClosedError(Exception):
    pass


class KubeRequestError(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response


class DictObject(dict):
    """ Represent dict-like objects as an object with key-attrributes.

    Example:
        data = DictObject({'x': 123})  # data.x -> 123
        data.x = 512  # data -> {"x": 512}
    """

    def __has_own_attribute(self, name: str) -> bool:
        return name in self.__class__.__dict__.keys()

    def __attribute_error(self, name: str) -> AttributeError:
        return AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        raise self.__attribute_error(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if self.__has_own_attribute(name):
            super().__setattr__(name, value)
        else:
            if isinstance(value, dict) and not isinstance(value, DictObject):
                value = DictObject(value)
            self[name] = value

    def __delattr__(self, name: str) -> None:
        if self.__has_own_attribute(name):
            super().__delattr__(name)
        elif name in self:
            del self[name]
        else:
            raise self.__attribute_error(name)


class RestClient:
    """Minimal REST client for communicate with KubeMQ Queue API"""

    def __init__(self, base_url: str) -> None:
        if '://' not in base_url:
            base_url = 'http://' + base_url
        self.base_url = base_url
        self.headers = {'Content-Type': 'application/json'}

    def __get_url(self, path: str) -> str:
        return self.base_url.rstrip('/') + '/' + path.lstrip('/')

    def __parse_response(self, resp) -> DictObject:
        return json.loads(resp.content, object_hook=DictObject)

    def _get(self, path: str) -> DictObject:
        resp = requests.get(self.__get_url(path),
                            headers=self.headers)
        return self.__parse_response(resp)

    def _post(self, path: str, data: dict) -> DictObject:
        resp = requests.post(self.__get_url(path),
                             json=data,
                             headers=self.headers)
        return self.__parse_response(resp)


class Message(DictObject):
    """Object describes KubeMQ Queue Message
    https://postman.kubemq.io/
    """

    KUBEMQ_MESSAGE_TEMPLATE = {
        'Id': '',
        'ClientID': '',
        'Channel': '',
        'Metadata': '',
        'Body': '',
        'Tags': DictObject({}),
        'Policy': DictObject({
            'ExpirationSeconds': 0,
            'DelaySeconds': 0,
            'MaxReceiveCount': 0,
            'MaxReceiveQueue': ''
        })
    }

    def __init__(self, msg: Optional[dict] = None) -> None:
        super().__init__()
        self.update(Message.KUBEMQ_MESSAGE_TEMPLATE)
        if msg:
            self.update(msg)

    @property
    def Body(self) -> bytes:
        return base64.b64decode(self['Body'].encode('utf8'))

    @Body.setter
    def Body(self, value: bytes) -> None:
        self['Body'] = base64.b64encode(value).decode('utf8')


class KubeRequest(DictObject):
    """Describe KubeMQ Queue "ReceiveMessage" request object.
    https://postman.kubemq.io/
    """

    KUBEMQ_REQUEST_TEMPLATE = {
        'RequestID': '',
        'ClientID': '',
        'Channel': '',
        'MaxNumberOfMessages': 1,
        'WaitTimeSeconds': 1,
        'IsPeak': False
    }

    def __init__(self) -> None:
        super().__init__()
        self.update(KubeRequest.KUBEMQ_REQUEST_TEMPLATE)


class MessageQueue(RestClient):
    """Implementation of KubeMQ "MessageQueue" class based on REST API"""

    def __init__(self,
                 queue_name: str,
                 kubemq_address: str,
                 client_id: str,
                 wait_time_seconds_queue_messages: int = 1) -> None:
        super().__init__(kubemq_address)
        self.queue_name = queue_name
        self.client_id = client_id
        self.wait_time_seconds = wait_time_seconds_queue_messages

        self.__server_time_offset_seconds = None

    def get_server_time(self) -> float:
        if self.__server_time_offset_seconds is None:
            local_ts = int(time.time())
            data = self.ping().data
            server_ts = data.ServerStartTime + data.ServerUpTimeSeconds
            self.__server_time_offset_seconds = server_ts - local_ts
        return time.time() + self.__server_time_offset_seconds

    def __create_request(self) -> KubeRequest:
        request = KubeRequest()
        request.Channel = self.queue_name
        request.ClientID = self.client_id
        return request

    def send_queue_message(self, message: Message) -> dict:
        message.Channel = self.queue_name
        message.ClientID = self.client_id
        return self._post('/queue/send', message)

    def receive_message(self, wait_time_seconds: int = 1) -> Optional[Message]:
        request = self.__create_request()
        request.MaxNumberOfMessages = 1
        request.WaitTimeSeconds = wait_time_seconds

        resp = self._post('/queue/receive', request)

        # Convert to "Message" object
        if 'Messages' in resp.data:
            resp.data.Messages = [Message(m) for m in resp.data.Messages]

        return resp

    def ack_all_queue_messages(self, wait_time_seconds: int = 1) -> dict:
        request = self.__create_request()
        request.WaitTimeSeconds = wait_time_seconds
        return self._post('/queue/ack_all', request)

    def ping(self) -> dict:
        return self._get('/ping')

    def create_transaction(self):
        return Transaction(self)


class Transaction:
    def __init__(self, queue: MessageQueue) -> None:
        self.client = queue

        self.__lock = threading.Lock()
        self.__thread = None
        self.__message = None

        self.__done = False

        self.__ts = None
        self.__visibility_expired_at = None
        self.__message_expired_at = None

    def close(self) -> None:
        self.__done = True
        atexit.unregister(self.__finallize)

    def receive(self,
                visibility_seconds: int = DEFAULT_MESSAGE_VISIBILITY_SECONDS,
                wait_time_seconds: int = 1) -> dict:

        self.__check_transaction()

        resp = self.client.receive_message(wait_time_seconds)
        self.__check_response_error(resp)

        if 'Messages' not in resp.data:
            self.close()
            return resp

        resp.Message = resp.data.Messages[0]
        del resp.data.Messages

        self.__start_visibility_thread(resp.Message, visibility_seconds)
        return resp

    def ack(self) -> None:
        with self.__lock:
            self.__check_transaction()
            self.close()

    def reject(self, delay: Optional[int] = None) -> None:
        with self.__lock:
            self.__check_transaction()

            if self.is_message_dead():
                # TODO: move message to DLQ
                self.close()
                return

            self.__message.Policy.MaxReceiveCount -= 1

            if delay is not None:
                self.__message.Policy.DelaySeconds = delay

            expiration_seconds = self.__get_message_expiration_seconds()
            if expiration_seconds is not None:
                self.__message.Policy.ExpirationSeconds = round(expiration_seconds)

            resp = self.client.send_queue_message(self.__message)
            self.__check_response_error(resp)
            self.close()

    def modify(self, message: Message) -> None:
        with self.__lock:
            self.__check_transaction()
            resp = self.client.send_queue_message(message)
            self.__check_response_error(resp)
            self.close()

    def extend_visibility(self, visibility_seconds: int) -> None:
        with self.__lock:
            self.__check_transaction()
            self.__visibility_expired_at += visibility_seconds

    def __get_message_expiration_seconds(self) -> float:
        if not self.__message:
            return None

        tags = self.__message.Tags
        attributes = self.__message.Attributes

        if 'ExpirationAt' not in attributes:
            return None

        if 'original_expiration_at' not in tags:
            tags.original_expiration_at = str(attributes.ExpirationAt / 10**9)  # Nanoseconds to Seconds

        server_time = self.client.get_server_time()
        expiration_at = float(tags.original_expiration_at)
        return expiration_at - server_time

    def is_message_expired(self) -> bool:
        if self.__message_expired_at is None:
            return False
        return time.time() >= self.__message_expired_at

    def is_receive_count_exceeded(self) -> bool:
        policy = self.__message.Policy
        attributes = self.__message.Attributes

        if 'MaxReceiveCount' not in policy:
            return False

        return attributes.ReceiveCount + 1 > policy.MaxReceiveCount

    def is_message_dead(self) -> bool:
        return self.is_message_expired() or self.is_receive_count_exceeded()

    def __thread_loop(self) -> None:
        while True:
            if self.__done:
                break

            if time.time() >= self.__visibility_expired_at:
                self.reject()

            time.sleep(1)

    def __start_visibility_thread(self,
                                  message: Message,
                                  visibility_seconds: int) -> None:

        self.__ts = time.time()
        self.__message = message

        self.__visibility_expired_at = self.__ts + visibility_seconds

        expiration_seconds = self.__get_message_expiration_seconds()
        if expiration_seconds is not None:
            self.__message_expired_at = self.__ts + expiration_seconds

        self.__thread = threading.Thread(target=self.__thread_loop, daemon=True)
        self.__thread.start()

        atexit.register(self.__finallize)

    def __check_transaction(self) -> None:
        if self.__done:
            raise TransactionClosedError()

    def __check_response_error(self, resp) -> None:
        if 'data' in resp and 'Error' in resp.data:
            raise KubeRequestError(resp.data.Error, resp)

        if resp.is_error:
            raise KubeRequestError('Request failed', resp)

    def __finallize(self) -> None:
        if self.__message and not self.__done:
            self.reject()
        else:
            self.close()

    def __del__(self) -> None:
        self.__finallize()


class KubeMessage(BaseMessage):
    def __init__(self,
                 queue: BaseQueue,
                 kube_message: Message,
                 kube_transaction: MessageQueue) -> None:

        self._queue = queue
        self.__message = kube_message
        self.__transaction = kube_transaction

    def get_body(self) -> str:
        return self.__message.Body.decode('utf8')

    def delete(self) -> None:
        self.__transaction.ack()

    def reject(self, visibility_timeout: float = None) -> None:
        delay = int(visibility_timeout or 0)
        self.__transaction.reject(delay)

    def extend_visibility_timeout(self, extension: int) -> None:
        self.__transaction.extend_visibility(visibility_seconds=extension)


class KubeQueue(BaseQueue):
    def __init__(self,
                 service: BaseQueueService,
                 kube_queue: MessageQueue):

        self._service = service
        self.kube_queue = kube_queue
        self.name = kube_queue.queue_name

    @property
    def config(self) -> dict:
        return self._service.config

    def __receive_transaction_message(self, wait_time_seconds: int = 30) -> Optional[KubeMessage]:
        transaction = self.kube_queue.create_transaction()

        resp = transaction.receive(
            visibility_seconds=self.config.get('message_visibility_seconds') or DEFAULT_MESSAGE_VISIBILITY_SECONDS,
            wait_time_seconds=wait_time_seconds)

        if not resp.is_error and 'Message' in resp:
            return KubeMessage(self, resp.Message, transaction)

        return None

    def iter_messages(self) -> Iterator[KubeMessage]:
        while True:
            message = self.__receive_transaction_message(wait_time_seconds=30)
            if message is not None:
                yield message

    def receive_message(self, timeout: Optional[int] = None) -> KubeMessage:
        if timeout is None:
            return next(self.iter_messages())

        return self.__receive_transaction_message(wait_time_seconds=timeout)

    def send_message(self,
                     body: str,
                     delay: Optional[float] = None,
                     **kwargs) -> bool:

        kube_message = Message()
        kube_message.Body = body.encode('utf8')
        kube_message.Policy.ExpirationSeconds = self.config.get('message_expiration_seconds') or DEFAULT_MESSAGE_EXPIRATION_SECONDS

        max_receive_count = self.config.get('max_receive_count')
        if max_receive_count:
            kube_message.Policy.MaxReceiveCount = max_receive_count

        if delay:
            kube_message.Policy.DelaySeconds = int(delay)

        resp = self.kube_queue.send_queue_message(kube_message)

        if resp.is_error or resp.get('data', {}).get('IsError'):
            return False
        return True

    def send_messages(self, entries: List[Dict]) -> Dict:
        response = {
            'Successful': [],
            'Failed': []
        }

        for entry in entries:
            res = self.send_message(
                body=entry['MessageBody'])

            if res:
                response['Successful'].append({'Id': entry['Id']})
            else:
                response['Failed'].append({'Id': entry['Id']})

        return response

    def purge(self) -> None:
        self.kube_queue.ack_all_queue_messages()

    def delete(self) -> None:
        self.purge()  # There is no method for delete queue in the KubeMQ


class KubeQueueService(BaseQueueService):
    def get_queue(self, name: str) -> KubeQueue:
        queue = MessageQueue(
            queue_name=name,
            client_id=self.config.get('client_id') or DEFAULT_CLIENT_ID,
            kubemq_address=f"{self.config['host']}:{self.config['port']}",
            wait_time_seconds_queue_messages=1)

        return KubeQueue(service=self,
                         kube_queue=queue)

    def check_connection(self, name: str) -> bool:
        try:
            queue = self.get_queue(name)
            resp = queue.kube_queue.ping()
            connected = resp.data.ServerUpTimeSeconds > 0
        except Exception:
            connected = False

        return connected

    def connection_keepalive(self):
        pass
