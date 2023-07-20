import sys
from datetime import (
    date,
    datetime,
)
from enum import (
    Enum,
    EnumMeta,
)
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    Union,
)

# "GenericMeta" isn't necessary in Python >=3.7
# https://github.com/hsolbrig/PyShEx/issues/17#issuecomment-427557545
# Also, see this for swagger compatability issues:
# https://github.com/swagger-api/swagger-codegen/issues/8921
try:
    from typing import GenericMeta  # Python v3.6
except ImportError:
    # In v3.7, GenericMeta doesn't exist but we don't need it
    class GenericMeta(type):
        pass

import yaml
from dateutil.parser import parse
from pydantic import BaseModel
from pydantic.schema import schema

from text2phenotype.common.log import operations_logger
from text2phenotype.common.version_info import get_version_info
from text2phenotype.constants.common import deserialize_enum


def _deserialize(data, klass):
    """Deserializes dict, list, str into an object.
    :param data: dict, list or str.
    :param klass: class literal, or string of class name.
    :return: object.
    """
    if data is None:
        return None

    has_generic_meta = sys.version_info.major == 3 and sys.version_info.minor < 7

    if klass in (float, str, bool, int):
        return _deserialize_primitive(data, klass)
    elif klass == object:
        return _deserialize_object(data)
    elif klass == datetime.date:
        return deserialize_date(data)
    elif klass == datetime:
        return deserialize_datetime(data)
    elif type(klass) in (EnumMeta, Enum):
        return deserialize_enum(data, klass)
    elif has_generic_meta and type(klass) == GenericMeta:
        # py_version < 3.6
        if klass.__extra__ == list:
            return _deserialize_list(data, klass.__args__[0])
        if klass.__extra__ == dict:
            return _deserialize_dict(data, klass.__args__[1])
    elif not has_generic_meta and hasattr(klass, '__origin__'):
        # py_version >= 3.7
        if klass.__origin__ == list:
            return _deserialize_list(data, klass.__args__[0])
        if klass.__origin__ == dict:
            return _deserialize_dict(data, klass.__args__[1])
    else:
        return deserialize_model(data, klass)


def _deserialize_primitive(data, klass) -> Union[int, float, str, bool]:
    """Deserializes to primitive type.
    :param data: data to deserialize.
    :param klass: class literal.
    :return: int, long, float, str, bool.
    """
    try:
        value = klass(data)
    except UnicodeEncodeError:
        value = str(data)
    except TypeError:
        value = data
    return value


def _deserialize_object(value):
    """Return a original value.
    :return: object.
    """
    return value


def deserialize_date(string: str) -> date:
    """Deserializes string to date.
    :param string: str.
    :return: date.
    """
    return parse(string).date()


def deserialize_datetime(string: str) -> datetime:
    """Deserializes string to datetime.
    The string should be in iso8601 datetime format.
    :param string: str.
    :return: datetime.
    """
    return parse(string)


def deserialize_model(data: Union[List, Dict], klass):
    """Deserializes list or dict to model.
    :param data: dict, list.
    :param klass: class literal.
    """
    instance = klass()

    if not instance.swagger_types:
        return data

    for attr, attr_type in instance.swagger_types.items():
        if data is not None \
                and instance.attribute_map[attr] in data \
                and isinstance(data, (list, dict)):
            value = data[instance.attribute_map[attr]]
            setattr(instance, attr, _deserialize(value, attr_type))

    return instance


def _deserialize_list(data: List, boxed_type) -> List:
    """Deserializes a list and its elements.
    :param data: list to deserialize.
    :param boxed_type: class literal.
    :return: deserialized list.
    """
    return [_deserialize(sub_data, boxed_type)
            for sub_data in data]


def _deserialize_dict(data: Dict, boxed_type) -> Dict:
    """Deserializes a dict and its elements.
    :param data: dict to deserialize.
    :param boxed_type: class literal.
    :return: deserialized dict.
    """
    return {k: _deserialize(v, boxed_type)
            for k, v in data.items()}


def generate_openapi_spec(template_file_path: Union[str, Path],
                          include_schemas: Optional[List[Type[BaseModel]]] = None,
                          exclude_endpoints: Optional[List[str]] = None) -> Dict:
    operations_logger.info(f'Generate OpenAPI spec from the template "{template_file_path}"')

    with open(template_file_path, 'r') as f:
        spec: Dict[str, Any] = yaml.safe_load(f)

    if include_schemas:
        openapi_schemas = schema(include_schemas, ref_prefix='#/components/schemas/')
        definitions = openapi_schemas['definitions']
        sorted_openapi_schemas = {key: definitions[key] for key in sorted(definitions)}

        schemas_section: Dict[str, Any] = spec.setdefault('components', {}) \
                                              .setdefault('schemas', {})
        schemas_section.update(sorted_openapi_schemas)

    if exclude_endpoints:
        paths_section = spec.setdefault('paths', {})
        for path in exclude_endpoints:
            paths_section.pop(path, None)

    info_section: Dict[str, Any] = spec.setdefault('info', {})

    if not info_section.get('version'):
        info_section['version'] = get_version_info().to_version_str()

    return spec
