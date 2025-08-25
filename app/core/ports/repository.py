from abc import ABC, abstractmethod
from typing import BinaryIO

from ..models import Document, Project, User


class DocumentRepository(ABC):
    @abstractmethod
    async def get(self, document_id: int) -> Document:
        """get document by id"""

    @abstractmethod
    async def get_all(self, username: str, project_id: int) -> list[Document]:
        """get document by id"""

    @abstractmethod
    async def save(self, document: Document) -> Document:
        """persist a document"""

    @abstractmethod
    async def delete(self, document: Document):
        """delete a document"""


class ProjectRepository(ABC):
    @abstractmethod
    async def get(self, project_id: int) -> Project:
        """get project by id"""

    @abstractmethod
    async def get_all(self, username: str) -> list[Project]:
        """get project by id"""

    @abstractmethod
    async def save(self, project: Project) -> Project:
        """persist a project"""

    @abstractmethod
    async def delete(self, project: Project):
        """delete a project"""


class UserRepository(ABC):
    @abstractmethod
    async def get_or_none(self, username: str) -> User | None:
        "get user by username"

    @abstractmethod
    async def exists(self, username: str) -> bool:
        "check if user with given username exists"

    @abstractmethod
    async def create(self, username: str, password) -> User:
        "create new user with unique username"


class FileRepository(ABC):
    @abstractmethod
    async def save(self, file_id: int, file: BinaryIO) -> None:
        """save a file"""

    @abstractmethod
    async def delete(self, file_id: int) -> None:
        """delete a file"""

    @abstractmethod
    async def get(self, file_id: int) -> BinaryIO:
        """retrive a saved file"""
