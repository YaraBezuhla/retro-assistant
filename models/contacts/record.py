from models.contacts.name import Name
from models.contacts.phone import Phone
from models.contacts.birthday import Birthday
from models.contacts.email import Email
from models.contacts.address import Address


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.emails = []
        self.birthday = None
        self.addresses = []

    def add_phone(self, phone_number):
        if self.find_phone(phone_number):
            raise ValueError(f"Phone '{phone_number}' already exists.")
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        if len(self.phones) <= 1:
            raise ValueError("Cannot remove the last phone number from a contact.")
        phone = self.find_phone(phone_number)
        if phone:
            self.phones.remove(phone)
        else:
            raise ValueError(f"Phone '{phone_number}' not found in record.")

    def edit_phone(self, old_number, new_number):
        phone = self.find_phone(old_number)
        if phone:
            self.phones[self.phones.index(phone)] = Phone(new_number)
        else:
            raise ValueError(f"Phone '{old_number}' not found in record.")

    def find_phone(self, phone_number):
        return next((p for p in self.phones if p.value == phone_number.strip()), None)

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def add_address(self, value):
        if self.find_address(value):
            raise ValueError(f"Address '{value}' already exists.")
        self.addresses.append(Address(value))

    def remove_address(self, value):
        found = self.find_address(value)
        if found:
            self.addresses.remove(found)
        else:
            raise ValueError(f"Address '{value}' not found in record.")

    def edit_address(self, old_value, new_value):
        addr = self.find_address(old_value)
        if addr:
            self.addresses[self.addresses.index(addr)] = Address(new_value)
        else:
            raise ValueError(f"Address '{old_value}' not found in record.")

    def find_address(self, value):
        return next((a for a in self.addresses if a.value == value), None)

    def add_email(self, email):
        if self.find_email(email):
            raise ValueError(f"Email '{email}' already exists.")
        self.emails.append(Email(email))

    def remove_email(self, email):
        found = self.find_email(email)
        if found:
            self.emails.remove(found)
        else:
            raise ValueError(f"Email '{email}' not found in record.")

    def edit_email(self, old_email, new_email):
        email = self.find_email(old_email)
        if email:
            self.emails[self.emails.index(email)] = Email(new_email)
        else:
            raise ValueError(f"Email '{old_email}' not found in record.")

    def find_email(self, email):
        return next((em for em in self.emails if em.value == email), None)

    def __setstate__(self, state):
        state.setdefault('emails', [])
        state.setdefault('addresses', [])
        self.__dict__.update(state)

    def __str__(self):
        parts = [
            f"Contact name: {self.name}",
            f"phones: {'; '.join(str(p) for p in self.phones) or '—'}",
        ]
        if self.emails:
            parts.append(f"emails: {'; '.join(str(e) for e in self.emails)}")
        if self.addresses:
            parts.append(f"addresses: {'; '.join(str(a) for a in self.addresses)}")
        if self.birthday:
            parts.append(f"birthday: {self.birthday}")
        return ", ".join(parts)