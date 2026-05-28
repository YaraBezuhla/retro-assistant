from __future__ import annotations

from models.notes.tag import Tag


class Note:
    MAX_LENGTH = 500

    def __init__(self, content: str, note_id: str | None = None):
        if not content or not content.strip():
            raise ValueError("Note content cannot be empty.")
        if len(content.strip()) > self.MAX_LENGTH:
            raise ValueError(f"Note content cannot exceed {self.MAX_LENGTH} characters.")
        self.id = note_id
        self.content = content.strip()
        self.tags: list[Tag] = []

    def add_tag(self, tag: str) -> None:
        if self.find_tag(tag):
            tag_val = tag.strip().lstrip("#").lower()
            raise ValueError(f"Tag '#{tag_val}' already exists.")
        self.tags.append(Tag(tag))

    def remove_tag(self, tag: str) -> None:
        found = self.find_tag(tag)
        if found:
            self.tags.remove(found)
        else:
            tag_val = tag.strip().lstrip("#").lower()
            raise ValueError(f"Tag '#{tag_val}' not found.")

    def find_tag(self, tag: str) -> Tag | None:
        tag_val = tag.strip().lstrip("#").lower()
        return next((t for t in self.tags if t.value == tag_val), None)

    def edit_content(self, new_content: str) -> None:
        if not new_content or not new_content.strip():
            raise ValueError("Note content cannot be empty.")
        if len(new_content.strip()) > self.MAX_LENGTH:
            raise ValueError(f"Note content cannot exceed {self.MAX_LENGTH} characters.")
        self.content = new_content.strip()

    def matches(self, query: str) -> bool:
        q = query.lower().lstrip("#")
        return q in self.content.lower() or any(q in t.value for t in self.tags)

    def __str__(self) -> str:
        tags_str = "  ".join(f"#{t.value}" for t in self.tags) if self.tags else "none"
        return f"[{self.id}]\n  {self.content}\n  Tags: {tags_str}"