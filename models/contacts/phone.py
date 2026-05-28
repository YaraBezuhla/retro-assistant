import re

from models.field import Field


class Phone(Field):
    _PATTERN = re.compile(r'^(\+380|380|0)\d{9}$')

    def __init__(self, value):
        if not isinstance(value, str) or not self._PATTERN.match(value.strip()):
            raise ValueError(
                f"Phone number '{value}' must be in one of the formats: "
                "+380XXXXXXXXX, 380XXXXXXXXX, or 0XXXXXXXXX."
            )
        super().__init__(value.strip())