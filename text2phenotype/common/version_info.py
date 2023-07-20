import json
import os
from datetime import datetime
from dateutil import parser
from pathlib import Path
from typing import (
    Dict,
    List,
    Union,
)

import git


class VersionInfo:
    def __init__(self, **kwargs):
        self.product_id: str = kwargs.get('product_id')
        self.product_version: str = kwargs.get('product_version')
        self.tags: list = kwargs.get('tags', [])
        self.active_branch: str = kwargs.get('active_branch')
        self.commit_id: str = kwargs.get('commit_id')
        self.commit_date: datetime = kwargs.get('commit_date')
        self.docker_image: str = kwargs.get('docker_image')

        if isinstance(self.commit_date, str):
            # isoformat date: '2018-11-20T19:57:42.652888'
            date, time = self.commit_date.split('T')
            year, month, day = date.split('-')
            hour, minute, second = time.split(':')

            self.commit_date = datetime(year=int(year),
                                        month=int(month),
                                        day=int(day),
                                        hour=int(hour),
                                        minute=int(minute),
                                        second=round(float(second)))

    @property
    def commit_date_string(self):
        if isinstance(self.commit_date, datetime):
            commit_date_string = self.commit_date.isoformat()
        else:
            commit_date_string = self.commit_date
        return commit_date_string

    def to_dict(self) -> Dict[str, object]:
        ret_val = dict()
        ret_val['product_id'] = self.product_id
        ret_val['product_version'] = self.product_version
        ret_val['tags'] = self.tags
        ret_val['active_branch'] = self.active_branch
        ret_val['commit_id'] = self.commit_id
        ret_val['docker_image'] = self.docker_image
        ret_val['commit_date'] = self.commit_date_string

        return ret_val

    def to_list_dict(self) -> List[Dict[str, object]]:
        return [self.to_dict()]

    def to_version_str(self) -> str:
        """Construct short version string.

        If Git `tag` available it will be returned as result (eg: '16.4.00')

        Else, version string will be combined from parts like:
            <commit_date>.<active_brach>.<short_commit_id>

        eg: '2021.07.30.MAPPS-123.a9bfc35'
        """

        if self.tags:
            return self.tags[0]

        version_parts = []

        if self.commit_date:
            version_parts.append(f'{self.commit_date:%Y.%m.%d}')

        if self.active_branch:
            version_parts.append(self.active_branch)

        if self.commit_id:
            version_parts.append(self.commit_id[:7])

        return '.'.join(version_parts)


def get_version_info(repo_path: Union[str, Path, None] = None) -> VersionInfo:
    """
    Function gathers information on the code in the active branch of the
    git repository specified by repo_path.

    :param repo_path: path to the Git repository, by default will taken current working dir
    :return: instance of VersionInfo
    """

    if not repo_path:
        repo_path = Path()

    try:
        metadata_file = Path(f'{repo_path}/.docker.metadata')
        metadata_path = metadata_file.resolve()

        with open(metadata_path) as f:
            metadata = json.load(f)

        timestamp = metadata.get("DOCKER_METADATA_TIMESTAMP")
        commit_utc = parser.parse(timestamp).isoformat()

        docker_org = metadata.get('DOCKER_TARGET_ORG')
        docker_repo = metadata.get('DOCKER_TARGET_REPO')
        docker_tag = metadata.get("DOCKER_TAG_EXPLICIT")

        if all([docker_org, docker_repo, docker_tag]):
            docker_image = f'{docker_org}/{docker_repo}:{docker_tag}'
        elif all([docker_repo, docker_tag]):
            docker_image = f'{docker_repo}:{docker_tag}'
        else:
            docker_image = None

        res = VersionInfo(tags=metadata.get("GIT_TAGS", []),
                          active_branch=metadata.get("GIT_BRANCH"),
                          commit_id=metadata.get("GIT_SHA"),
                          commit_date=commit_utc,
                          product_id=metadata.get("GIT_REPO"),
                          docker_image=docker_image)

    except FileNotFoundError:

        repo = git.Repo(repo_path)
        try:
            branch = repo.active_branch.name
        except TypeError:
            branch = 'DETACHED HEAD'
        commit = repo.commit()

        # get product_id
        dirname = os.path.dirname(repo.git_dir)
        product_id = os.path.basename(dirname)

        # collect tags
        tags = []

        for t in repo.tags:
            if t.commit.hexsha == commit.hexsha:
                tags.append(t.name)

        # get ISO formatted datetime
        ts = commit.committed_datetime.timestamp()
        commit_utc = datetime.utcfromtimestamp(ts)

        res = VersionInfo(tags=tags,
                          active_branch=branch,
                          commit_id=commit.hexsha,
                          commit_date=commit_utc.isoformat(),
                          product_id=product_id)

    return res
