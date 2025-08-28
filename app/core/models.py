from dataclasses import dataclass
from typing import TypeAlias


@dataclass
class Document:
    id: int | None
    project_id: int
    upload_filename: str


Username: TypeAlias = str


@dataclass
class User:
    id: int | None
    username: Username
    password: str


@dataclass
class Project:
    id: int | None
    name: str
    description: str
    owner: Username
    collaborators: set[Username]
    documents: list[Document]
