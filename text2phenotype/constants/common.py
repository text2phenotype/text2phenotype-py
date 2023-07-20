from enum import Enum, IntEnum
from typing import Union, Type, Optional


class FileExtensions(Enum):
    PDF = 'pdf'
    TXT = 'txt'
    XPS = 'xps'
    JSON = 'json'
    PNG = 'png'
    YML = 'yml'
    YAML = 'yaml'

    # text2phenotype App - until .json extension is no longer so sensitive in S3
    ANN = 'ann'
    DEMO = 'demographics'
    HEPC = 'hepc'
    OCR = 'ocr'
    PHI_TOKENS = 'phi_tokens'
    SUMMARY = 'summary'

    @classmethod
    def has_value(cls, value: str):
        try:
            cls(value)
        except ValueError:
            return False
        else:
            return True

    def __str__(self):
        return self.value


class ContentTypes:
    PDF = 'application/pdf'
    TEXT = 'text/plain'
    JSON = 'application/json'
    PNG = 'image/png'
    XPS = 'application/oxps'

    __lookup = {
        FileExtensions.PDF: PDF,
        FileExtensions.TXT: TEXT,
        FileExtensions.XPS: XPS,
        FileExtensions.JSON: JSON,
        FileExtensions.PNG: PNG,
        FileExtensions.ANN: TEXT,
        FileExtensions.DEMO: JSON,
        FileExtensions.HEPC: JSON,
        FileExtensions.OCR: JSON,
        FileExtensions.PHI_TOKENS: JSON,
        FileExtensions.SUMMARY: JSON,
    }

    @classmethod
    def get_content_type(cls, extension: str) -> str:
        extension = extension.lower()
        if FileExtensions.has_value(extension):
            ext = FileExtensions(extension)
            return cls.__lookup[ext]
        else:
            return cls.JSON


def deserialize_enum(data: Union[int, str, Enum],
                     enum: Type[Union[Enum, IntEnum]]) -> Optional[Type[Union[Enum, IntEnum]]]:
    """Deserializes a value to its enum type
    :param data: value to deserilize
    :param enum: enum class
    :return: deserialized enum value
    """
    if data is None or isinstance(data, enum):
        return data

    if issubclass(enum, IntEnum):
        if isinstance(data, str):
            try:
                value = enum[data.split('.')[-1]]
            except KeyError:
                value = enum(int(data))
        elif isinstance(data, int):
            value = enum(data)
    else:
        value = enum(data)

    return value


VERSION_INFO_KEY = 'VersionInfo'

OCR_PAGE_SPLITTING_KEY = ['\x0c']
BEGINNING_SECTIONS = [OCR_PAGE_SPLITTING_KEY[0], 'page', 'dictated by', 'signed by', '\n\n\n', '.\n', '. ', '\n\n', '\n']
