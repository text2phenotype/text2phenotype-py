import datetime
import json
import pyrfc3339
import pytz

from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Any,
    Dict,
)


class CustomJsonEncoder(json.JSONEncoder):

    def default(self, obj: object) -> str:

        if type(obj) in [datetime.date]:
            return str(obj)

        if type(obj) == datetime.datetime:
            return pyrfc3339.generate(obj.replace(tzinfo=pytz.utc))

        if type(obj) == set:  # convert set to a list and return as string
            return str([self.default(i) for i in obj])

        try:
            default_encoding = json.JSONEncoder.default(self, obj)
        except TypeError:
            default_encoding = str(obj)

        return default_encoding


class CustomJsonDecoder(json.JSONDecoder):

    def decode(self, json_string: str) -> Dict[Any, Any]:
        obj = super(CustomJsonDecoder, self).decode(json_string)
        for key, val in obj.items():
            try:
                obj[key] = pyrfc3339.parse(val)
            except ValueError:
                pass
        return obj


class JsonSerializableMethodsMixin(ABC):
    def to_dict(self) -> dict:
        raise NotImplementedError()

    def to_json(self, **json_dumps_kwargs) -> str:
        return json.dumps(self.to_dict(), **json_dumps_kwargs)

    def fill_from_dict(self, data: dict) -> None:
        raise NotImplementedError()

    def fill_from_json(self, json_str: str) -> None:
        data = json.loads(json_str)
        return self.fill_from_dict(data)
