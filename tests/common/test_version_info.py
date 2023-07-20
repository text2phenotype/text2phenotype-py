import unittest
import logging

from git.exc import InvalidGitRepositoryError
from unittest.mock import patch, mock_open
from datetime import datetime
from pathlib import Path

from text2phenotype.common.version_info import VersionInfo, get_version_info


class TestVersionInfo(unittest.TestCase):
    now = datetime.utcnow()
    test_time = datetime(now.year,
                         now.month,
                         now.day,
                         now.hour,
                         now.minute,
                         now.second)

    mock_data = {
        'product_id': 'text2phenotype-py',
        'product_version': '1.2.3',
        'commit_id': 'ABCDEF1234567890',
        'commit_date': test_time.isoformat(),
        'tags': ['test1', 'test2'],
        'active_branch': 'DETACHED HEAD',
        'docker_image': 'text2phenotypeinc/text2phenotype-py:test_ABCDEF1234567890_20181128134813',
    }

    mock_metadata = f'''{{ \
      "DOCKER_METADATA_TIMESTAMP": "{test_time.strftime('%Y%m%d%H%M%S')}", \
      "DOCKER_TAG_EXPLICIT": "test_ABCDEF1234567890_20181128134813", \
      "DOCKER_TARGET_ORG": "text2phenotypeinc", \
      "DOCKER_TARGET_REPO": "text2phenotype-py", \
      "GIT_BRANCH": "DETACHED HEAD", \
      "GIT_BRANCH_SAFE": "DETACHED HEAD", \
      "GIT_REPO": "text2phenotype-py", \
      "GIT_SHA": "ABCDEF1234567890", \
      "GIT_TAGS": ["test1", "test2"]
    }}'''

    def test_from_dict(self):
        ver_info = VersionInfo(**self.mock_data)
        self.assertEqual(ver_info.product_id, self.mock_data['product_id'])
        self.assertEqual(ver_info.product_version, self.mock_data['product_version'])
        self.assertEqual(ver_info.commit_id, self.mock_data['commit_id'])
        self.assertEqual(ver_info.commit_date, self.test_time)
        self.assertListEqual(ver_info.tags, self.mock_data['tags'])
        self.assertEqual(ver_info.active_branch, self.mock_data['active_branch'])

    def test_from_no_dict(self):
        ver_info = VersionInfo()
        self.assertIsNone(ver_info.product_id)
        self.assertIsNone(ver_info.product_version)
        self.assertIsNone(ver_info.commit_id)
        self.assertIsNone(ver_info.commit_date)
        self.assertListEqual(ver_info.tags, [])
        self.assertIsNone(ver_info.active_branch)

    def test_to_dict(self):
        test_dict = VersionInfo(**self.mock_data).to_dict()
        self.assertDictEqual(test_dict, self.mock_data)

    def test_get_version_info_from_git(self):
        with patch("pathlib.Path.resolve") as mock_file:
            mock_file.side_effect = FileNotFoundError

            repo_path = Path(__file__).parents[2]

            try:
                ver_info = get_version_info(repo_path)
            except InvalidGitRepositoryError as err:
                logging.warning("No valid git repository detected ('%s'). Skipping... ", err)
            else:
                ver_dict = ver_info.to_dict()
                ver_info2 = VersionInfo(**ver_dict)

                self.assertEqual(ver_info.product_id, ver_info2.product_id)
                self.assertEqual(ver_info.product_version, ver_info2.product_version)
                self.assertEqual(ver_info.commit_id, ver_info2.commit_id)
                self.assertEqual(ver_info.commit_date, ver_info2.commit_date)
                self.assertListEqual(ver_info.tags, ver_info2.tags)
                self.assertEqual(ver_info.active_branch, ver_info2.active_branch)
                self.assertEqual(ver_info.docker_image, None)

    def test_get_version_info_from_metadata(self):
        repo_path = Path(__file__).parents[2]
        metadata_path = repo_path / ".docker.metadata"

        with patch("builtins.open", mock_open(read_data=self.mock_metadata)) as mock_file:
            assert open(metadata_path).read() == self.mock_metadata
            mock_file.assert_called_with(metadata_path)

            ver_info = get_version_info(repo_path)

            # Check result with "mock_data" without "product_version"
            expected_data = self.mock_data.copy()
            del expected_data['product_version']
            ver_info2 = VersionInfo(**expected_data)

            self.assertEqual(ver_info.product_id, ver_info2.product_id)
            self.assertEqual(ver_info.product_version, ver_info2.product_version)
            self.assertEqual(ver_info.commit_id, ver_info2.commit_id)
            self.assertEqual(ver_info.commit_date, ver_info2.commit_date)
            self.assertListEqual(ver_info.tags, ver_info2.tags)
            self.assertEqual(ver_info.active_branch, ver_info2.active_branch)
            self.assertEqual(ver_info.docker_image, ver_info2.docker_image)
