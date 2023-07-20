from collections import defaultdict
import json
import base64

from typing import (
    Callable,
    List,
    Union,
    Tuple,
    Optional,
    Dict,
)

from text2phenotype.apiclients.base_client import BaseClient
from text2phenotype.common.speech import chunk_text
from text2phenotype.common.log import operations_logger
from text2phenotype.common.version_info import VersionInfo
from text2phenotype.constants.common import VERSION_INFO_KEY
from text2phenotype.constants.environment import Environment
from text2phenotype.mpi.data_structures import (
    MPIInput,
    MPIMatch,
)
from text2phenotype.ocr.data_structures import (
    OCRPageInfo,
    OCRCoordinate,
)

BASE64_TAG = 'BASE64::'


def validate_annotation_text(annotation, original_text):
    annot_range = annotation['range']
    annot_text = annotation['text'].replace('\n', ' ')

    actual = original_text[annot_range[0]:annot_range[1]].replace('\n', ' ')

    if not actual == annot_text:
        raise Exception(f'Expected {annot_text}; was {actual}.')


def aggregate_summary(aggregate, response, original_text, offset):
    if not aggregate:
        return response

    for aspect, annotations in response.items():
        if aspect not in aggregate:
            aggregate[aspect] = []

        for annotation in annotations:
            annotation['range'][0] += offset
            annotation['range'][1] += offset

            if aspect == 'Medication':
                if len(annotation['medStrengthNum']):
                    annotation['medStrengthNum'][1] += offset
                    annotation['medStrengthNum'][2] += offset

                if len(annotation['medStrengthUnit']):
                    annotation['medStrengthUnit'][1] += offset
                    annotation['medStrengthUnit'][2] += offset

            validate_annotation_text(annotation, original_text)

        aggregate[aspect].extend(annotations)

    return aggregate


def aggregate_single_summary_aspect(aggregate, response, original_text, offset):
    if not aggregate:
        return response

    for annotation in response:
        annotation['range'][0] += offset
        annotation['range'][1] += offset

        validate_annotation_text(annotation, original_text)

        aggregate.append(annotation)

    return aggregate


def aggregate_redact(aggregate, response, original_text, offset):
    if aggregate is None:
        return response

    if not response:
        return aggregate

    return aggregate + response


def aggregate_phi_tokens(aggregate, response, original_text, offset):
    for phi in response:
        phi['range'][0] += offset
        phi['range'][1] += offset

        validate_annotation_text(phi, original_text)

        aggregate.append(phi)

    return aggregate


def aggregate_demographics(aggregate, response, original_text=None, offset=None):
    if 'demographics' not in aggregate:
        aggregate = response
    else:
        if response.get('pat_names'):
            if not aggregate['pat_names']:
                aggregate['pat_names'] = response['pat_names']
            else:
                aggregate['pat_names'].extend(response['pat_names'])
        if response.get('demographics'):
            for key, value in response['demographics'].items():
                if key in aggregate['demographics']:

                    aggregate['demographics'][key].extend(value)
                else:
                    aggregate['demographics'][key] = value
        if (VERSION_INFO_KEY in aggregate and VERSION_INFO_KEY in response):
            version_info_list_dict = aggregate[VERSION_INFO_KEY]
            response_info = response[VERSION_INFO_KEY]
            if isinstance(version_info_list_dict, dict):
                version_info_list_dict = [version_info_list_dict]
                operations_logger.warning('demographic chunk still using Dict Version Info aggregate')
            if isinstance(response_info, dict):
                response_info = [response_info]
                operations_logger.warning('demographic chunk still using Dict Version Info response')
            agg_version_info = VersionInfo(**version_info_list_dict[0])
            response_version_info = VersionInfo(**response_info[0])
            if (agg_version_info.product_version != response_version_info.product_version and
                    agg_version_info.product_id==response_version_info.product_id):
                raise ValueError('Biomed Versions were not consistent across chunks')
    return aggregate


class BiomedRequest:
    def __init__(self,
                 text: Optional[str] = None,
                 data: Optional[object] = None,
                 models: Optional[Dict[str, List[str]]] = None,
                 tid: Optional[str] = None):
        self.text = text
        self.data = data
        self.models = models
        self.tid = tid

    def as_json(self):
        return json.dumps({'text': fr"{self.text}", 'data': self.data, 'models': self.models, 'tid': self.tid})


class BioMedMetadataServiceClient(BaseClient):
    ENVIRONMENT_VARIABLE = Environment.METADATA_SERVICE_API_BASE
    API_ENDPOINT = '/'
    DEFAULT_HEADERS = {'Content-Type': 'application/json'}

    def get_required_features(self, operations: list, biomed_version: str = None):
        biomed_request = BiomedRequest(data={'operations': operations, 'biomed_version': biomed_version})
        return self._send_request('requiredfeatures', biomed_request)

    def live(self) -> Optional[Union[dict, bool]]:
        response = self.get('/health/live')
        response.raise_for_status()
        return True if response.status_code == 204 else response.json()

    def ready(self) -> Optional[dict]:
        response = self.get('/health/ready', timeout=3)
        response.raise_for_status()
        return response.json()

    def version(self) -> Optional[dict]:
        response = self.get('/version')
        response.raise_for_status()
        return response.json()

    def _send_request(self,
                      endpoint: str,
                      biomed_request: BiomedRequest) -> Optional[Union[str, dict, List[dict]]]:

        operations_logger.debug(f'Sending request to Biomed Metadata Service endpoint {self.api_base}/{endpoint}...',
                                tid=biomed_request.tid)
        response = self.post(endpoint, data=biomed_request.as_json())
        response.raise_for_status()
        return response.json()


class BioMedClient(BioMedMetadataServiceClient):
    ENVIRONMENT_VARIABLE = Environment.BIOMED_API_BASE

    def __init__(self,
                 api_base: Optional[str] = None,
                 max_doc_word_count: Optional[int] = None):
        """Client to send HTTP requests to a Biomed service endpoint.

        :param max_doc_word_count: The maximum length of text to process at a time.
            NOTE this default value of 10k is too low, recommend setting to 100000
        """
        super().__init__(api_base)

        if max_doc_word_count is None:
            max_doc_word_count = Environment.BIOMED_MAX_DOC_WORD_COUNT.value

        self.max_word_count = max_doc_word_count
        self.models = self._get_models()

    def autofill_hepc_form(self, text: str, tid: str = None) -> dict:
        biomed_request = BiomedRequest(text=text, models=self.models, tid=tid)
        return self._send_request('autofillhepcform', biomed_request)

    def get_clinical_summary(self, text: str, tid: str = None) -> dict:
        biomed_request = BiomedRequest(text=text, models=self.models, tid=tid)
        return self._send_request('summary/clinical', biomed_request)

    def get_oncology_summary(self, text: str, tid: str = None) -> dict:
        biomed_request = BiomedRequest(text=text, models=self.models, tid=tid)
        return self._send_request('summary/oncology', biomed_request)

    def get_phi_tokens(self, text: str, tid: str = None) -> List[dict]:
        biomed_request = BiomedRequest(text=text, models=self.models, tid=tid)
        return self._send_request('deid/phitokens', biomed_request)

    def get_phi_coordinates(self,
                            ocr_pages: List[OCRPageInfo],
                            tid: str = None) -> Tuple[List[OCRCoordinate], List[dict]]:
        json_body = json.dumps([page.to_dict() for page in ocr_pages])
        biomed_request = BiomedRequest(data=json_body, models=self.models, tid=tid)
        response = self._send_request('deid/phicoordinates', biomed_request)
        json_response = json.loads(response)
        coordinates_and_tokens = ([OCRCoordinate.from_dict(coord) for coord in json_response[0]], json_response[1])
        return coordinates_and_tokens

    def get_redacted_text(self, text: str, tid: str = None):
        biomed_request = BiomedRequest(text, tid=tid)
        return self._send_request('deid/redact_text', biomed_request)

    def get_matching_documents(self, mpi_input: MPIInput, tid: str = None) -> List[dict]:
        json_body = json.dumps(mpi_input.to_dict())
        biomed_request = BiomedRequest(data=json_body, models=self.models, tid=tid)
        response = self._send_request('patientmatching', biomed_request)
        json_response = json.loads(response)
        mpi_output = [MPIMatch.from_dict(resp) for resp in json_response]
        return mpi_output

    def get_demographics(self, text: str, tid: str = None) -> dict:
        biomed_request = BiomedRequest(text=text, models=self.models, tid=tid)
        return self._send_request('demographics', biomed_request)

    def run_train_test_job(self, model_metadata: dict, job_metadata: dict, data_source: dict, tid: str = None):
        biomed_request = BiomedRequest(data={**model_metadata, **job_metadata, **data_source}, tid=tid)
        return self._send_request('traintest', biomed_request)

    def get_oncology_tokens(self, text: str, tid: str = None) -> List[dict]:
        biomed_request = BiomedRequest(text=text, models=self.models, tid=tid)

        return self._send_request('oncology', biomed_request)

    @staticmethod
    def _get_models() -> Optional[Dict]:
        models = Environment.BIOMED_MODELS.value
        if not models:
            return None

        if models.startswith(BASE64_TAG):
            temp = models.strip(BASE64_TAG)
            models = base64.b64decode(temp.encode('utf-8')).decode('utf-8')

        models = json.loads(models)
        operations_logger.debug(f'Using Biomed models: {models}')

        return models

    def _send_request(self,
                      endpoint: str,
                      biomed_request: BiomedRequest) -> Union[str, dict, List[dict]]:

        operations_logger.debug(f'Sending request to Biomed endpoint {self.api_base}/{endpoint}...',
                                tid=biomed_request.tid)

        if self.max_word_count:
            if endpoint == 'summary/clinical' or endpoint == 'summary/oncology':
                return self.__chunk_request(endpoint, biomed_request, aggregate_summary, defaultdict(list))
            elif endpoint == 'deid/redact_text':
                return self.__chunk_request(endpoint, biomed_request, aggregate_redact, "")
            elif endpoint == 'deid/phitokens':
                return self.__chunk_request(endpoint, biomed_request, aggregate_phi_tokens, [])
            elif endpoint == 'demographics':
                return self.__chunk_request(endpoint, biomed_request, aggregate_demographics, dict())
            elif endpoint == 'oncology':
                return self.__chunk_request(endpoint, biomed_request, aggregate_single_summary_aspect, [])

        return self.__send_that_request(endpoint, biomed_request)

    def __send_that_request(self,
                            endpoint: str,
                            biomed_request) -> Optional[Union[str, dict, List[dict]]]:
        response = self.post(endpoint, data=biomed_request.as_json())
        if response.ok:
            return response.json()
        response.raise_for_status()

    def __chunk_request(self,
                        endpoint: str,
                        biomed_request: BiomedRequest,
                        aggregate_fx: Callable,
                        aggregate: Union[dict, str, list]) -> Union[str, dict, List[dict]]:

        chunks = chunk_text(biomed_request.text, self.max_word_count)

        if len(chunks) == 1:
            return self.__send_that_request(endpoint, biomed_request)

        # TODO: threading?
        num_chunks = len(chunks)
        for i, chunk in enumerate(chunks, start=1):
            span, text = chunk
            chunk_request = BiomedRequest(text,
                                          biomed_request.data,
                                          biomed_request.models,
                                          biomed_request.tid)

            operations_logger.debug(f'Sending chunk {i} of {num_chunks} (span: {span}) to endpoint {endpoint}...')
            response = self.__send_that_request(endpoint, chunk_request)

            aggregate = aggregate_fx(aggregate, response, biomed_request.text, span[0])

        return aggregate
