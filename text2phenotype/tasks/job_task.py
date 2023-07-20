import os
import uuid
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from typing import (
    ClassVar,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Union,
)

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    root_validator,
    validator,
)

from text2phenotype.constants.deid import DeidGroupings
from text2phenotype.constants.features import FeatureType
from text2phenotype.open_api.models import ReprocessOptions
from text2phenotype.tasks.task_enums import (
    TaskOperation,
    WorkStatus,
    WorkType,
)
from text2phenotype.tasks.task_info import SummaryTask
from text2phenotype.tasks.utils import get_manifest_job_storage_key
from text2phenotype.tasks.work_tasks import BaseTask


class JobDocumentInfo(BaseModel):
    status: WorkStatus = None
    filename: str = None


class UserInfo(BaseModel):
    key_id: Optional[str] = Field(None, nullable=True)
    user_uuid: Optional[str] = Field(None, nullable=True)
    full_name: Optional[str] = Field(None, nullable=True)
    primary_email: Optional[str] = Field(None, nullable=True)


class UserAction(str, Enum):
    """Enum of values used to log user actions"""
    create = 'create'
    reprocess = 'reprocess'
    cancel = 'cancel'
    purge = 'purge'


class UserActionLogEntry(BaseModel):
    action: UserAction
    created_at: datetime = None
    user_info: UserInfo = None

    @validator('created_at', pre=True)
    def set_default_create_at(v):
        return v or datetime.now(timezone.utc)


class JobTask(BaseTask):
    WORK_TYPE: ClassVar[WorkType] = WorkType.job
    CACHED_PROPERTIES: ClassVar[Set[str]] = {
        'job_id',
        'user_canceled',
        'stop_documents_on_failure',
        'reprocess_options',
        'model_version',
    }

    _processed_files: Optional[Dict[str, str]] = PrivateAttr(None)

    job_id: str = Field(None, description='By default will be generated random UUID')
    document_info: Dict[str, JobDocumentInfo] = {}  # document_id -> JobDocumentInfo

    # Used in the Discharge service.
    # This field is required to support old manifests, created without "document_info".
    legacy_document_ids: Optional[List[str]] = Field(None, alias='document_ids')

    operations: List[TaskOperation] = []
    summary_tasks: List[SummaryTask] = []
    required_features: Set[FeatureType] = []
    bulk_source_bucket: str = None
    bulk_source_directory: str = None

    deid_filter: Optional[str] = None
    bulk_destination_directory: Optional[str] = ''
    user_info: Optional[UserInfo] = None
    app_destination: Optional[str] = None
    biomed_version: Optional[str] = Field(None, nullable=True)
    reprocess_options: Optional[ReprocessOptions] = None

    user_canceled: Optional[bool] = None
    stop_documents_on_failure: Optional[bool] = True

    user_actions_log: List[UserActionLogEntry] = []

    @root_validator(pre=True)
    def check_legacy_fields(cls, values):
        # MAPPS-183
        # Fill the "document_info" section if it's empty.
        # This situation can occurs if it's an old version of job manifest, without
        # the "document_info" section.

        document_info = values.setdefault('document_info', {})
        processed_files = values.get('processed_files')

        if processed_files and not document_info:
            for filename, doc_id in processed_files.items():
                doc_info = JobDocumentInfo(status=WorkStatus.not_started,
                                           filename=filename)
                document_info[doc_id] = doc_info.dict()

        # MAPPS-402
        # Support obsolete "processed_files" field for backwards compatibility

        processed_files = values.pop('processed_files', None)

        if processed_files:
            for filename, doc_id in processed_files.items():
                doc = JobDocumentInfo.parse_obj(document_info.get(doc_id, {}))
                doc.filename = filename
                document_info[doc_id] = doc.dict()

        # MAPPS-400
        # Move obsole "user_canceled_info" into "user_actions_log" list

        user_actions_log = values.get('user_actions_log', deque())

        if not user_actions_log:
            # Add "Job Create" entry
            details = {'created_at': values.get('started_at'),
                       'user_info': values.get('user_info')}

            create_log_entry = UserActionLogEntry(action=UserAction.create, **details)
            user_actions_log.append(create_log_entry)

            # Add "User Canceled" entry
            canceled_info = values.pop('user_canceled_info', {})
            if canceled_info:
                details = {'created_at': canceled_info.get('canceled_at'),
                           'user_info': canceled_info.get('canceled_by')}
                cancel_log_entry = UserActionLogEntry(action=UserAction.cancel, **details)
                user_actions_log.append(cancel_log_entry)

            values['user_actions_log'] = user_actions_log

        return values

    @validator('job_id', pre=True, always=True)
    def set_job_id_default(cls, v):
        return v or uuid.uuid4().hex

    @validator('bulk_source_bucket', pre=True, always=True)
    def set_bulk_source_bucket_lower(cls, value):
        if value:
            return value.lower()
        return ''

    @validator('bulk_destination_directory', pre=True, always=True)
    def set_bulk_destination_directory_default(cls, value):
        return value or ''

    @validator('user_info', pre=True, always=True)
    def set_user_info_default(cls, v):
        return v if v is not None else {}

    @validator('document_info', pre=True, always=True)
    def set_document_info_default(cls, v):
        return v if v is not None else {}

    @validator('required_features', pre=True)
    def set_required_features(cls, v):
        if isinstance(v, dict):
            if 'features' not in v:
                raise ValueError(
                    'Wrong structure for "required_features" dict ("features" key is missing)')
            return v['features']
        return v

    @validator('summary_tasks', pre=True, always=True)
    def set_summary_tasks(cls, v):
        return v or []

    @validator('user_actions_log', pre=True, always=True)
    def set_user_actions_log_as_deque(cls, v):
        return deque(v or [])

    @property
    def document_ids(self) -> List[str]:
        return list(self.document_info.keys())

    @property
    def redis_key(self) -> str:
        return self.job_id

    @property
    def status(self) -> WorkStatus:
        if not self.document_info:
            return WorkStatus.not_started

        # Return "canceling" status if there are "processing" documents in the canceled job
        min_docs_status = min(document.status for document in self.document_info.values())
        if min_docs_status is WorkStatus.processing and self.user_canceled:
            return WorkStatus.canceling

        return min_docs_status

    def add_file(self, source: str, document_id: str):
        if source in self.processed_files:
            return

        self.document_info[document_id] = JobDocumentInfo(status=WorkStatus.processing,
                                                          filename=source)

        # Update "processed_files" mapping to be able to lookup document_id by file name
        self.processed_files[source] = document_id

    def log_user_action(self,
                        action: UserAction,
                        user_info: Optional[Union[UserInfo, dict]] = None) -> None:

        if user_info and not isinstance(user_info, UserInfo):
            user_info = UserInfo.parse_obj(user_info)

        log_entry = UserActionLogEntry(action=action, user_info=user_info)
        self.user_actions_log.append(log_entry)

    def filter_user_actions(
            self,
            include: Optional[Iterable[UserAction]] = None) -> Iterable[UserActionLogEntry]:
        """Filter user actions starting from latest entry"""

        reversed_log = reversed(self.user_actions_log)

        if not include:
            yield from reversed_log
        else:
            include = set(include)
            yield from filter(lambda x: x.action in include, reversed_log)

    @property
    def processed_files(self) -> Dict[str, str]:
        """Generate "process_files" dict for backwards compatibility"""

        if self._processed_files is None:
            self._processed_files = {doc.filename: doc_id
                                     for doc_id, doc in self.document_info.items()}

        return self._processed_files

    @property
    def complete(self) -> bool:
        return self.status.is_completed

    def to_customer_facing_json(self) -> str:
        return self.json()

    @classmethod
    def from_json(cls, json_str: Union[str, bytes]) -> 'JobTask':
        return cls.parse_raw(json_str)

    @property
    def metadata_file_key(self) -> str:
        purged = self.status is WorkStatus.purged
        return self.get_metadata_file_key(self.job_id, purged=purged)

    @classmethod
    def get_metadata_file_key(cls, job_id, purged: bool = False) -> str:
        return get_manifest_job_storage_key(job_id, purged=purged)


class LegacyJobTask(JobTask):
    """The version of JobTask class for parse archived metadata files.

    It omits the validation of items in `required_features` field because
    the `FeatureType` enum is updated periodically and that's why old
    archived Job manifests can't be parsed/validated correctly.
    """

    # Original type hint for `required_features` is `Set[FeatureType]`.
    # It's updated to `Set[int]` to prevent validation issues related to
    # inconsistency with actual `FeatureType` enum in the `text2phenotype-py` lib.
    required_features: Set[int] = []
