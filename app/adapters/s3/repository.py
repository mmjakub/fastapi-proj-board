import asyncio
from functools import partial
from typing import BinaryIO

import boto3

from app.core.ports.repository import FileRepository


class S3FileRepository(FileRepository):
    def __init__(self, bucket_name: str, **kwargs):
        self.s3 = boto3.client("s3", **kwargs)
        self.bucket = bucket_name

    async def save(self, file_id: int, file: BinaryIO) -> None:
        await asyncio.get_running_loop().run_in_executor(
            None, partial(self.s3.upload_fileobj, file, self.bucket, str(file_id))
        )

    async def delete(self, file_id: int) -> None:
        await asyncio.get_running_loop().run_in_executor(
            None, partial(self.s3.delete_object, Bucket=self.bucket, Key=str(file_id))
        )

    async def get(self, file_id: int) -> BinaryIO:
        def _get_file() -> BinaryIO:
            try:
                return self.s3.get_object(Bucket=self.bucket, Key=str(file_id))["Body"]
            except self.s3.exceptions.NoSuchKey:
                raise FileNotFoundError

        return await asyncio.get_running_loop().run_in_executor(None, _get_file)
