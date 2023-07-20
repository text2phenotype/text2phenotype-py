import os
from text2phenotype.annotations.file_helpers import AnnotationSet
from text2phenotype.common import common
from text2phenotype.tagtog.tag_tog_annotation import TagTogAnnotationSet
from text2phenotype.tagtog.tag_tog_client import TagTogClient, DEFAULT_TAG_TOG_PROJ_OWNER
from text2phenotype.tagtog.tag_tog_client_data_source import TagTogClientDataSource

run = False
if run:
    client = TagTogClient(project='diagnosis_signsymptom_validation')
    parent_dir = '/Users/shannon.fee/Downloads/teamcity-text2phenotype'
    ann_dir = 'BIOMED-1962/diagnosis_symptom_human_machine'
    orig_dir = 'mimic/shareclef-ehealth-evaluation-lab-2014-task-2-disorder-attributes-in-clinical-reports-1.0/20200306/RADIOLOGY_REPORT'
    folder = 'RADIOLOGY'
    text_file_list = common.get_file_list(os.path.join(parent_dir, orig_dir), '.txt', True)

    for txt_fp in text_file_list:
        # a=client.push_text_verbatim(txt_fp, folder='mimic_shareeclef')
        ann_fp = txt_fp.replace(f'/{orig_dir}/', f'/{ann_dir}/{orig_dir}/').replace('.txt', '.ann')
        if os.path.isfile(ann_fp):
            ann_set = AnnotationSet.from_file_content(common.read_text(ann_fp))

            ann_json: TagTogAnnotationSet = TagTogAnnotationSet()
            ann_json.from_annotation_set_for_text(
                ann_set,
                inverse_annotation_legend={'diagnosis': 'e_3', 'signsymptom': 'e_3', 'problem': 'e_3'})
            i = 0
            txt = common.read_text(txt_fp)
            while txt[i] in ['\n', ' ', '\t']:
                i += 1

            txt_1 = '-' * i + txt[i:]
            a = client.push_text_ann_verbatim(
                txt_1, ann_json.to_json(), folder=folder, doc_id=os.path.split(txt_fp)[1])
run_2 = False
if run_2:
    client = TagTogClientDataSource(project='demographics', proj_owner=DEFAULT_TAG_TOG_PROJ_OWNER,
                                    parent_dir='/Users/shannon.fee/Downloads/teamcity-text2phenotype')
    client.copy_annotation('CEPuser', 'master')
