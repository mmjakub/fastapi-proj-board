import pytest

from app.errors import ForbiddenError, ProjectNotFound, UserNotFound
import app.transaction_script as ts


def equals_test_project(project):
    assert project["id"] == 1
    assert project["owner"] == "alice"
    assert project["documents"] == []
    assert project["info"]["name"] == "test_name"
    assert project["info"]["description"] == "test_description"
    return True


def equals_test_info(info):
    assert info["name"] == "test_name"
    assert info["description"] == "test_description"
    return True


def equals_new_info(info):
    assert info["name"] == "new_name"
    assert info["description"] == "new_description"
    return True


async def test_can_create_project(Session):
    project = await ts.create_project("alice", "test_name", "test_description", Session)

    assert equals_test_project(project)


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_project_list_contains_user_project(Session):
    projects = await ts.list_projects("alice", Session)

    assert len(projects) == 1
    assert equals_test_project(projects[0])


async def test_deleting_non_existing_project_raises(Session, file_service):
    with pytest.raises(ProjectNotFound) as exc_info:
        await ts.delete_project(1, "alice", Session, file_service)
    assert exc_info.value.reason == "<Project:1> does not exist"


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_owner_can_delete_project(Session, file_service):
    await ts.delete_project(1, "alice", Session, file_service)
    projects = await ts.list_projects("alice", Session)
    assert len(projects) == 0


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_others_cannot_delete_project(Session, file_service):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.delete_project(1, "bob", Session, file_service)
    assert exc_info.value.reason == "Must be project owner to do this"

    projects = await ts.list_projects("alice", Session)
    assert len(projects) == 1


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_collaborator_cannot_delete_project(Session, file_service):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.delete_project(1, "bob", Session, file_service)
    assert exc_info.value.reason == "Must be project owner to do this"

    projects = await ts.list_projects("alice", Session)
    assert len(projects) == 1


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_owner_can_invite_others(Session, file_service):
    await ts.invite_user("bob", 1, "alice", Session)
    projects = await ts.list_projects("bob", Session)
    assert len(projects) == 1


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_inviting_nonexisten_user_raises(Session, file_service):
    with pytest.raises(UserNotFound) as exc_info:
        await ts.invite_user("fake", 1, "alice", Session)
    assert exc_info.value.reason == "<User:fake> does not exist"


async def test_inviting_to_nonexistent_project_raises(Session, file_service):
    with pytest.raises(ProjectNotFound) as exc_info:
        await ts.invite_user("bob", 1, "alice", Session)
    assert exc_info.value.reason == "<Project:1> does not exist"


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_user_cannot_invite_others(Session, file_service):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.invite_user("charlie", 1, "bob", Session)
    assert exc_info.value.reason == "Must be project owner to do this"
    projects = await ts.list_projects("charlie", Session)
    assert len(projects) == 0


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_collaborator_cannot_invite_others(Session, file_service):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.invite_user("charlie", 1, "bob", Session)
    assert exc_info.value.reason == "Must be project owner to do this"
    projects = await ts.list_projects("charlie", Session)
    assert len(projects) == 0


async def test_nonexistent_project_info_raises(Session, file_service):
    with pytest.raises(ProjectNotFound) as exc_info:
        await ts.get_project_info(1, "alice", Session)
    assert exc_info.value.reason == "<Project:1> does not exist"


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_others_cannot_view_project_info(Session, file_service):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.get_project_info(1, "bob", Session)
    assert exc_info.value.reason == "Must be project collaborator to do this"


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_project_info_is_correct(Session, file_service):
    info = await ts.get_project_info(1, "alice", Session)
    assert equals_test_info(info)


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_collaborator_can_get_correct_info(Session, file_service):
    info = await ts.get_project_info(1, "bob", Session)
    assert equals_test_info(info)


async def test_changing_nonexistent_project_info_raises(Session, file_service):
    with pytest.raises(ProjectNotFound) as exc_info:
        await ts.change_project_info("new_name", "new_description", 1, "alice", Session)
    assert exc_info.value.reason == "<Project:1> does not exist"


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_others_cannot_change_project_info(Session, file_service):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.change_project_info("new_name", "new_description", 1, "bob", Session)
    assert exc_info.value.reason == "Must be project collaborator to do this"


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_owner_can_change_project_info(Session, file_service):
    info = await ts.change_project_info("new_name", "new_description", 1, "alice", Session)
    assert equals_new_info(info)

    info = await ts.get_project_info(1, "alice", Session)
    assert equals_new_info(info)

    info = await ts.get_project_info(1, "bob", Session)
    assert equals_new_info(info)


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_collaborator_can_change_info(Session, file_service):
    info = await ts.change_project_info("new_name", "new_description", 1, "alice", Session)
    assert equals_new_info(info)

    info = await ts.get_project_info(1, "alice", Session)
    assert equals_new_info(info)

    info = await ts.get_project_info(1, "bob", Session)
    assert equals_new_info(info)
