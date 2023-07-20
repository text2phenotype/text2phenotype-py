import datetime
import os
from collections import namedtuple
from pathlib import Path
from tempfile import (
    gettempdir,
    mkdtemp,
    mkstemp,
)
from typing import (
    Type,
    Union,
)

from dateutil.parser import parse

from text2phenotype.constants.common import FileExtensions
from text2phenotype.constants.features import FeatureType
from text2phenotype.tasks.document_info import DocumentInfo
from text2phenotype.tasks.job_task import (
    JobDocumentInfo,
    JobTask,
    UserInfo,
)
from text2phenotype.tasks.task_enums import (
    WorkStatus,
    TaskEnum,
    TaskOperation,
    TaskStatus,
    WorkType,
)
from text2phenotype.tasks.task_info import (
    AllModelSummaryTaskInfo,
    AnnotationTaskInfo,
    AppIngestTaskInfo,
    AppReprocessTaskInfo,
    ChunkTaskInfo,
    CovidLabModelTaskInfo,
    CovidSpecificTaskInfo,
    DeduplicatorTaskInfo,
    DeidTaskInfo,
    DemographicsTaskInfo,
    DisassembleTaskInfo,
    DischargeTaskInfo,
    DiseaseSignTaskInfo,
    DrugModelTaskInfo,
    ImagingFindingTaskInfo,
    LabModelTaskInfo,
    OncologyOnlyTaskInfo,
    OperationInfo,
    PHITokenTaskInfo,
    ReassembleTaskInfo,
    SmokingTaskInfo,
    TaskInfo,
    VectorizeTaskInfo,
    VitalSignTaskInfo,
    PDFEmbedderTaskInfo,
    OCRTaskInfo
)
from text2phenotype.tasks.tasks_constants import TasksConstants
from text2phenotype.tasks.work_tasks import (
    ChunkTask,
    DocumentTask,
)

TempDir = namedtuple('TempDir', ['path', 'files'])


def create_temp_files() -> TempDir:
    temp_dir = gettempdir()
    temp_dir = mkdtemp(dir=temp_dir)

    pdf_file = mkstemp(suffix='.pdf', dir=temp_dir)[1]
    txt_file = mkstemp(suffix='.txt', dir=temp_dir)[1]

    return TempDir(temp_dir, [pdf_file, txt_file])


def get_result_file_key(task_info: Type[Union[ChunkTaskInfo, TaskInfo]]) -> str:
    if task_info.WORK_TYPE is WorkType.document:
        return os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                            DOCUMENT_ID,
                            f'{DOCUMENT_ID}.{task_info.RESULTS_FILE_EXTENSION}')
    elif task_info.WORK_TYPE is WorkType.chunk:
        return os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                            DOCUMENT_ID,
                            TasksConstants.STORAGE_CHUNKS_PREFIX,
                            CHUNK_ID,
                            f'{CHUNK_ID}.{task_info.RESULTS_FILE_EXTENSION}')
    else:
        raise Exception('Unknown work type')


required_features_values = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 24, 25, 26, 27, 28, 29,
                            30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 47, 48, 49, 50, 51, 54, 56,
                            57, 58, 59, 62, 64, 65, 69, 70, 71, 72, 73, 75, 76, 78, 80, 81, 82, 83, 84, 85, 86, 87, 88,
                            89, 90, 91, 95, 96, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
                            116, 117, 118, 119, 120, 121]

REQUIRED_FEATURES = set(FeatureType(item) for item in required_features_values)

DOCUMENT_SIZE = 6072
SOURCE_TXT = 'john-stevens.pdf.txt'
SOURCE_PDF = 'john-stevens.pdf'
SOURCE_HASH = '0b545611f260efb0eb6983bcb6deea60b1de81e02df36228d6e6677fb6cc98f8'
USER_UUID = 'd403b86620814354b6a032a18d061da6'
DOCUMENT_UUID = '618d0470f82441acb662c309b0ab1ccf'

JOB_ID = '45801a8d0ff74ef9b60dd60ebdc0c2f0'
DOCUMENT_ID = '364ec9cae3694a27a407359cf0cffdf3'
CHUNK_ID = '364ec9cae3694a27a407359cf0cffdf3_00001'

SOURCE_TXT_FILE = Path(__file__).parent.joinpath(SOURCE_TXT)
SOURCE_PDF_FILE = Path(__file__).parent.joinpath(SOURCE_PDF)

EXTRACTED_TEXT_FILE = Path(__file__).parent.joinpath('john-stevens.pdf.txt')
VECTORIZATION_RESULT_FILE = Path(__file__).parent.joinpath('fixture_vectorization.json')
ANNOTATIONS_RESULT_FILE = Path(__file__).parent.joinpath('fixture_annotations.json')
FIXTURE_CLINICAL_SUMMARY = Path(__file__).parent.joinpath('fixture_clinical_summary.json')
FIXTURE_COVID_SPECIFIC = Path(__file__).parent.joinpath('fixture_covid_specific.json')
FIXTURE_DEID = Path(__file__).parent.joinpath('fixture_deid.txt')
FIXTURE_DRUG = Path(__file__).parent.joinpath('fixture_drugs.json')
FIXTURE_DEMOGRAPHICS = Path(__file__).parent.joinpath('fixture_demographics.json')
FIXTURE_ONCOLOGY_ONLY = Path(__file__).parent.joinpath('fixture_oncology_only.json')
FIXTURE_ONCOLOGY_SUMMARY = Path(__file__).parent.joinpath('fixture_oncology_summary.json')
FIXTURE_PHI_TOKENS = Path(__file__).parent.joinpath('fixture_phi_tokens.json')

# CHUNK PDF TMP FILES #######
OCR_CHUNKS_DIR = 'ocr_chunks'
CHUNK_1_EXTRACTED = 'fixture_0.extracted_text.txt'
CHUNK_2_EXTRACTED = 'fixture_1.extracted_text.txt'
CHUNK_3_EXTRACTED = 'fixture_2.extracted_text.txt'

CHUNK_1_PDF = 'fixture_chunk_0.pdf'
CHUNK_2_PDF = 'fixture_chunk_1.pdf'
CHUNK_3_PDF = 'fixture_chunk_2.pdf'

CHUNK_1_COORDS = 'fixture_0.text_coordinates'
CHUNK_2_COORDS = 'fixture_1.text_coordinates'
CHUNK_3_COORDS = 'fixture_2.text_coordinates'

CHUNK_1_LINES = 'fixture_0.text_lines'
CHUNK_2_LINES = 'fixture_1.text_lines'
CHUNK_3_LINES = 'fixture_2.text_lines'

CHUNK_1_EXTRACTED_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_1_EXTRACTED)
CHUNK_2_EXTRACTED_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_2_EXTRACTED)
CHUNK_3_EXTRACTED_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_3_EXTRACTED)

CHUNK_1_PDF_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_1_PDF)
CHUNK_2_PDF_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_2_PDF)
CHUNK_3_PDF_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_3_PDF)

CHUNK_1_COORDS_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_1_COORDS)
CHUNK_2_COORDS_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_2_COORDS)
CHUNK_3_COORDS_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_3_COORDS)

CHUNK_1_LINES_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_1_LINES)
CHUNK_2_LINES_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_2_LINES)
CHUNK_3_LINES_FILE = Path(__file__).parent.joinpath(OCR_CHUNKS_DIR, CHUNK_3_LINES)
###########################


CHUNKS_MAPPING = {
    TaskEnum.annotate: ANNOTATIONS_RESULT_FILE,
    TaskEnum.vectorize: VECTORIZATION_RESULT_FILE,
    TaskEnum.clinical_summary: FIXTURE_CLINICAL_SUMMARY,
    TaskEnum.covid_specific: FIXTURE_COVID_SPECIFIC,
    TaskEnum.deid: FIXTURE_DEID,
    TaskEnum.demographics: FIXTURE_DEMOGRAPHICS,
    TaskEnum.oncology_only: FIXTURE_ONCOLOGY_ONLY,
    TaskEnum.oncology_summary: FIXTURE_ONCOLOGY_SUMMARY,
    TaskEnum.phi_tokens: FIXTURE_PHI_TOKENS,
}

# TODO: should make function for this
CHUNK_TEXT_FILE_KEY = os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                                   DOCUMENT_ID,
                                   TasksConstants.STORAGE_CHUNKS_PREFIX,
                                   CHUNK_ID,
                                   f'{CHUNK_ID}.'
                                   f'{TasksConstants.DOCUMENT_TEXT_SUFFIX}.'
                                   f'{FileExtensions.TXT.value}')

DOCUMENT_TEXT_FILE_KEY = os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                                      DOCUMENT_ID,
                                      f'{DOCUMENT_ID}.'
                                      f'{TasksConstants.DOCUMENT_TEXT_SUFFIX}.'
                                      f'{FileExtensions.TXT.value}')

DOCUMENT_SOURCE_TEXT_FILE_KEY = os.path.join(TasksConstants.STORAGE_DOCUMENTS_PREFIX,
                                             DOCUMENT_ID,
                                             f'{DOCUMENT_ID}.'
                                             f'{TasksConstants.SOURCE_FILE_SUFFIX}.'
                                             f'{Path(SOURCE_TXT).suffix[1:]}')

job_info = JobDocumentInfo(
    status=WorkStatus.processing
)

user_info = UserInfo(
    user_uuid=USER_UUID
)


class ChunkDataTaskInfo:
    covid_specific = CovidSpecificTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 564061, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 13, 977781, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(CovidSpecificTaskInfo),
        status=TaskStatus.completed_success,
    )
    phi_tokens = PHITokenTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 564061, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 13, 977781, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(PHITokenTaskInfo),
        status=TaskStatus.completed_success,
    )
    demographic = DemographicsTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 564061, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 13, 977781, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(DemographicsTaskInfo),
        status=TaskStatus.completed_success,
    )
    vectorize = VectorizeTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 46, 673778, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 491936, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(VectorizeTaskInfo),
        status=TaskStatus.completed_success,
    )
    annotate = AnnotationTaskInfo(
        attempts=1,
        status=TaskStatus.completed_success,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 36, 249246, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 29, 46, 649456, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(AnnotationTaskInfo),
    )

    oncology_only = OncologyOnlyTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 587883, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 15, 662822, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(OncologyOnlyTaskInfo),
        status=TaskStatus.completed_success,
    )
    drug = DrugModelTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 587883, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 15, 662822, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(DrugModelTaskInfo),
        status=TaskStatus.completed_success,
    )
    lab = LabModelTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 597629, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 12, 335899, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(LabModelTaskInfo),
        status=TaskStatus.completed_success,
    )
    covid_lab = CovidLabModelTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 597629, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 12, 335899, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(CovidLabModelTaskInfo),
        status=TaskStatus.completed_success,
    )
    device_procedure = OncologyOnlyTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 587883, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 15, 662822, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(OncologyOnlyTaskInfo),
        status=TaskStatus.completed_success,
    )
    disease_sign = DiseaseSignTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 587883, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 15, 662822, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(DiseaseSignTaskInfo),
        status=TaskStatus.completed_success,
    )

    vital = VitalSignTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 597629, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 12, 335899, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(VitalSignTaskInfo),
        status=TaskStatus.completed_success,
    )

    smoking = SmokingTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 597629, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 12, 335899, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(SmokingTaskInfo),
        status=TaskStatus.completed_success,
    )
    imaging_finding = ImagingFindingTaskInfo(
        attempts=1,
        started_at=datetime.datetime(2020, 7, 16, 18, 29, 59, 597629, tzinfo=datetime.timezone.utc),
        completed_at=datetime.datetime(2020, 7, 16, 18, 30, 12, 335899, tzinfo=datetime.timezone.utc),
        results_file_key=get_result_file_key(ImagingFindingTaskInfo),
        status=TaskStatus.completed_success,
    )


class DocumentDataTaskInfo:
    annotate = AnnotationTaskInfo(
        status=TaskStatus.completed_success,
        results_file_key=get_result_file_key(AnnotationTaskInfo)
    )

    app_ingest = AppIngestTaskInfo(
        attempts=3,
        started_at=parse('2020-07-16 18:30:46.827705+00:00'),
        completed_at=parse('2020-07-16 18:30:53.675475+00:00'),
        doc_ref_uuid=DOCUMENT_UUID,
        status=TaskStatus.completed_success,
    )

    app_reprocess = AppReprocessTaskInfo(
        attempts=1,
        started_at=parse('2020-07-16 18:30:46.827705+00:00'),
        completed_at=parse('2020-07-16 18:30:53.675475+00:00'),
        status=TaskStatus.completed_success,
    )

    app_summary = AllModelSummaryTaskInfo(
        results_file_key=get_result_file_key(AllModelSummaryTaskInfo),
        status=TaskStatus.completed_success,
    )

    deduplicator = DeduplicatorTaskInfo(
        attempts=1,
        started_at=parse('2020-07-16 18:30:24.411787+00:00'),
        completed_at=parse('2020-07-16 18:30:26.598765+00:00'),
        results_file_key=get_result_file_key(DeduplicatorTaskInfo),
        status=TaskStatus.completed_success,
    )

    deid = DeidTaskInfo(
        attempts=1,
        started_at=parse('2020-07-16 18:30:24.393733+00:00'),
        completed_at=parse('2020-07-16 18:30:27.201457+00:00'),
        # TODO: it seems redacted_txt_file_key is useless field
        redacted_txt_file_key=get_result_file_key(DeidTaskInfo),
        results_file_key=get_result_file_key(DeidTaskInfo),
        status=TaskStatus.completed_success,
    )

    demographics = DemographicsTaskInfo(
        results_file_key=get_result_file_key(DemographicsTaskInfo),
        status=TaskStatus.completed_success,
    )
    disassembler = DisassembleTaskInfo(
        attempts=1,
        started_at=parse('2020-07-16 18:29:34.156832+00:00'),
        completed_at=parse('2020-07-16 18:29:36.233134+00:00'),
        status=TaskStatus.completed_success,
    )

    discharge = DischargeTaskInfo(
        status=TaskStatus.submitted,
        dependencies=[
            TaskEnum.disassemble,
            TaskEnum.reassemble,
            TaskEnum.app_ingest,
            TaskEnum.deid,
            TaskEnum.deduplicator,
        ],
    )
    app_summary = AllModelSummaryTaskInfo(
        attempts=1,
        started_at=parse('2020-07-16 18:30:24.393733+00:00'),
        completed_at=parse('2020-07-16 18:30:27.201457+00:00'),
        # TODO: it seems redacted_txt_file_key is useless field
        results_file_key=get_result_file_key(AllModelSummaryTaskInfo),
        status=TaskStatus.completed_success,

    )
    oncology_only = OncologyOnlyTaskInfo(
        results_file_key=get_result_file_key(OncologyOnlyTaskInfo),
        status=TaskStatus.completed_success,
    )

    phi_tokens = PHITokenTaskInfo(
        results_file_key=get_result_file_key(PHITokenTaskInfo),
        status=TaskStatus.completed_success,
    )
    vital = VitalSignTaskInfo(
        results_file_key=get_result_file_key(VitalSignTaskInfo),
        status=TaskStatus.completed_success,
    )

    drug = DrugModelTaskInfo(
        results_file_key=get_result_file_key(DrugModelTaskInfo),
        status=TaskStatus.completed_success,
    )
    smoking = VitalSignTaskInfo(
        results_file_key=get_result_file_key(VitalSignTaskInfo),
        status=TaskStatus.completed_success,
    )

    covid_lab = DrugModelTaskInfo(
        results_file_key=get_result_file_key(DrugModelTaskInfo),
        status=TaskStatus.completed_success,
    )
    lab = VitalSignTaskInfo(
        results_file_key=get_result_file_key(VitalSignTaskInfo),
        status=TaskStatus.completed_success,
    )

    imaging_finding = DrugModelTaskInfo(
        results_file_key=get_result_file_key(DrugModelTaskInfo),
        status=TaskStatus.completed_success,
    )
    device_procedure = VitalSignTaskInfo(
        results_file_key=get_result_file_key(VitalSignTaskInfo),
        status=TaskStatus.completed_success,
    )
    pdf_embedder = PDFEmbedderTaskInfo(
        results_file_key=get_result_file_key(PDFEmbedderTaskInfo),
        status=TaskStatus.submitted
    )
    ocr = OCRTaskInfo(
        results_file_key=get_result_file_key(OCRTaskInfo),
        status=TaskStatus.completed_success
    )

    disease_sign = DrugModelTaskInfo(
        results_file_key=get_result_file_key(DrugModelTaskInfo),
        status=TaskStatus.completed_success,
    )

    reassembler = ReassembleTaskInfo(
        attempts=1,
        started_at=parse('2020-07-16 18:30:17.679937+00:00'),
        completed_at=parse('2020-07-16 18:30:24.304179+00:00'),
        status=TaskStatus.completed_success,
    )

    vectorize = VectorizeTaskInfo(
        status=TaskStatus.completed_success,
    )


document_info = DocumentInfo(
    document_id=DOCUMENT_ID,
    document_size=DOCUMENT_SIZE,
    source=SOURCE_TXT,
    source_file_key=DOCUMENT_SOURCE_TEXT_FILE_KEY,
    source_hash=SOURCE_HASH,
    text_file_key=DOCUMENT_TEXT_FILE_KEY,
    tid=DOCUMENT_ID,
)

CHUNK_TASK = ChunkTask(
    started_at=datetime.datetime(2020, 7, 16, 18, 29, 35, 580915, tzinfo=datetime.timezone.utc),
    completed_at=datetime.datetime(2020, 7, 16, 18, 30, 17, 590309, tzinfo=datetime.timezone.utc),
    task_statuses={
        TaskEnum.phi_tokens: ChunkDataTaskInfo.phi_tokens,
        TaskEnum.vectorize: ChunkDataTaskInfo.vectorize,
        TaskEnum.annotate: ChunkDataTaskInfo.annotate,
        TaskEnum.drug: ChunkDataTaskInfo.drug,
        TaskEnum.oncology_only: ChunkDataTaskInfo.oncology_only,
        TaskEnum.vital_signs: ChunkDataTaskInfo.vital,
        TaskEnum.lab: ChunkDataTaskInfo.lab,
        TaskEnum.covid_lab: ChunkDataTaskInfo.covid_lab,
        TaskEnum.smoking: ChunkDataTaskInfo.oncology_only,
        TaskEnum.device_procedure: ChunkDataTaskInfo.device_procedure,
        TaskEnum.imaging_finding: ChunkDataTaskInfo.imaging_finding,
        TaskEnum.demographics: ChunkDataTaskInfo.demographic,
        TaskEnum.disease_sign: ChunkDataTaskInfo.disease_sign
    },
    performed_tasks=[
        TaskEnum.phi_tokens,
        TaskEnum.vectorize,
        TaskEnum.annotate,
        TaskEnum.oncology_only,
        TaskEnum.demographics,
    ],
    document_id=DOCUMENT_ID,
    job_id=JOB_ID,
    text_span=[0, 100000],
    chunk_num=1,
    chunk_size=DOCUMENT_SIZE,
    text_file_key=CHUNK_TEXT_FILE_KEY,
    processing_duration=183,
)

DOCUMENT_TASK = DocumentTask(
    started_at=parse('2020-07-16 18:29:32.609304+00:00'),
    completed_at=parse('2020-07-16 18:30:53.714540+00:00'),
    task_statuses={
        TaskEnum.discharge: DocumentDataTaskInfo.discharge,
        TaskEnum.disassemble: DocumentDataTaskInfo.disassembler,
        TaskEnum.reassemble: DocumentDataTaskInfo.reassembler,
        TaskEnum.app_ingest: DocumentDataTaskInfo.app_ingest,
        TaskEnum.app_reprocess: DocumentDataTaskInfo.app_reprocess,
        TaskEnum.deid: DocumentDataTaskInfo.deid,
        TaskEnum.deduplicator: DocumentDataTaskInfo.deduplicator,
        TaskEnum.phi_tokens: DocumentDataTaskInfo.phi_tokens,
        TaskEnum.vectorize: DocumentDataTaskInfo.vectorize,
        TaskEnum.annotate: DocumentDataTaskInfo.annotate,
        TaskEnum.app_summary: DocumentDataTaskInfo.app_summary,
        TaskEnum.demographics: DocumentDataTaskInfo.demographics},
    job_id=JOB_ID,
    operation_statuses={
        TaskOperation.app_ingest: OperationInfo(
            operation=TaskOperation.app_ingest,
            status=TaskStatus.processing,
        )
    },
    document_info=document_info,
    chunk_tasks=[
        TaskEnum.phi_tokens,
        TaskEnum.vectorize,
        TaskEnum.annotate,
        TaskEnum.oncology_only,
        TaskEnum.demographics,
    ],
    chunks=[CHUNK_ID],
    operations=[TaskOperation.app_ingest],
    performed_tasks=[
        TaskEnum.disassemble,
        TaskEnum.reassemble,
        TaskEnum.deid,
        TaskEnum.deduplicator,
        TaskEnum.app_ingest,
        TaskEnum.app_ingest,
        TaskEnum.app_ingest,
        TaskEnum.discharge,
    ],
)

DOCUMENT_TASK_WITH_OCR = DocumentTask(
    started_at=parse('2020-07-16 18:29:32.609304+00:00'),
    completed_at=parse('2020-07-16 18:30:53.714540+00:00'),
    task_statuses={
        TaskEnum.discharge: DocumentDataTaskInfo.discharge,
        TaskEnum.disassemble: DocumentDataTaskInfo.disassembler,
        TaskEnum.reassemble: DocumentDataTaskInfo.reassembler,
        TaskEnum.app_ingest: DocumentDataTaskInfo.app_ingest,
        TaskEnum.app_reprocess: DocumentDataTaskInfo.app_reprocess,
        TaskEnum.deid: DocumentDataTaskInfo.deid,
        TaskEnum.deduplicator: DocumentDataTaskInfo.deduplicator,
        TaskEnum.phi_tokens: DocumentDataTaskInfo.phi_tokens,
        TaskEnum.vectorize: DocumentDataTaskInfo.vectorize,
        TaskEnum.annotate: DocumentDataTaskInfo.annotate,
        TaskEnum.app_summary: DocumentDataTaskInfo.app_summary,
        TaskEnum.demographics: DocumentDataTaskInfo.demographics,
        TaskEnum.pdf_embedder: DocumentDataTaskInfo.pdf_embedder,
        TaskEnum.ocr: DocumentDataTaskInfo.ocr
    },
    job_id=JOB_ID,
    operation_statuses={
        TaskOperation.app_ingest: OperationInfo(
            operation=TaskOperation.app_ingest,
            status=TaskStatus.processing,
        )
    },
    document_info=document_info,
    chunk_tasks=[
        TaskEnum.phi_tokens,
        TaskEnum.vectorize,
        TaskEnum.annotate,
        TaskEnum.oncology_only,
        TaskEnum.demographics,
    ],
    chunks=[CHUNK_ID],
    operations=[TaskOperation.app_ingest],
    performed_tasks=[
        TaskEnum.disassemble,
        TaskEnum.reassemble,
        TaskEnum.deid,
        TaskEnum.deduplicator,
        TaskEnum.app_ingest,
        TaskEnum.app_ingest,
        TaskEnum.app_ingest,
        TaskEnum.discharge,
    ],
)

JOB_TASK = JobTask(
    job_id=JOB_ID,

    # TODO: this field should be renamed
    document_info={
        DOCUMENT_ID: job_info,
    },
    operations=[TaskOperation.app_ingest],
    required_features=REQUIRED_FEATURES,
    processed_files={
        SOURCE_TXT: DOCUMENT_ID,
    },
    started_at=parse('2020-07-16 18:29:29.675159+00:00'),
    user_info=user_info,
    app_destination='Test Destination 0',
)
