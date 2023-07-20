from abc import ABC, abstractmethod
from enum import Enum
import os
import shutil
from typing import Union, Any

from text2phenotype.common import common
from text2phenotype.common.log import operations_logger
from text2phenotype.common.data_source import DataSourceContext


class VectorCache(ABC):
    """Class for caching a temporary file, eg the vectorized output from FeatureService or Bert tokenizer"""

    DEFAULT_ROOT = "/tmp"

    CACHE_TYPE = ""  # holds the file extension in the derived classes

    def __init__(
        self,
        context: Union[DataSourceContext, str],
        cache_root: str = DEFAULT_ROOT,
    ):
        """
        Set the context for the file cache, and a desired root directory if not the default
        :param context: subfolder used to separate train/dev/test caches
        :param cache_root: target folder to store the context in
        """
        self.context = context.value if isinstance(context, DataSourceContext) else context
        self._cache_root = (
            cache_root  # TODO: make this into a TemporaryDirectory that we can delete
        )
        self.cache_path = os.path.join(self._cache_root, str(self.context))
        self.cache_file_map = {}

        # zap the prior cache if it exists, so we load the files into cache once per session
        if os.path.exists(self.cache_path):
            shutil.rmtree(self.cache_path)
        os.makedirs(self.cache_path, exist_ok=True)
        operations_logger.debug(f"Created vector cache folder: {self.cache_path}")

    def __setitem__(self, file_key: str, data: Any):
        """
        Set the given data object to the cache
        :param file_key: str, generally the relative file path for a txt or FS file
        :param data: The target data to be stored
        :return:
        """
        self.cache_file_map[file_key] = self._get_vector_file_path(file_key)
        self.write(data, file_key)
        operations_logger.debug(f"Wrote cached vector file to: {self.cache_file_map[file_key]}")

    def __getitem__(self, file_key: str) -> Any:
        """
        Get the target data from the given file_key
        :param file_key: str, generally the relative file path for a txt or FS file
        :return: Any
        """
        return self.read(file_key)

    def __delitem__(self, file_key: str):
        """
        Remove a key from the cache; for now leave the file (will otherwise be overwritten if readded)
        :param file_key:str, generally the relative file path for a txt or FS file
        :return:
        """
        del self.cache_file_map[file_key]

    @abstractmethod
    def read(self, file_key):
        """Reader for target filetype"""
        raise NotImplementedError

    @abstractmethod
    def write(self, data, file_key):
        """Writer for target filetype"""
        raise NotImplementedError

    def exists(self, file_key: str) -> bool:
        """
        Test if cache file exists for given key
        :param file_key: str, generally the relative file path for a txt or FS file
        :return: bool
        """
        return os.path.exists(self._get_vector_file_path(file_key))

    def cleanup(self):
        """
        Manually remove the cache path and all its contents
        :return: None
        """
        if os.path.exists(self.cache_path):
            shutil.rmtree(self.cache_path)

    def _get_vector_file_path(self, txt_file_path):
        """file_key to the cache path"""
        if txt_file_path.startswith("/"):
            # join doesnt like joining when one of the other paths leads with the system root
            txt_file_path = txt_file_path[1:]
        return os.path.join(self.cache_path, f"{txt_file_path}.{self.CACHE_TYPE}")


class VectorCachePkl(VectorCache):
    """Save and load cache files as pickles"""
    CACHE_TYPE = "pkl"

    def read(self, file_key):
        return common.read_pkl(self.cache_file_map[file_key])

    def write(self, data, file_key):
        common.write_pkl(data, self.cache_file_map[file_key])


class VectorCacheJson(VectorCache):
    """Save and load cache files as JSON"""
    CACHE_TYPE = "json"

    def read(self, file_key):
        return common.read_json(self.cache_file_map[file_key])

    def write(self, data, file_key):
        common.write_json(data, self.cache_file_map[file_key])

