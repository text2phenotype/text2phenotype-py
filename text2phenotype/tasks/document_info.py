from typing import Optional

from pydantic import BaseModel


class DocumentInfo(BaseModel):
    document_id: str
    source: str  # original source path to document in customer storage
    text_file_key: Optional[str] = None  # path to original document text in our storage
    source_file_key: Optional[str] = None  # path to original document object in our storage
    source_hash: Optional[str] = None  # hash of the original document content in original format (pdf or txt)
    document_size: Optional[int] = None  # the length of document content in bytes
    tid: str

    def to_json(self) -> str:
        return self.json()

    def to_customer_facing_json(self) -> str:
        fields = {
            'document_id',
            'source',
            'source_hash',
            'tid',
        }
        return self.json(include=fields)
