import pickle
from pathlib import Path

from models.contacts.address_book import AddressBook
from repositories.abstract_contact_repository import AbstractContactRepository


class PickleContactRepository(AbstractContactRepository):
    def __init__(self, path: Path):
        self._path = path

    def load(self) -> AddressBook:
        try:
            with open(self._path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return AddressBook()

    def save(self, book: AddressBook) -> None:
        with open(self._path, "wb") as f:
            pickle.dump(book, f)