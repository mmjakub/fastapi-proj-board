from abc import ABC, abstractmethod
from typing import BinaryIO, Protocol


class FileService(ABC):
    @abstractmethod
    async def save(self, file_id: int, file: BinaryIO) -> None:
        """save a file"""

    @abstractmethod
    async def delete(self, file_id: int) -> None:
        """delete a file"""

    @abstractmethod
    async def get(self, file_id: int) -> BinaryIO:
        """retrive a saved file"""


class SupportsHashing(Protocol):
    def hash(self, plain: str) -> str: ...
    def verify(self, plain: str, hash: str) -> bool: ...
