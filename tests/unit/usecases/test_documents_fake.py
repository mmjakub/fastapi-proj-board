import pytest

from app.core import services as sut
from app.core.errors import ForbiddenError, ResourceNotFound


# Create
async def test_owner_can_create_a_document(
    test_user, test_project_id, nonexistent_document_id, test_filename, test_file, fake_repo, fake_file_repo
):
    fake_repo.setup_id(nonexistent_document_id)
    document = await sut.create_document(
        test_user, test_project_id, test_filename, test_file, fake_repo, fake_file_repo
    )

    assert document.id == nonexistent_document_id
    assert document.project_id == test_project_id
    assert document.upload_filename == test_filename


async def test_collaborator_can_create_a_document(
    collaborator, test_project_id, nonexistent_document_id, test_filename, test_file, fake_repo, fake_file_repo
):
    fake_repo.setup_id(nonexistent_document_id)
    document = await sut.create_document(
        collaborator, test_project_id, test_filename, test_file, fake_repo, fake_file_repo
    )

    assert document.id == nonexistent_document_id
    assert document.project_id == test_project_id
    assert document.upload_filename == test_filename


async def test_user_can_download_created_document(
    test_user, test_project_id, nonexistent_document_id, test_filename, test_file, fake_repo, fake_file_repo
):
    fake_repo.setup_id(nonexistent_document_id)
    await sut.create_document(test_user, test_project_id, test_filename, test_file, fake_repo, fake_file_repo)

    filename, file = await sut.download_document(test_user, nonexistent_document_id, fake_repo, fake_file_repo)

    assert file == test_file
    assert filename == test_filename


async def test_external_user_cannot_create_a_document(
    unrelated_user, test_project_id, test_filename, test_file, fake_repo, fake_file_repo
):
    with pytest.raises(ForbiddenError):
        await sut.create_document(unrelated_user, test_project_id, test_filename, test_file, fake_repo, fake_file_repo)


# Update
async def test_owner_can_update_a_document(
    test_user, existing_document_id, new_filename, new_file, fake_repo, fake_file_repo
):
    document = await sut.update_document(
        test_user, existing_document_id, new_filename, new_file, fake_repo, fake_file_repo
    )

    assert document.id == existing_document_id
    assert document.upload_filename == new_filename


async def test_collaborator_can_update_a_document(
    collaborator, existing_document_id, new_filename, new_file, fake_repo, fake_file_repo
):
    document = await sut.update_document(
        collaborator, existing_document_id, new_filename, new_file, fake_repo, fake_file_repo
    )

    assert document.id == existing_document_id
    assert document.upload_filename == new_filename


async def test_user_can_download_updated_document(
    test_user, existing_document_id, new_filename, new_file, fake_repo, fake_file_repo
):
    await sut.update_document(test_user, existing_document_id, new_filename, new_file, fake_repo, fake_file_repo)

    filename, file = await sut.download_document(test_user, existing_document_id, fake_repo, fake_file_repo)

    assert file == new_file
    assert filename == new_filename


async def test_external_user_cannot_update_a_document(
    unrelated_user, existing_document_id, new_filename, new_file, fake_repo, fake_file_repo
):
    with pytest.raises(ForbiddenError):
        await sut.update_document(
            unrelated_user, existing_document_id, new_filename, new_file, fake_repo, fake_file_repo
        )


async def test_user_cannot_update_a_nonexistent_document(
    test_user, nonexistent_document_id, new_filename, new_file, fake_repo, fake_file_repo
):
    with pytest.raises(ResourceNotFound):
        await sut.update_document(test_user, nonexistent_document_id, new_filename, new_file, fake_repo, fake_file_repo)


# Delete
async def test_owner_can_delete_a_document(test_user, existing_document_id, fake_repo, fake_file_repo, fake_tasks):
    await sut.delete_document(test_user, existing_document_id, fake_repo, fake_file_repo, fake_tasks)
    await fake_tasks.complete_tasks()

    assert not fake_file_repo.contains(existing_document_id)


async def test_collaborator_can_delete_a_document(
    collaborator, existing_document_id, fake_repo, fake_file_repo, fake_tasks
):
    await sut.delete_document(collaborator, existing_document_id, fake_repo, fake_file_repo, fake_tasks)
    await fake_tasks.complete_tasks()

    assert not fake_file_repo.contains(existing_document_id)


async def test_external_user_cannot_delete_a_document(
    unrelated_user, existing_document_id, fake_repo, fake_file_repo, fake_tasks
):
    with pytest.raises(ForbiddenError):
        await sut.delete_document(unrelated_user, existing_document_id, fake_repo, fake_file_repo, fake_tasks)


async def test_user_cannot_delete_a_nonexistent_document(
    test_user, nonexistent_document_id, fake_repo, fake_file_repo, fake_tasks
):
    with pytest.raises(ResourceNotFound):
        await sut.delete_document(test_user, nonexistent_document_id, fake_repo, fake_file_repo, fake_tasks)


# Download
async def test_owner_can_download_a_document(
    test_user, existing_document_id, test_filename, test_file, fake_repo, fake_file_repo
):
    filename, file = await sut.download_document(test_user, existing_document_id, fake_repo, fake_file_repo)

    assert filename == test_filename
    assert file.read() == test_file.read()


async def test_collaborator_can_download_a_document(
    collaborator, existing_document_id, test_filename, test_file, fake_repo, fake_file_repo
):
    filename, file = await sut.download_document(collaborator, existing_document_id, fake_repo, fake_file_repo)

    assert filename == test_filename
    assert file.read() == test_file.read()


async def test_external_user_cannot_download_a_document(
    unrelated_user, existing_document_id, test_filename, fake_repo, fake_file_repo
):
    with pytest.raises(ForbiddenError):
        await sut.download_document(unrelated_user, existing_document_id, fake_repo, fake_file_repo)


async def test_user_cannot_download_a_nonexistent_document(
    test_user, nonexistent_document_id, fake_repo, fake_file_repo
):
    with pytest.raises(ResourceNotFound):
        await sut.download_document(test_user, nonexistent_document_id, fake_repo, fake_file_repo)


# List Documents
@pytest.mark.parametrize("user", ["test_user", "collaborator"])
async def test_allowed_users_can_list_project_documents(user, test_project_id, test_project, fake_repo):
    documents = await sut.list_project_documents(user, test_project_id, fake_repo)

    assert len(documents) == 2
    assert documents == test_project.documents


async def test_external_user_cannot_list_project_documents(unrelated_user, test_project_id, fake_repo):
    with pytest.raises(ForbiddenError):
        await sut.list_project_documents(unrelated_user, test_project_id, fake_repo)
