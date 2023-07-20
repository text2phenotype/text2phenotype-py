import os
import tempfile
import unittest

import numpy as np

from text2phenotype.common.vector_cache import VectorCachePkl, VectorCacheJson
from text2phenotype.common import common
from text2phenotype.common.data_source import DataSourceContext


class VectorCacheJsonTests(unittest.TestCase):
    tmp_root = None
    data = {"input_ids": np.array([0, 1, 99, 0.0])}

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_root = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp_root.cleanup()

    def test_init_and_cleanup(self):
        train_cache = VectorCacheJson("train", cache_root=self.tmp_root.name)
        assert os.path.exists(
            train_cache.cache_path
        ), f"Not able fo find created cache path: {train_cache.cache_path}"
        train_cache.cleanup()
        assert not os.path.exists(
            train_cache.cache_path
        ), f"Cache path still exists when should have been removed: {train_cache.cache_path}"

    def test_set_get_json(self):
        file_key = "my_inputs.txt"
        data = {"input_ids": [0, 1, 99, 0.0]}
        cache = VectorCacheJson("train", cache_root=self.tmp_root.name)
        cache[file_key] = data

        assert cache.exists(
            file_key
        ), f"File does not exist: {cache.cache_file_map[file_key]}"
        # load json manually to confirm it is a json
        json_data = common.read_json(cache._get_vector_file_path(file_key))
        self.assertDictEqual(data, json_data)

        cached_data = cache[file_key]
        self.assertDictEqual(data, cached_data)

    def test_bad_file_key(self):
        file_key = "/my_dir/my_inputs.txt"
        data = {"input_ids": [0, 1, 99, 0.0]}
        context = DataSourceContext.train
        cache = VectorCacheJson(context, cache_root=self.tmp_root.name)
        cache[file_key] = data
        self.assertEqual(
            os.path.join(self.tmp_root.name, str(context.value), file_key[1:] + ".json"),
            cache.cache_file_map[file_key])
        assert cache.exists(
            file_key
        ), f"File does not exist: {cache._get_vector_file_path(file_key)}"



class VectorCachePklTests(unittest.TestCase):
    tmp_root = None
    data = {"input_ids": np.array([0, 1, 99, 0.0])}

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_root = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp_root.cleanup()

    def test_init_and_cleanup(self):
        train_cache = VectorCachePkl("train", cache_root=self.tmp_root.name)
        assert os.path.exists(
            train_cache.cache_path
        ), f"Not able fo find created cache path: {train_cache.cache_path}"
        train_cache.cleanup()
        assert not os.path.exists(
            train_cache.cache_path
        ), f"Cache path still exists when should have been removed: {train_cache.cache_path}"

    def test_setitem(self):
        train_cache = VectorCachePkl("train", cache_root=self.tmp_root.name)
        train_cache["my_inputs.txt"] = self.data
        cached_data = common.read_pkl(train_cache.cache_file_map["my_inputs.txt"])
        np.testing.assert_array_equal(self.data["input_ids"], cached_data["input_ids"])

    def test_getitem(self):
        file_key = "my_inputs.txt"
        train_cache = VectorCachePkl("train", cache_root=self.tmp_root.name)
        train_cache.cache_file_map[file_key] = train_cache._get_vector_file_path(file_key)
        common.write_pkl(self.data, train_cache.cache_file_map[file_key])

        cache_return = train_cache[file_key]
        self.assertEqual(["input_ids"], list(cache_return.keys()))
        np.testing.assert_array_equal(self.data["input_ids"], cache_return["input_ids"])

    def test_delitem(self):
        file_key = "my_inputs.txt"
        data = {"input_ids": np.array([0, 1, 99, 0.0])}
        train_cache = VectorCachePkl("train", cache_root=self.tmp_root.name)
        # add file to cache without using setter
        train_cache.cache_file_map[file_key] = train_cache._get_vector_file_path(file_key)
        common.write_pkl(data, train_cache.cache_file_map[file_key])

        del train_cache[file_key]
        self.assertEqual({}, train_cache.cache_file_map)


if __name__ == "__main__":
    unittest.main()
