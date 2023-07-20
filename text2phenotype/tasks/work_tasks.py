import json
import os
from abc import (
    ABC,
    abstractmethod,
)
from datetime import (
    datetime,
    timezone,
)
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    TYPE_CHECKING,
)

from pydantic import (
    BaseModel,
    Field,
    validator,
)

from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import Environment
from text2phenotype.tasks.document_info import DocumentInfo
from text2phenotype.tasks.task_enums import (
    TaskEnum,
    TaskOperation,
    TaskStatus,
    WorkStatus,
    WorkType,
)
from text2phenotype.tasks.task_info import (
    OperationInfo,
    SummaryTask,
    TaskInfo,
)
from text2phenotype.tasks.task_message import TaskMessage
from text2phenotype.tasks.tasks_constants import TasksConstants

if TYPE_CHECKING:
    from text2phenotype.tasks.job_task import JobTask


class BaseTask(BaseModel, ABC):
    WORK_TYPE: ClassVar[WorkType] = None

    DEFAULT_CACHED_PROPERTIES: ClassVar[Set[str]] = {'work_type'}
    CACHED_PROPERTIES: ClassVar[Set[str]] = set()

    version: str = Environment.TASK_WORKER_VERSION
    model_version: Optional[str] = Field(None, nullable=True)
    started_at: datetime = Field(None, description='By default will be set a current datetime')
    completed_at: Optional[datetime] = None
    work_type: WorkType = None

    class Config:
        @staticmethod
        def schema_extra(schema: Dict[str, Any], model: Type['BaseTask']) -> None:
            total_duration_field = {
                'total_duration': {
                    'description': 'Total duration',
                    'format': 'float',
                    'title': 'Total Duration',
                    'type': 'number'
                }
            }
            schema.get('properties', {}).update(total_duration_field)

    @validator('version', pre=True, always=True)
    def check_version(cls, v):
        if v != Environment.TASK_WORKER_VERSION:
            operations_logger.warning(
                f'Actual task_worker version = "{Environment.TASK_WORKER_VERSION}" '
                f'but document has version = "{v}"')
        return v

    @validator('started_at', pre=True, always=True)
    def set_default_started_at(cls, v):
        return v or datetime.now(timezone.utc)

    @validator('work_type', pre=True, always=True)
    def set_work_type(cls, v):
        return cls.WORK_TYPE

    def dict(self, *args, **kwargs) -> dict:
        values = super().dict(*args, **kwargs)

        key = 'total_duration'
        values[key] = self.total_duration

        include = kwargs.get('include') or {key}
        exclude = kwargs.get('exclude') or {}

        if key in exclude or key not in include:
            del values[key]

        return values

    def to_json(self) -> str:
        return self.json()

    @property
    def total_duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()

    @property
    @abstractmethod
    def redis_key(self) -> str:
        pass

    @property
    @abstractmethod
    def metadata_file_key(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def get_metadata_file_key(cls, **kwargs) -> str:
        pass

    def create_task_message(self):
        return TaskMessage(work_type=self.WORK_TYPE,
                           redis_key=self.redis_key)

    @classmethod
    def from_json(cls,
                  json_str: Union[str, bytes]) -> Union['DocumentTask', 'ChunkTask', 'JobTask']:

        data = json.loads(json_str)
        work_type = WorkType(data['work_type'])

        if work_type is WorkType.document:
            return DocumentTask(**data)

        elif work_type is WorkType.chunk:
            return ChunkTask(**data)

        elif work_type is WorkType.job:
            from text2phenotype.tasks.job_task import JobTask
            return JobTask(**data)


class WorkTask(BaseTask):
    task_statuses: Dict[TaskEnum, TaskInfo] = {}
    performed_tasks: List[TaskEnum] = []

    @validator('task_statuses', pre=True, always=True)
    def set_task_statuses(cls, task_statuses):
        res = {}
        for task, data in task_statuses.items():
            if not isinstance(task, TaskEnum):
                res[TaskEnum(task)] = TaskInfo.create(**data)
            else:
                res[task] = data
        return res

    @property
    def redis_key(self) -> str:
        raise NotImplementedError()

    @property
    def metadata_file_key(self) -> str:
        raise NotImplementedError()

    @classmethod
    def get_metadata_file_key(cls, **kwargs) -> str:
        raise NotImplementedError()

    @property
    def complete(self) -> bool:
        return all(task_info.complete for task_info in self.task_statuses.values())

    @property
    def successful(self) -> bool:
        return self.check_successful()

    def check_successful(self, exclude: Optional[Tuple[Type[TaskInfo]]] = None) -> bool:
        all_work_tasks = self.task_statuses.values()

        # Exclude the set of tasks to examine that others were completed succesfully
        # For example, in the DischargeWorker we should exclude discharge task
        # because it actually does not finished
        if exclude:
            all_work_tasks = (t for t in all_work_tasks if not isinstance(t, exclude))

        return all(task_info.status is TaskStatus.completed_success for task_info in all_work_tasks)

    @property
    def status(self) -> WorkStatus:
        all_statuses = set(WorkStatus.from_task_status(task_info.status)
                           for task_info in self.task_statuses.values())

        if WorkStatus.not_started in all_statuses:
            if len(all_statuses) > 1:
                all_statuses.remove(WorkStatus.not_started)
                all_statuses.add(WorkStatus.processing)
            else:
                return WorkStatus.not_started

        if WorkStatus.processing in all_statuses:
            if WorkStatus.canceled in all_statuses:
                return WorkStatus.canceling

        elif {WorkStatus.canceled, WorkStatus.completed_failure} <= all_statuses:
            return WorkStatus.completed_failure

        return min(all_statuses)


class DocumentTask(WorkTask):
    """A class that holds a list of all tasks to be performed for a single document"""

    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    CACHED_PROPERTIES: ClassVar[Set[str]] = {
        'document_info',
        'job_id',
        'failed_tasks',
    }

    document_info: DocumentInfo = None
    operations: List[TaskOperation] = []
    operation_statuses: Dict[TaskOperation, OperationInfo] = {}
    summary_tasks: List[SummaryTask] = []
    job_id: str = None
    chunks: List[str] = []
    failed_chunks: Dict[str, List[TaskEnum]] = {}  # Chunk ID -> [list of failed tasks]
    chunk_tasks: List[TaskEnum] = []
    failed_tasks: List[TaskEnum] = []

    @validator('operation_statuses', pre=True, always=True)
    def set_operation_statuses(cls, v, values: Dict):
        operation_statuses = v or {}

        if not operation_statuses:
            for operation in values.get('operations', []):
                operation_info = OperationInfo.create(operation=operation)
                operation_statuses[operation_info.operation] = operation_info
            return operation_statuses

        result = {}

        for operation, data in operation_statuses.items():
            if isinstance(operation, TaskOperation):
                result[operation] = data
            else:
                operation_info = OperationInfo.create(**data)
                result[operation_info.operation] = operation_info

        return result

    def __repr__(self):
        return (f'Document ID: {self.document_info.document_id}\n'
                f'Job ID: {self.job_id}\n'
                f'Task Statuses: {self.task_statuses}\n'
                f'Processing complete: {self.complete}\n'
                f'Processing successful: {self.successful}\n')

    @property
    def redis_key(self) -> str:
        return self.document_id

    @property
    def document_id(self) -> str:
        return self.document_info.document_id

    @property
    def text_file_key(self):
        return self.document_info.text_file_key

    @property
    def metadata_file_key(self) -> str:
        return self.get_metadata_file_key(self.document_id)

    @classmethod
    def get_metadata_file_key(cls, document_id: str) -> str:
        doc_key = os.path.join(
            TasksConstants.STORAGE_DOCUMENTS_PREFIX,
            document_id,
            f'{document_id}.{TasksConstants.METADATA_FILE_EXTENSION}'
        )
        return doc_key

    def add_chunk(self, chunk: 'ChunkTask'):
        self.chunks.append(chunk.redis_key)

    def to_customer_facing_json(self, dest_prefix: str = '') -> str:
        operation_results = {}
        for op, op_info in self.operation_statuses.items():
            if op_info.results_file_key:
                op_info.results_file_key = os.path.join(dest_prefix, op_info.results_file_key)

            operation_results[op.value] = op_info.dict()

        document_info = json.loads(self.document_info.to_customer_facing_json())

        json_dictionary = {
            'started_at': datetime.isoformat(self.started_at) if self.started_at else None,
            'completed_at': datetime.isoformat(self.completed_at) if self.completed_at else None,
            'document_info': document_info,
            'operations': [o.value for o in self.operations],
            'operation_results': operation_results,
            'job_id': self.job_id,
            'total_duration': self.total_duration,
        }

        return json.dumps(json_dictionary)

    @classmethod
    def from_json(cls, data: Union[str, bytes]) -> 'DocumentTask':
        return cls.parse_raw(data)


class ChunkTask(WorkTask):
    """A class that holds a list of all tasks to be performed for a single document"""

    WORK_TYPE: ClassVar[WorkType] = WorkType.chunk

    document_id: str
    job_id: str
    text_span: List[int]
    chunk_num: int
    chunk_size: int
    text_file_key: str = None
    processing_duration: Optional[int] = None

    @validator('processing_duration', always=True)
    def set_processing_duration(cls, v, values):
        if not v:
            task_statuses = values.get('task_statuses') or {}
            # check complete status
            if not all(task_info.complete for task_info in task_statuses.values()):
                return None
            return int(sum(t.processing_duration for t in task_statuses.values()
                           if t.processing_duration is not None))
        return v

    @property
    def redis_key(self) -> str:
        return f'{self.document_id}_{str(self.chunk_num).zfill(5)}'

    @classmethod
    def from_json(cls, data: Union[str, bytes]) -> 'ChunkTask':
        return cls.parse_raw(data)

    @property
    def metadata_file_key(self) -> str:
        return self.get_metadata_file_key(self.document_id, self.redis_key)

    @classmethod
    def get_metadata_file_key(cls, document_id: str, redis_key: str) -> str:
        chunk_key = os.path.join(
            TasksConstants.STORAGE_DOCUMENTS_PREFIX,
            document_id,
            TasksConstants.STORAGE_CHUNKS_PREFIX,
            redis_key,
            f'{redis_key}.{TasksConstants.METADATA_FILE_EXTENSION}'
        )
        return chunk_key
