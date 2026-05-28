from datetime import datetime, date

from models.field import Field


class Birthday(Field):
    def __init__(self, value):
        try:
            parsed = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        if parsed > date.today():
            raise ValueError("Birthday cannot be a future date.")
        super().__init__(parsed)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")
