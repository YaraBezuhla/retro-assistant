from datetime import datetime, timedelta

from models.contacts.address_book import AddressBook


class BirthdayService:
    def __init__(self, book: AddressBook):
        self._book = book

    def get_upcoming(self, days: int) -> list[dict]:
        current_day = datetime.now().date()
        end_date = current_day + timedelta(days=days)
        result = []

        for contact in self._book.values():
            if contact.birthday is None:
                continue
            birth_date = contact.birthday.value

            try:
                birthday = birth_date.replace(year=current_day.year)
            except ValueError:
                birthday = birth_date.replace(year=current_day.year, day=28)

            if birthday < current_day:
                try:
                    birthday = birth_date.replace(year=current_day.year + 1)
                except ValueError:
                    birthday = birth_date.replace(year=current_day.year + 1, day=28)

            if current_day <= birthday <= end_date:
                result.append({
                    "name": contact.name.value,
                    "greeting_date": birthday,
                    "birthday": birth_date.strftime("%d.%m.%Y"),
                })

        return sorted(result, key=lambda x: x["greeting_date"])
