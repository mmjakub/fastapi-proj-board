import asyncio
from unittest.mock import call

import pytest

from app.core import services as sut
from app.core.errors import ForbiddenError, CollaboratorConflict, ResourceNotFound
from app.core.models import Document


async def test_user_can_create_project(test_user, test_name, test_description, test_project, mock_repo):
    mock_repo.save.return_value = test_project

    project = await sut.create_project(test_user, test_name, test_description, mock_repo)

    mock_repo.save.assert_called_once()
    assert project == test_project


async def test_project_list_is_empty_when_user_has_no_projects(test_user, mock_repo):
    mock_repo.get_all.return_value = []

    projects = await sut.list_projects(test_user, mock_repo)

    mock_repo.get_all.assert_called_once_with(test_user)
    assert projects == []


async def test_project_list_contains_user_projects(test_user, test_project, mock_repo):
    mock_repo.get_all.return_value = [test_project]

    projects = await sut.list_projects(test_user, mock_repo)

    mock_repo.get_all.assert_called_once_with(test_user)
    assert projects == [test_project]


# Get Project
async def test_user_can_get_project_he_owns(test_user, test_project, mock_repo):
    mock_repo.get.return_value = test_project

    project = await sut.get_project(test_user, test_project.id, mock_repo)

    mock_repo.get.assert_called_once_with(test_project.id)
    assert project == test_project


async def test_user_can_get_project_he_collaborates_on(collaborator, test_project, mock_repo):
    test_project.collaborators.add(collaborator)
    mock_repo.get.return_value = test_project

    project = await sut.get_project(collaborator, test_project.id, mock_repo)

    mock_repo.get.assert_called_once_with(test_project.id)
    assert project == test_project


async def test_user_cannot_get_project_without_access(unrelated_user, test_project, mock_repo):
    mock_repo.get.return_value = test_project

    with pytest.raises(ForbiddenError):
        await sut.get_project(unrelated_user, test_project.id, mock_repo)


async def test_user_cannot_get_nonexistent_project(test_user, test_id, mock_repo):
    mock_repo.get.side_effect = ResourceNotFound(f"Project <id:{test_id}> does not exist")

    with pytest.raises(ResourceNotFound):
        await sut.get_project(test_user, test_id, mock_repo)


# Update Project
async def test_user_can_update_project_he_owns(test_user, test_project, updated_project, new_project_info, mock_repo):
    mock_repo.get.return_value = test_project
    mock_repo.save.return_value = updated_project

    project = await sut.update_project(test_user, test_project.id, *new_project_info, mock_repo)

    mock_repo.get.assert_called_once_with(test_project.id)
    mock_repo.save.assert_called_once_with(updated_project)
    assert project == updated_project


async def test_user_can_update_project_he_collaborates_on(
    collaborator, test_project, updated_project, new_project_info, mock_repo
):
    test_project.collaborators.add(collaborator)
    updated_project.collaborators.add(collaborator)
    mock_repo.get.return_value = test_project
    mock_repo.save.return_value = updated_project

    project = await sut.update_project(collaborator, test_project.id, *new_project_info, mock_repo)

    mock_repo.get.assert_called_once_with(test_project.id)
    mock_repo.save.assert_called_once_with(updated_project)
    assert project == updated_project


async def test_user_cannot_update_project_without_access(
    unrelated_user, test_project, updated_project, new_project_info, mock_repo
):
    mock_repo.get.return_value = test_project

    with pytest.raises(ForbiddenError):
        await sut.update_project(unrelated_user, test_project.id, *new_project_info, mock_repo)
    mock_repo.save.assert_not_awaited()


# Delete Project
async def test_user_can_delete_project_he_owns(test_user, test_project, mock_repo, mock_file_repo, mock_tasks):
    mock_repo.get.return_value = test_project

    await sut.delete_project(test_user, test_project.id, mock_repo, mock_file_repo, mock_tasks)

    mock_repo.delete.assert_awaited_once_with(test_project)
    mock_repo.get.assert_awaited_once_with(test_project.id)


async def test_when_project_is_deleted_tasks_are_added_to_delete_files(
    test_user, test_project, mock_repo, mock_file_repo, mock_tasks
):
    test_project.documents.append(Document(1, 1, "foo"))
    test_project.documents.append(Document(2, 1, "bar"))
    mock_repo.get.return_value = test_project

    await sut.delete_project(test_user, test_project.id, mock_repo, mock_file_repo, mock_tasks)
    mock_tasks.add_task.assert_has_calls(
        (
            call(mock_file_repo.delete, 1),
            call(mock_file_repo.delete, 2),
        )
    )


async def test_when_project_is_deleted_files_are_deleted(
    test_user, test_project, mock_repo, mock_file_repo, mock_tasks
):
    test_project.documents.append(Document(1, 1, "foo"))
    test_project.documents.append(Document(2, 1, "bar"))
    mock_repo.get.return_value = test_project

    tasks = []
    mock_tasks.add_task.side_effect = lambda f, x: tasks.append(asyncio.create_task(f(x)))

    await sut.delete_project(test_user, test_project.id, mock_repo, mock_file_repo, mock_tasks)
    await asyncio.gather(*tasks)

    mock_file_repo.delete.assert_has_awaits(
        (
            call(1),
            call(2),
        )
    )


async def test_user_cannot_delete_project_he_collaborates_on(
    collaborator, test_project, mock_repo, mock_file_repo, mock_tasks
):
    test_project.collaborators.add(collaborator)
    mock_repo.get.return_value = test_project

    with pytest.raises(ForbiddenError):
        await sut.delete_project(collaborator, test_project.id, mock_repo, mock_file_repo, mock_tasks)
    mock_repo.get.assert_called_once_with(test_project.id)
    mock_repo.delete.assert_not_called()


async def test_user_cannot_delete_project_without_access(
    unrelated_user, test_project, mock_repo, mock_file_repo, mock_tasks
):
    mock_repo.get.return_value = test_project

    with pytest.raises(ForbiddenError):
        await sut.delete_project(unrelated_user, test_project.id, mock_repo, mock_file_repo, mock_tasks)
    mock_repo.get.assert_called_once_with(test_project.id)
    mock_repo.delete.assert_not_called()


# Invite
async def test_user_can_add_a_collaborator_to_project_he_owns(
    test_user, unrelated_user, test_project, mock_repo, mock_user_repo
):
    mock_repo.get.return_value = test_project
    mock_user_repo.exists.return_value = True

    await sut.add_user_to_project(test_user, test_project.id, unrelated_user, mock_repo, mock_user_repo)

    mock_user_repo.exists.assert_called_once_with(unrelated_user)
    mock_repo.save.assert_called_once_with(test_project)
    assert unrelated_user in test_project.collaborators


async def test_user_cannot_add_a_collaborator_to_project_he_owns_when_ivitee_already_collaborates(
    test_user, collaborator, test_project, mock_repo, mock_user_repo
):
    test_project.collaborators.add(collaborator)
    mock_repo.get.return_value = test_project
    mock_user_repo.exists.return_value = True

    with pytest.raises(CollaboratorConflict):
        await sut.add_user_to_project(test_user, test_project.id, collaborator, mock_repo, mock_user_repo)

    mock_user_repo.exists.assert_called_once_with(collaborator)
    mock_repo.save.assert_not_called()
    assert collaborator in test_project.collaborators


async def test_user_cannot_add_a_collaborator_to_project_he_only_collaborates_on(
    collaborator, unrelated_user, test_project, mock_repo, mock_user_repo
):
    test_project.collaborators.add(collaborator)
    mock_repo.get.return_value = test_project
    mock_user_repo.exists.return_value = True

    with pytest.raises(ForbiddenError):
        await sut.add_user_to_project(collaborator, test_project.id, unrelated_user, mock_repo, mock_user_repo)

    mock_user_repo.exists.assert_not_called()
    mock_repo.save.assert_not_called()
    assert unrelated_user not in test_project.collaborators


async def test_user_cannot_add_a_collaborator_to_project_he_has_no_access_to(
    unrelated_user, test_project, mock_repo, mock_user_repo
):
    mock_repo.get.return_value = test_project
    mock_user_repo.exists.return_value = True

    with pytest.raises(ForbiddenError):
        await sut.add_user_to_project(unrelated_user, test_project.id, unrelated_user, mock_repo, mock_user_repo)

    mock_user_repo.exists.assert_not_called()
    mock_repo.save.assert_not_called()
    assert unrelated_user not in test_project.collaborators
