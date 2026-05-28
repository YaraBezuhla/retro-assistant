from models.contacts.address_book import AddressBook
from models.contacts.record import Record
from services.birthday_service import BirthdayService


class ContactService:
    def __init__(self, book: AddressBook):
        self._book = book
        self._birthdays = BirthdayService(book)

    @property
    def book(self) -> AddressBook:
        return self._book

    def find_contact(self, name: str) -> Record | None:
        return self._book.find_record(name)


    def add_contact(self, name: str, phone: str) -> str:
        record = self._book.find_record(name)
        if record is None:
            record = Record(name)
            record.add_phone(phone)
            self._book.add_record(record)
            return "Contact added."
        record.add_phone(phone)
        return "Contact updated."

    def change_phone(self, name: str, old_phone: str, new_phone: str) -> str:
        record = self._require(name)
        record.edit_phone(old_phone, new_phone)
        return f"Phone updated for {name}."

    def delete_contact(self, name: str) -> str:
        self._require(name)
        self._book.delete_record(name)
        return f"Contact {name} deleted."

    def remove_phone(self, name: str, phone: str) -> str:
        record = self._require(name)
        record.remove_phone(phone)
        return f"Phone '{phone}' removed from {name}."

    def show_phone(self, name: str) -> str:
        return str(self._require(name))

    def show_all(self) -> str:
        return "\n".join(map(str, self._book.data.values())) or "Address book is empty."


    def add_email(self, name: str, email: str) -> str:
        record = self._require(name)
        record.add_email(email)
        return f"Email added for {name}."

    def change_email(self, name: str, old_email: str, new_email: str) -> str:
        record = self._require(name)
        record.edit_email(old_email, new_email)
        return f"Email updated for {name}."

    def remove_email(self, name: str, email: str) -> str:
        record = self._require(name)
        record.remove_email(email)
        return f"Email removed for {name}."

    def show_email(self, name: str) -> str:
        record = self._require(name)
        if not record.emails:
            return f"No emails for {name}."
        return f"{name}: {'; '.join(str(e) for e in record.emails)}"


    def add_address(self, name: str, address: str) -> str:
        record = self._require(name)
        record.add_address(address)
        return f"Address added for {name}."

    def change_address(self, name: str, old_address: str, new_address: str) -> str:
        record = self._require(name)
        record.edit_address(old_address, new_address)
        return f"Address updated for {name}."

    def remove_address(self, name: str, address: str) -> str:
        record = self._require(name)
        record.remove_address(address)
        return f"Address removed for {name}."

    def show_address(self, name: str) -> str:
        record = self._require(name)
        if not record.addresses:
            return f"No addresses for {name}."
        return f"{name}: {'; '.join(str(a) for a in record.addresses)}"


    def add_birthday(self, name: str, birthday: str) -> str:
        record = self._require(name)
        existed = record.birthday is not None
        record.add_birthday(birthday)
        return f"Birthday updated for {name}." if existed else f"Birthday added for {name}."

    def show_birthday(self, name: str) -> str:
        record = self._require(name)
        return str(record.birthday) if record.birthday else f"No birthday for {name}."

    def get_upcoming_birthdays(self, days: int) -> str:
        upcoming = self._birthdays.get_upcoming(days)
        if not upcoming:
            return "No upcoming birthdays yet."
        return "\n".join(f"{e['name']}: {e['birthday']}" for e in upcoming)


    def _require(self, name: str) -> Record:
        record = self._book.find_record(name)
        if record is None:
            raise KeyError(name)
        return record
