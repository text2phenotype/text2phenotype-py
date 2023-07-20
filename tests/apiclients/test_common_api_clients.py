import json
import unittest
from unittest.mock import patch
from uuid import uuid4

from text2phenotype.apiclients import (
    IntakeClient,
    DischargeClient,
    SandsClient,
    MIPSAPIClient,
)
from text2phenotype.apiclients.base_client import BaseClient
from text2phenotype.constants.environment import Environment


class BaseTestCase(unittest.TestCase):
    """Test API clients by check arguments passed to "requests" library"""
    __test__ = False

    REQUESTS_TARGET = 'text2phenotype.apiclients.base_client.requests'

    API_CLIENT_CLASS = None
    ENVIRONMENT_VARIABLE = None

    def setUp(self) -> None:
        super().setUp()

        self.PAYLOAD = {'uuid': uuid4().hex}

        self.client: BaseClient = self.API_CLIENT_CLASS()

        requests_patcher = patch(self.REQUESTS_TARGET)
        self.requests_mock = requests_patcher.start()
        self.addCleanup(requests_patcher.stop)

    def tearDown(self) -> None:
        super().tearDown()
        self.requests_mock.reset_mock()

    def assert_requests_call(self,
                             method,
                             expected_endpoint,
                             headers=None,
                             **expected_kwargs):

        method_func = getattr(self.requests_mock, method)
        args, kwargs = method_func.call_args

        # Check endpoint
        url = args[0]
        url_endpoint = url[-len(expected_endpoint):]
        self.assertEqual(url_endpoint, expected_endpoint)

        # Check headers
        if headers is not None:
            self.assert_headers(kwargs, headers)

        # Check passed kwargs
        for key, val in expected_kwargs.items():
            self.assertEqual(kwargs[key], val)

        return args, kwargs

    def assert_headers(self, kwargs, expected_headers):
        self.assertIn('headers', kwargs)
        headers = kwargs.get('headers', {})

        for key, val in expected_headers.items():
            self.assertIn(key, headers)
            self.assertEqual(headers[key], val)

    def requests_get_call_args(self):
        return self.requests_mock.get.call_args

    def requests_post_call_args(self):
        return self.requests_mock.post.call_args

    def test_api_base(self):
        # Check common part of client's api base
        expected_api_base = self.ENVIRONMENT_VARIABLE.value
        client_api_base = self.client.api_base[:len(expected_api_base)]
        self.assertEqual(client_api_base, expected_api_base)


class TestIntakeClient(BaseTestCase):
    __test__ = True

    API_CLIENT_CLASS = IntakeClient
    ENVIRONMENT_VARIABLE = Environment.INTAKE_URL

    def test_process_document_text(self):
        self.client.process_document_text(self.PAYLOAD)
        self.assert_requests_call('post', '/document/process/text', json=self.PAYLOAD)

    def test_process_document_file(self):
        self.client.process_document_file(content=b'123', filename='123.txt', body=self.PAYLOAD)
        _, kwargs = self.assert_requests_call('post', '/document/process/file')

        expected_payload = (None, json.dumps(self.PAYLOAD), 'application/json')
        self.assertEqual(kwargs['files']['payload'], expected_payload)

    def test_process_document_corpus(self):
        self.client.process_document_corpus(self.PAYLOAD)
        self.assert_requests_call('post', '/document/process/corpus', json=self.PAYLOAD)

    def test_reprocess_job(self):
        job_id = uuid4().hex
        self.client.reprocess_job(job_id, self.PAYLOAD)

        expected_endpoint = f'/job/reprocess/{job_id}'
        self.assert_requests_call('post', expected_endpoint, json=self.PAYLOAD)

    def test_stop_job(self):
        job_id = uuid4().hex
        self.client.stop_job(job_id, self.PAYLOAD)

        expected_endpoint = f'/job/stop/{job_id}'
        self.assert_requests_call('post', expected_endpoint, json=self.PAYLOAD)

    def test_purge_job(self):
        job_id = uuid4().hex
        self.client.purge_job(job_id, self.PAYLOAD)

        expected_endpoint = f'/job/purge/{job_id}'
        self.assert_requests_call('post', expected_endpoint, json=self.PAYLOAD)


class TestDischargeClient(BaseTestCase):
    __test__ = True

    API_CLIENT_CLASS = DischargeClient
    ENVIRONMENT_VARIABLE = Environment.DISCHARGE_URL

    GET_METHODS = [
        ('job_status', '/job/status/{}'),
        ('job_pickup', '/job/pickup/{}'),
        ('document_status', '/document/status/{}'),
        ('document_pickup', '/document/pickup/{}'),
        ('chunk_status', '/chunk/status/{}'),
        ('chunk_pickup', '/chunk/pickup/{}'),
    ]

    def test_all_get_methods(self):
        for func_name, endpoint_tpl in self.GET_METHODS:
            func = getattr(self.client, func_name)
            self.assertIsNotNone(func)

            test_uuid = uuid4().hex
            func(test_uuid)

            self.assert_requests_call('get', endpoint_tpl.format(test_uuid))


class RemoveUserRelationsTest:
    REMOVE_USER_RELATIONS_BASE = ''

    def test_remove_user_relations(self):
        self.assertTrue(self.REMOVE_USER_RELATIONS_BASE)
        expected_headers = {'X-Api-Key': Environment.INTERNAL_COMMUNICATION_API_KEY.value}

        self.client.remove_user_relations()
        self.assert_requests_call('post',
                                  f'{self.REMOVE_USER_RELATIONS_BASE}/users/remove_user_relations/',
                                  headers=expected_headers,
                                  timeout=15)


class TestSandsClient(BaseTestCase, RemoveUserRelationsTest):
    __test__ = True

    API_CLIENT_CLASS = SandsClient
    ENVIRONMENT_VARIABLE = Environment.SANDS_API_BASE

    REMOVE_USER_RELATIONS_BASE = '/api/admin'


class TestMIPSClient(BaseTestCase, RemoveUserRelationsTest):
    __test__ = True

    API_CLIENT_CLASS = MIPSAPIClient
    ENVIRONMENT_VARIABLE = Environment.MIPS_API_BASE

    X_FORWARDED_FOR = uuid4().hex
    EXPECTED_HEADERS = {'X-Forwarded-For': X_FORWARDED_FOR}

    REMOVE_USER_RELATIONS_BASE = '/portal/api/integration/v1/management'

    def test_check_api_keys(self):
        api_key = uuid4().hex
        expected_data = {'api_key': api_key}

        self.client.check_api_keys(api_key, self.X_FORWARDED_FOR)
        self.assert_requests_call('post',
                                  '/portal/api/integration/v1/api_keys/check/',
                                  data=expected_data,
                                  headers=self.EXPECTED_HEADERS)

    def test_send_character_count(self):
        api_key = uuid4().hex
        count = 123
        endpoint = f'/{uuid4().hex}'

        expected_data = {
            'api_key': api_key,
            'character_count': count,
            'endpoint': endpoint,
        }

        self.client.send_character_count(api_key, self.X_FORWARDED_FOR, count, endpoint)
        self.assert_requests_call('post',
                                  '/portal/api/integration/v1/billing/',
                                  data=expected_data,
                                  headers=self.EXPECTED_HEADERS)
