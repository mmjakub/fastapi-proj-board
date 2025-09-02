import pytest


async def test_can_save_and_load_a_file(repository, test_file_factory):
    await repository.save(42, test_file_factory())
    received_file = await repository.get(42)

    assert received_file.read() == test_file_factory().read()


async def test_can_delete_existing_file(repository, test_file_factory):
    await repository.save(42, test_file_factory())

    await repository.delete(42)

    with pytest.raises(FileNotFoundError):
        await repository.get(42)


async def test_can_delete_nonexisting_file(repository):
    await repository.delete(42)


async def test_cannot_load_nonexisting_file(repository):
    with pytest.raises(FileNotFoundError):
        await repository.get(42)
