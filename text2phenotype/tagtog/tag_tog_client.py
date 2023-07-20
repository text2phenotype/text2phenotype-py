from typing import List

from requests.auth import HTTPBasicAuth
import requests
import os
import json

from text2phenotype.apiclients.base_client import BaseClient
from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import Environment

DEFAULT_TAG_TOG_PROJ_OWNER = 'tagtogadmin'


class TagTogClient(BaseClient):

    def __init__(self, project: str, proj_owner: str = DEFAULT_TAG_TOG_PROJ_OWNER):
        super().__init__(f'{Environment.TAG_TOG_API.value}')

        self.auth = HTTPBasicAuth(
            username=Environment.TAG_TOG_USER.value,
            password=Environment.TAG_TOG_PWD.value
        )
        self.project = project
        self.proj_owner = proj_owner

        self.documents_suffix = '/documents/v1'
        self.params = {'project': project, 'owner': proj_owner}
        self._annotation_legend = None

    @property
    def annotation_legend(self):
        if not self._annotation_legend:
            self._annotation_legend = self.get_annotation_legend()
        return self._annotation_legend

    @property
    def inverse_annotation_legend(self):
        return {v: k for k, v in self.annotation_legend.items()}

    def push_pdf(self, file_path: str, folder: str):
        params = {**self.params, 'folder': folder}
        file = [(os.path.split(file_path)[1], open(file_path, 'rb'))]
        return self._send_doc_request(params=params, files=file)

    def push_pdf_ann(self, pdf_name: str, ann_name: str, folder: str, member: str='master'):
        params = {**self.params, 'folder': folder, "format": "default-plus-annjson", "output": "null", 'member': member}
        files = [("files", open(pdf_name, 'rb')), ("files", open(ann_name))]
        return self._send_doc_request(params=params, files=files)

    def push_text_verbatim(self, file_path: str, folder: str):
        params = {**self.params, 'folder': folder, 'format': 'verbatim'}
        file = [(os.path.split(file_path)[1], open(file_path))]
        return self._send_doc_request(params=params, files=file)

    def get_all_doc_ids_folder(self, proj_folder=None):
        folder_fp = 'pool' if not proj_folder else os.path.join('pool', proj_folder)
        query = f'folder:{folder_fp}'
        operations_logger.info(f'Running a tag tog search with query = {query}')
        # https://docs.tagtog.net/search-queries.html#search-by-folder
        docs = self.search(search_query=query)
        operations_logger.info(f'Found {len(docs)} Number of documents in the expected folder')
        if len(docs) > 0:
            doc_ids = [doc['id'] for doc in docs]
            return doc_ids

    def _send_doc_request(self, **kwargs):
        return self.post(self.documents_suffix, auth=self.auth, **kwargs)

    def _get_doc_request(self, **kwargs):
        return self.get(self.documents_suffix, auth=self.auth, **kwargs)

    def _get_request(self, **kwargs):
        url = self._get_url(self.documents_suffix)
        return requests.get(url, auth=self.auth, **kwargs)

    def search(self, search_query) -> List[dict]:
        page = 0
        docs = list()
        while page > -1:
            params = {**self.params, 'search': search_query, 'page': page}
            out = self._get_request(params=params)
            docs.extend(out.json().get('docs'))
            page = out.json().get('pages', {}).get('next')
        return docs

    def get_html_by_doc_id(self, doc_id: str):
        params = {**self.params, 'ids': doc_id, 'output': 'html'}
        return self._get_doc_request(params=params)

    def get_text_by_doc_id(self, doc_id: str):
        params = {**self.params, 'ids': doc_id, 'output': 'text'}
        return self._get_doc_request(params=params)

    def update_annotations(self, html_text: str, ann_json_dict: dict, doc_id, member='master'):
        params = {**self.params, 'output': 'null', 'format': 'anndoc', 'member': member}
        files = {
            'ann': (f'{doc_id}.ann.json', json.dumps(ann_json_dict)),
            'plain': (f'{doc_id}.plain.html', html_text)}
        return self._send_doc_request(params=params, files=files)

    def get_annotation_legend(self):
        return self.get('settings/v1/annotationsLegend', auth=self.auth, params=self.params).json()

    def push_text_ann_verbatim(self, text, ann_json, folder, doc_id, annotator_id: str = 'master'):
        params = {**self.params, 'format': 'verbatim-plus-annjson', 'output': 'null', 'folder': folder,
                  'member': annotator_id}
        files = [(doc_id, text),
                 (doc_id.replace('.txt', '.ann.json'), json.dumps(ann_json))]
        return self._send_doc_request(params=params, files=files)

    def push_text_ann_verbatim_from_fp(self, text_fp, ann_json_fp, base_fp: str, folder, annotator_id: str = 'master'):
        params = {**self.params, 'format': 'verbatim-plus-annjson', 'output': 'null', 'folder': folder,
                  'member': annotator_id}
        files = [(base_fp, open(text_fp)),
                 (base_fp, open(ann_json_fp))]
        return self._send_doc_request(params=params, files=files)

    def get_member_annjson(self, doc_id, member):
        params = {**self.params, 'ids': doc_id, 'member': member, 'output': 'ann.json'}
        return self._get_request(params=params)

    def copy_annotation(self, doc_id, old_member, new_member):
        ann_json = self.get_member_annjson(doc_id=doc_id, member=old_member).json()
        if ann_json.get('entities'):
            html = self.get_html_by_doc_id(doc_id=doc_id).text
            self.update_annotations(html, ann_json_dict=ann_json, doc_id=doc_id, member=new_member)

    def delete_records(self, record_ids: List[str]) -> requests.Response:
        """Delete records from a TagTog project.
        @param record_ids: The list of record ids to delete.
        @returns The request response
        """
        params = {**self.params, 'idType': 'tagtogID', 'ids': record_ids}

        return requests.delete(self._get_url(self.documents_suffix), params=params, auth=self.auth)
