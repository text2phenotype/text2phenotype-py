from requests import Response

from text2phenotype.apiclients.base_client import (
    BaseClient,
    CommonAPIMethodsMixin,
    response_json,
)
from text2phenotype.constants.environment import Environment


class DischargeClient(BaseClient, CommonAPIMethodsMixin):
    ENVIRONMENT_VARIABLE = Environment.DISCHARGE_URL
    API_ENDPOINT = '/discharge/'

    def job_status(self, uuid: str) -> Response:
        return self.get(f'/job/status/{uuid}')

    def job_pickup(self, uuid: str) -> Response:
        return self.get(f'/job/pickup/{uuid}')

    def document_status(self, uuid: str) -> Response:
        return self.get(f'/document/status/{uuid}')

    def document_pickup(self, uuid: str) -> Response:
        return self.get(f'/document/pickup/{uuid}')

    def chunk_status(self, chunk_id: str) -> Response:
        return self.get(f'/chunk/status/{chunk_id}')

    def chunk_pickup(self, chunk_id: str) -> Response:
        return self.get(f'/chunk/pickup/{chunk_id}')


@response_json
class DischargeJsonClient(DischargeClient):
    """Implementation of "DischargeClient" returns JSON-deserialized response"""
    pass
