import os

from text2phenotype.annotations.file_helpers import AnnotationSet
from text2phenotype.common import common
from text2phenotype.common.log import operations_logger
from text2phenotype.tagtog.helper_functions import add_annotation_to_doc_id, upload_raw_text_with_annotation_set
from text2phenotype.tagtog.tag_tog_client import TagTogClient, DEFAULT_TAG_TOG_PROJ_OWNER
from text2phenotype.tagtog.tagtog_html_to_text import TagTogText


class TagTogClientDataSource:
    """
    A class to help abstract interacting with the tag tog client

    """

    RAW_TEXT_DIR = 'raw_text'
    TEXT_SUFFIX = '.txt'

    def __init__(
            self,
            project: str,
            proj_owner: str = DEFAULT_TAG_TOG_PROJ_OWNER
    ):
        """
        :param project: tag tog project name
        :param proj_owner: who created the tag tog project, will almost always be tagtogadmin
        """
        self.project = project
        self.tag_tog_client = TagTogClient(project=self.project, proj_owner=proj_owner)

        self._ann_legend = None

    @property
    def annotation_legend(self):
        return self.tag_tog_client.annotation_legend

    @property
    def inverse_ann_legend(self):
        # returns a dictionary of label to class_id
        return self.tag_tog_client.inverse_annotation_legend

    @staticmethod
    def text2phenotype_api_out_path_from_uuid(uuid, extension, text2phenotype_api_out_dir: str):
        return os.path.join(text2phenotype_api_out_dir, 'processed', 'documents', uuid, f'{uuid}.{extension}')

    def __doc_id_to_text2phenotype_uuid(self, text2phenotype_api_out_dir):
        """
         :param text2phenotype_api_out_dir:
        :return: a dictionary of tag_tog_doc_id: filename
        """
        all_file_ids = {a['id'] for a in self.tag_tog_client.search("*")}

        # use the metadata output file from text2phenotype-api output to create a mapping of original doc_id --> text2phenotype_uuid
        output_metadata_files = common.get_file_list(text2phenotype_api_out_dir, '.metadata.json', recurse=True)
        if len(output_metadata_files) == 0:
            out_mapping = dict()
            job_manifest = common.get_file_list(text2phenotype_api_out_dir, '.manifest.json', recurse=True)
            job_manifest_json = common.read_json(job_manifest[0])
            file_mapping = job_manifest_json['processed_files']
            for file in file_mapping:
                doc_id = os.path.split(file)[1].replace(self.TEXT_SUFFIX, '')
                if doc_id in all_file_ids:
                    out_mapping[doc_id] = file_mapping[file]
                else:
                    for i in all_file_ids:
                        if doc_id in i:
                            out_mapping[i] = file_mapping[file]

        else:
            out_mapping = dict()
            for file in output_metadata_files:
                metadata = common.read_json(file)
                doc_info = metadata['document_info']
                uuid = doc_info['document_id']
                doc_id = os.path.split(doc_info['source'])[1].replace(self.TEXT_SUFFIX, '')

                if doc_id in all_file_ids:
                    out_mapping[doc_id] = uuid
                else:
                    for i in all_file_ids:
                        if doc_id in i:
                            out_mapping[i] = uuid
        return out_mapping

    def upload_text_from_text2phenotype_nlp_out(
            self,
            prediction_file_extension,
            local_pred_parent_dir: str,
            tag_tog_subfolder,
            member_list=None):
        """
        :param prediction_file_extension: the file extension of where to find the nlp results for upload
         ie: clinical_summary.json
        :param local_pred_parent_dir: THe local directory where you have the /processed/documents output files
        :param tag_tog_subfolder: the tag tog subfolder
        :param member_list: the members you want to upload annotations for
        :return: None, uploads to tag tog

        Assumes that text is collocated with outbox data
        """
        operations_logger.info(f"Using Annotation Legend: {self.annotation_legend}")
        for text2phenotype_pred_path in common.get_file_list(local_pred_parent_dir, prediction_file_extension, True):
            uuid = os.path.split(text2phenotype_pred_path)[1].replace(prediction_file_extension, '').strip('.')
            ann_set = AnnotationSet.from_biomed_output_json(common.read_json(text2phenotype_pred_path))
            # try if extracted text in folder
            text_path = text2phenotype_pred_path.replace(prediction_file_extension.strip('.'), 'extracted_text.txt')
            if os.path.isfile(text_path):
                text = common.read_text(text_path)
            else:
                operations_logger.warning(f"No text file found at {text_path}, skipping file upload")
                text = None
                continue

            upload_raw_text_with_annotation_set(
                tag_tog_folder=tag_tog_subfolder,
                text=text,
                deduplicate=False,
                split_into_chunks=False,
                ann_set=ann_set,
                member_ids=member_list,
                doc_id=uuid,
                tag_tog_client=self.tag_tog_client
            )

    def add_ann_2_docs_from_nlp_output(self, prediction_file_extension, text2phenotype_api_out_dir: str, member_list=None):
        """
        Assumes that the original name of the text file in the inbox folder pre-text2phenotype-api matches the doc_id in tag tog
        This is always true if running the get_html_from_pdfs process
        :param prediction_file_extension: ie: .clinical_summary
        :param text2phenotype_api_out_dir: the local path to the text2phenotype-api output folder
        :param member_list: the tag tog userids you want to upload annotations for
        :return: None
        """
        operations_logger.info(f"Using Annotation Legend: {self.annotation_legend}")
        text2phenotype_pred_mapping = self.__doc_id_to_text2phenotype_uuid(text2phenotype_api_out_dir=text2phenotype_api_out_dir)
        operations_logger.info(f'Found {len(text2phenotype_pred_mapping)} doc ids')
        for doc_id in text2phenotype_pred_mapping:
            uuid = text2phenotype_pred_mapping[doc_id]

            # if we already have the html file locally use that otherwise sync from tag tog api
            # get path for the biomed nlp predictions
            text2phenotype_pred_path = self.text2phenotype_api_out_path_from_uuid(
                uuid=uuid,
                extension=prediction_file_extension,
                text2phenotype_api_out_dir=text2phenotype_api_out_dir)

            ann_set = AnnotationSet.from_biomed_output_json(common.read_json(text2phenotype_pred_path))

            add_annotation_to_doc_id(
                doc_id=doc_id, ann_set=ann_set, tag_tog_client=self.tag_tog_client, member_ids=member_list)

    def push_local_pdfs_to_tag_tog(self, subfolder: str, pdfs_dir: str):
        """
        :param subfolder: tag tog subfolder you want to upload to
        :param pdfs_dir: local directory where pdfs that you want to upload are
        :return: None, pdfs will appear in tag  tog, make sure your project settings include
        "allow for native annotations"
        """
        pdfs = common.get_file_list(pdfs_dir, '.pdf', recurse=True)
        operations_logger.info(
            f'Adding {len(pdfs)} files to project {self.project} subfolder: {subfolder}')
        for pdf_fp in pdfs:
            if ' ' not in pdf_fp:
                response = self.tag_tog_client.push_pdf(file_path=pdf_fp, folder=subfolder)
                operations_logger.info(response.text)

    def fill_html_and_text_folders(self, subfolder: str, local_text_dir: str):
        """
        :param local_text_dir: here to write text files locally, ideally should be an empty folder
        :param subfolder: tag tog subfolder
        :return None, but writes to your project folders local_text_dir/raw_text/doc_id.txt
        """

        doc_ids = self.tag_tog_client.get_all_doc_ids_folder(subfolder)

        operations_logger.info(f'Found {len(doc_ids)} doc _ids in folder {subfolder}')

        for doc_id in doc_ids:
            request = self.tag_tog_client.get_html_by_doc_id(doc_id=doc_id)
            # try getting html if it doesn't work that's ok
            if request.ok:
                raw_html = request.text
            else:
                operations_logger.warning(request.text)
                continue
            text = TagTogText(raw_html).raw_text
            text_path = os.path.join(local_text_dir, f'{doc_id}.txt')
            os.makedirs(os.path.dirname(text_path), exist_ok=True)

            common.write_text(text, text_path)
