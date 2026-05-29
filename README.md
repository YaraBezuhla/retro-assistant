# Retro Assistant

A retro-themed terminal contact and note manager built with Python and Textual. Manage contacts, phone numbers, emails, addresses, birthdays, and tagged notes.

---

## Technologies

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.13+ |
| Persistence | Python `pickle` (built-in) | — |
| UI Framework | [Textual](https://textual.textualize.io/) | 3.2.0 |
| Testing | [pytest](https://pytest.org/) | 9.0.3 |



---

## Architecture

The project follows a strict layered architecture:

```
UI (Textual widgets)
      │
      ▼
Commands (command registry + dispatcher)
      │
      ▼
Services (ContactService, NoteService, BirthdayService)
      │
      ▼
Models (Record / Note + field-level validation)
      │
Repositories (PickleContactRepository, PickleNoteRepository)
```

**Key patterns:**

- **Command pattern** — every user action is a `CommandDef` registered in `CommandRegistry`
- **Repository pattern** — persistence is decoupled behind `AbstractRepository`; currently backed by pickle files
- **Service layer** — all business logic lives in services, not in models or commands
- **Field validation** — each model field (`Phone`, `Email`, `Birthday`, etc.) raises `ValueError` on invalid input so errors surface early
- **`@input_error` decorator** — converts `ValueError` / `KeyError` into user-friendly strings without crashing the app

---

## Project Structure

```
retro-assistant/
├── main.py                          # Composition root
├── requirements.txt
│
├── models/
│   ├── field.py                     # Base Field class
│   ├── contacts/
│   │   ├── record.py                # Contact entity
│   │   ├── address_book.py          # Collection of contacts (UserDict)
│   │   ├── name.py / phone.py / email.py / address.py / birthday.py
│   └── notes/
│       ├── note.py                  # Note entity (numeric ID + tags)
│       ├── notebook.py              # Collection of notes (UserDict)
│       └── tag.py
│
├── services/
│   ├── contact_service.py
│   ├── note_service.py
│   └── birthday_service.py
│
├── commands/
│   ├── registry.py                  # CommandRegistry + CommandDef
│   ├── contact_commands.py
│   ├── address_commands.py
│   ├── email_commands.py
│   ├── birthday_commands.py
│   └── note_commands.py
│
├── repositories/
│   ├── abstract_contact_repository.py
│   ├── abstract_note_repository.py
│   ├── pickle_contact_repository.py
│   └── pickle_note_repository.py
│
├── helpers/
│   └── error_handler.py             # @input_error decorator
│
├── ui/
│   ├── tui.py                       # RetroBotApp (Textual App)
│   ├── retro.tcss                   # TCSS stylesheet (neon green theme)
│   └── retro_design_system.py       # Color tokens + layout constants
│
└── tests/
    └── test_bot.py
```

---

## Features

### Contact Management

| Command | Description |
|---|---|
| `add <name> <phone>` | Add a new contact or add phone to existing |
| `change <name> <old_phone> <new_phone>` | Replace a phone number |
| `remove-phone <name> <phone>` | Remove a phone number |
| `phone <name>` | Show all phone numbers for a contact |
| `delete <name>` | Remove a contact |
| `add-email <name> <email>` | Add an email address |
| `change-email <name> <old_email> <new_email>` | Replace an email address |
| `remove-email <name> <email>` | Remove an email address |
| `show-email <name>` | Show all emails for a contact |
| `add-address <name> <address>` | Add a physical address |
| `change-address <name> <old_address> <new_address>` | Replace an address |
| `remove-address <name> <address>` | Remove an address |
| `show-address <name>` | Show all addresses for a contact |
| `add-birthday <name> <DD.MM.YYYY>` | Set birthday |
| `show-birthday <name>` | Show a contact's birthday |
| `all` | List all contacts |

**Phone validation** — accepts Ukrainian formats: `+380XXXXXXXXX`, `380XXXXXXXXX`, `0XXXXXXXXX`.  
**Email validation** — RFC-compliant regex check.  
**Birthday format** — `DD.MM.YYYY` only.

---

### Note Management

| Command | Description |
|---|---|
| `add-note <content>` | Create a new note (max 500 chars) |
| `edit-note <id> <content>` | Edit note content |
| `delete-note <id>` | Delete a note |
| `show-note <id>` | Display a single note |
| `all-notes` | List all notes |
| `find-note <query>` | Search notes by content or tag |
| `add-tag <id> <tag>` | Add a `#tag` to a note |
| `remove-tag <id> <tag>` | Remove a tag |
| `notes-by-tag <tag>` | Find all notes with a given tag |

Each note gets a numeric ID on creation. Run `all-notes` to see IDs. Tags are stored lowercase and normalized automatically.

---

### Birthday Reminders

| Command | Description |
|---|---|
| `birthdays` | Show upcoming birthdays (default: next 7 days) |
| `birthdays <days>` | Show birthdays within the next N days |

---

### UI

- **Two modes** — Contact mode and Note mode, switchable from the sidebar
- **Command input** — type any command at the bottom input bar and press Enter
- **Keyboard navigation** — sidebar buttons, input field

---

## Getting Started

### Prerequisites

- Python 3.13 or later

### Install

```powershell
# Clone the repo
git clone <repo-url>
cd retro-assistant

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Run

```powershell
python main.py
```

Data is persisted automatically to `addressbook.pkl` and `notebook.pkl` in the project root. These files are created on first run.

### Tests

```powershell
python -m pytest
```

---
