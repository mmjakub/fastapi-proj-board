import pytest

from app.core import services as sut
from app.core.errors import ForbiddenError, ResourceNotFound


# Create
@pytest.mark.parametrize("user", ["test_user", "collaborator"])
async def test_allowed_users_can_create_a_document(
    user,
    test_project,
    nonexistent_document_id,
    created_document,
    test_filename,
    test_file,
    mock_repo,
    mock_file_repo,
):
    document = await sut.create_document(
        user, test_project.id, test_filename, test_file, mock_repo, mock_file_repo
    )

    assert document.id == nonexistent_document_id
    assert document.project_id == test_project.id
    assert document.upload_filename == test_filename
    mock_file_repo.save.assert_awaited_once_with(nonexistent_document_id, test_file)


@pytest.mark.parametrize("user", ["test_user", "collaborator"])
async def test_user_can_download_created_document(
    user,
    test_project,
    nonexistent_document_id,
    test_filename,
    test_file,
    created_document,
    mock_repo,
    mock_file_repo,
):
    test_project.documents.append(created_document)
    mock_file_repo.get.return_value = test_file
    await sut.create_document(
        user, test_project.id, test_filename, test_file, mock_repo, mock_file_repo
    )

    filename, file = await sut.download_document(
        user, nonexistent_document_id, mock_repo, mock_file_repo
    )

    assert file == test_file
    assert filename == test_filename


async def test_external_user_cannot_create_a_document(
    unrelated_user, test_project, mock, mock_repo, mock_file_repo
):
    with pytest.raises(ForbiddenError):
        await sut.create_document(
            unrelated_user, test_project.id, mock, mock, mock_repo, mock_file_repo
        )

    mock_repo.get_project_by_id.assert_awaited_once_with(test_project.id)
    mock_repo.save_project.assert_not_awaited()
    mock_file_repo.save.assert_not_awaited()


# Update
@pytest.mark.parametrize("user", ["test_user", "collaborator"])
async def test_allowed_users_can_update_a_document(
    user,
    existing_document_id,
    test_project,
    new_filename,
    new_file,
    mock_repo,
    mock_file_repo,
):
    document = await sut.update_document(
        user, existing_document_id, new_filename, new_file, mock_repo, mock_file_repo
    )

    assert document.id == existing_document_id
    assert document.upload_filename == new_filename
    mock_file_repo.save.assert_awaited_once_with(existing_document_id, new_file)


async def test_external_user_cannot_update_a_document(
    unrelated_user, existing_document_id, test_project, mock, mock_repo, mock_file_repo
):
    with pytest.raises(ForbiddenError):
        await sut.update_document(
            unrelated_user, existing_document_id, mock, mock, mock_repo, mock_file_repo
        )

    mock_repo.get_project_by_document_id.assert_awaited_once_with(existing_document_id)
    mock_repo.save_project.assert_not_awaited()
    mock_file_repo.save.assert_not_awaited()


async def test_user_cannot_update_a_nonexistent_document(
    test_user, nonexistent_document_id, mock, mock_repo, mock_file_repo
):
    mock_repo.get_project_by_document_id.side_effect = ResourceNotFound

    with pytest.raises(ResourceNotFound):
        await sut.update_document(
            test_user, nonexistent_document_id, mock, mock, mock_repo, mock_file_repo
        )

    mock_repo.get_project_by_document_id.assert_awaited_once_with(
        nonexistent_document_id
    )
    mock_repo.save_project.assert_not_awaited()
    mock_repo.create_document.assert_not_awaited()
    mock_file_repo.save.assert_not_awaited()


# Delete
@pytest.mark.parametrize("user", ["test_user", "collaborator"])
async def test_allowed_users_can_delete_a_document(
    user,
    existing_document_id,
    test_project,
    test_document,
    mock_repo,
    mock_file_repo,
    mock_tasks,
):
    await sut.delete_document(
        user, existing_document_id, mock_repo, mock_file_repo, mock_tasks
    )

    assert test_document not in test_project.documents
    mock_repo.save_project.assert_awaited_once_with(test_project)
    mock_tasks.add_task.assert_called_once_with(
        mock_file_repo.delete, existing_document_id
    )


async def test_external_user_cannot_delete_a_document(
    unrelated_user, existing_document_id, mock_repo, mock_file_repo, mock_tasks
):
    with pytest.raises(ForbiddenError):
        await sut.delete_document(
            unrelated_user, existing_document_id, mock_repo, mock_file_repo, mock_tasks
        )

    mock_repo.get_project_by_document_id.assert_awaited_once_with(existing_document_id)
    mock_repo.save_project.assert_not_awaited()
    mock_tasks.add_task.assert_not_called()
    mock_file_repo.delete.assert_not_awaited()


async def test_user_cannot_delete_a_nonexistent_document(
    test_user, nonexistent_document_id, mock_repo, mock_file_repo, mock_tasks
):
    mock_repo.get_project_by_document_id.side_effect = ResourceNotFound

    with pytest.raises(ResourceNotFound):
        await sut.delete_document(
            test_user, nonexistent_document_id, mock_repo, mock_file_repo, mock_tasks
        )

    mock_repo.get_project_by_document_id.assert_awaited_once_with(
        nonexistent_document_id
    )
    mock_repo.save_project.assert_not_awaited()
    mock_tasks.add_task.assert_not_called()
    mock_file_repo.delete.assert_not_awaited()


# Download
@pytest.mark.parametrize("user", ["test_user", "collaborator"])
async def test_allowed_users_can_download_a_document(
    user, existing_document_id, test_filename, test_file, mock_repo, mock_file_repo
):

    filename, file = await sut.download_document(
        user, existing_document_id, mock_repo, mock_file_repo
    )

    assert filename == test_filename
    assert file == test_file
    mock_repo.get_project_by_document_id.assert_awaited_once_with(existing_document_id)
    mock_file_repo.get.assert_awaited_once_with(existing_document_id)


async def test_external_user_cannot_download_a_document(
    unrelated_user, existing_document_id, test_filename, mock_repo, mock_file_repo
):
    with pytest.raises(ForbiddenError):
        await sut.download_document(
            unrelated_user, existing_document_id, mock_repo, mock_file_repo
        )

    mock_repo.get_project_by_document_id.assert_awaited_once_with(existing_document_id)
    mock_file_repo.get.assert_not_awaited()


async def test_user_cannot_download_a_nonexistent_document(
    test_user, nonexistent_document_id, mock_repo, mock_file_repo
):
    mock_repo.get_project_by_document_id.side_effect = ResourceNotFound

    with pytest.raises(ResourceNotFound):
        await sut.download_document(
            test_user, nonexistent_document_id, mock_repo, mock_file_repo
        )

    mock_repo.get_project_by_document_id.assert_awaited_once_with(
        nonexistent_document_id
    )


# List Documents
@pytest.mark.parametrize("user", ["test_user", "collaborator"])
async def test_allowed_users_can_list_project_documents(
    user, test_project_id, test_project, mock_repo
):
    documents = await sut.list_project_documents(user, test_project_id, mock_repo)

    assert len(documents) == 2
    assert documents == test_project.documents
    mock_repo.get_project_by_id.assert_awaited_once_with(test_project_id)


async def test_external_user_cannot_list_project_documents(
    unrelated_user, test_project_id, mock_repo
):
    with pytest.raises(ForbiddenError):
        await sut.list_project_documents(unrelated_user, test_project_id, mock_repo)
    mock_repo.get_project_by_id.assert_awaited_once_with(test_project_id)
