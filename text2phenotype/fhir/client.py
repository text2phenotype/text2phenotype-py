import json
import re
from typing import List
from urllib.parse import urlparse

import requests
from fhirclient.models.patient import Patient
from fhirclient.models.organization import Organization

from text2phenotype.common.log import operations_logger


class FhirError(Exception):
    pass


class FhirClient:
    """Client class used to connect to FHIR server and operate on resources."""
    def __init__(self, settings):
        self.api_base = settings['api_base']
        self.access_token = settings.get('access_token')

        if 'logger' in settings:
            self.logger = settings['logger']
        else:
            self.logger = operations_logger

        self.headers = {'Content-Type': 'application/json+fhir'}
        if self.access_token is not None:
            self.headers.update({'Authorization': 'Bearer '
                                 f'{self.api_base}'})
        if self.is_connected:
            self.logger.info(f'FHIR server connected and ready')
        else:
            raise FhirError('Unable to connect to FHIR server')

    @property
    def is_connected(self) -> bool:
        try:
            scheme = urlparse(self.api_base)[0]
            netloc = urlparse(self.api_base)[1]
            self.logger.debug(f'testing FHIR server connectivity {scheme}://{netloc}')
            resp = requests.get(f'{scheme}://{netloc}',
                                headers={'Content-Type': 'text/html'})
            if resp.status_code == 200 and resp.text == 'Welcome to the FHIR server':
                self.logger.debug(f'response={resp.text}')
                return True
        except Exception as e:
            self.logger.exception(e)
        return False

    def read_patients(self) -> List[Patient]:
        resp = requests.get(f'{self.api_base}/Patient',
                            headers=self.headers)
        if resp.status_code != 200:
            self.logger.error(f'response={resp.text}')
            raise FhirError
        patients = []
        for entry in resp.json()['entry']:
            p = Patient(entry['resource'])
            self.logger.debug(p)
            patients.append(p)
        return patients

    def read_patient(self, fhir_id: str) -> Patient:
        resp = requests.get(f'{self.api_base}/Patient/{fhir_id}',
                            headers=self.headers)
        if resp.status_code != 200:
            self.logger.error(f'response={resp.text}')
            raise FhirError
        return Patient(resp.json())

    def create_patient(self, p: Patient) -> str:
        self.logger.debug(f'creating patient resource: {p.as_json()}')
        resp = requests.post(f'{self.api_base}/Patient',
                             data=json.dumps(p.as_json()),
                             headers=self.headers)
        self.logger.debug(resp.text)
        if resp.status_code != 201:
            raise Exception('Resource not created!')
        else:
            div = resp.json()['text']['div']
            patient_id = re.search('Patient\/(\d*)\/', div).groups()[0]
        return patient_id

    def read_organizations(self) -> List[Organization]:
        resp = requests.get(f'{self.api_base}/Organization',
                            headers=self.headers)
        if resp.status_code != 200:
            self.logger.error(f'response={resp.text}')
            raise FhirError
        organizations = []
        for entry in resp.json()['entry']:
            o = Organization(entry['resource'])
            self.logger.debug(o)
            organizations.append(o)
        return organizations

    def read_organization(self, fhir_id: str) -> Organization:
        resp = requests.get(f'{self.api_base}/Organization/{fhir_id}',
                            headers=self.headers)
        if resp.status_code != 200:
            self.logger.error(f'response={resp.text}')
            raise FhirError
        return Organization(resp.json())

    def create_organization(self, o: Organization) -> str:
        resp = requests.post(f'{self.api_base}/Organization',
                             data=json.dumps(o.as_json()),
                             headers=self.headers)