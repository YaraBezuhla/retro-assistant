from collections import UserDict

from models.contacts.record import Record


class AddressBook(UserDict):

    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find_record(self, key):
        return self.data.get(key)

    def delete_record(self, key):
        del self[key]
