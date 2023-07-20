from abc import (
    ABC,
    abstractmethod
)
from enum import Enum
from typing import (
    Dict,
    List,
    Optional,
)

from slack_sdk.models.blocks import (
    MarkdownTextObject,
    PlainTextObject,
    SectionBlock,
    TextObject
)


class SlackMessage(ABC):

    @abstractmethod
    def to_dict(self) -> Dict:
        pass


class PlainTextMessage(SlackMessage):

    def __init__(self, text: str):
        self.text: Optional[str] = text

    def to_dict(self) -> Dict:
        return {
            "text": self.text
        }


class SectionType(Enum):
    plain_text = "plain_text"
    markdown = "mrkdwn"


class SectionMessage(SlackMessage):

    def __init__(self):
        self.sections: List[SectionBlock] = []

    def add_section(self, section_type: SectionType, text: str) -> 'SectionMessage':
        text_obj: TextObject
        if section_type == SectionType.markdown:
            text_obj = MarkdownTextObject(text=text)
        else:
            text_obj = PlainTextObject(text=text)
        self.sections.append(SectionBlock(text=text_obj))
        return self

    def to_dict(self) -> Dict:
        return {
            "blocks": [section.to_dict() for section in self.sections]
        }
