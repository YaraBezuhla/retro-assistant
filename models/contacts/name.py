from models.field import Field


class Name(Field):
    def __init__(self, value):
        if not str(value).strip():
            raise ValueError("Name cannot be empty.")
        super().__init__(value)