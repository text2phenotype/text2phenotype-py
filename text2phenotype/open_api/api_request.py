import uuid

from typing import (
    List,
    Optional,
    Union,
)

from pydantic import (
    BaseModel,
    validator,
)

from text2phenotype.tasks.job_task import UserInfo
from text2phenotype.tasks.task_enums import TaskOperation


class APIRequest(BaseModel):
    document_text: Optional[str] = None
    document_url: Optional[str] = None
    source_bucket: Optional[str] = None
    source_directory: Optional[str] = None
    destination_directory: Optional[str] = None
    operations: Optional[List[TaskOperation]] = None
    user_info: Optional[UserInfo] = None
    app_destination: Optional[str] = None
    tid: Optional[str] = None
    biomed_version: Optional[str] = None
    model_version: Optional[str] = None
    deid_filter: Optional[str] = None

    @validator('tid', pre=True, always=True)
    def set_default_tid(cls, tid):
        return tid or str(uuid.uuid4())

    @classmethod
    def from_json(cls, json_str: Union[str, bytes, bytearray]) -> 'APIRequest':
        return cls.parse_raw(json_str)
