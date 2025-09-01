from abc import ABC, abstractmethod
from typing import BinaryIO

from ..models import Document, Project, User, Username


class DataRepository(ABC):
    @abstractmethod
    async def get_project_by_id(self, project_id: int) -> Project:
        """get project by id"""

    @abstractmethod
    async def get_project_by_document_id(self, document_id: int) -> Project:
        """get a project that contains a document with given id"""

    @abstractmethod
    async def get_all_projects_by_username(self, user: Username) -> list[Project]:
        """get all projects where user is a collaborator"""

    @abstractmethod
    async def save_project(self, project: Project) -> Project:
        """persist a project"""

    @abstractmethod
    async def delete_project(self, project: Project) -> None:
        """delete a project"""

    @abstractmethod
    async def create_project(
        self, owner: Username, name: str, description: str
    ) -> Project:
        """crate a new project"""

    @abstractmethod
    async def create_document(self, project_id: int, upload_filename: str) -> Document:
        """crate a new document in project"""

    @abstractmethod
    async def create_user(self, username: Username, password: str) -> User:
        """create new user with unique username"""

    @abstractmethod
    async def get_user(self, username: Username) -> User:
        """get user by username"""

    @abstractmethod
    async def user_exists(self, username: Username) -> bool:
        """check if user with given username exists"""


class FileRepository(ABC):
    @abstractmethod
    async def save(self, file_id: int, file: BinaryIO) -> None:
        """save a file"""

    @abstractmethod
    async def delete(self, file_id: int) -> None:
        """delete a file"""

    @abstractmethod
    async def get(self, file_id: int) -> BinaryIO:
        """retrieve a saved file"""
