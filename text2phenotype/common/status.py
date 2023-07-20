from enum import Enum, auto
from typing import Dict, Tuple, Optional
from http import HTTPStatus


class Status(Enum):
    dead = HTTPStatus.SERVICE_UNAVAILABLE
    alive = HTTPStatus.OK
    conditional = HTTPStatus.CREATED
    healthy = HTTPStatus.OK


class Component(Enum):
    database = auto()
    fhir = auto()
    fhir_azure_api = auto()
    queue = auto()
    intake = auto()
    ctakes = auto()
    biomed = auto()
    sands = auto()
    features = auto()
    neuroner = auto()
    text2phenotype_api = auto()


class StatusReport:
    def __init__(self, statuses: Optional[Dict[Component, Tuple[Status, Optional[str]]]] = None):
        self.statuses: Dict[Component, Tuple[Status, Optional[str]]] = statuses if statuses else {}

    def add_status(self, component: Component, status: Tuple[Status, Optional[str]]):
        self.statuses[component] = status

    def as_json(self) -> dict:
        return {k.name: (v[0].name, v[1]) for k, v in self.statuses.items()}
