from collections import UserDict

from models.notes.note import Note


class Notebook(UserDict):
    def __init__(self):
        super().__init__()
        self._next_id = 1

    def add_note(self, content: str) -> Note:
        note = Note(content, note_id=str(self._next_id))
        self.data[note.id] = note
        self._next_id += 1
        return note

    def find_note(self, note_id: str) -> Note | None:
        return self.data.get(note_id)

    def delete_note(self, note_id: str) -> None:
        del self[note_id]