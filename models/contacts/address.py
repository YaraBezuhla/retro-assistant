from models.field import Field


class Address(Field):
    def __init__(self, value):
        if not str(value).strip():
            raise ValueError("Address cannot be empty.")
        super().__init__(value)
