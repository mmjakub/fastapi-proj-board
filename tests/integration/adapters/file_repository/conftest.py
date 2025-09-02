import contextlib
import os
import shutil
from io import BytesIO
from typing import BinaryIO

import boto3
import pytest
from moto import mock_aws

from app.adapters.local_file.repository import LocalFileRepository
from app.adapters.s3.repository import S3FileRepository


os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def pytest_generate_tests(metafunc):
    if "repository" in metafunc.fixturenames:
        metafunc.parametrize("repository", ["local", "mock_s3"], indirect=True)


@contextlib.contextmanager
def tmp_dir():
    tmp_dir = os.urandom(8).hex()
    os.mkdir(tmp_dir)
    yield tmp_dir
    shutil.rmtree(tmp_dir)


@pytest.fixture()
def repository(request):
    match request.param:
        case "local":
            with tmp_dir() as path:
                yield LocalFileRepository(path)
        case "mock_s3":
            with mock_aws():
                bucket_name = "test_bucket"
                boto3.resource("s3").Bucket(bucket_name).create()
                yield S3FileRepository(bucket_name)
        case x:
            raise ValueError(f"Invalid repository type: '{x}'")


@pytest.fixture()
def test_file_factory():
    def factory(content: str = "foobar") -> BinaryIO:
        return BytesIO(content.encode())

    return factory
