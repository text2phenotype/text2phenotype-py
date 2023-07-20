import unittest

from text2phenotype.common import singleton


class TestSingletonCache(unittest.TestCase):
    obj = {"foo": "bar", "baz": 1}

    def test_get_put(self):
        cache = singleton.SingletonCache()
        cache.put("my_obj", self.obj)
        self.assertEqual(self.obj, cache.get("my_obj"))

    def test_exists(self):
        cache = singleton.SingletonCache()
        cache.put("my_obj", self.obj)
        self.assertTrue(cache.exists("my_obj"))
        self.assertFalse(cache.exists("not_my_obj"))

    def test_clear(self):
        cache = singleton.SingletonCache()
        cache.put("my_obj", self.obj)
        # test remove one object
        obj2 = self.obj.copy()
        obj2.update({"new": "thing"})
        cache.put("my_obj2", obj2)
        cache.clear("my_obj")
        self.assertFalse(cache.exists("my_obj"))
        self.assertTrue(cache.exists("my_obj2"))

        # test clear all
        cache.clear()
        self.assertEqual([], list(cache._SingletonCache__cache.keys()))


if __name__ == '__main__':
    unittest.main()
