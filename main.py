from pathlib import Path

from commands import contact_registry, note_registry
from repositories.pickle_contact_repository import PickleContactRepository
from repositories.pickle_note_repository import PickleNoteRepository
from services.contact_service import ContactService
from services.note_service import NoteService
from ui.tui import AssistantBotApp

DATA_FILE = Path(__file__).resolve().parent / "addressbook.pkl"
NOTES_FILE = Path(__file__).resolve().parent / "notebook.pkl"


def main() -> None:
    repo = PickleContactRepository(DATA_FILE)
    book = repo.load()
    service = ContactService(book)

    note_repo = PickleNoteRepository(NOTES_FILE)
    notebook = note_repo.load()
    note_service = NoteService(notebook)

    AssistantBotApp(
        service=service,
        registry=contact_registry,
        repo=repo,
        note_service=note_service,
        note_registry=note_registry,
        note_repo=note_repo,
    ).run()


if __name__ == "__main__":
    main()