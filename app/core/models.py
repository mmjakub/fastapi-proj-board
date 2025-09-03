from dataclasses import dataclass
from typing import TypeAlias


@dataclass
class Document:
    id: int
    project_id: int
    upload_filename: str


Username: TypeAlias = str


@dataclass
class User:
    id: int
    username: Username
    password: str


@dataclass
class Project:
    id: int
    name: str
    description: str
    owner: Username
    collaborators: set[Username]
    documents: list[Document]
