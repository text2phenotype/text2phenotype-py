import copy
import json

from datetime import date
from typing import List, Tuple


class Demographics:
    def __init__(self, **kwargs):
        self.ssn: List[Tuple[str, float]] = kwargs.get('ssn', [])
        self.mrn: List[Tuple[str, float]] = kwargs.get('mrn', [])
        self.pat_first: List[Tuple[str, float]] = kwargs.get('pat_first', [])
        self.pat_middle: List[Tuple[str, float]] = kwargs.get('pat_middle', [])
        self.pat_last: List[Tuple[str, float]] = kwargs.get('pat_last', [])
        self.pat_initials: List[Tuple[str, float]] = kwargs.get('pat_initials', [])
        self.pat_age: List[Tuple[str, float]] = kwargs.get('pat_age', [])
        self.pat_street: List[Tuple[str, float]] = kwargs.get('pat_street', [])
        self.pat_zip: List[Tuple[str, float]] = kwargs.get('pat_zip', [])
        self.pat_city: List[Tuple[str, float]] = kwargs.get('pat_city', [])
        self.pat_state: List[Tuple[str, float]] = kwargs.get('pat_state', [])
        self.pat_phone: List[Tuple[str, float]] = kwargs.get('pat_phone', [])
        self.pat_email: List[Tuple[str, float]] = kwargs.get('pat_email', [])
        self.insurance: List[Tuple[str, float]] = kwargs.get('insurance', [])
        self.facility_name: List[Tuple[str, float]] = kwargs.get('facility_name', [])
        self.sex: List[Tuple[str, float]] = kwargs.get('sex', [])
        self.dob: List[Tuple[date, float]] = kwargs.get('dob', [])
        self.dr_first: List[Tuple[str, float]] = kwargs.get('dr_first', [])
        self.dr_middle: List[Tuple[str, float]] = kwargs.get('dr_middle', [])
        self.dr_last: List[Tuple[str, float]] = kwargs.get('dr_last', [])
        self.dr_initials: List[Tuple[str, float]] = kwargs.get('dr_initials', [])
        self.dr_age: List[Tuple[str, float]] = kwargs.get('dr_age', [])
        self.dr_street: List[Tuple[str, float]] = kwargs.get('dr_street', [])
        self.dr_zip: List[Tuple[str, float]] = kwargs.get('dr_zip', [])
        self.dr_city: List[Tuple[str, float]] = kwargs.get('dr_city', [])
        self.dr_state: List[Tuple[str, float]] = kwargs.get('dr_state', [])
        self.dr_phone: List[Tuple[str, float]] = kwargs.get('dr_phone', [])
        self.dr_fax: List[Tuple[str, float]] = kwargs.get('dr_fax', [])
        self.dr_email: List[Tuple[str, float]] = kwargs.get('dr_email', [])
        self.dr_id: List[Tuple[str, float]] = kwargs.get('dr_id', [])
        self.dr_org: List[Tuple[str, float]] = kwargs.get('dr_org', [])
        self.ethnicity: List[Tuple[str, float]] = kwargs.get('ethnicity', [])
        self.race: List[Tuple[str, float]] = kwargs.get('race', [])
        self.language: List[Tuple[str, float]] = kwargs.get('language', [])
        self.pat_full_name: List[Tuple[str, float]] = kwargs.get('pat_full_name', [])
        self.dr_full_names: List[Tuple[str, float]] = kwargs.get('dr_full_name', [])

    def add_entry(self, demographics_type: str, text: str, score: float) -> None:
        current = getattr(self, demographics_type.lower())
        current.append((text, score))

    def add_entry_list(self, demographic_type: str, entry_list: list):
        current = getattr(self, demographic_type.lower())
        current.extend(entry_list)

    def to_dict(self) -> dict:
        return copy.deepcopy(vars(self))

    @staticmethod
    def highest_prob(entries: List[tuple]):
        if len(entries) > 1:
            return [sorted(entries, key=lambda token: token[1])[0]]
        else:
            return entries

    def to_final_dict(self):
        return {'ssn': self.ssn,
                'mrn': self.mrn,
                'sex': self.highest_prob(self.sex),
                'dob': self.highest_prob(self.dob),
                'pat_first': self.highest_prob(self.pat_first),
                'pat_last': self.highest_prob(self.pat_last),
                'pat_age': self.pat_age,
                'pat_street': self.pat_street,
                'pat_zip': self.pat_zip,
                'pat_city': self.pat_city,
                'pat_state': self.pat_state,
                'pat_phone': self.pat_phone,
                'pat_email': self.pat_email,
                'insurance': self.insurance,
                'facility_name': self.facility_name,
                'dr_first': self.dr_first,
                'dr_last': self.dr_last,
                'pat_full_name': self.highest_prob(self.pat_full_name),
                'dr_full_names': self.dr_full_names,
                'race': self.race,
                'ethnicity': self.ethnicity}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @property
    def first_name(self):
        if self.pat_first:
            return max(self.pat_first, key=lambda token: token[1])[0]
        else:
            return None

    @property
    def last_name(self):
        if self.pat_last:
            return max(self.pat_last, key=lambda token: token[1])[0]
        else:
            return None

    @property
    def date_of_birth(self):
        if self.dob:
            return max(self.dob, key=lambda token: token[1])[0]
        else:
            return None

    @property
    def gender(self):
        if self.sex:
            return max(self.sex, key=lambda token: token[1])[0]

    def __getitem__(self, item):
        if hasattr(self, item):
            return getattr(self, item)
