import io
import os
import boto3
import botocore

from tempfile import TemporaryFile
from urllib.parse import urlparse

from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import Environment


def write_s3(data: bytes, file_name: str, bucket_name: str) -> bool:
    operations_logger.info(f'writing {file_name} to s3 bucket {bucket_name}')
    client = boto3.client(
        's3',
        endpoint_url=Environment.AWS_ENDPOINT_S3.value,
        aws_access_key_id=Environment.AWS_ACCESS_ID.value,
        aws_secret_access_key=Environment.AWS_ACCESS_KEY.value,
    )
    operations_logger.debug('s3 client created')

    content_type = ''
    if file_name.endswith('pdf'):
        content_type = 'application/pdf'
    elif file_name.endswith('txt'):
        content_type = 'text/plain'

    try:
        client.put_object(Bucket=bucket_name, Key=file_name, Body=data, ContentDisposition='inline', ContentType=content_type)
    except Exception as e:
        operations_logger.exception('An error occurred when writing to s3 bucket:', exc_info=True)
        return False
    return True


def write_bytes_to_s3(file_path: str, bucket_name: str) -> bool:
    operations_logger.debug(f'write_bytes_to_s3 for file {file_path} to '
                            f'bucket {bucket_name}')

    with open(file_path, 'rb') as rb_file:
        contents = rb_file.read()

    file_name = os.path.basename(file_path)
    data_result = write_s3(data=contents,
                           file_name=file_name,
                           bucket_name=bucket_name)

    return data_result


def get_content_from_s3_url(s3_url: str) -> bytes:
    """
    Given an external S3 url, fetch and return the contents of the file

    :param str|unicode s3_url:
    :return: contents of the requested file
    :rtype: str|unicode
    """
    url_obj = urlparse(s3_url)
    filename = os.path.basename(url_obj.path)
    operations_logger.debug('getting {} from {}'.format(filename, s3_url))
    client = boto3.client(
        's3',
        endpoint_url=Environment.AWS_ENDPOINT_S3.value,
        aws_access_key_id=Environment.AWS_ACCESS_ID.value,
        aws_secret_access_key=Environment.AWS_ACCESS_KEY.value,
    )
    operations_logger.debug('s3 client created')

    with TemporaryFile() as f:
        operations_logger.debug('temp file open: {}'.format(f))
        client.download_fileobj(s3_url.split('/')[-2], filename, f)
        f.seek(0)
        data = f.read()
    # TODO: this usage of r.content works well for smaller files, will need
    # optimization for larger files (see https://stackoverflow.com/a/16696317 )
    operations_logger.debug(f'returning content from get_content_from_s3_url'
                            f'({s3_url}')
    return data

# ------------------------------------------------------------------
# s3 methods, put these in text2phenotype.common.aws (after fixing the bucket name default)


def get_s3_client():
    """
    Get an instance of an "s3" client. Reads endpoint and keys from the environment. I think.
    :returns: botocore.client.S3
    """
    client = boto3.client("s3")
    # client = boto3.client(
    #     's3',
    #     endpoint_url=Environment.AWS_ENDPOINT_S3.value,
    #     aws_access_key_id=Environment.AWS_ACCESS_ID.value,
    #     aws_secret_access_key=Environment.AWS_ACCESS_KEY.value,
    # )
    operations_logger.debug('s3 client created')
    return client


def get_matching_s3_keys(bucket, prefix="", suffix=""):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    s3 = get_s3_client()
    kwargs = {"Bucket": bucket}

    # If the prefix is a single string (not a tuple of strings), we can
    # do the filtering directly in the S3 API.
    if isinstance(prefix, str):
        kwargs["Prefix"] = prefix

    while True:

        # The S3 API response is a large blob of metadata.
        # 'Contents' contains information about the listed objects.
        resp = s3.list_objects_v2(**kwargs)
        if "Contents" not in resp:
            raise ValueError(f"No content found at prefix: {prefix}; Check if prefix exists in bucket {bucket}")
        for obj in resp["Contents"]:
            key = obj["Key"]
            if key.startswith(prefix) and key.endswith(suffix):
                yield key

        # The S3 API is paginated, returning up to 1000 keys at a time.
        # Pass the continuation token into the next response, until we
        # reach the final page (when this field is missing).
        try:
            kwargs["ContinuationToken"] = resp["NextContinuationToken"]
        except KeyError:
            break


def list_keys(bucket, key_prefix):
    """
    List keys with given prefix. Uses list_objects_v2 directly
    May have issues with pagination on larger (>1000) key lists
    """
    s3_client = boto3.client("s3")
    # call only returns first 1000 keys
    contents = s3_client.list_objects_v2(Bucket=bucket, Prefix=key_prefix)["Contents"]
    key_list = [entry["Key"] for entry in contents]
    return key_list


def get_object(s3_client, bucket, key):
    s3_obj = s3_client.get_object(Bucket=bucket, Key=key)
    output = s3_obj["Body"].read()
    return output


def get_object_str(s3_client, bucket, key):
    """
    Read a key in a bucket and return it as a string
    """
    output_string = get_object(s3_client, bucket, key).decode("utf-8")
    return output_string


def put_object(s3_client, bucket, key, obj):
    """
    Put an object in the bucket at given key
    Currently untested restrictions on types of data (eg bytes, strings, pkl)

    :param s3_client: botocore.client.S3
    :param bucket: str
    :param key: str, the S3 path to place the object; does not include bucket name
    :param obj: Any
    """
    s3_client.put_object(Bucket=bucket, Key=key, Body=obj)


def download_file(s3_client, bucket, s3_file_key, local_file_path):
    """
    :param s3_client: botocore.client.S3
    :param bucket: str
    :param s3_file_key: str
    :param local_file_path: str
    """
    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
    try:
        file_exists = True
        s3_client.download_file(bucket, s3_file_key, local_file_path)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            file_exists = False
            operations_logger.info(f"The object does not exist: {s3_file_key}")
        else:
            raise
    if file_exists:
        operations_logger.debug(f"Wrote S3 file: {s3_file_key} -> {local_file_path}")


def sync_down_files(s3_client, bucket, s3_keys, local_folder_path):
    """
    Download set of files from s3_keys to a local path
    Iterates through keys, taking only the "filename" and saving with that filename to `local_folder_path`
    :param s3_client: botocore.client.S3
    :param bucket: str
    :param s3_keys: List[str]
    :param local_folder_path: str
    :return: list
    """
    os.makedirs(local_folder_path, exist_ok=True)
    saved_filenames = []
    for key in s3_keys:
        prefix, filename = os.path.split(key)
        local_filename = os.path.join(local_folder_path, filename)
        download_file(s3_client, bucket=bucket, s3_file_key=key, local_file_path=local_filename)

        saved_filenames.append(local_filename)
    return saved_filenames
