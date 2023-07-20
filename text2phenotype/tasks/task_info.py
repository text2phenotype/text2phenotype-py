import copy
import inspect
import json
import os
import sys

from abc import ABC
from datetime import datetime
from typing import (
    BinaryIO,
    ClassVar,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

from pydantic import (
    BaseModel,
    Field,
    root_validator,
    validator,
)

from text2phenotype.common.featureset_annotations import MachineAnnotation
from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import Environment
from text2phenotype.services import get_storage_service
from text2phenotype.tasks.task_enums import (
    ModelTask,
    TaskEnum,
    TaskOperation,
    TaskStatus,
    WorkType,
)
from text2phenotype.tasks.tasks_constants import TasksConstants

# Define alias for complex typing annotation
ChunksIterable = Iterable[Tuple[List[int], Union[dict, list]]]


class OperationInfo(BaseModel):
    operation: TaskOperation
    status: TaskStatus = Field(None, description=f'By default will be set {TaskStatus.processing.value} status')
    results_file_key: str = None
    error_messages: List[str] = []

    @validator('status', pre=True, always=True)
    def set_default_status(cls, v):
        return v or TaskStatus.processing

    def to_json(self) -> str:
        return self.json()

    def fill_from_task_info(self, task_info: 'TaskInfo') -> None:
        self.results_file_key = task_info.results_file_key
        self.status = task_info.status
        self.error_messages.extend(task_info.error_messages)

    @classmethod
    def create(cls, **data) -> 'OperationInfo':
        operation = data.get('operation')

        if isinstance(operation, str):
            operation = TaskOperation(operation)

        if operation is TaskOperation.summary_custom:
            operation_info_class = SummaryCustomOperationInfo
        else:
            operation_info_class = OperationInfo

        return operation_info_class(**data)


class SummaryCustomOperationInfo(OperationInfo):
    summary_results: List[str] = []

    def fill_from_task_info(self, task_info: 'SummaryCustomTaskInfo') -> None:
        super().fill_from_task_info(task_info)
        self.summary_results = task_info.summary_results.copy()


class TaskInfo(BaseModel, ABC):
    QUEUE_NAME: ClassVar[str] = None
    WORK_TYPE: ClassVar[WorkType] = None
    RESULTS_FILE_EXTENSION: ClassVar[str] = None
    TASK_TYPE: ClassVar[TaskEnum] = None

    task: TaskEnum = None
    status: TaskStatus = Field(None, description=f'By default will be set {TaskStatus.not_started.value} status')
    results_file_key: str = None
    error_messages: List[str] = []
    attempts: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    docker_image: str = None
    dependencies: List[TaskEnum] = []
    model_dependencies: List[TaskEnum] = []
    processing_duration: Optional[float] = None

    def __init__(self, *args, requires_ocr=False, **kwargs):
        super().__init__(*args, **kwargs)
        if requires_ocr:
            self.dependencies.append(TaskEnum.ocr)
            self.dependencies = list(set(self.dependencies))

    @validator('task', pre=True, always=True)
    def set_task_type(cls, v):
        return cls.TASK_TYPE

    @validator('status', pre=True, always=True)
    def set_default_status(cls, v):
        return v or TaskStatus.not_started

    def dict(self, *args, **kwargs) -> dict:
        if not self.processing_duration and self.started_at and self.completed_at:
            self.processing_duration = (self.completed_at - self.started_at).total_seconds()
        values = super().dict(*args, **kwargs)
        return values

    @property
    def complete(self):
        return self.status in TaskStatus.completed_statuses()

    def add_dependency(self, dependency: TaskEnum):
        self.dependencies.append(dependency)

    @classmethod
    def download_storage_file(cls, storage_client, source_file: str) -> str:
        """
        Download a text file from storage and return its text

        :param source_file: source location in the storage
        """
        operations_logger.info(f'{cls.TASK_TYPE.value} TaskInfo class downloading'
                               f' document {source_file}')
        object_bytes = storage_client.get_content(source_file)
        operations_logger.debug(f'{cls.TASK_TYPE.value} TaskInfo class done '
                                f'downloading document. Bytes: {len(object_bytes)}')

        source_text = object_bytes.decode("utf-8")

        return source_text

    def to_json(self) -> str:
        return self.json()

    def to_customer_facing_json(self) -> str:
        customer_fields = {
            'task',
            'status',
            'results_file_key',
            'started_at',
            'completed_at',
        }
        return self.json(include=customer_fields)

    @staticmethod
    def create(**kwargs) -> 'TaskInfo':
        task = TaskEnum(kwargs.get('task'))
        return create_task_info(task, **kwargs)


class ChunkTaskInfo(TaskInfo):
    WORK_TYPE: ClassVar[WorkType] = WorkType.chunk

    @staticmethod
    def update_json_response_ranges(biomed_response_list: List[dict], text_span: List[int]):
        for biomed_response in biomed_response_list:
            biomed_response['range'][0] += text_span[0]
            biomed_response['range'][1] += text_span[0]
        return biomed_response_list

    @classmethod
    def get_document_results_file_key(cls, document_id: str):
        return os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                            document_id,
                            f'{document_id}.'
                            f'{cls.RESULTS_FILE_EXTENSION}')

    @classmethod
    def write_document_results(cls,
                               data: Optional[bytes],
                               document_id: str,
                               storage_client,
                               file: Optional[BinaryIO] = None) -> str:

        results_file_key = cls.get_document_results_file_key(document_id)
        container = storage_client.get_container()

        if file is not None:
            container.write_fileobj(file, file_name=results_file_key)

        elif data is not None:
            container.write_bytes(data=data, file_name=results_file_key)

        else:
            raise AttributeError('At least one argument "data" or "file" should be not None')

        return results_file_key

    @classmethod
    def iter_chunk_results(cls,
                           chunks: List['ChunkTask'],
                           storage_client) -> ChunksIterable:

        for chunk_task in chunks:
            task_info = chunk_task.task_statuses[cls.TASK_TYPE]
            chunk_result_data = json.loads(
                cls.download_storage_file(storage_client, task_info.results_file_key))
            yield chunk_task.text_span, chunk_result_data


class OCRProcessTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.OCR_PROCESS_TASKS_QUEUE.value
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    RESULTS_FILE_EXTENSION: ClassVar[str] = f'{TasksConstants.DOCUMENT_TEXT_SUFFIX}.pdf'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.ocr_process

    png_pages: Dict[int, str] = {}  # filepaths to ocr data in file storage
    text_coords_directory_file_key: str = None
    text_coords_lines_file_key: str = None


class OCRReassembleTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.OCR_REASSEMBLE_TASKS_QUEUE.value
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.ocr_reassemble


class OCRSplitterTaskInfo(TaskInfo):
    WORK_TYPE: ClassVar[WorkType] = WorkType.document

    page_offset: int
    pdf_chunk_file_key: str = None


class OCRTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.OCR_TASKS_QUEUE.value
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    RESULTS_FILE_EXTENSION: ClassVar[str] = f'{TasksConstants.DOCUMENT_TEXT_SUFFIX}.pdf'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.ocr

    png_pages: Dict[int, str] = {}

    pdf_chunking_done: bool = False
    pdf_splitting_done: bool = False

    pdf_chunk_statuses: Dict[int, OCRSplitterTaskInfo] = {}
    ocr_process_statuses: Dict[int, OCRProcessTaskInfo] = {}  # page_offset -> OCRPRocessTaskInfo
    ocr_reassemble_status: OCRReassembleTaskInfo = None

    text_coords_directory_file_key: str = None
    text_coords_lines_file_key: str = None

    @property
    def is_ocr_process_successful(self) -> bool:
        return self.pdf_splitting_done and \
               all(p.status is TaskStatus.completed_success
                   for p in self.ocr_process_statuses.values())

    @property
    def is_ocr_process_failed(self) -> bool:
        return any(p.status in {TaskStatus.failed, TaskStatus.completed_failure}
                   for p in self.ocr_process_statuses.values())


class DisassembleTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.DISASSEMBLE_TASKS_QUEUE.value
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.disassemble


class ReassembleTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.REASSEMBLE_TASKS_QUEUE.value
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.reassemble

    dependencies: List[TaskEnum] = [TaskEnum.disassemble]


class PDFEmbedderTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.PDF_EMBEDDER_TASKS_QUEUE.value
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.pdf_embedder
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'embedded.pdf'

    dependencies: List[TaskEnum] = [
        TaskEnum.reassemble
    ]  # need reassembled  token results


class DeidTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.DEID_TASKS_QUEUE.value
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.deid
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'redacted'
    GLOBAL_REDACT_FILTER_EXT: ClassVar[str] = 'utilized_phi_tokens'

    redacted_txt_file_key: str = None
    redacted_phi_tokens_file_key: str = None
    dependencies: List[TaskEnum] = [
        TaskEnum.phi_tokens,
        TaskEnum.demographics,
        TaskEnum.reassemble
    ]  # need reassembled PHI token results


class AppIngestTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.APP_INGEST_TASKS_QUEUE.value
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.app_ingest

    dependencies: List[TaskEnum] = [
        TaskEnum.app_summary,
        TaskEnum.deid,
        TaskEnum.demographics,
        TaskEnum.deduplicator,
    ]

    doc_ref_uuid: Optional[str] = None


class DeduplicatorTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.DEDUPLICATOR_TASKS_QUEUE.value
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.deduplicator
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'deduplicator.json'

    dependencies: List[TaskEnum] = [TaskEnum.reassemble]


class AppReprocessTaskInfo(AppIngestTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.APP_REPROCESS_TASK_QUEUE.value
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.app_reprocess


class DischargeTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.DISCHARGE_QUEUE.value
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.discharge


class AnnotationTaskInfo(ChunkTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.ANNOTATE_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'annotations.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.annotate
    FDL_ENABLED: ClassVar[bool] = Environment.FDL_ENABLED.value

    @validator('dependencies', always=True, pre=True)
    def check_dependencies(cls, v: list):
        if cls.FDL_ENABLED and TaskEnum.fdl not in v:
            v.append(TaskEnum.fdl)
        return v

    @classmethod
    def get_from_storage(cls, document_id: str, num_chunks: int) -> MachineAnnotation:
        annotations = MachineAnnotation()

        for index in range(1, num_chunks + 1):
            prefix = '0' * (5 - len(str(index)))
            chunk_key = f'{document_id}_{prefix}{index}'

            annotation_file_key = os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                                               document_id,
                                               TasksConstants.STORAGE_CHUNKS_PREFIX,
                                               f'{chunk_key}',
                                               f'{chunk_key}.{cls.RESULTS_FILE_EXTENSION}')

            service = get_storage_service()
            container = service.get_container()
            try:
                content = container.get_object_content(annotation_file_key)
            except Exception as e:
                operations_logger.exception(f'Failed download annotation file: {e}')
            else:
                annotations.fill_from_json(content.decode())
        return annotations


class FDLTaskInfo(ChunkTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.FDL_TASK_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'fdl_results.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.fdl

    @classmethod
    def get_fdl_result_file_key(cls, document_id: str, chunk_id: str) -> str:
        return os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                            document_id,
                            TasksConstants.STORAGE_CHUNKS_PREFIX,
                            f'{chunk_id}',
                            f'{chunk_id}.{cls.RESULTS_FILE_EXTENSION}')


class VectorizeTaskInfo(ChunkTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.VECTORIZE_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'vectorization.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.vectorize

    dependencies: List[TaskEnum] = [TaskEnum.annotate]


class SingleModelTaskInfo(ChunkTaskInfo):
    dependencies: List[TaskEnum] = [TaskEnum.vectorize]


class PHITokenTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.PHI_TOKEN_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'phi_tokens.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.phi_tokens
    model_dependencies: List[TaskEnum] = [TaskEnum.demographics]


class SmokingTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.SMOKING_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'smoking.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.smoking


class DeviceProcedureTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.DEVICE_PROCEDURE_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'device_procedure.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.device_procedure


class ImagingFindingTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.IMAGING_FINDING_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'imaging_finding.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.imaging_finding


class DiseaseSignTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.DISEASE_SIGN_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'disease_sign.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.disease_sign
    model_dependencies: List[TaskEnum] = [TaskEnum.family_history]


class FamilyHistoryTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.FAMILY_HISTORY_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'family_history.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.family_history


class SDOHTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.SDOH_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'sdoh.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.sdoh


class VitalSignTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.VITAL_SIGN_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'vital_signs.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.vital_signs


class CovidLabModelTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.COVID_LAB_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'covid_lab.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.covid_lab


class LabModelTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.LAB_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'lab.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.lab


class DrugModelTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.DRUG_TASKS_QUEUE.value
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.drug
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'drug.json'


class DemographicsTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.DEMOGRAPHICS_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'demographics.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.demographics


class OncologyOnlyTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.ONCOLOGY_ONLY_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'oncology_only.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.oncology_only


class ICD10DiagnosisTaskInfo(SingleModelTaskInfo):
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'icd10_diagnosis.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.icd10_diagnosis
    QUEUE_NAME: ClassVar[str] = Environment.ICD10_DIAGNOSIS_QUEUE.value


class BladderRiskTaskInfo(SingleModelTaskInfo):
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'bladder_risk.json'
    QUEUE_NAME: ClassVar[str] = Environment.BLADDER_RISK_TASKS_QUEUE.value
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.bladder_risk


class SummaryTask(BaseModel):
    results_filename: str = Field(..., description='File name for json output')
    models: List[ModelTask]

    def get_storage_key(self, document_id: str) -> str:
        return os.path.join(
            TasksConstants.STORAGE_DOCUMENTS_PREFIX,
            document_id,
            f'{document_id}.{self.results_filename}',
        )

    @classmethod
    def collect_tasks_set(
            cls,
            summary_tasks: List['SummaryTask'],
            expected_type: Union[TaskEnum, TaskOperation, ModelTask] = TaskEnum) -> Set[TaskEnum]:
        """Collect required tasks (model-tasks) from a list of SummaryTasks items.

        Result enum-items will be casted to required type: TaskEnum (default),
        TaskOperation or ModelTask.
        """

        tasks_set: Set[ModelTask] = set()

        for summary in summary_tasks:
            tasks_set |= set(summary.models)

        if expected_type is ModelTask:
            return tasks_set

        return set(expected_type(task.value) for task in tasks_set)

    def __hash__(self) -> int:
        return hash((self.results_filename, tuple(self.models)))


class BiomedSummaryTaskInfo(TaskInfo):
    WORK_TYPE: ClassVar[WorkType] = WorkType.document
    QUEUE_NAME: ClassVar[str] = Environment.SUMMARY_TASKS_QUEUE.value

    def iter_summary_tasks(self) -> Iterable[SummaryTask]:
        yield SummaryTask(models=self.model_dependencies,
                          results_filename=self.RESULTS_FILE_EXTENSION)

    def add_result_file_key(self, result_file_key):
        self.results_file_key = result_file_key


class ClinicalSummaryTaskInfo(BiomedSummaryTaskInfo):
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'clinical_summary.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.clinical_summary
    model_dependencies: List[TaskEnum] = [TaskEnum.disease_sign, TaskEnum.drug,
                                          TaskEnum.lab, TaskEnum.smoking]
    dependencies: List[TaskEnum] = model_dependencies + [TaskEnum.reassemble]


class OncologySummaryTaskInfo(BiomedSummaryTaskInfo):
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'oncology_summary.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.oncology_summary
    model_dependencies: List[TaskEnum] = [TaskEnum.disease_sign, TaskEnum.drug,
                                          TaskEnum.oncology_only]
    dependencies: List[TaskEnum] = model_dependencies + [TaskEnum.reassemble]


class BladderSummaryTaskInfo(BiomedSummaryTaskInfo):
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'bladder_summary.json'
    QUEUE_NAME: ClassVar[str] = Environment.BLADDER_SUMMARY_TASKS_QUEUE.value
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.summary_bladder
    model_dependencies: List[TaskEnum] = [TaskEnum.doctype,
                                          TaskEnum.oncology_only,
                                          TaskEnum.bladder_risk]
    dependencies: List[TaskEnum] = model_dependencies + [TaskEnum.reassemble]


class AllModelSummaryTaskInfo(BiomedSummaryTaskInfo):
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'app_summary.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.app_summary

    model_dependencies: List[TaskEnum] = [
        TaskEnum.disease_sign, TaskEnum.drug, TaskEnum.oncology_only, TaskEnum.lab,
        TaskEnum.covid_lab, TaskEnum.vital_signs, TaskEnum.imaging_finding,
        TaskEnum.device_procedure, TaskEnum.smoking
    ]
    dependencies: List[TaskEnum] = model_dependencies + [TaskEnum.reassemble]


class CovidSpecificTaskInfo(BiomedSummaryTaskInfo):
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'covid_specific.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.covid_specific
    model_dependencies: List[TaskEnum] = [TaskEnum.covid_lab,
                                          TaskEnum.device_procedure,
                                          TaskEnum.imaging_finding]
    dependencies: List[TaskEnum] = model_dependencies + [TaskEnum.reassemble]


class SummaryCustomTaskInfo(BiomedSummaryTaskInfo):
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.summary_custom

    summary_tasks: List[SummaryTask] = []
    summary_results: List[str] = []

    model_dependencies: List[TaskEnum] = []
    dependencies: List[TaskEnum] = [TaskEnum.reassemble]

    @root_validator(pre=False)
    def fill_dependencies(cls, values: Dict):
        summary_tasks: List[SummaryTask] = values.get('summary_tasks')

        if summary_tasks:
            model_dependencies: Set[TaskEnum] = set(values.get('model_dependencies', []))
            model_dependencies |= SummaryTask.collect_tasks_set(summary_tasks,
                                                                expected_type=TaskEnum)

            dependencies: Set[TaskEnum] = set(values.get('dependencies', []))
            dependencies |= model_dependencies

            values['model_dependencies'] = list(model_dependencies)
            values['dependencies'] = list(dependencies)

        return values

    @validator('summary_tasks', pre=True, always=True)
    def cast_summary_tasks_to_list(cls, v) -> List:
        return v or []

    def iter_summary_tasks(self) -> Iterable[SummaryTask]:
        yield from self.summary_tasks

    def add_result_file_key(self, result_file_key):
        self.summary_results.append(result_file_key)


class GeneticsTaskInfo(SingleModelTaskInfo):
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'genetics.json'
    QUEUE_NAME: ClassVar[str] = Environment.GENETICS_TASKS_QUEUE.value
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.genetics


class DocumentTypeTaskInfo(SingleModelTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.DOC_TYPE_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'doctype.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.doctype


class DateOfServiceTaskInfo(ChunkTaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.DOS_TASKS_QUEUE.value
    RESULTS_FILE_EXTENSION: ClassVar[str] = 'dos.json'
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.date_of_service


class AppPurgeTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.APP_PURGE_TASKS_QUEUE.value
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.app_purge
    WORK_TYPE: ClassVar[WorkType] = WorkType.document


class PurgeTaskInfo(TaskInfo):
    QUEUE_NAME: ClassVar[str] = Environment.PURGE_QUEUE.value
    TASK_TYPE: ClassVar[TaskEnum] = TaskEnum.purge
    WORK_TYPE: ClassVar[WorkType] = WorkType.document


class TaskDependencies:
    @classmethod
    def iter_dependent_tasks(cls, task: TaskEnum) -> Iterable[TaskEnum]:
        skip_for_next = {task}

        def _iter_deep(task: TaskEnum) -> Iterable:
            yield task

            for sup_task in TASK_MAPPING:
                if sup_task in skip_for_next:
                    continue

                dependencies = create_task_info(sup_task).dependencies
                if task in dependencies:
                    skip_for_next.add(sup_task)
                    yield from _iter_deep(sup_task)

        yield from _iter_deep(task)

    @classmethod
    def iter_dependencies_deep(cls, task: TaskEnum) -> Iterable[Tuple[TaskEnum, TaskInfo]]:
        task_info = create_task_info(task)
        yield task, task_info

        for sub_task in set(task_info.dependencies + task_info.model_dependencies):
            yield from cls.iter_dependencies_deep(sub_task)

    @classmethod
    def get_chunk_tasks(
            cls,
            operations: List[TaskOperation],
            summary_tasks: Optional[List[SummaryTask]] = None) -> Dict[TaskEnum, TaskInfo]:

        operations: Set[Union[TaskOperation, ModelTask]] = set(operations)

        # Add "summary_custom" required models to the operations list
        if summary_tasks and TaskOperation.summary_custom in operations:
            operations |= SummaryTask.collect_tasks_set(summary_tasks,
                                                        expected_type=TaskOperation)

        def iter_chunk_tasks_deep(task: TaskEnum):
            for task, task_info in cls.iter_dependencies_deep(task):
                if task_info.WORK_TYPE is WorkType.chunk:
                    yield task, task_info

        tasks_dir: Dict[TaskEnum, TaskInfo] = dict()

        for operation in operations:
            task = TaskEnum(operation.value)

            for dep, task_info in iter_chunk_tasks_deep(task):
                tasks_dir.setdefault(dep, task_info)

        return tasks_dir

    @classmethod
    def get_document_tasks(
            cls,
            operations: List[TaskOperation],
            summary_tasks: Optional[List[SummaryTask]] = None) -> Dict[TaskEnum, TaskInfo]:

        operations: Set[Union[TaskOperation, ModelTask]] = set(operations)

        # Add "summary_custom" required models to the operations list
        if summary_tasks and TaskOperation.summary_custom in operations:
            operations |= SummaryTask.collect_tasks_set(summary_tasks,
                                                        expected_type=TaskOperation)

        requires_ocr: bool = TaskOperation.ocr in operations

        tasks_dir: Dict[TaskEnum, TaskInfo] = dict()
        discharge_task: DischargeTaskInfo = tasks_dir.setdefault(
            TaskEnum.discharge, DischargeTaskInfo(requires_ocr=requires_ocr))

        if requires_ocr:
            tasks_dir[TaskEnum.ocr] = OCRTaskInfo()  # Make sure the OCR task is actually added!

        if operations == {TaskOperation.ocr}:
            # only one operation requested, and it's OCR. no need to disassemble
            return tasks_dir

        discharge_task.dependencies.append(TaskEnum.disassemble)
        discharge_task.dependencies.append(TaskEnum.reassemble)
        tasks_dir[TaskEnum.disassemble] = DisassembleTaskInfo(requires_ocr=requires_ocr)  # always disassemble
        tasks_dir[TaskEnum.reassemble] = ReassembleTaskInfo(
            requires_ocr=requires_ocr)  # must reassemble after we disassemble

        def iter_document_tasks_deep(task: TaskEnum):
            for task, task_info in cls.iter_dependencies_deep(task):
                if task_info.WORK_TYPE is WorkType.document:
                    yield task, task_info

        for operation in operations:
            task = TaskEnum(operation.value)

            for task, task_info in iter_document_tasks_deep(task):
                if task not in tasks_dir:
                    tasks_dir.setdefault(task, task_info)
                    discharge_task.dependencies.append(task)

        # Fill SummaryCustomTaskInfo
        summary_task_info: Optional[SummaryCustomTaskInfo] = tasks_dir.get(TaskEnum.summary_custom)
        if summary_task_info:
            summary_task_info.summary_tasks = summary_tasks

        # pdf_embedding is last step before discharge
        if TaskEnum.pdf_embedder in tasks_dir:
            pdf_dependencies = copy.deepcopy(discharge_task.dependencies)
            if TaskEnum.pdf_embedder in pdf_dependencies:
                pdf_dependencies.remove(TaskEnum.pdf_embedder)
            tasks_dir[TaskEnum.pdf_embedder].dependencies = pdf_dependencies

        return tasks_dir


# Mapping: task -> task info class
TASK_MAPPING: Dict[TaskEnum, Type[TaskInfo]] = {}

# Fill TASK_MAPPING based on TaskInfo.TASK_TYPE variable
for _, task_info_class in inspect.getmembers(sys.modules[__name__]):
    if not isinstance(task_info_class, type) \
            or not issubclass(task_info_class, TaskInfo):
        continue

    task = getattr(task_info_class, 'TASK_TYPE', None)

    if task:
        TASK_MAPPING[task] = task_info_class

# There is no specific TaskInfo class for "train_test"
# Question: Does this task using?
TASK_MAPPING[TaskEnum.train_test] = TaskInfo

# Check for missed tasks
for task in set(TaskEnum) - set(TASK_MAPPING.keys()):
    operations_logger.warning(f'There is no TaskInfo class related to task \'{task}\'')


def create_task_info(task_enum: TaskEnum, **kwargs) -> TaskInfo:
    task_info_class = TASK_MAPPING.get(task_enum)

    if not task_info_class:
        task_info_class = TaskInfo
        operations_logger.error(f'The concrete class *TaskInfo was not found '
                                f'for the "{task_enum}" task, but it should be. '
                                f'The base class "{task_info_class.__name__}" is used instead.')

    return task_info_class(**kwargs)
