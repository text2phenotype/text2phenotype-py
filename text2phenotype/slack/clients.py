from abc import (
    ABC,
    abstractmethod
)
from typing import Optional

from slack_sdk import WebhookClient

from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import Environment

from .messages import SlackMessage


class SlackClient(ABC):

    @abstractmethod
    def post_message(self, message: SlackMessage):
        pass


class WebhookSlackClient(SlackClient):

    def __init__(self, *, webhook_url: Optional[str] = None):
        self._url: str = webhook_url or Environment.SLACK_WEBHOOK_URL.value
        self._client = WebhookClient(url=self._url)

    def post_message(self, message: SlackMessage):
        operations_logger.debug("Sending Slack message with webhook")
        if not self._url:
            operations_logger.warning(
                "Could not send message to Slack: `MDL_COMN_SLACK_WEBHOOK_URL` environment variable not set")
            return None
        try:
            self._client.send_dict(message.to_dict())
        except Exception:
            operations_logger.exception("Failed to send Slack message with webhook")
