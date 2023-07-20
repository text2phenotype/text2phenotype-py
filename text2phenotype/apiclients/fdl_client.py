from typing import Dict

from text2phenotype.apiclients.base_client import BaseClient
from text2phenotype.common.log import operations_logger


class FDLClient(BaseClient):
    DEFAULT_HEADERS = {'Content-Type': 'plain/text'}

    def process_data(self, text: str) -> Dict[int, dict]:
        """Returns the dictionary with concepts which were found for each feature_type

        client = FDLClient('http://0.0.0.0:10000')
        result = client.process_data('text')

        result
        {
            '1': {
                'age': str()
                'content': list()
                'dob': str()
                'docId': str()
                'gender': str()
            },
            ...
        }
        """
        try:
            resp = self.post('/', data=text.encode('utf-8'))
            if resp.ok:
                return resp.json()
        except UnicodeEncodeError as ex:
            operations_logger.error(f'Encoding text as UTF-8 failed: {ex.reason}')

        return {}
