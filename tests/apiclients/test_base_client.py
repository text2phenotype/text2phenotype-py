import functools
import unittest
from typing import (
    Any,
    Callable,
    Dict,
    Tuple,
)
from unittest.mock import patch
from uuid import uuid4

from text2phenotype.apiclients.base_client import (
    BaseClient,
    CommonAPIMethodsMixin,
)
from text2phenotype.constants.environment import (
    Environment,
    EnvironmentVariable,
)


class TestEnvironment(Environment):
    FAKE_API_BASE = EnvironmentVariable(name='FAKE_API_BASE',
                                        value='https://environment.var/')


class FakeTestClient(BaseClient):
    """Fake client to check the BaseClient behavior"""

    ENVIRONMENT_VARIABLE = TestEnvironment.FAKE_API_BASE
    API_ENDPOINT = '/api/v2/'

    def _mock_call_args(target: str) -> Callable:
        """Auxiliary decorator to mock required method and return call arguments"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Tuple[Tuple[Any], Dict[str, Any]]:
                with patch(f'{BaseClient.__module__}.{target}') as mock:
                    func(*args, **kwargs)
                    return mock.call_args
            return wrapper
        return decorator

    @_mock_call_args('requests.get')
    def get(self, endpoint='/get', *args, **kwargs):
        super().get(endpoint, *args, **kwargs)

    @_mock_call_args('requests.post')
    def post(self, endpoint='/post', *args, **kwargs):
        super().post(endpoint, *args, **kwargs)

    
class TestBaseClient(unittest.TestCase):
    CUSTOM_KWARG_NAME = 'specific_requests_option'

    def _join_path(self, *args):
        """Join arguments to url/path"""
        first = [str(p).strip('/') for p in args[:-1]]
        last = [str(l).lstrip('/') for l in args[-1:]]
        return '/'.join(first + last)

    def test_init_arguments(self):
        """Test __init__ of Api Clients"""
        def _check_client(client, expected_url):
            self.assertEqual(client.api_base, expected_url)

            # Check get(), post() arguments
            for method in (client.get, client.post):
                args, kwargs = method()
                url = args[0]
                self.assertTrue(url.startswith(expected_url))

        # By default ApiClient should take value from the environment variable
        expected_api_base = self._join_path(TestEnvironment.FAKE_API_BASE.value,
                                            FakeTestClient.API_ENDPOINT)
        
        _check_client(FakeTestClient(), expected_api_base)

        # User can pass a custom url
        custom_url = 'https://custom.api.base/additional/path/'
        expected_api_base = self._join_path(custom_url, FakeTestClient.API_ENDPOINT)
        _check_client(FakeTestClient(custom_url), expected_api_base)

    def test_get_post_common_args(self):
        endpoint = f'/{uuid4().hex}'
        
        client = FakeTestClient()
        expected_url = self._join_path(client.api_base, endpoint)
        
        for method in (client.get, client.post):
            args, kwargs = method(endpoint)
            url = args[0]
            self.assertEqual(url, expected_url)

            custom_kwargs = {self.CUSTOM_KWARG_NAME: uuid4().hex}
            args, kwargs = method(endpoint, **custom_kwargs)
            url = args[0]
            self.assertEqual(url, expected_url)
            self.assertEqual(kwargs[self.CUSTOM_KWARG_NAME], custom_kwargs[self.CUSTOM_KWARG_NAME])

    def test_method_get(self):
        endpoint = f'/get/{uuid4().hex}'
        expected_params = {'uuid': uuid4().hex}
        
        client = FakeTestClient()
        expected_url = self._join_path(client.api_base, endpoint)

        args, _ = client.get(endpoint)
        url, params = args
        self.assertEqual(url, expected_url)
        self.assertIsNone(params)

        args, _ = client.get(endpoint, expected_params)
        url, params = args
        self.assertEqual(url, expected_url)
        self.assertDictEqual(params, expected_params)

    def test_method_post(self):
        endpoint = f'/post/{uuid4().hex}'
        
        expected_data = {'data': uuid4().hex}
        expected_json = {'json': uuid4().hex}
        
        client = FakeTestClient()
        expected_url = self._join_path(client.api_base, endpoint)

        args, kwargs = client.post(endpoint)
        url = args[0]
        self.assertEqual(url, expected_url)
        self.assertEqual(set(kwargs.keys()), {'data', 'json'})

        _, kwargs = client.post(endpoint, data=expected_data, json=expected_json)
        self.assertEqual(kwargs['data'], expected_data)
        self.assertEqual(kwargs['json'], expected_json)

    def test_default_kwargs(self):
        with self.subTest('Test common "default_kwargs" behavior'):
            self.assertDictEqual(FakeTestClient.DEFAULT_KWARGS, {})

            client = FakeTestClient()
            self.assertIsInstance(client.default_kwargs, dict)
            self.assertDictEqual(client.default_kwargs, {})

            # Add default kwarg to instance
            expected_value = uuid4().hex
            client.default_kwargs[self.CUSTOM_KWARG_NAME] = expected_value

            for method in (client.get, client.post):
                # Default option should be passed to requests
                _, kwargs = method()
                self.assertEqual(kwargs[self.CUSTOM_KWARG_NAME], expected_value)

                # Should be used custom value if passed directly
                custom_value = {self.CUSTOM_KWARG_NAME: uuid4().hex}
                _, kwargs = method(**custom_value)
                self.assertEqual(kwargs[self.CUSTOM_KWARG_NAME], custom_value[self.CUSTOM_KWARG_NAME])

        with self.subTest('Test "DEFAULT_KWARGS"'):
            expected_value = uuid4().hex

            class AnotherTestClient(FakeTestClient):
                DEFAULT_KWARGS = {self.CUSTOM_KWARG_NAME: expected_value}

            self.assertTrue(AnotherTestClient.DEFAULT_KWARGS)

            client = AnotherTestClient()
            self.assertDictEqual(client.default_kwargs, AnotherTestClient.DEFAULT_KWARGS)

            for method in (client.get, client.post):
                _, kwargs = method()
                self.assertEqual(kwargs[self.CUSTOM_KWARG_NAME], expected_value)

    def test_default_headers(self):
        test_header_name = 'X-Test-Header'

        with self.subTest('Test common "headers" behavior'):
            self.assertFalse(FakeTestClient.DEFAULT_HEADERS)

            client = FakeTestClient()
            self.assertIsInstance(client.headers, dict)
            self.assertDictEqual(client.headers, {})

            # Add default kwarg to instance
            expected_value = uuid4().hex
            client.headers[test_header_name] = expected_value

            for method in (client.get, client.post):
                # Default headers should be passed to requests
                _, kwargs = method()
                headers = kwargs['headers']
                self.assertEqual(headers[test_header_name], expected_value)

                # Should be used custom value if passed directly
                custom_value = {test_header_name: uuid4().hex}
                _, kwargs = method(headers=custom_value)
                headers = kwargs['headers']
                self.assertEqual(headers[test_header_name], custom_value[test_header_name])

        with self.subTest('Test "DEFAULT_KWARGS"'):
            expected_value = uuid4().hex

            class AnotherTestClient(FakeTestClient):
                DEFAULT_HEADERS = {test_header_name: expected_value}

            self.assertTrue(AnotherTestClient.DEFAULT_HEADERS)

            client = AnotherTestClient()
            self.assertDictEqual(client.headers, AnotherTestClient.DEFAULT_HEADERS)

            for method in (client.get, client.post):
                _, kwargs = method()
                headers = kwargs['headers']
                self.assertEqual(headers[test_header_name], expected_value)

    def test_common_api_methods_mixin(self):
        class AnotherTestClient(FakeTestClient, CommonAPIMethodsMixin):
            pass

        client = AnotherTestClient()

        expected_url = self._join_path(client.api_base, '/health/ready')
        args, _ = client.ready()
        url = args[0]
        self.assertEqual(url, expected_url)

        client.live()
        client.version()
        