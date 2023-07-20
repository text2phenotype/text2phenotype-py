from typing import (
    Dict,
    Optional,
)

import requests

from text2phenotype.constants.environment import Environment

from .base_client import BaseClient


class MIPSAPIClient(BaseClient):
    ENVIRONMENT_VARIABLE = Environment.MIPS_API_BASE
    API_ENDPOINT = '/portal'

    COMMON_API = '/api/common/v1'
    INTEGRATION_API = '/api/integration/v1'

    def check_api_keys(self, api_key: str, x_forwarded_for: str) -> Optional[Dict]:
        """Check Api-Key in the MIPS and return Api-Key details (key_id, user_uuid, etc) for valid keys"""

        resp = self.post(f'{self.INTEGRATION_API}/api_keys/check/',
                         data={'api_key': api_key},
                         headers={'X-Forwarded-For': x_forwarded_for})

        return resp.json() if resp.ok else None

    def send_character_count(self,
                             api_key: str,
                             x_forwarded_for: str,
                             character_count: int,
                             endpoint: int) -> bool:
        data = dict(
            api_key=api_key,
            character_count=character_count,
            endpoint=endpoint
        )

        resp = self.post(f'{self.INTEGRATION_API}/billing/',
                         data=data,
                         headers={'X-Forwarded-For': x_forwarded_for})
        return resp.ok

    def remove_user_relations(self) -> requests.Response:
        headers = self.headers.copy()
        headers['X-Api-Key'] = Environment.INTERNAL_COMMUNICATION_API_KEY.value
        return self.post(f'{self.INTEGRATION_API}/management/users/remove_user_relations/',
                         headers=headers,
                         timeout=15)

    def live(self) -> requests.Response:
        return self.get(f'{self.INTEGRATION_API}/health/live/')

    def ready(self) -> requests.Response:
        return self.get(f'{self.INTEGRATION_API}/health/ready/')
