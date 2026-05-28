import re

from models.field import Field

_EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')


class Email(Field):
    def __init__(self, email):
        if not isinstance(email, str) or not _EMAIL_PATTERN.fullmatch(email):
            raise ValueError("Invalid email format. Expected: user@example.com")
        super().__init__(email)
