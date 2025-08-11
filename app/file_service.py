from abc import abstractmethod, ABC
import asyncio
from functools import partial
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryFile
from typing import BinaryIO
from uuid import UUID

import boto3


class FileService(ABC):
    @abstractmethod
    async def save(self, file_id: UUID, file: BinaryIO) -> None:
        """save a file"""

    @abstractmethod
    async def delete(self, file_id: UUID) -> None:
        """delete a file"""

    @abstractmethod
    async def get(self, file_id: UUID) -> BinaryIO:
        """retrive a saved file"""


class FakeFileService(FileService):
    def __init__(self):
        self.files = {}

    async def save(self, file_id: UUID, file: BinaryIO) -> None:
        temp_file = TemporaryFile()
        self.files[file_id] = temp_file
        copyfileobj(file, temp_file)

    async def delete(self, file_id: UUID) -> None:
        del self.files[file_id]

    async def get(self, file_id: UUID) -> BinaryIO:
        file = self.files[file_id]
        file.seek(0)
        return file


class LocalFileService(FileService):
    def __init__(self, temp_dir: str = "temp_files"):
        self.root_dir = root_dir = Path.cwd() / temp_dir
        if not root_dir.is_dir():
            root_dir.mkdir()

    async def save(self, file_id: UUID, file: BinaryIO) -> None:
        path = self.root_dir / str(file_id)
        with path.open("wb") as dest:
            copyfileobj(file, dest)

    async def delete(self, file_id: UUID) -> None:
        path = self.root_dir / str(file_id)
        path.unlink()

    async def get(self, file_id: UUID) -> BinaryIO:
        path = self.root_dir / str(file_id)
        return path.open("rb")


class S3FileService(FileService):
    def __init__(self, bucket: str):
        self.s3 = boto3.client("s3")
        self.bucket = bucket

    async def save(self, file_id: UUID, file: BinaryIO) -> None:
        await asyncio.get_running_loop().run_in_executor(
            None, partial(self.s3.upload_fileobj, file, self.bucket, str(file_id))
        )

    async def delete(self, file_id: UUID) -> None:
        await asyncio.get_running_loop().run_in_executor(
            None, partial(self.s3.delete_object, Bucket=self.bucket, Key=str(file_id))
        )

    async def get(self, file_id: UUID) -> BinaryIO:
        def _get_file() -> BinaryIO:
            return self.s3.get_object(Bucket=self.bucket, Key=str(file_id))["Body"].iter_chunks()

        return await asyncio.get_running_loop().run_in_executor(None, _get_file)
