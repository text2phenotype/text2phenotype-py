import requests

from text2phenotype.constants.environment import Environment

from .base_client import BaseClient


class SandsClient(BaseClient):
    ENVIRONMENT_VARIABLE = Environment.SANDS_API_BASE
    API_ENDPOINT = '/app'

    ADMIN_API = '/api/admin'
    COMMON_API = '/api/common'
    PATIENT_API = '/api/patient'

    def remove_user_relations(self) -> requests.Response:
        headers = self.headers.copy()
        headers['X-Api-Key'] = Environment.INTERNAL_COMMUNICATION_API_KEY.value

        return self.post(f'{self.ADMIN_API}/users/remove_user_relations/',
                         headers=headers,
                         timeout=15)
