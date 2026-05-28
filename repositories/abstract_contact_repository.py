from abc import ABC, abstractmethod
from models.contacts.address_book import AddressBook


class AbstractContactRepository(ABC):
    @abstractmethod
    def load(self) -> AddressBook: ...

    @abstractmethod
    def save(self, book: AddressBook) -> None: ...