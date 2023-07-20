import copy
import uuid
from enum import Enum
from pathlib import Path
from typing import (
    ClassVar,
    List,
    Optional,
    Set,
)

import magic
from pydantic import (
    BaseModel,
    Field,
    root_validator,
    validator,
)

from text2phenotype.common.log import operations_logger
from text2phenotype.constants.common import FileExtensions
from text2phenotype.constants.deid import DeidGroupings
from text2phenotype.constants.environment import Environment
from text2phenotype.tasks.task_enums import (
    EnumAliasesMixin,
    TaskEnum,
    TaskOperation,
)
from text2phenotype.tasks.task_info import SummaryTask


OPERATION_FLAGS = {
    TaskOperation.ocr: Environment.OCR_OPERATION_ENABLED.value,
    TaskOperation.deid: Environment.DEID_OPERATION_ENABLED.value,
    TaskOperation.demographics: Environment.DEMOGRAPHICS_OPERATION_ENABLED.value,
    TaskOperation.clinical_summary: Environment.CLINICAL_SUMMARY_OPERATION_ENABLED.value,
    TaskOperation.oncology_summary: Environment.ONCOLOGY_SUMMARY_OPERATION_ENABLED.value,
    TaskOperation.oncology_only: Environment.ONCOLOGY_ONLY_OPERATION_ENABLED.value,
    TaskOperation.app_ingest: Environment.APP_INGEST_OPERATION_ENABLED.value,
    TaskOperation.annotate: Environment.ANNOTATE_OPERATION_ENABLED.value,

    # MAPPS-485: The "bladder_risk" operation should not be callable in the API any longer.
    # It should be a prerequisite of "bladder_summary".
    #
    # It's necessary to have "bladder_risk" in the "TaskOperations" enum to keep consistency
    # between Text2phenotype-Py, Intake and Biomed. That's why "bladder_risk" has excluded from
    # "AllowedOperations".
    TaskOperation.bladder_risk: False,
}

allowed_operations = {}
for operation in TaskOperation:
    if operation not in OPERATION_FLAGS or OPERATION_FLAGS.get(operation):
        allowed_operations[operation.name] = operation.value

allowed_text_operations = copy.deepcopy(allowed_operations)
allowed_text_operations.pop(TaskOperation.ocr.name, None)

if not allowed_operations:
    message = 'At least one operation should be enabled in the features flags'
    operations_logger.error(f'Wrong configuration. {message}')
    raise Exception(message)


class _OperationsEnum(str, EnumAliasesMixin, Enum):
    """The "pydantic" models ignore items from regular python Enums.
    Need to do multiple inheritance (str, Enum) for compatibility.
    """
    __aliases__ = TaskOperation.__aliases__.copy()


AllowedTaskOperations = _OperationsEnum('AllowedTaskOperations', allowed_operations)
AllowedTextTaskOperations = _OperationsEnum('AllowedTextTaskOperations', allowed_text_operations)


class AbstractProcessRequest(BaseModel):
    _validate_summary_custom: ClassVar[bool] = True

    operations: List[AllowedTaskOperations]
    summary_custom: Optional[List[SummaryTask]] = Field(
        [],
        description=f'This field is required for "{TaskOperation.summary_custom.value}" operation')
    deid_filter: Optional[str] = Field(None, nullable=True)
    biomed_version: Optional[str] = Field(None, nullable=True)
    tid: Optional[str] = ''
    model_version: Optional[str] = Field(None, nullable=True)

    @validator('tid', pre=True, always=True)
    def set_default_tid(cls, tid):
        return tid or str(uuid.uuid4())

    @validator('operations', pre=True, always=True)
    def convert_legacy_summary_operations_names(cls, operations):
        operations = operations or []
        result = []

        for op in operations:
            try:
                op = TaskOperation(op).value
            except ValueError:
                pass
            result.append(op)

        return result

    @validator('deid_filter', pre=True, always=True)
    def set_deid_filter(cls, deid_filter):

        operations_logger.info(f"DEID FILTER {deid_filter}")
        if deid_filter not in DeidGroupings.__members__ and deid_filter is not None:
            raise KeyError(f'{deid_filter} Not in {DeidGroupings.__members__.keys()}')
        return deid_filter

    @validator('summary_custom', pre=False, always=True)
    def validate_unique_filenames(cls, summary_tasks: List[SummaryTask]):
        filenames = set()
        for summary in summary_tasks:
            if summary.results_filename in filenames:
                raise ValueError(f'File names in custom summaries should be unique: '
                                 f'"{summary.results_filename}" is used several times.')
            filenames.add(summary.results_filename)
        return summary_tasks

    @root_validator(pre=False)
    def validate_summary_custom_config(cls, values):
        if not cls._validate_summary_custom:
            return values

        operations = values.get('operations', [])
        summary_custom = values.get('summary_custom')

        if TaskOperation.summary_custom in operations:
            if not summary_custom:
                raise ValueError(
                    'Inproperly configured: '
                    '"summary_custom" section is empty but required for the operation')
        else:
            if summary_custom:
                raise ValueError(
                    '"summary_custom" section is not empty but operation was not requested')

        return values

    def collect_required_operations_set(self) -> Set[TaskOperation]:
        return set(self.operations) | SummaryTask.collect_tasks_set(self.summary_custom,
                                                                    expected_type=TaskOperation)


class IntakeFile(BaseModel):
    filename: str = ...

    @validator('filename', pre=True, always=True)
    def check_file(cls, filename):
        orig_extension = Path(filename.lower()).suffix
        orig_file_extension = orig_extension[1:] if orig_extension else orig_extension
        try:
            extension = FileExtensions(orig_file_extension)
        except ValueError:
            operations_logger.error(f'This type is not supported "{orig_file_extension}"')
            raise ValueError('Wrong file type')
        else:
            if extension not in [FileExtensions.PDF, FileExtensions.TXT]:
                operations_logger.error(f'This type is not supported "{orig_file_extension}"')
                raise ValueError('Wrong file type')
        return filename

    @property
    def extension(self) -> FileExtensions:
        orig_extension = Path(self.filename.lower()).suffix
        orig_file_extension = orig_extension[1:] if orig_extension else orig_extension
        return FileExtensions(orig_file_extension)

    @property
    def requires_ocr(self) -> bool:
        return self.extension == FileExtensions.PDF


class ReprocessOptions(AbstractProcessRequest):
    _validate_summary_custom: ClassVar[bool] = False

    operations: Optional[List[AllowedTaskOperations]] = Field(
        [],
        description=('The list of operations that should be performed. '
                     'By default, will be taken Job related operations.')
    )

    force_all_documents: Optional[bool] = Field(
        False,
        description='Force reprocess all Job documents, including successful. '
                    'By default, successful documents will be skipped.'
    )

    force_all_tasks: Optional[bool] = Field(
        False,
        description='Force reprcess all tasks, including successful. '
                    'By default, successful tasks will be skipped.'
    )

    force_start: Optional[bool] = Field(
        False,
        description='Force start the reprocess, '
                    'even if job in the "canceling" or "processing" state.'
    )

    document_ids: Optional[List[str]] = Field(
        [],
        description='Reprocess only selected documents instead of all job related'
    )

    tasks: Optional[List[TaskEnum]] = Field(
        [],
        description='Specify the list of tasks which should be reprocessed.'
    )

    @validator('operations', 'document_ids', 'tasks', always=True, pre=True)
    def set_default_list(cls, v):
        return v or []

    @root_validator(pre=True)
    def check_legacy_fields(cls, values):
        # Support "include_successful_documents" flag for backwards compatibility
        # Now this flag renamed to "force_all_documents"
        if 'include_successful_documents' in values:
            v = values.pop('include_successful_documents')
            values.setdefault('force_all_documents', v)
        return values


class BaseProcessing(AbstractProcessRequest):
    app_destination: Optional[str] = ''
    stop_documents_on_failure: Optional[bool] = True


class DocumentProcessingCorpus(BaseProcessing):
    source_bucket: str
    source_directory: str
    destination_directory: str

    @validator('source_directory', 'destination_directory')
    def validate_not_empty(cls, v, field):
        if not v:
            raise ValueError('Field should not be empty')
        return v


class DocumentProcessingText(BaseProcessing):
    operations: List[AllowedTextTaskOperations]
    document_text: str


class DocumentProcessingFile(BaseModel):
    file: bytes
    payload: BaseProcessing

    class Config:
        extra = 'allow'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filename = kwargs.get('filename')
        if not self.filename:
            raise ValueError('"filename" field is required')
        orig_extension = Path(self.filename.lower()).suffix
        self.orig_file_extension = orig_extension[1:] if orig_extension else orig_extension
        try:
            extension = FileExtensions(self.orig_file_extension)
        except ValueError:
            operations_logger.error(f'This type is not supported "{self.orig_file_extension}"',
                                    tid=self.payload.tid)
            raise ValueError('Wrong file type')
        else:
            if extension not in [FileExtensions.PDF, FileExtensions.TXT]:
                operations_logger.error(f'This type is not supported "{self.orig_file_extension}"',
                                        tid=self.payload.tid)
                raise ValueError('Wrong file type')

    @validator('file')
    def check_file(cls, file):
        if 'text' in magic.from_buffer(file):
            try:
                file.decode('utf-8')
            except UnicodeError:
                raise ValueError('Wrong encoding')
        return file

    @property
    def extension(self) -> FileExtensions:
        return FileExtensions(self.orig_file_extension)

    @property
    def requires_ocr(self) -> bool:
        return self.extension == FileExtensions.PDF
