import asyncio
from io import BytesIO
import itertools
from typing import BinaryIO

from app.core.errors import ResourceNotFound
from app.core.models import Document, User, Username, Project
from app.core.ports.repository import FileRepository, UserRepository, ProjectRepository
from app.core.ports.gateway import PasswordHashGateway, TaskQueueGateway


class FakeProjectRepository(ProjectRepository):
    def __init__(self, setup: list[Project] = []):
        self._projects: dict[int, Project] = {}
        self._next_id: int | None = None
        for project in setup:
            self.setup_project(project)

    async def get(self, project_id: int) -> Project:
        project = self._projects.get(project_id)
        if project is None:
            raise ResourceNotFound(f"No project with id:<{project_id}>")
        return project

    async def get_all(self, user: Username) -> list[Project]:
        return [p for p in self._projects.values() if user in p.collaborators]

    async def save(self, project: Project) -> Project:
        if project.id is None:
            project.id = self._gen_id()
        self._projects[project.id] = project
        return project

    async def delete(self, project: Project) -> None:
        if project.id is None:
            raise RuntimeError("Project.id is None")
        del self._projects[project.id]

    async def create_document(self, project_id: int, upload_filename) -> Document:
        document = Document(self._gen_id(), project_id, upload_filename)
        self._projects[project_id].documents.append(document)
        return document

    async def get_by_document_id(self, document_id: int) -> Project:
        if document_id is None:
            raise RuntimeError("Document.id is None")
        for p in self._projects.values():
            for d in p.documents:
                if d.id == document_id:
                    return p
        raise ResourceNotFound(f"<Document id={document_id}> not found in any project")

    def setup_id(self, next_id: int) -> None:
        self._next_id = next_id

    def setup_project(self, project: Project) -> None:
        if project.id is None:
            raise RuntimeError("Project.id is none")
        self._projects[project.id] = project

    def contains(self, project) -> bool:
        return project.id is not None and project.id in self._projects and self._projects[project.id] == project

    def _gen_id(self) -> int:
        if self._next_id is None:
            raise RuntimeError("cannot assign id - call .setup_id() first")
        next_id, self.next_id = self._next_id, None
        return next_id


class FakeFileRepository(FileRepository):
    def __init__(self, setup_id_text: list[tuple[int, str]] = []):
        self.files: dict[int, BinaryIO] = {k: BytesIO(v.encode()) for k, v in setup_id_text}

    async def save(self, file_id: int, file: BinaryIO) -> None:
        self.files[file_id] = file

    async def delete(self, file_id: int) -> None:
        del self.files[file_id]

    async def get(self, file_id: int) -> BinaryIO:
        return self.files[file_id]

    def contains(self, file_id: int) -> bool:
        return file_id in self.files


class FakeUserRepository(UserRepository):
    def __init__(self, users: list[tuple[Username, str]] = []):
        self.id_gen = itertools.count(1)
        self.users = {u: User(next(self.id_gen), u, pw) for u, pw in users}

    async def get_or_none(self, username: Username) -> User | None:
        print(self.users)
        return self.users.get(username)

    async def exists(self, username: Username) -> bool:
        return username in self.users

    async def create(self, username: Username, password) -> User:
        user = User(next(self.id_gen), username, password)
        self.users[username] = user
        return user


class FakePasswordHashGateway(PasswordHashGateway):
    def hash(self, plain: str) -> str:
        return plain


class FakeTaskQueueGateway(TaskQueueGateway):
    def __init__(self):
        self.tasks = []

    def add_task(self, func, *args, **kwargs) -> None:
        self.tasks.append(asyncio.create_task(func(*args, **kwargs)))

    async def complete_tasks(self) -> None:
        await asyncio.gather(*self.tasks)
