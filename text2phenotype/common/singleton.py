from typing import Any


def singleton(class_):
    """
    https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


class SingletonCache:
    def __init__(self):
        self.__cache = dict()

    def get(self, key: str) -> Any:
        """
        :param key: unique key for cached resource
        :return: the cached resource
        """
        return self.__cache.get(key)

    def put(self, key: str, value: Any) -> None:
        """
        :param key: unique resource key
        :param value: resource to store in cache
        :return: None
        """
        self.__cache[key] = value

    def exists(self, key: str) -> bool:
        """
        :param key: unique resource key
        :return: bool True/False the resource exists in cache
        """
        return key in self.__cache

    def clear(self, key: str = None):
        """
        Clear the given key from cache, or clear the full cache if no key is given

        :param key: unique resource key
        """
        if not key:
            self.__cache = dict()
        else:
            del self.__cache[key]
