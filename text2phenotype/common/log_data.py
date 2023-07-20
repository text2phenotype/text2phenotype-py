import copy

from enum import Enum
from typing import List, Dict


class HIPAALogData:

    def __init__(self):
        self.ip_address: str = None
        self.user_id: int = None
        self.user_email: str = None
        self.url: str = None
        self.data_accessed: HIPAADataAccessed = HIPAADataAccessed()
        self.deidentified: bool = False
        self.message: str = None
        self.module: str = None  # override LogRecord default
        self.function_name: str = None  # override LogRecord default

    def to_dict(self) -> Dict:
        result = copy.copy(self.__dict__)
        result['data_accessed'] = self.data_accessed.to_dict()

        return result


class HIPAADataAccessed:

    def __init__(self):
        self.Patient: List[int] = []
        self.DocumentReference: List[int] = []
        self.HepCForm: List[int] = []
        self.MedicationStatement: List[int] = []
        self.Annotation: List[int] = []
        self.User: List[int] = []
        self.Destination: List[int] = []

    def to_dict(self) -> Dict:
        return copy.deepcopy(self.__dict__)


class ExtraKeys(Enum):
    TRANSACTION_ID = 'transaction_id'
    HIPAA_LOG_DATA = 'hipaa_log_data'
