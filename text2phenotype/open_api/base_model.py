import pprint
from enum import IntEnum

from text2phenotype.open_api import util
from typing import Dict, List, TypeVar, Type, Optional

T = TypeVar('T')


class Model:
    # swaggerTypes: The key is attribute name and the
    # value is attribute type.
    swagger_types = {}

    # attributeMap: The key is attribute name and the
    # value is json key in definition.
    attribute_map = {}

    @classmethod
    def from_dict(cls: Type[T], dikt) -> T:
        """Returns the dict as a model"""
        return util.deserialize_model(dikt, cls)

    def to_dict(self) -> Dict:
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in self.swagger_types.items():
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self) -> str:
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other

    @staticmethod
    def convert_enum_dict_keys(target: Dict, enum: Type[IntEnum]) -> Optional[Dict[Type[IntEnum], List[str]]]:
        result = {}
        if target:
            for k, v in target.items():
                result[util.deserialize_enum(k, enum)] = v
        return result

    @staticmethod
    def convert_enum_list(target: list, enum: Type[IntEnum]) -> Optional[List[Type[IntEnum]]]:
        result = []
        if target:
            for item in target:
                result.append(util.deserialize_enum(item, enum))
        return result
