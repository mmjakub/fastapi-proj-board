import pytest

from app.core import services as sut
from app.core.errors import ForbiddenError, CollaboratorConflict, ResourceNotFound


# Create
async def test_user_can_create_project(test_user, test_name, test_description, test_project_id, empty_fake_repo):
    empty_fake_repo.setup_id(test_project_id)

    project = await sut.create_project(test_user, test_name, test_description, empty_fake_repo)

    assert project.id == test_project_id
    assert project.name == test_name
    assert project.description == test_description
    assert project.owner == test_user
    assert project.collaborators == {test_user}


# List
async def test_project_list_is_empty_when_user_has_no_projects(unrelated_user, fake_repo):
    projects = await sut.list_projects(unrelated_user, fake_repo)

    assert projects == []


async def test_project_list_contains_projects_owned_by_user(test_user, test_project, test_project2, fake_repo):
    projects = await sut.list_projects(test_user, fake_repo)

    assert projects == [test_project, test_project2]


async def test_project_list_contains_projects_that_user_collaborats_on(
    collaborator, test_project, test_project2, fake_repo
):
    projects = await sut.list_projects(collaborator, fake_repo)

    assert projects == [test_project, test_project2]


# Get Project
async def test_user_can_get_project_he_owns(test_user, test_project, fake_repo):
    project = await sut.get_project(test_user, test_project.id, fake_repo)

    assert project == test_project


async def test_user_can_get_project_he_collaborates_on(collaborator, test_project, fake_repo):
    project = await sut.get_project(collaborator, test_project.id, fake_repo)

    assert project == test_project


async def test_user_cannot_get_project_without_access(unrelated_user, test_project, fake_repo):
    with pytest.raises(ForbiddenError):
        await sut.get_project(unrelated_user, test_project.id, fake_repo)


async def test_getting_nonexistent_project_raises(test_user, test_project_id, empty_fake_repo):
    with pytest.raises(ResourceNotFound):
        await sut.get_project(test_user, test_project_id, empty_fake_repo)


# Update Project
async def test_user_can_update_project_he_owns(test_user, test_project, updated_project, new_project_info, fake_repo):
    project = await sut.update_project(test_user, test_project.id, *new_project_info, fake_repo)

    assert project == updated_project


async def test_user_can_update_project_he_collaborates_on(
    collaborator, test_project, updated_project, new_project_info, fake_repo
):
    project = await sut.update_project(collaborator, test_project.id, *new_project_info, fake_repo)

    assert project == updated_project


async def test_user_cannot_update_project_without_access(
    unrelated_user, test_project, updated_project, new_project_info, fake_repo
):
    with pytest.raises(ForbiddenError):
        await sut.update_project(unrelated_user, test_project.id, *new_project_info, fake_repo)


# Delete Project
async def test_user_can_delete_project_he_owns(test_user, test_project, fake_repo, fake_file_repo, fake_tasks):

    await sut.delete_project(test_user, test_project.id, fake_repo, fake_file_repo, fake_tasks)

    assert not fake_repo.contains(test_project)


async def test_when_project_is_deleted_files_are_deleted(
    test_user, test_project, fake_repo, fake_file_repo, fake_tasks
):
    await sut.delete_project(test_user, test_project.id, fake_repo, fake_file_repo, fake_tasks)
    await fake_tasks.complete_tasks()

    assert not fake_file_repo.contains(1) and not fake_file_repo.contains(2)


async def test_user_cannot_delete_project_he_collaborates_on(
    collaborator, test_project, fake_repo, fake_file_repo, fake_tasks
):
    with pytest.raises(ForbiddenError):
        await sut.delete_project(collaborator, test_project.id, fake_repo, fake_file_repo, fake_tasks)

    assert fake_repo.contains(test_project)


async def test_user_cannot_delete_project_without_access(
    unrelated_user, test_project, fake_repo, fake_file_repo, fake_tasks
):
    with pytest.raises(ForbiddenError):
        await sut.delete_project(unrelated_user, test_project.id, fake_repo, fake_file_repo, fake_tasks)
    assert fake_repo.contains(test_project)


# Invite
async def test_user_can_add_a_collaborator_to_project_he_owns(
    test_user, unrelated_user, test_project, fake_repo, fake_user_repo
):
    await sut.add_user_to_project(test_user, test_project.id, unrelated_user, fake_repo, fake_user_repo)

    assert unrelated_user in test_project.collaborators


async def test_user_cannot_add_a_collaborator_to_project_he_owns_when_ivitee_already_collaborates(
    test_user, collaborator, test_project, fake_repo, fake_user_repo
):
    with pytest.raises(CollaboratorConflict):
        await sut.add_user_to_project(test_user, test_project.id, collaborator, fake_repo, fake_user_repo)


async def test_user_cannot_add_a_collaborator_to_project_he_only_collaborates_on(
    collaborator, unrelated_user, test_project, fake_repo, fake_user_repo
):
    with pytest.raises(ForbiddenError):
        await sut.add_user_to_project(collaborator, test_project.id, unrelated_user, fake_repo, fake_user_repo)

    assert unrelated_user not in test_project.collaborators


async def test_user_cannot_add_a_collaborator_to_project_he_has_no_access_to(
    unrelated_user, test_project, fake_repo, fake_user_repo
):
    with pytest.raises(ForbiddenError):
        await sut.add_user_to_project(unrelated_user, test_project.id, unrelated_user, fake_repo, fake_user_repo)

    assert unrelated_user not in test_project.collaborators
