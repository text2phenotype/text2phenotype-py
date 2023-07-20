import functools
from enum import Enum
from typing import Dict

from text2phenotype.constants.redis import DatabaseMapping


class EnumAliasesMixin:
    """Add support of __aliases__ (alternative values of enum items"""
    __aliases__ = {}

    @classmethod
    def _missing_(cls, value):
        """Handle values missing in the Enum"""
        if value in cls.__aliases__:
            value = cls.__aliases__[value]
            return cls(value)
        return super()._missing_(value)

    @classmethod
    def __modify_schema__(cls, schema):
        """Method used in the pydantic OpenAPI schema generation"""
        enum_values = set(schema.get('enum'))

        # Add aliases to enum of allowed values
        for alias, val in cls.__aliases__.items():
            if val in enum_values:
                enum_values.add(alias)

        schema['enum'] = sorted(list(enum_values))
        return schema


class ModelTask(str, Enum):
    """Individual Biomed model tasks"""
    bladder_risk = 'bladder_risk'
    covid_lab = 'covid_lab'
    date_of_service = 'date_of_service'
    demographics = 'demographics'
    device_procedure = 'device_procedure'
    disease_sign = 'disease_sign'
    doctype = 'doctype'
    drug = 'drug'
    genetics = 'genetics'
    icd10_diagnosis = 'icd10_diagnosis'
    imaging_finding = 'imaging_finding'
    lab = 'lab'
    oncology_only = 'oncology_only'
    phi_tokens = 'phi_tokens'
    smoking = 'smoking'
    vital_signs = 'vital_signs'
    family_history = 'family_history'
    sdoh = 'sdoh'


class TaskOperation(str, EnumAliasesMixin, Enum):
    # Individual model operations
    bladder_risk = ModelTask.bladder_risk.value  # MAPPS-485: excluded from "AllowedOperations"
    covid_lab = ModelTask.covid_lab.value
    date_of_service = ModelTask.date_of_service.value
    demographics = ModelTask.demographics.value
    device_procedure = ModelTask.device_procedure.value
    disease_sign = ModelTask.disease_sign.value
    doctype = ModelTask.doctype.value
    drug = ModelTask.drug.value
    genetics = ModelTask.genetics.value
    icd10_diagnosis = ModelTask.icd10_diagnosis.value
    imaging_finding = ModelTask.imaging_finding.value
    lab = ModelTask.lab.value
    oncology_only = ModelTask.oncology_only.value
    phi_tokens = ModelTask.phi_tokens.value
    smoking = ModelTask.smoking.value
    vital_signs = ModelTask.vital_signs.value
    family_history = ModelTask.family_history.value
    sdoh = ModelTask.sdoh.value

    annotate = 'annotate'
    app_ingest = 'app_ingest'
    app_reprocess = 'app_reprocess'
    deid = 'deid'
    ocr = 'ocr'
    pdf_embedder = 'pdf_embedder'

    # Summary operations
    clinical_summary = 'clinical_summary'
    covid_specific = 'covid_specific'
    oncology_summary = 'oncology_summary'
    summary_bladder = 'summary_bladder'
    summary_custom = 'summary_custom'

    # TODO: Rename summary-items according to the values.
    # This requires updates in several repositories in many places.
    # https://gettext2phenotype.atlassian.net/browse/MAPPS-455

    # Support of previous "summary" enum values for backwards compatibility.
    # This required to parse metadata files created before rename.
    # "__aliases__" field used in the "EnumAliasesMixin".
    __aliases__: Dict[str, str] = dict(summary_clinical=clinical_summary,
                                       summary_oncology=oncology_summary,
                                       summary_covid=covid_specific)

    @classmethod
    @functools.lru_cache(None)
    def biomed_operations(cls):
        return set(TaskOperation(model.value) for model in ModelTask)


class TaskEnum(str, EnumAliasesMixin, Enum):
    # Individual model operations
    bladder_risk = ModelTask.bladder_risk.value
    covid_lab = ModelTask.covid_lab.value
    date_of_service = ModelTask.date_of_service.value
    demographics = ModelTask.demographics.value
    device_procedure = ModelTask.device_procedure.value
    disease_sign = ModelTask.disease_sign.value
    doctype = ModelTask.doctype.value
    drug = ModelTask.drug.value
    genetics = ModelTask.genetics.value
    icd10_diagnosis = ModelTask.icd10_diagnosis.value
    imaging_finding = ModelTask.imaging_finding.value
    lab = ModelTask.lab.value
    oncology_only = ModelTask.oncology_only.value
    phi_tokens = ModelTask.phi_tokens.value
    smoking = ModelTask.smoking.value
    vital_signs = ModelTask.vital_signs.value
    family_history = ModelTask.family_history.value
    sdoh = ModelTask.sdoh.value

    annotate = TaskOperation.annotate.value
    app_ingest = TaskOperation.app_ingest.value
    app_reprocess = TaskOperation.app_reprocess.value
    deduplicator = 'deduplicator'
    deid = TaskOperation.deid.value
    disassemble = 'disassemble'
    discharge = 'discharge'
    fdl = 'fdl'
    ocr = TaskOperation.ocr.value
    ocr_process = 'ocr_process'
    ocr_reassemble = 'ocr_reassemble'
    pdf_embedder = TaskOperation.pdf_embedder.value
    train_test = 'train_test'
    vectorize = 'vectorize'
    reassemble = 'reassemble'

    purge = 'purge'
    app_purge = 'app_purge'

    # Summary tasks
    clinical_summary = TaskOperation.clinical_summary.value
    oncology_summary = TaskOperation.oncology_summary.value
    covid_specific = TaskOperation.covid_specific.value
    app_summary = 'summary_app'
    summary_bladder = TaskOperation.summary_bladder.value
    summary_custom = TaskOperation.summary_custom.value

    # TODO: Rename summary-items according to the values.
    # This requires updates in several repositories in many places.
    # https://gettext2phenotype.atlassian.net/browse/MAPPS-455

    # Support of previous "summary" enum values for backwards compatibility.
    # This required to parse metadata files created before rename.
    # "__aliases__" field used in the "EnumAliasesMixin" method.
    __aliases__: Dict[str, str] = TaskOperation.__aliases__.copy()
    __aliases__.update(app_summary=app_summary)


class WorkType(str, Enum):
    job = 'job'
    document = 'document'
    chunk = 'chunk'

    @property
    def redis_db(self):
        return WORKTYPE_TO_REDISDB[self]


WORKTYPE_TO_REDISDB = {
    WorkType.job: DatabaseMapping.JOBS,
    WorkType.document: DatabaseMapping.DOCUMENTS,
    WorkType.chunk: DatabaseMapping.CHUNKS,
}


class TaskStatus(str, Enum):
    processing = 'processing'
    not_started = 'not started'
    submitted = 'submitted'
    started = 'started'
    failed = 'failed'
    completed_success = 'completed - success'
    completed_failure = 'completed - failure'
    canceled = 'canceled'

    @classmethod
    @functools.lru_cache(None)
    def completed_statuses(cls):
        return {cls.completed_success, cls.completed_failure, cls.canceled}

    @classmethod
    @functools.lru_cache(None)
    def submitted_statuses(cls):
        return {cls.submitted, cls.started, cls.processing}


class WorkStatus(str, Enum):
    """Statuses enum for the whole Work Task"""

    # This order of items is important for calculate the JobTask.status
    processing = TaskStatus.processing.value
    not_started = TaskStatus.not_started.value
    canceling = 'canceling'
    canceled = TaskStatus.canceled.value
    purging = 'purging'
    purged = 'purged'
    completed_failure = TaskStatus.completed_failure.value
    completed_success = TaskStatus.completed_success.value

    @property
    @functools.lru_cache(None)
    def __ranks(self):
        return {status: rank for rank, status in enumerate(self.__class__)}

    def __lt__(self, other):
        if not isinstance(other, WorkStatus):
            raise ValueError(f'{other} should be type of {self.__class__}')
        return self.__ranks[self] < self.__ranks[other]

    @property
    def is_completed(self):
        """Check if current enum item is any "completed" status"""
        return self in self.completed_statuses()

    @property
    def is_processing(self):
        """Check if current enum item is any "processing" status"""
        return self in self.processing_statuses()

    @classmethod
    @functools.lru_cache(None)
    def completed_statuses(cls):
        return {cls.completed_success, cls.completed_failure, cls.canceled, cls.purged}

    @classmethod
    @functools.lru_cache(None)
    def processing_statuses(cls):
        return {cls.processing, cls.canceling, cls.purging}

    @classmethod
    def from_task_status(cls, task_status: TaskStatus) -> 'WorkStatus':
        if task_status in TaskStatus.submitted_statuses() or task_status is TaskStatus.failed:
            return cls.processing

        return cls(task_status.value)
