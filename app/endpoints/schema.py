from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: int = Field(examples=[1], description="Id used to reference the document by")
    filename: str = Field(examples=["myfile.txt"], description="Name of the document file")


class ProjectInfo(BaseModel):
    name: str = Field(examples=["My new Project"])
    description: str = Field(examples=["Let's do cool stuff together!"])


class ProjectResponse(BaseModel):
    id: int = Field(examples=[1])
    info: ProjectInfo
    documents: list[DocumentResponse]
    owner: str = Field(examples=["alice"], description="Username of the project owner")


class RegisterUserRequest(BaseModel):
    username: str = Field(examples=["alice"])
    password: str = Field(examples=["top$ecret123"])


class UserResponse(BaseModel):
    username: str = Field(examples=["alice"])
    owned_projects: list[int] = Field(examples=[[], [1, 2]], description="List of ids of projects owned by the user")
    projects: list[int] = Field(
        examples=[[], [1, 2]],
        description="List of ids of projects on which the user collaborates. This includes projects owned by the user",
    )


class ErrorResponse(BaseModel):
    message: str = Field(
        examples=["Description of what went wrong"], description="Short human readable description of the error"
    )


class OAuthTokenResponse(BaseModel):
    access_token: str = Field(
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0."
            "KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30"
        ],
        description="encoded value of the JWT",
    )
    token_type: str = Field(examples=["Bearer"], description="Type of the access_token")
    expires: int = Field(examples=[3600], description="Duration (in seconds) for which the token is valid")


class OAuthErrorValue(str, Enum):
    invalid_request = "invalid_request"
    invalid_client = "invalid_client"
    invalid_grant = "invalid_grant"
    invalid_scope = "invalid_scope"
    unauthorized_client = "unauthorized_client"
    unsupported_grant_type = "unsupported_grant_type"


class OAuthErrorResponse(BaseModel):
    error: OAuthErrorValue = Field(
        examples=["invalid_grant"], description="Error codes according to OAuth specification"
    )
    error_description: str | None = Field(
        examples=["Invalid username/password"], description="Short human readable description of the error"
    )


error_responses: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
}
