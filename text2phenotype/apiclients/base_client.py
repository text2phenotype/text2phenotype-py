import functools
from typing import (
    Any,
    Callable,
    Optional,
    Type,
    Union,
)

import requests
from requests import Response

from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import EnvironmentVariable


def logging(func):
    @functools.wraps(func)
    def wrapper(client: 'BaseClient', endpoint: str, *args, tid: str = None, **kwargs) -> Response:
        url = client._get_url(endpoint)
        operations_logger.debug(f'Sending {func.__name__.upper()} request to the {url}', tid=tid)

        try:
            resp = func(client, endpoint, *args, tid=tid, **kwargs)
        except requests.exceptions.ConnectionError:
            operations_logger.error(f'Service unavailable: {client.api_base}', tid=tid)
            raise
        else:
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError:
                operations_logger.error(f'Bad status for the current request. '
                                        f'Status Code = {resp.status_code}, '
                                        f'Content = {resp.content}',
                                        tid=tid)
            return resp
    return wrapper


def response_json(item: Union['BaseClient', Type, Callable]):
    """Decorate methods to return deserialized JSON response"""

    def decorate_method(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            if isinstance(res, Response):
                res.raise_for_status()
                return res.json()
            return res

        # Update func.__annotations__
        ret_annotation = wrapper.__annotations__.get('return')
        if not ret_annotation or isinstance(ret_annotation, Response):
            wrapper.__annotations__['return'] = Any

        return wrapper

    def decorate_all_methods(obj):
        # Find methods (exclude "object" class)
        cls = obj if isinstance(obj, type) else obj.__class__
        methods_set = set()

        for class_ in cls.mro()[:-1]:
            for name, attr in class_.__dict__.items():
                if callable(attr):
                    methods_set.add(name)

        for name in methods_set:
            func = getattr(obj, name)
            setattr(obj, name, decorate_method(func))

        return obj

    if isinstance(item, type):
        WrappedClass = type(item.__name__, (item, ), {})  # Create copy of source class
        return decorate_all_methods(WrappedClass)

    elif isinstance(item, BaseClient):
        return decorate_all_methods(item)

    return decorate_method(item)


class BaseClient:
    ENVIRONMENT_VARIABLE: Optional[EnvironmentVariable] = None
    API_ENDPOINT: str = '/'

    DEFAULT_HEADERS: Optional[dict] = None
    DEFAULT_KWARGS: dict = {}

    def __init__(self, api_base: Optional[str] = None):
        if api_base is None and self.ENVIRONMENT_VARIABLE:
            api_base = self.ENVIRONMENT_VARIABLE.value

        if not api_base:
            error_message = f'API base URL is not defined for the "{self.__class__}". '

            if self.ENVIRONMENT_VARIABLE:
                error_message += f'You should define "{self.ENVIRONMENT_VARIABLE.name}" ' \
                                 f'environment variable or pass not empty "api_base" argument.'
            else:
                error_message += 'There is no environment variable, ' \
                                 'the "api_base" argument should not be empty.'

            raise ValueError(error_message)

        self.api_base = api_base
        self.api_base = self._get_url(self.API_ENDPOINT)

        self.headers = self.DEFAULT_HEADERS.copy() if self.DEFAULT_HEADERS else {}
        self.default_kwargs = self.DEFAULT_KWARGS.copy() if self.DEFAULT_KWARGS else {}

    def _update_kwargs_with_defaults(self, kwargs: dict) -> dict:
        """Create copy of kwargs dict included "default_kwargs" values"""

        result = self.default_kwargs.copy()

        if self.headers:
            result['headers'] = self.headers.copy()

        result.update(kwargs)
        return result

    def _get_url(self, endpoint: str) -> str:
        endpoint = endpoint.lstrip('/')
        api_base = self.api_base.rstrip('/')
        return f'{api_base}/{endpoint}'

    @logging
    def post(self, endpoint: str, data=None, json=None, tid: str = None, **kwargs) -> Response:
        url = self._get_url(endpoint)
        kwargs = self._update_kwargs_with_defaults(kwargs)
        return requests.post(url, data=data, json=json, **kwargs)

    @logging
    def get(self, endpoint: str, params=None, tid: str = None, **kwargs) -> Response:
        url = self._get_url(endpoint)
        kwargs = self._update_kwargs_with_defaults(kwargs)
        return requests.get(url, params, **kwargs)


class CommonAPIMethodsMixin:
    """API methods common for most of API services"""

    def ready(self) -> Response:
        return self.get('/health/ready')

    def live(self) -> bool:
        resp = self.get('/health/live')
        return resp.ok

    def version(self) -> Optional[dict]:
        resp = self.get('/version')
        resp.raise_for_status()
        return resp.json()
