import re

from models.field import Field


class Tag(Field):
    def __init__(self, value: str):
        value = value.strip().lstrip("#").lower()
        if not value:
            raise ValueError("Tag cannot be empty.")
        if not re.match(r"^[\w-]+$", value):
            raise ValueError(
                f"Tag '{value}' is invalid. Use only letters, digits, hyphens, or underscores."
            )
        super().__init__(value)