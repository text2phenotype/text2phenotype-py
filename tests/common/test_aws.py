from itertools import product
import os
import unittest
import tempfile
from moto import mock_s3

from text2phenotype.common import aws


class TestAws(unittest.TestCase):
    @mock_s3
    def test_put_get(self):
        bucket = "my_bucket"
        key = "foo/bar"
        s3_client = aws.get_s3_client()
        s3_client.create_bucket(Bucket=bucket)
        aws.put_object(s3_client, bucket, key, "baz")

        bytez = aws.get_object(s3_client, bucket, key)
        self.assertIsInstance(bytez, bytes)
        self.assertEqual(b"baz", bytez)

    @mock_s3
    def test_put_get_object_str(self):
        bucket = "my_bucket"
        key = "foo/bar"
        s3_client = aws.get_s3_client()
        s3_client.create_bucket(Bucket=bucket)
        aws.put_object(s3_client, bucket, key, "baz")

        obj_str = aws.get_object_str(s3_client, bucket, key)
        self.assertEqual("baz", obj_str)

    @mock_s3
    def test_list_keys(self):
        bucket = "my_bucket"
        keys = ["foo/1", "foo/2", "foo/3"]
        value = "baz"
        s3_client = aws.get_s3_client()
        s3_client.create_bucket(Bucket=bucket)
        for key in keys:
            aws.put_object(s3_client, bucket, key, value)

        out_keys = aws.list_keys(bucket, "foo")
        self.assertEqual(keys, out_keys)

    @mock_s3
    def test_get_matching_s3_keys(self):
        bucket = "my_bucket"
        n_keys_per_prefix = 1500
        keys = [
            "/".join([prefix, str(digit)])
            for prefix, digit in product(["foo", "bar"], list(range(n_keys_per_prefix)))
        ]
        s3_client = aws.get_s3_client()
        s3_client.create_bucket(Bucket=bucket)
        for key in keys:
            aws.put_object(s3_client, bucket, key, "I'm content!")

        matches = list(aws.get_matching_s3_keys(bucket, "foo"))
        self.assertEqual(n_keys_per_prefix, len(matches))
        self.assertEqual(
            set([f"foo/{i}" for i in range(n_keys_per_prefix)]),
            set(matches),
        )

    @mock_s3
    def test_sync_down_files(self):
        bucket = "my_bucket"
        keys = ["foo/bar/1", "foo/baz/1", "foo/bar/3"]
        value = "baz"
        s3_client = aws.get_s3_client()
        s3_client.create_bucket(Bucket=bucket)
        for key in keys:
            aws.put_object(s3_client, bucket, key, value)

        with tempfile.TemporaryDirectory() as td:
            file_paths = aws.sync_down_files(s3_client, bucket, keys, td)
            for k, filename in zip(keys, file_paths):
                # the last part of the key name is what is stored locally
                # NOTE: this doesnt behave well if a key ends with the same filename!
                # eg "foo/baz/1" overwrites "foo/bar/1" in the location "tmp_dir/1"
                self.assertEqual(os.path.join(td, os.path.split(k)[1]), filename)
                assert os.path.isfile(filename)


if __name__ == '__main__':
    unittest.main()
