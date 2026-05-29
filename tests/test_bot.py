import pytest
from datetime import date

from models.contacts.name import Name
from models.contacts.address_book import AddressBook
from models.contacts.record import Record
from services.contact_service import ContactService
from commands import contact_registry

from models.notes.note import Note
from models.notes.notebook import Notebook
from models.notes.tag import Tag
from services.note_service import NoteService


# ── helpers ───────────────────────────────────────────────────────────────────

VALID_PHONE = "0934567890"
VALID_PHONE_2 = "0987654321"


def make_service(*contacts: tuple[str, str]) -> ContactService:
    book = AddressBook()
    service = ContactService(book)
    for name, phone in contacts:
        service.add_contact(name, phone)
    return service


# ── Name validation ───────────────────────────────────────────────────────────

def test_valid_name():
    assert Name("Alice").value == "Alice"


def test_empty_name_raises():
    with pytest.raises(ValueError):
        Name("")


# ── add_contact ───────────────────────────────────────────────────────────────

def test_add_contact_valid():
    service = make_service()
    result = service.add_contact("Alice", VALID_PHONE)
    assert result == "Contact added."
    assert service.find_contact("Alice") is not None


def test_add_contact_short_phone():
    service = make_service()
    with pytest.raises(ValueError):
        service.add_contact("Alice", "1234567")
    assert service.find_contact("Alice") is None


# ── show_phone ────────────────────────────────────────────────────────────────

def test_show_phone_existing():
    service = make_service(("Alice", VALID_PHONE))
    result = service.show_phone("Alice")
    assert VALID_PHONE in result


def test_show_phone_nonexistent():
    service = make_service()
    with pytest.raises(KeyError):
        service.show_phone("Ghost")


# ── change_phone ──────────────────────────────────────────────────────────────

def test_change_phone_existing():
    service = make_service(("Alice", VALID_PHONE))
    result = service.change_phone("Alice", VALID_PHONE, VALID_PHONE_2)
    assert result == "Phone updated for Alice."
    assert service.find_contact("Alice").find_phone(VALID_PHONE_2) is not None


def test_change_phone_nonexistent():
    service = make_service()
    with pytest.raises(KeyError):
        service.change_phone("Ghost", VALID_PHONE, VALID_PHONE_2)


# ── show_all ──────────────────────────────────────────────────────────────────

def test_show_all_with_records():
    service = make_service(("Alice", VALID_PHONE))
    result = service.show_all()
    assert "Alice" in result


def test_show_all_empty_book():
    service = make_service()
    result = service.show_all()
    assert "empty" in result.lower()


# ── delete_contact ────────────────────────────────────────────────────────────

def test_delete_contact_existing():
    service = make_service(("Alice", VALID_PHONE))
    result = service.delete_contact("Alice")
    assert result == "Contact Alice deleted."
    assert service.find_contact("Alice") is None


def test_delete_contact_nonexistent():
    service = make_service()
    with pytest.raises(KeyError):
        service.delete_contact("Ghost")


# ── birthday ──────────────────────────────────────────────────────────────────

def test_add_birthday_existing():
    service = make_service(("Alice", VALID_PHONE))
    result = service.add_birthday("Alice", "15.06.1990")
    assert result == "Birthday added for Alice."
    assert service.find_contact("Alice").birthday is not None


def test_add_birthday_nonexistent():
    service = make_service()
    with pytest.raises(KeyError):
        service.add_birthday("Ghost", "15.06.1990")


def test_add_birthday_wrong_format():
    service = make_service(("Alice", VALID_PHONE))
    with pytest.raises(ValueError):
        service.add_birthday("Alice", "1990-06-15")


def test_show_birthday_existing():
    service = make_service(("Alice", VALID_PHONE))
    service.add_birthday("Alice", "15.06.1990")
    result = service.show_birthday("Alice")
    assert "15.06.1990" in result


def test_show_birthday_nonexistent():
    service = make_service()
    with pytest.raises(KeyError):
        service.show_birthday("Ghost")


def test_upcoming_birthdays_has_results():
    book = AddressBook()
    r = Record("Alice")
    r.add_birthday(date.today().strftime("%d.%m.%Y"))
    book.add_record(r)
    service = ContactService(book)
    result = service.get_upcoming_birthdays(7)
    assert "Alice" in result


def test_upcoming_birthdays_empty():
    service = make_service()
    result = service.get_upcoming_birthdays(7)
    assert "No upcoming birthdays yet." in result


# ── Command layer: missing args returns error string ──────────────────────────

MISSING_ARGS_ERROR = "Usage:"


@pytest.mark.parametrize("cmd_name", [
    "add",
    "change-phone",
    "delete-contact",
    "show-phone",
    "add-birthday",
    "show-birthday",
])
def test_missing_args(cmd_name):
    service = make_service()
    result = contact_registry.execute(cmd_name, [], service)
    assert MISSING_ARGS_ERROR in result


# ── Notes ────────────────────────────────────────────────────────────────────

def make_note_service(*contents: str) -> NoteService:
    notebook = Notebook()
    service = NoteService(notebook)
    for content in contents:
        service.add_note(content)
    return service


def test_add_note_valid():
    service = make_note_service()
    result = service.add_note("Hello world")
    assert result == "Note added."
    assert service.notebook.find_note("1") is not None


def test_add_note_empty_raises():
    service = make_note_service()
    with pytest.raises(ValueError):
        service.add_note("")


def test_delete_note_valid():
    service = make_note_service("To delete")
    result = service.delete_note("1")
    assert result == "Note deleted."
    assert service.notebook.find_note("1") is None


def test_delete_note_nonexistent_raises():
    service = make_note_service()
    with pytest.raises(KeyError):
        service.delete_note("99")