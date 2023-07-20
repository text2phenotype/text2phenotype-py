from typing import Optional

from pydantic import (
    BaseModel,
    validator,
)
import semantic_version

from text2phenotype import tasks
from text2phenotype.tasks.task_enums import WorkType


class TaskMessage(BaseModel):
    work_type: WorkType = None
    redis_key: str = None
    is_reprocess_task: Optional[bool] = None
    sender: Optional[str] = None
    version: Optional[str] = None

    @validator('version', pre=True, always=True)
    def check_version(cls, v):
        if not v:
            return tasks.__version__
        elif not semantic_version.validate(v):
            raise ValueError(f'Invalid value for version, {v}')
        elif not semantic_version.Version(v) in tasks.version_spec:
            raise ValueError(f'Service version ({tasks.__version__}) does not compatible '
                             f'with the request version ({v}), spec {tasks.version_spec}')
        return v

    @classmethod
    def from_json(cls, json_str: str) -> 'TaskMessage':
        return cls.parse_raw(json_str)

    def to_json(self) -> str:
        return self.json(exclude_none=True)

    def __repr__(self):
        return (f"Work Type: {self.work_type.value if self.work_type else None}, "
                f"Redis Key: {self.redis_key} "
                f"Sender: {self.sender}")

    def __hash__(self):
        return hash(self.to_json())


class OCRTaskMessage(TaskMessage):
    page_offset: Optional[int] = None
    is_pdf_chunk: Optional[bool] = None
