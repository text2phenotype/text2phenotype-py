from enum import Enum
from typing import (
    Any,
    Dict,
    Optional,
    Union,
)

from text2phenotype.constants.environment import Environment
from .drivers import S3Storage


class StorageProvidersEnum(Enum):
    S3 = 'S3'


class StorageProvider:
    """ Storage provider factory

    :arg StorageProvidersEnum storage_service: Storage service name, by default, is StorageProvidersEnum.S3
    """

    def __init__(self, storage_service: Optional[StorageProvidersEnum] = StorageProvidersEnum.S3, **kwargs):
        if storage_service == StorageProvidersEnum.S3:
            self.provider = S3Storage
            self.options = {
                'aws_access_key_id': Environment.AWS_ACCESS_ID.value,
                'aws_secret_access_key': Environment.AWS_ACCESS_KEY.value,
                'bucket_name': Environment.STORAGE_CONTAINER_NAME.value,
                'region_name': Environment.AWS_REGION_NAME.value,
                'endpoint_url': Environment.AWS_ENDPOINT_URL.value or None,  # Empty value should be replaced to None
            }
        self.options.update(kwargs)


def get_storage_service(provider: Optional[StorageProvidersEnum] = None, options: Dict[str, Any] = None) -> \
        Union[S3Storage]:
    """ Get Storage service instance

    :param provider: Value for a storage provider, by default, will be used DEFAULT_STORAGE_SERVICE
    :param options: Dictionary with some special or additional parameters
    :return: Storage instance, one of (S3Storage, )
    """
    if not provider and options:
        raise AttributeError('Please define service provider')

    provider = provider or getattr(StorageProvidersEnum, Environment.DEFAULT_STORAGE_SERVICE.value)
    if not options:
        options = {}
    storage = StorageProvider(provider, **options)
    return storage.provider(**storage.options)
