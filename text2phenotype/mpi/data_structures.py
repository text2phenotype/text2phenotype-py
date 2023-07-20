from typing import List, Dict
import pandas as pd


class MPIInput:
    DOC_ATTR = 'document_id'
    FILES_ATTR = 'permitted_files'

    def __init__(self, document_id: int = None, permitted_files: List[int] = None):
        self.document_id = document_id
        self.permitted_files = permitted_files or []

    @classmethod
    def from_dict(cls, data: Dict):
        result = cls()
        result.document_id = data.get(cls.DOC_ATTR)
        result.permitted_files = data.get(cls.FILES_ATTR)
        return result

    def to_dict(self) -> Dict:
        data = {self.DOC_ATTR: self.document_id,
                self.FILES_ATTR: self.permitted_files}
        return data


class MPIMatch:
    DOC_ATTR = 'doc_id'
    PROB_ATTR = 'probability'

    def __init__(self, doc_id: int = None, probability: float = None):
        self.doc_id = doc_id
        self.probability = probability

    @classmethod
    def from_dict(cls, data: Dict):
        result = cls()

        if cls.DOC_ATTR in data:
            result.doc_id = int(data[cls.DOC_ATTR])

        if cls.PROB_ATTR in data:
            result.probability = float(data[cls.PROB_ATTR])

        return result

    def to_dict(self) -> Dict:
        data = {self.DOC_ATTR: self.doc_id,
                self.PROB_ATTR: self.probability}
        return data

    @classmethod
    def from_df_row(cls, row: pd.Series):
        result = cls()
        result.doc_id = row.doc_id_2
        result.probability = row.predicted
        return result
