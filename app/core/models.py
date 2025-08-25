from dataclasses import dataclass


@dataclass
class Document:
    id: int | None
    project_id: int
    upload_filename: str


@dataclass
class User:
    id: int | None
    username: str
    password: str


@dataclass
class Project:
    id: int | None
    name: str
    description: str
    owner_username: str
    collaborator_usernames: set[str]
    documents: list[Document]
