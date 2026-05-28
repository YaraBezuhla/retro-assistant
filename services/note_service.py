from models.notes.note import Note
from models.notes.notebook import Notebook


class NoteService:
    def __init__(self, notebook: Notebook):
        self._notebook = notebook

    @property
    def notebook(self) -> Notebook:
        return self._notebook

    def add_note(self, content: str) -> str:
        self._notebook.add_note(content)
        return "Note added."

    def edit_note(self, note_id: str, new_content: str) -> str:
        note = self._require(note_id)
        note.edit_content(new_content)
        return "Note updated."

    def delete_note(self, note_id: str) -> str:
        self._require(note_id)
        self._notebook.delete_note(note_id)
        return "Note deleted."

    def show_note(self, note_id: str) -> str:
        return str(self._require(note_id))

    def show_all(self) -> str:
        if not self._notebook.data:
            return "Notebook is empty."
        return "\n\n".join(str(n) for n in self._notebook.data.values())

    def format_find(self, query: str) -> str:
        results = [n for n in self._notebook.data.values() if n.matches(query)]
        if not results:
            return f"No notes found for '{query}'."
        return "\n\n".join(self._note_str(n) for n in results)


    def add_tag(self, note_id: str, tag: str) -> str:
        note = self._require(note_id)
        note.add_tag(tag)
        tag_val = tag.strip().lstrip("#").lower()
        return f"Tag '#{tag_val}' added."

    def remove_tag(self, note_id: str, tag: str) -> str:
        note = self._require(note_id)
        note.remove_tag(tag)
        tag_val = tag.strip().lstrip("#").lower()
        return f"Tag '#{tag_val}' removed."

    def format_by_tag(self, tag: str) -> str:
        tag_val = tag.strip().lstrip("#").lower()
        results = [
            n for n in self._notebook.data.values()
            if any(t.value == tag_val for t in n.tags)
        ]
        if not results:
            return f"No notes with tag '#{tag_val}'."
        return "\n\n".join(self._note_str(n) for n in sorted(results, key=lambda n: n.content))

    @staticmethod
    def _note_str(note) -> str:
        tags_str = "  ".join(f"#{t.value}" for t in note.tags) if note.tags else "none"
        return f"  {note.content}\n  Tags: {tags_str}"


    def _require(self, note_id: str) -> Note:
        note = self._notebook.find_note(note_id)
        if note is None:
            raise KeyError(note_id)
        return note