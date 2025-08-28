from abc import ABC, abstractmethod
from typing import BinaryIO

from ..models import Document, Project, User, Username


class DocumentRepository(ABC):
    @abstractmethod
    async def get(self, document_id: int) -> Document:
        """get document by id"""

    @abstractmethod
    async def get_all(self, user: Username, project_id: int) -> list[Document]:
        """get all documents available for user in a project with given id"""

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
    async def get_all(self, user: Username) -> list[Project]:
        """get all project available for user"""

    @abstractmethod
    async def save(self, project: Project) -> Project:
        """persist a project"""

    @abstractmethod
    async def delete(self, project: Project):
        """delete a project"""


class UserRepository(ABC):
    @abstractmethod
    async def get_or_none(self, username: Username) -> User | None:
        "get user by username"

    @abstractmethod
    async def exists(self, username: Username) -> bool:
        "check if user with given username exists"

    @abstractmethod
    async def create(self, username: Username, password) -> User:
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
