import pickle
from pathlib import Path

from models.notes.notebook import Notebook
from repositories.abstract_note_repository import AbstractNoteRepository


class PickleNoteRepository(AbstractNoteRepository):
    def __init__(self, path: Path):
        self._path = path

    def load(self) -> Notebook:
        try:
            with open(self._path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return Notebook()

    def save(self, notebook: Notebook) -> None:
        with open(self._path, "wb") as f:
            pickle.dump(notebook, f)