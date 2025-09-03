from pathlib import Path
from shutil import copyfileobj
from typing import BinaryIO

from app.core.ports.repository import FileRepository


class LocalFileRepository(FileRepository):
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    async def save(self, file_id: int, file: BinaryIO) -> None:
        path = self.data_dir / str(file_id)
        with path.open("wb") as dest:
            copyfileobj(file, dest)

    async def delete(self, file_id: int) -> None:
        path = self.data_dir / str(file_id)
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    async def get(self, file_id: int) -> BinaryIO:
        path = self.data_dir / str(file_id)
        return path.open("rb")
