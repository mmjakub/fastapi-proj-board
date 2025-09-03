from fastapi import APIRouter, UploadFile
from fastapi.responses import StreamingResponse

from ..core.models import Document
from ..jwt import JwtUsernameDep
from .dependencies import PagingDep
from .schema import DocumentResponse, error_responses, PagedList

router = APIRouter(tags=["document"], responses=error_responses)


def make_document_response(document: Document) -> DocumentResponse:
    return DocumentResponse(id=document.id, filename=document.upload_filename)


@router.get("/projects/{project_id}/documents", summary="List project documents")
async def list_all(
    project_id: int, paging: PagingDep, username: JwtUsernameDep
) -> PagedList[DocumentResponse]:
    """
    List documents in a project
      - **project_id**: id of the project, in which to create the document

    Optional query parameters
      - **page**: int = 0: page number, defaults to first page
      - **limit**: int = 20: items per page, defaults to 20

    Responses:
      - 200: Success
      - 401: Authentication required
      - 403: Not authorized to view documents in this project
      - 422: Invalid input
    """
    raise NotImplementedError


@router.post(
    "/projects/{project_id}/documents", status_code=201, summary="Create a document"
)
async def create(
    project_id: int, file: UploadFile, username: JwtUsernameDep
) -> DocumentResponse:
    """
    Upload a file to create a new document in a project. Returns created document.
      - **project_id**: id of the project, in which to create the document
      - **file**: attached file

    Responses:
      - 201: Document created
      - 401: Authentication required
      - 403: Not authorized to create documents in this project
      - 422: Invalid input
    """
    raise NotImplementedError


@router.get("/documents/{document_id}", summary="Download a document")
async def get(document_id: int, username: JwtUsernameDep) -> StreamingResponse:
    """
    Download a file represented by a document
    - **document_id**: required

    Responses:
      - 200: Success
      - 401: Authentication required
      - 403: Not authorized to download this document
      - 422: Invalid input
    """
    raise NotImplementedError


@router.put("/documents/{document_id}", summary="Update a document")
async def update(
    document_id: int, file: UploadFile, username: JwtUsernameDep
) -> DocumentResponse:
    """
    Upload a new file that will replace contents of a document
    - **document_id**:  required
    - **file**: attached file

    Responses:
      - 200: Success
      - 401: Authentication required
      - 403: Not authorized to update this document
      - 422: Invalid input
    """
    raise NotImplementedError


@router.delete("/documents/{document_id}", status_code=204, summary="Delete a document")
async def delete(
    document_id: int,
    username: JwtUsernameDep,
) -> None:
    """
    Delete a document
    - **document_id**: required

    Responses:
      - 204: Success
      - 401: Authentication required
      - 403: Not authorized to delete this document
      - 422: Invalid input
    """
    raise NotImplementedError
