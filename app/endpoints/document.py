from fastapi import APIRouter, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse

from ..core.models import Document
from ..core.services import (
    list_project_documents,
    create_document,
    download_document,
    update_document,
    delete_document,
)
from ..jwt import JwtUsernameDep
from .dependencies import PagingDep, DataRepositoryDep, FileRepositoryDep
from .schema import DocumentResponse, error_responses, PagedList, PageInfo

router = APIRouter(tags=["document"], responses=error_responses)


def make_document_response(document: Document) -> DocumentResponse:
    return DocumentResponse(id=document.id, filename=document.upload_filename)


@router.get("/projects/{project_id}/documents", summary="List project documents")
async def list_all(
    project_id: int,
    paging: PagingDep,
    username: JwtUsernameDep,
    repository: DataRepositoryDep,
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
    documents = await list_project_documents(username, project_id, repository)
    # TODO: real repository-based paging
    return PagedList(
        items=[make_document_response(d) for d in documents],
        page=PageInfo(
            page_index=0,
            page_size=len(documents),
            total_pages=1,
            total_elements=len(documents),
        ),
    )


@router.post(
    "/projects/{project_id}/documents", status_code=201, summary="Create a document"
)
async def create(
    project_id: int,
    file: UploadFile,
    username: JwtUsernameDep,
    data_repo: DataRepositoryDep,
    file_repo: FileRepositoryDep,
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
    document = await create_document(
        username, project_id, file.filename, file.file, data_repo, file_repo
    )
    return make_document_response(document)


@router.get("/documents/{document_id}", summary="Download a document")
async def get(
    document_id: int,
    username: JwtUsernameDep,
    data_repo: DataRepositoryDep,
    file_repo: FileRepositoryDep,
) -> StreamingResponse:
    """
    Download a file represented by a document
    - **document_id**: required

    Responses:
      - 200: Success
      - 401: Authentication required
      - 403: Not authorized to download this document
      - 422: Invalid input
    """
    filename, file = await download_document(
        username, document_id, data_repo, file_repo
    )
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(
        file, headers=headers, media_type="application/octet-stream"
    )


@router.put("/documents/{document_id}", summary="Update a document")
async def update(
    document_id: int,
    file: UploadFile,
    username: JwtUsernameDep,
    data_repo: DataRepositoryDep,
    file_repo: FileRepositoryDep,
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
    document = await update_document(
        username, document_id, file.filename, file.file, data_repo, file_repo
    )
    return make_document_response(document)


@router.delete("/documents/{document_id}", status_code=204, summary="Delete a document")
async def delete(
    document_id: int,
    username: JwtUsernameDep,
    data_repo: DataRepositoryDep,
    file_repo: FileRepositoryDep,
    tasks: BackgroundTasks,
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
    await delete_document(username, document_id, data_repo, file_repo, tasks)
