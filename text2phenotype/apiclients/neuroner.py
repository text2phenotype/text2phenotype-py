from typing import Any

from text2phenotype.constants.environment import Environment

from .base_client import BaseClient


class NeuroNERClient(BaseClient):
    ENVIRONMENT_VARIABLE = Environment.NEURONER_API_BASE
    DEFAULT_KWARGS = {'verify': False}

    def _send_request(self, endpoint, text) -> Any:
        data = {'text': text}
        resp = self.post(endpoint, json=data)
        resp.raise_for_status()
        return resp.json()

    def deid(self, text: str):
        return self._send_request('/deid', text)

    def medication(self, text: str):
        return self._send_request('/medication', text)
