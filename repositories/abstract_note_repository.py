from abc import ABC, abstractmethod
from models.notes.notebook import Notebook


class AbstractNoteRepository(ABC):
    @abstractmethod
    def load(self) -> Notebook: ...

    @abstractmethod
    def save(self, notebook: Notebook) -> None: ...