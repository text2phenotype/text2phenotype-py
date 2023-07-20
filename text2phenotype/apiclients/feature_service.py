import json
from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

from text2phenotype.apiclients.base_client import BaseClient
from text2phenotype.common.featureset_annotations import (
    MachineAnnotation,
    Vectorization,
)
from text2phenotype.constants.environment import Environment
from text2phenotype.constants.features import FeatureType
from text2phenotype.open_api.base_model import Model


class FeatureRequest(Model):
    def __init__(self, **kwargs):
        self.swagger_types = {
            'text': str,
            'features': List[FeatureType],
            'tokens': Dict[str, object],
            'tid': str,
            'metadata': Dict[str, object]
        }

        self.attribute_map = {
            'text': 'text',
            'features': 'features',
            'tokens': 'tokens',
            'tid': 'tid',
            'metadata': 'metadata'
        }

        self._text: str = kwargs.get('text')
        self._features: Optional[List[FeatureType]] = self.convert_enum_list(kwargs.get('features'), FeatureType)
        self._tokens: Dict[str, object] = kwargs.get('tokens')
        self._tid: str = kwargs.get('tid')
        self._metadata: dict = kwargs.get('metadata')

    def as_json(self):
        return json.dumps({'text': fr"{self.text}",
                           'tokens': self.tokens,
                           'features': self.features,
                           'tid': self.tid,
                           'metadata': self.metadata})

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text):
        self._text = text

    @property
    def features(self) -> Optional[List[FeatureType]]:
        if type(self._features) is not list:
            self._features = list(self._features)
        return self._features

    @features.setter
    def features(self, features: Optional[List[FeatureType]]):
        self._features = self.convert_enum_list(features, FeatureType)

    @property
    def tokens(self) -> Dict[str, object]:
        return self._tokens

    @tokens.setter
    def tokens(self, tokens):
        self._tokens = tokens

    @property
    def tid(self) -> str:
        return self._tid

    @tid.setter
    def tid(self, tid: str):
        self._tid = tid

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value


class FeatureServiceClient(BaseClient):
    ENVIRONMENT_VARIABLE = Environment.FEAT_API_BASE
    DEFAULT_HEADERS = {'Content-Type': 'application/json'}

    def annotate(self, text: str, features: Set[FeatureType] = None, tid: str = None) -> MachineAnnotation:
        feature_request = FeatureRequest(text=text, features=features, tid=tid)
        return MachineAnnotation(json_dict_input=self._send_request('feature_set/annotate', feature_request))

    def annotate_vectorize(self, text: str, features: Set[FeatureType] = None,
                           tid: str = None) -> Tuple[MachineAnnotation, Vectorization]:
        feature_request = FeatureRequest(text=text, features=features, tid=tid)
        json_response = self._send_request('feature_set/annotatevectorize', feature_request)
        return (MachineAnnotation(json_dict_input=json_response['annotations']),
                Vectorization(json_input_dict=json_response['vectors']))

    def vectorize(self,
                  tokens: MachineAnnotation,
                  features: Set[FeatureType] = None,
                  tid: str = None) -> Vectorization:

        feature_request = FeatureRequest(tokens=tokens.to_dict(), features=features, tid=tid)
        vectorization = Vectorization(json_input_dict=self._send_request('feature_set/vectorize', feature_request))
        return vectorization

    def live(self) -> Optional[dict]:
        response = self.get('/health/live')
        if response.ok:
            return response.json()
        response.raise_for_status()

    def ready(self) -> Optional[dict]:
        response = self.get('/health/ready')
        if response.ok:
            return response.json()
        response.raise_for_status()

    def version(self) -> Optional[dict]:
        response = self.get('/version')
        if response.ok:
            return response.json()
        response.raise_for_status()

    def _send_request(self, endpoint: str, feature_request: FeatureRequest) -> Optional[dict]:
        """
        :raise HTTPError if response status code is bad
        """
        response = self.post(endpoint,
                             data=feature_request.as_json(),
                             tid=feature_request.tid)
        if response.ok:
            return response.json()
        response.raise_for_status()
