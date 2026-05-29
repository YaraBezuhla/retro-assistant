import string
import textwrap
from datetime import date

from textual.app import App, ComposeResult
from textual.widgets import Button, Label, RichLog, Input, DataTable
from textual.containers import Vertical, Horizontal
from textual import events, on

from commands.registry import CommandRegistry
from repositories.abstract_contact_repository import AbstractContactRepository
from repositories.abstract_note_repository import AbstractNoteRepository
from services.contact_service import ContactService
from services.note_service import NoteService
from ui.retro_design_system import (
    SAGE, SAGE_MID, FOREST_MID,
    CLAY,
    MINT,
    RUST,
    AMBER,
    TEXT_BRIGHT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM,
)


class RetroBotApp(App):
    CSS_PATH = ["retro.tcss"]

    def __init__(
        self,
        service: ContactService,
        registry: CommandRegistry,
        repo: AbstractContactRepository,
        note_service: NoteService,
        note_registry: CommandRegistry,
        note_repo: AbstractNoteRepository,
    ):
        super().__init__()
        self._service       = service
        self._cmd_registry  = registry
        self._repo          = repo
        self._note_service  = note_service
        self._note_registry = note_registry
        self._note_repo     = note_repo
        self._mode: str | None             = None
        self._selected_contact: str | None = None
        self._selected_note: str | None    = None
        self._detail_type: str | None      = None
        # Wizard / multi-step state
        self._add_step: int     = 0
        self._add_name_buf: str = ""
        self._edit_step: int    = 0
        self._edit_old_val: str = ""
        # View state
        self._search_query: str      = ""
        self._note_search_query: str = ""
        self._note_col_width: int    = 60
        # CLI — history & autocomplete
        self._history: list[str]             = []
        self._history_idx: int               = -1
        self._suggestions: list[tuple[str, str]] = []
        self._suggestion_idx: int            = -1
        self._suppress_autocomplete: bool    = False

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Horizontal(id="app-header"):
            yield Label("Retro Assistant", id="header-logo")

        with Horizontal(id="layout"):

            # ── Sidebar ───────────────────────────────────────────────────────
            with Vertical(id="sidebar"):
                yield Button("All contacts",         id="btn-all",       classes="menu-btn")
                yield Button("Search contacts",      id="btn-search",    classes="menu-btn")
                yield Button("Add contact",          id="btn-add",       classes="menu-btn")
                yield Button("Upcoming birthdays",   id="btn-birthdays", classes="menu-btn")
                yield Label("Notes",                 id="sidebar-notes-label")
                yield Button("All notes",            id="btn-notes",     classes="menu-btn")
                yield Button("Search Notes",         id="btn-find-note", classes="menu-btn")
                yield Button("Add note",             id="btn-add-note",  classes="menu-btn")
                with Vertical(id="sidebar-info"):
                    yield Label("contacts: 0",  id="sys-contacts")
                    yield Label("notes: 0",     id="sys-notes")

            # ── Main panel ────────────────────────────────────────────────────
            with Vertical(id="main-panel"):

                with Vertical(id="content-area"):

                    # Default view: system log
                    with Vertical(id="log-view"):
                        yield RichLog(id="output", highlight=True, markup=True)

                    # Detail panel (phone / email / address edit+delete)
                    with Vertical(id="detail-actions"):
                        with Horizontal(id="detail-title-row"):
                            yield Button("←", id="detail-back", classes="back-btn")
                            yield Label("",   id="detail-label")
                        with Horizontal(id="detail-add-row", classes="action-row"):
                            yield Button("Add",    id="detail-add",    classes="detail-btn")
                        with Horizontal(id="detail-edit-row", classes="action-row"):
                            yield Button("Edit",   id="detail-edit",   classes="detail-btn")
                            yield Button("Remove", id="detail-delete", classes="detail-btn")
                        with Horizontal(id="detail-bday-row", classes="action-row"):
                            yield Button("Set / Change", id="detail-bday-set", classes="detail-btn")

                    # Contacts list view
                    with Vertical(id="contacts-view"):
                        with Horizontal(classes="view-header-row"):
                            yield Button("←", id="contacts-back", classes="back-btn")
                            yield Label("Contacts", id="contacts-view-title", classes="row-title")
                        yield DataTable(id="contacts-table", cursor_type="row")
                        with Vertical(id="contact-actions"):
                            yield Label("", id="selected-label")
                            with Horizontal(classes="action-row"):
                                yield Button("Phones",   id="act-phone",     classes="action-btn")
                                yield Button("Emails",   id="act-email",     classes="action-btn")
                                yield Button("Address",  id="act-address",   classes="action-btn")
                            with Horizontal(classes="action-row"):
                                yield Button("Birthday", id="act-show-bday", classes="action-btn")
                                yield Button("Remove",   id="act-delete",    classes="action-btn")

                    # Notes table view
                    with Vertical(id="notes-view"):
                        with Horizontal(classes="view-header-row"):
                            yield Button("←",    id="notes-back", classes="back-btn")
                            yield Label("Notes", id="notes-view-title", classes="row-title")
                        yield DataTable(id="notes-table", cursor_type="row")
                        with Vertical(id="note-actions"):
                            yield Label("", id="note-selected-label")
                            with Horizontal(classes="action-row"):
                                yield Button("Edit",        id="note-edit",    classes="action-btn")
                                yield Button("Add tag",     id="note-add-tag", classes="action-btn")
                            with Horizontal(classes="action-row"):
                                yield Button("Remove tag",  id="note-rm-tag",  classes="action-btn")
                                yield Button("Remove",      id="note-delete",  classes="action-btn")

                with Vertical(id="cmd-area"):
                    yield Label("", id="suggestions-bar")
                    yield Label("", id="cmd-hint")
                    with Horizontal(id="cmd-bar"):
                        yield Input(placeholder="type a command...",   id="cmd-input")

    # ── Startup ───────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        log = self.query_one("#output", RichLog)
        sep = f"[{FOREST_MID}]" + "═" * 48 + f"[/{FOREST_MID}]"
        log.write(sep)
        log.write(
            f"  [bold {SAGE}]RETRO ASSISTANT[/bold {SAGE}]"
            f"  [{TEXT_DIM}]contact + notes manager[/{TEXT_DIM}]"
        )
        log.write(sep)
        log.write("")
        log.write(f"[{TEXT_DIM}]SYSTEM READY. DATA LOADED.[/{TEXT_DIM}]")
        log.write(
            f"  Use [{CLAY}]menu[/{CLAY}] or type a command below."
            f"  Type [{SAGE}]help[/{SAGE}] to list all commands."
        )
        log.write("")

        ct = self.query_one("#contacts-table", DataTable)
        ct.add_column("Name")
        ct.add_column("Phones")
        ct.add_column("Emails")
        ct.add_column("Address")
        ct.add_column("Birthday")
        self.call_after_refresh(self._fit_contact_columns)
        self.query_one("#notes-table", DataTable).add_columns("Note", "Tags")

        self.query_one("#contacts-view").display   = False
        self.query_one("#notes-view").display      = False
        self.query_one("#detail-actions").display    = False
        self.query_one("#detail-add-row").display    = False
        self.query_one("#detail-bday-row").display   = False
        self.query_one("#contact-actions").display = False
        self.query_one("#note-actions").display    = False

        self._update_contact_count()
        self._update_note_count()

        self.query_one("#cmd-input", Input).focus()

    # ── Counters & column sizing ──────────────────────────────────────────────

    def _update_contact_count(self) -> None:
        count = len(self._service.book.data)
        self.query_one("#sys-contacts", Label).update(
            f"[{TEXT_DIM}]contacts: [bold {SAGE_MID}]{count}[/bold {SAGE_MID}][/{TEXT_DIM}]"
        )

    def _update_note_count(self) -> None:
        count = len(self._note_service.notebook.data)
        self.query_one("#sys-notes", Label).update(
            f"[{TEXT_DIM}]notes: [bold {MINT}]{count}[/bold {MINT}][/{TEXT_DIM}]"
        )

    def _fit_contact_columns(self) -> None:
        ct = self.query_one("#contacts-table", DataTable)
        w = ct.size.width - 1
        if w <= 20 or not ct.ordered_columns:
            return
        name_w  = max(10, int(w * 0.20))
        phone_w = max(10, int(w * 0.18))
        email_w = max(8,  int(w * 0.18))
        bday_w  = max(8,  int(w * 0.12))
        addr_w  = max(5,  w - name_w - phone_w - email_w - bday_w)
        for col, cw in zip(ct.ordered_columns, [name_w, phone_w, email_w, addr_w, bday_w]):
            col.width = cw
            col.auto_width = False
        ct.refresh()

    def _fit_notes_columns(self) -> None:
        nt = self.query_one("#notes-table", DataTable)
        w = nt.size.width - 1
        if w <= 20 or not nt.ordered_columns:
            return
        tags_w = max(15, int(w * 0.25))
        note_w = max(20, w - tags_w)
        self._note_col_width = max(10, note_w - 2)
        for col, cw in zip(nt.ordered_columns, [note_w, tags_w]):
            col.width = cw
            col.auto_width = False
        nt.refresh()

    def _refit_notes(self) -> None:
        nt = self.query_one("#notes-table", DataTable)
        if nt.size.width <= 20:
            return
        self._fit_notes_columns()
        self._populate_notes_table(self._note_search_query)

    def on_resize(self) -> None:
        self.call_after_refresh(self._fit_contact_columns)
        self.call_after_refresh(self._fit_notes_columns)

    # ── View helpers ──────────────────────────────────────────────────────────

    def _show_log_view(self) -> None:
        self.query_one("#log-view").display      = True
        self.query_one("#contacts-view").display = False
        self.query_one("#notes-view").display    = False

    def _show_contacts_view(self) -> None:
        self._selected_note      = None
        self._note_search_query  = ""
        self.query_one("#log-view").display      = False
        self.query_one("#contacts-view").display = True
        self.query_one("#notes-view").display    = False
        self._hide_detail_actions()
        self.call_after_refresh(self._fit_contact_columns)

    def _show_notes_view(self) -> None:
        self.query_one("#log-view").display      = False
        self.query_one("#contacts-view").display = False
        self.query_one("#notes-view").display    = True
        self.call_after_refresh(self._refit_notes)

    def _hide_detail_actions(self) -> None:
        self.query_one("#detail-actions").display = False
        self._detail_type = None

    def _show_detail_actions(self, detail_type: str, label: str) -> None:
        self._detail_type = detail_type
        self.query_one("#detail-label", Label).update(label)
        is_bday     = detail_type == "birthday"
        has_add     = detail_type in ("phone", "email", "address")
        back_only   = detail_type == "back_only"
        self.query_one("#detail-edit-row").display    = not is_bday and not back_only
        self.query_one("#detail-add-row").display     = has_add    and not back_only
        self.query_one("#detail-bday-row").display    = is_bday    and not back_only
        self.query_one("#detail-actions").display     = True

    # ── Contact data helpers ──────────────────────────────────────────────────

    @staticmethod
    def _data_health(record) -> tuple[int, str]:
        flags  = [bool(record.phones), bool(record.emails),
                  bool(record.addresses), bool(record.birthday)]
        score  = sum(flags)
        blocks = "".join("█" if f else "░" for f in flags)
        return score, blocks

    @staticmethod
    def _note_preview(note) -> str:
        if not note:
            return ""
        return note.content[:40] + "…" if len(note.content) > 40 else note.content

    def _update_note_label(self, note) -> None:
        tags    = "  ".join(f"#{t.value}" for t in note.tags) if note and note.tags else ""
        preview = self._note_preview(note)
        self.query_one("#note-selected-label", Label).update(
            f"[{TEXT_DIM}]>[/{TEXT_DIM}] [{MINT}]{preview}[/{MINT}]"
            + (f"  [{TEXT_DIM}]{tags}[/{TEXT_DIM}]" if tags else "")
        )

    def _parse_item_index(self, raw: str, items: list, log: RichLog, inp: Input) -> int | None:
        try:
            idx = int(raw.strip()) - 1
        except ValueError:
            log.write(f"[bold {RUST}]Enter a number.[/bold {RUST}]")
            inp.clear()
            return None
        if 0 <= idx < len(items):
            return idx
        log.write(f"[bold {RUST}]Enter 1–{len(items)}.[/bold {RUST}]")
        inp.clear()
        return None

    # ── Contacts table ────────────────────────────────────────────────────────

    def _populate_contacts_table(self, filter_query: str = "") -> None:
        self.query_one("#contact-actions").display = False
        self._selected_contact = None

        table = self.query_one("#contacts-table", DataTable)
        table.clear()

        q     = filter_query.strip().lower()
        count = 0
        for name, record in self._service.book.data.items():
            if q:
                hit = (
                    q in name.lower()
                    or any(q in str(p) for p in record.phones)
                    or any(q in str(e) for e in record.emails)
                )
                if not hit:
                    continue
            phones = "; ".join(str(p) for p in record.phones)    or "—"
            emails = "; ".join(str(e) for e in record.emails)    or "—"
            addrs  = "; ".join(str(a) for a in record.addresses) or "—"
            bday   = str(record.birthday) if record.birthday else "—"
            table.add_row(str(record.name), phones, emails, addrs, bday, key=name)
            count += 1

        title = self.query_one("#contacts-view-title", Label)
        if q:
            suffix = "es" if count != 1 else ""
            title.update(
                f"[bold {CLAY}]Search:[/bold {CLAY}]"
                f" [{SAGE}]{filter_query}[/{SAGE}]"
                f"  [{TEXT_DIM}]{count} match{suffix}[/{TEXT_DIM}]"
            )
        else:
            total  = len(self._service.book.data)
            plural = "s" if total != 1 else ""
            title.update(
                f"[bold {CLAY}]Contacts[/bold {CLAY}]"
                f"  [{TEXT_DIM}]{total} record{plural}[/{TEXT_DIM}]"
            )

    def _show_contact_profile(self, name: str) -> None:
        record = self._service.find_contact(name)
        if not record:
            return
        score, blocks = self._data_health(record)
        hc = MINT if score == 4 else CLAY if score >= 2 else AMBER if score == 1 else RUST
        self.query_one("#selected-label", Label).update(
            f"[{TEXT_DIM}]>[/{TEXT_DIM}] [bold {TEXT_BRIGHT}]{name}[/bold {TEXT_BRIGHT}]"
            f"  [{hc}]{blocks}[/{hc}]  [{TEXT_DIM}]{score}/4[/{TEXT_DIM}]"
        )
        self.query_one("#contact-actions").display = True

    # ── Notes table ───────────────────────────────────────────────────────────

    def _populate_notes_table(self, filter_query: str = "") -> None:
        table = self.query_one("#notes-table", DataTable)
        prev_selected = self._selected_note if not filter_query else None
        table.clear()
        self.query_one("#note-actions").display = False
        self._selected_note = None
        wrap_w = max(20, self._note_col_width)
        count = 0
        for note_id, note in self._note_service.notebook.data.items():
            if filter_query and not note.matches(filter_query):
                continue
            tags      = "  ".join(f"#{t.value}" for t in note.tags) or "—"
            wrapped    = textwrap.wrap(note.content, width=wrap_w)
            note_text  = "\n".join(wrapped) if wrapped else note.content
            row_height = max(1, len(wrapped))
            table.add_row(note_text, tags, key=note_id, height=row_height)
            count += 1
        title = self.query_one("#notes-view-title", Label)
        if filter_query:
            if count == 0:
                title.update(
                    f"[bold {CLAY}]Search:[/bold {CLAY}]"
                    f" [{SAGE}]{filter_query}[/{SAGE}]"
                    f"  [bold {RUST}]Nothing found[/bold {RUST}]"
                )
            else:
                suffix = "es" if count != 1 else ""
                title.update(
                    f"[bold {CLAY}]Search:[/bold {CLAY}]"
                    f" [{SAGE}]{filter_query}[/{SAGE}]"
                    f"  [{TEXT_DIM}]{count} match{suffix}[/{TEXT_DIM}]"
                )
        else:
            total  = len(self._note_service.notebook.data)
            plural = "s" if total != 1 else ""
            title.update(
                f"[bold {CLAY}]Notes[/bold {CLAY}]"
                f"  [{TEXT_DIM}]{total} note{plural}[/{TEXT_DIM}]"
            )
        if prev_selected and prev_selected in self._note_service.notebook.data:
            self._selected_note = prev_selected
            try:
                table.move_cursor(row=table.get_row_index(prev_selected))
                self.query_one("#note-actions").display = True
                note = self._note_service.notebook.find_note(prev_selected)
                if note:
                    self._update_note_label(note)
            except Exception:
                pass

    def _reset_mode(self) -> None:
        self._mode              = None
        self._add_step          = 0
        self._add_name_buf      = ""
        self._edit_step         = 0
        self._edit_old_val      = ""
        self._note_search_query = ""
        inp = self.query_one("#cmd-input", Input)
        inp.placeholder    = "type a command..."
        inp.clear()
        self._hide_detail_actions()
        self._clear_suggestions()

    def _show_contact_after_change(self) -> None:
        contact = self._selected_contact
        self._reset_mode()
        self._populate_contacts_table(self._search_query)
        self._show_contacts_view()
        if contact:
            self._selected_contact = contact
            self._show_contact_profile(contact)

    def _save(self) -> None:
        self._repo.save(self._service.book)

    def _save_notes(self) -> None:
        self._note_repo.save(self._note_service.notebook)

    # ── Sidebar: contacts ─────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn-search")
    def handle_search(self) -> None:
        self._mode         = "search"
        self._search_query = ""
        self._populate_contacts_table()
        self._show_contacts_view()
        inp             = self.query_one("#cmd-input", Input)
        inp.placeholder = "Type to filter contacts…"
        inp.clear()
        inp.focus()

    @on(Button.Pressed, "#btn-add")
    def handle_add_contact(self) -> None:
        self._mode     = "add"
        self._add_step = 1
        self._show_log_view()
        self._hide_detail_actions()
        log = self.query_one("#output", RichLog)
        inp = self.query_one("#cmd-input", Input)
        log.write(
            f"\n[bold {CLAY}]Add Contact[/bold {CLAY}]"
            f"  [{TEXT_DIM}]step 1 / 2[/{TEXT_DIM}]\n"
            f"  Enter contact [bold {SAGE}]name[/bold {SAGE}]:"
        )
        inp.placeholder = "contact name"
        inp.focus()

    @on(Button.Pressed, "#btn-all")
    def handle_all(self) -> None:
        self._reset_mode()
        self._populate_contacts_table()
        self._show_contacts_view()

    @on(Button.Pressed, "#btn-birthdays")
    def handle_birthdays(self) -> None:
        self._reset_mode()
        self._mode = "upcoming_birthdays"
        self._show_log_view()
        log = self.query_one("#output", RichLog)
        inp = self.query_one("#cmd-input", Input)
        log.write(f"\n[bold {CLAY}]Upcoming Birthdays[/bold {CLAY}]")
        log.write(f"  Enter [bold {SAGE}]number of days[/bold {SAGE}] to look ahead:")
        inp.placeholder = "number of days"
        inp.clear()
        inp.focus()

    # ── Sidebar: notes ────────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn-notes")
    def handle_notes(self) -> None:
        self._reset_mode()
        self._populate_notes_table()
        self._show_notes_view()

    @on(Button.Pressed, "#btn-add-note")
    def handle_add_note(self) -> None:
        self._mode = "add_note"
        self._show_log_view()
        log = self.query_one("#output", RichLog)
        inp = self.query_one("#cmd-input", Input)
        log.write(
            f"\n[bold {MINT}]Add Note[/bold {MINT}]"
            f" — enter: [bold {SAGE}]note content…[/bold {SAGE}]"
        )
        inp.placeholder = "note content…"
        inp.focus()

    @on(Button.Pressed, "#btn-find-note")
    def handle_find_note_btn(self) -> None:
        self._reset_mode()
        self._mode = "search_note"
        self._note_search_query = ""
        self._populate_notes_table()
        self._show_notes_view()
        inp = self.query_one("#cmd-input", Input)
        inp.placeholder = "search notes…"
        inp.clear()
        inp.focus()

    # ── Back navigation ───────────────────────────────────────────────────────

    @on(Button.Pressed, "#contacts-back")
    def contacts_back(self) -> None:
        self._reset_mode()
        self._search_query = ""
        self._show_log_view()

    @on(Button.Pressed, "#notes-back")
    def notes_back(self) -> None:
        self._selected_note = None
        self._reset_mode()
        self._show_log_view()

    @on(Button.Pressed, "#detail-back")
    def detail_back(self) -> None:
        contact = self._selected_contact
        self._reset_mode()
        self._populate_contacts_table(self._search_query)
        self._show_contacts_view()
        if contact:
            self._selected_contact = contact
            self._show_contact_profile(contact)

    # ── Contacts table row selection ──────────────────────────────────────────

    @on(DataTable.HeaderSelected, "#contacts-table")
    def handle_contact_header_selected(self, event: DataTable.HeaderSelected) -> None:
        event.stop()

    @on(DataTable.RowSelected, "#contacts-table")
    def handle_row_selected(self, event: DataTable.RowSelected) -> None:
        name = event.row_key.value
        if not name:
            return
        self._selected_contact = name
        self._show_contact_profile(name)

    # ── Contact action buttons ────────────────────────────────────────────────

    @on(Button.Pressed, "#act-delete")
    def act_delete(self) -> None:
        if not self._selected_contact:
            return
        name = self._selected_contact
        try:
            self._service.delete_contact(name)
            self._save()
            self._update_contact_count()
            self.notify(f"'{name}' deleted.", severity="information")
        except KeyError:
            self.notify(f"'{name}' not found.", severity="error")
        self._populate_contacts_table(self._search_query)

    @on(Button.Pressed, "#act-phone, #act-email, #act-address")
    def act_field(self, event: Button.Pressed) -> None:
        if not self._selected_contact:
            return
        record = self._service.find_contact(self._selected_contact)
        if not record:
            return
        field = event.button.id.removeprefix("act-")   # "phone" | "email" | "address"
        _cfg = {
            "phone":   ("Phone",   "phones",    SAGE,         record.phones),
            "email":   ("Email",   "emails",    SAGE_MID,     record.emails),
            "address": ("Address", "addresses", TEXT_PRIMARY, record.addresses),
        }
        singular, plural, color, items = _cfg[field]
        self._show_log_view()
        log = self.query_one("#output", RichLog)
        log.write(
            f"\n[bold {CLAY}]{plural.title()}[/bold {CLAY}]"
            f"  [{TEXT_DIM}]{self._selected_contact}[/{TEXT_DIM}]"
        )
        if items:
            for i, item in enumerate(items, 1):
                log.write(f"    [{TEXT_DIM}]{i}.[/{TEXT_DIM}]  [{color}]{item}[/{color}]")
            items_str    = "  ·  ".join(str(x) for x in items)
            detail_label = (
                f"[bold {CLAY}]{singular}[/bold {CLAY}]"
                f"  [{TEXT_DIM}]—[/{TEXT_DIM}]"
                f"  [{color}]{items_str}[/{color}]"
            )
        else:
            log.write(f"  [{TEXT_DIM}]No {plural} registered.[/{TEXT_DIM}]")
            detail_label = (
                f"[bold {CLAY}]{singular}[/bold {CLAY}]"
                f"  [{TEXT_DIM}]— no {plural} registered[/{TEXT_DIM}]"
            )
        self._show_detail_actions(field, detail_label)

    @on(Button.Pressed, "#act-show-bday")
    def act_show_birthday(self) -> None:
        if not self._selected_contact:
            return
        record = self._service.find_contact(self._selected_contact)
        if not record:
            return
        self._show_log_view()
        log = self.query_one("#output", RichLog)
        log.write(
            f"\n[bold {CLAY}]Birthday[/bold {CLAY}]"
            f"  [{TEXT_DIM}]{self._selected_contact}[/{TEXT_DIM}]"
        )
        if record.birthday:
            log.write(f"  [bold {CLAY}]{record.birthday}[/bold {CLAY}]")
            detail_label = (
                f"[bold {CLAY}]Birthday[/bold {CLAY}]"
                f"  [{TEXT_DIM}]—[/{TEXT_DIM}]"
                f"  [bold {CLAY}]{record.birthday}[/bold {CLAY}]"
            )
        else:
            log.write(f"  [{TEXT_DIM}]No birthday set.[/{TEXT_DIM}]")
            detail_label = (
                f"[bold {CLAY}]Birthday[/bold {CLAY}]"
                f"  [{TEXT_DIM}]— not set[/{TEXT_DIM}]"
            )
        self._show_detail_actions("birthday", detail_label)

    @on(Button.Pressed, "#detail-bday-set")
    def detail_bday_set(self) -> None:
        if not self._selected_contact:
            return
        record = self._service.find_contact(self._selected_contact)
        if not record:
            return
        self._mode = "add_birthday"
        self._hide_detail_actions()
        inp = self.query_one("#cmd-input", Input)
        log = self.query_one("#output", RichLog)
        action = "Change" if record.birthday else "Add"
        log.write(
            f"\n[bold {CLAY}]{action} Birthday[/bold {CLAY}]"
            f"  [{TEXT_DIM}]{self._selected_contact}[/{TEXT_DIM}]"
        )
        if record.birthday:
            log.write(
                f"  [{TEXT_DIM}]current:[/{TEXT_DIM}] [{CLAY}]{record.birthday}[/{CLAY}]"
                f"  [{TEXT_DIM}](will be replaced)[/{TEXT_DIM}]"
            )
        log.write(f"  Enter date: [bold {SAGE}]DD.MM.YYYY[/bold {SAGE}]")
        inp.placeholder = "DD.MM.YYYY"
        inp.focus()

    @on(Button.Pressed, "#detail-add")
    def detail_add(self) -> None:
        if not self._selected_contact:
            return
        _cfg = {
            "phone":   ("add_phone",   "Add Phone",   "phone number"),
            "email":   ("add_email",   "Add Email",   "email address"),
            "address": ("add_address", "Add Address", "address"),
        }
        cfg = _cfg.get(self._detail_type)
        if not cfg:
            return
        mode, title, placeholder = cfg
        self._mode = mode
        self._hide_detail_actions()
        inp = self.query_one("#cmd-input", Input)
        log = self.query_one("#output", RichLog)
        log.write(
            f"\n[bold {CLAY}]{title}[/bold {CLAY}]"
            f"  [{TEXT_DIM}]{self._selected_contact}[/{TEXT_DIM}]"
        )
        log.write(f"  Enter [bold {SAGE}]{placeholder}[/bold {SAGE}]:")
        inp.placeholder = placeholder
        inp.clear()
        inp.focus()

    # ── Detail edit / delete (phone · email · address) ──────────────────────

    @on(Button.Pressed, "#detail-edit")
    def detail_edit(self) -> None:
        record = self._service.find_contact(self._selected_contact)
        if not record:
            return
        _cfg = {
            "phone":   ("edit_phone",   list(record.phones),    "phone",   "phone number"),
            "email":   ("edit_email",   list(record.emails),    "email",   "email address"),
            "address": ("edit_address", list(record.addresses), "address", "address"),
        }
        cfg = _cfg.get(self._detail_type)
        if not cfg:
            return
        mode, items, label, placeholder = cfg
        if not items:
            self.notify(f"No {label} available for editing.", severity="warning")
            return
        self._mode = mode
        self._hide_detail_actions()
        self._show_log_view()
        log = self.query_one("#output", RichLog)
        inp = self.query_one("#cmd-input", Input)
        log.write(
            f"\n[bold {CLAY}]Edit {label.title()}[/bold {CLAY}]"
            f"  [{TEXT_DIM}]{self._selected_contact}[/{TEXT_DIM}]"
        )
        if len(items) == 1:
            self._edit_old_val = str(items[0])
            self._edit_step    = 2
            log.write(
                f"  [{TEXT_DIM}]current:[/{TEXT_DIM}]  [{TEXT_SECONDARY}]{self._edit_old_val}[/{TEXT_SECONDARY}]\n"
                f"  Enter [bold {SAGE}]new {placeholder}[/bold {SAGE}]:"
            )
            inp.placeholder = f"new {placeholder}"
            inp.value = self._edit_old_val
        else:
            self._edit_step = 1
            inp.clear()
            log.write(f"  [{TEXT_DIM}]select {label} to edit:[/{TEXT_DIM}]")
            for i, item in enumerate(items, 1):
                log.write(f"    [{TEXT_DIM}]{i}.[/{TEXT_DIM}]  [{TEXT_SECONDARY}]{item}[/{TEXT_SECONDARY}]")
            log.write(f"  Enter [bold {CLAY}]number[/bold {CLAY}] (1–{len(items)}):")
            inp.placeholder = f"1–{len(items)}"
        inp.focus()

    @on(Button.Pressed, "#detail-delete")
    def detail_delete(self) -> None:
        if not self._selected_contact:
            return
        record = self._service.find_contact(self._selected_contact)
        if not record:
            return

        detail_type = self._detail_type
        _cfg = {
            "phone":   (list(record.phones),    "remove-phone",   "phone",   "delete_phone"),
            "email":   (list(record.emails),    "remove-email",   "email",   "delete_email"),
            "address": (list(record.addresses), "remove-address", "address", "delete_address"),
        }
        if detail_type not in _cfg:
            return
        items, cmd, label, delete_mode = _cfg[detail_type]

        self._hide_detail_actions()

        if not items:
            self.notify(f"No {label}s to remove.", severity="warning")
            return

        if len(items) == 1:
            result = self._cmd_registry.execute(cmd, [self._selected_contact, str(items[0])], self._service)
            is_success = "removed" in result
            if is_success:
                self._save()
            self.notify(result, severity="information" if is_success else "error")
            self._reset_mode()
            self._show_contacts_view()
            self._show_contact_profile(self._selected_contact)
        else:
            log = self.query_one("#output", RichLog)
            inp = self.query_one("#cmd-input", Input)
            log.write(
                f"\n[bold {CLAY}]Remove {label.title()}[/bold {CLAY}]"
                f"  [{TEXT_DIM}]{self._selected_contact}[/{TEXT_DIM}]"
            )
            for i, item in enumerate(items, 1):
                log.write(f"    [{TEXT_DIM}]{i}.[/{TEXT_DIM}]  [{TEXT_SECONDARY}]{item}[/{TEXT_SECONDARY}]")
            log.write(f"  Enter [bold {RUST}]number[/bold {RUST}] (1–{len(items)}):")
            self._mode = delete_mode
            self._edit_step = 1
            inp.placeholder = f"1–{len(items)}"
            inp.focus()

    # ── Notes table ───────────────────────────────────────────────────────────

    @on(DataTable.RowSelected, "#notes-table")
    def handle_note_selected(self, event: DataTable.RowSelected) -> None:
        note_id = event.row_key.value
        if not note_id:
            return
        self._selected_note = note_id
        self._update_note_label(self._note_service.notebook.find_note(note_id))
        self.query_one("#note-actions").display = True

    # ── Note action buttons ───────────────────────────────────────────────────

    @on(Button.Pressed, "#note-edit")
    def note_edit(self) -> None:
        if not self._selected_note:
            return
        self._mode = "edit_note"
        self._show_log_view()
        log  = self.query_one("#output", RichLog)
        inp  = self.query_one("#cmd-input", Input)
        note = self._note_service.notebook.find_note(self._selected_note)
        if note:
            log.write(
                f"\n[bold {MINT}]Edit Note[/bold {MINT}]\n"
                f"  [{TEXT_DIM}]current content:[/{TEXT_DIM}]\n"
                f"  [{TEXT_SECONDARY}]{note.content}[/{TEXT_SECONDARY}]\n"
                f"  Enter [bold {SAGE}]new content[/bold {SAGE}]:"
            )
            inp.value = note.content
        inp.placeholder = "new content…"
        inp.focus()

    @on(Button.Pressed, "#note-delete")
    def note_delete(self) -> None:
        if not self._selected_note:
            return
        note_id = self._selected_note
        try:
            self._note_service.delete_note(note_id)
            self._save_notes()
            self._update_note_count()
            self.notify("Note deleted.", severity="information")
        except KeyError:
            self.notify("Note not found.", severity="error")
        self._populate_notes_table()

    @on(Button.Pressed, "#note-add-tag")
    def note_add_tag(self) -> None:
        if not self._selected_note:
            return
        self._mode = "add_note_tag"
        self._show_log_view()
        note = self._note_service.notebook.find_note(self._selected_note)
        log  = self.query_one("#output", RichLog)
        inp  = self.query_one("#cmd-input", Input)
        log.write(
            f"\n[bold {MINT}]Add Tag[/bold {MINT}]"
            f"  [{TEXT_DIM}]{self._note_preview(note)}[/{TEXT_DIM}]"
        )
        if note and note.tags:
            existing = "  ".join(f"[{MINT}]#{t.value}[/{MINT}]" for t in note.tags)
            log.write(f"  [{TEXT_DIM}]existing:[/{TEXT_DIM}]  {existing}")
        log.write(f"  Enter [bold {SAGE}]tag name[/bold {SAGE}]:")
        inp.placeholder = "tagname"
        inp.focus()

    @on(Button.Pressed, "#note-rm-tag")
    def note_rm_tag(self) -> None:
        if not self._selected_note:
            return
        self._mode = "rm_note_tag"
        self._show_log_view()
        note = self._note_service.notebook.find_note(self._selected_note)
        log  = self.query_one("#output", RichLog)
        inp  = self.query_one("#cmd-input", Input)
        log.write(
            f"\n[bold {MINT}]Remove Tag[/bold {MINT}]"
            f"  [{TEXT_DIM}]{self._note_preview(note)}[/{TEXT_DIM}]"
        )
        if note and note.tags:
            tags_list = "  ".join(f"[{MINT}]#{t.value}[/{MINT}]" for t in note.tags)
            log.write(f"  [{TEXT_DIM}]tags:[/{TEXT_DIM}]  {tags_list}")
        else:
            log.write(f"  [{TEXT_DIM}]No tags to remove.[/{TEXT_DIM}]")
        log.write(f"  Enter tag to [bold {RUST}]remove[/bold {RUST}]:")
        inp.placeholder = "tag to remove"
        inp.focus()

    # ── Autocomplete & history ────────────────────────────────────────────────

    def _all_command_defs(self) -> list[tuple[str, str]]:
        specials = [
            ("help",  "— show all commands"),
            ("exit",  "— quit the application"),
        ]
        return (
            specials
            + [(c.name, c.description) for c in self._cmd_registry.commands()]
            + [(c.name, c.description) for c in self._note_registry.commands()]
        )

    def _build_suggestions(self, text: str) -> None:
        if self._mode is not None or not text.strip():
            self._clear_suggestions()
            return

        parts    = text.split()
        word     = parts[0] if parts else ""
        has_args = len(parts) > 1 or text.endswith(" ")

        all_cmds = self._all_command_defs()
        matches  = [c for c in all_cmds if c[0].startswith(word)]
        exact    = next((c for c in matches if c[0] == word), None)

        if not matches:
            self._clear_suggestions()
            return

        if has_args or (exact and len(matches) == 1):
            self._suggestions    = []
            self._suggestion_idx = -1
            self.query_one("#suggestions-bar", Label).update("")
            self._show_hint(exact) if exact else self.query_one("#cmd-hint", Label).update("")
            return

        self._suggestions = matches
        self._suggestion_idx = 0 if len(matches) == 1 else -1
        self._render_suggestions()

    def _render_suggestions(self) -> None:
        bar      = self.query_one("#suggestions-bar", Label)
        hint_lbl = self.query_one("#cmd-hint",        Label)

        if not self._suggestions:
            bar.update("")
            hint_lbl.update("")
            return

        parts = []
        for i, (name, _) in enumerate(self._suggestions):
            if i == self._suggestion_idx:
                parts.append(f"[bold {SAGE}]❯ {name}[/bold {SAGE}]")
            else:
                parts.append(f"[{TEXT_PRIMARY}]{name}[/{TEXT_PRIMARY}]")
        bar.update("   ".join(parts))

        if self._suggestion_idx >= 0:
            self._show_hint(self._suggestions[self._suggestion_idx])
        else:
            hint_lbl.update(
                f"[{TEXT_DIM}]↑↓ — navigate   Tab — apply[/{TEXT_DIM}]"
            )

    def _show_hint(self, cmd: tuple[str, str]) -> None:
        name, desc = cmd
        self.query_one("#cmd-hint", Label).update(
            f"[{SAGE_MID}]{name}[/{SAGE_MID}]  [{TEXT_DIM}]{desc}[/{TEXT_DIM}]"
        )

    def _clear_suggestions(self) -> None:
        self._suggestions    = []
        self._suggestion_idx = -1
        try:
            self.query_one("#suggestions-bar", Label).update("")
            self.query_one("#cmd-hint",        Label).update("")
        except Exception:
            pass

    def _navigate_history(self, delta: int) -> None:
        if not self._history:
            return
        inp = self.query_one("#cmd-input", Input)
        if delta < 0:
            if self._history_idx == -1:
                self._history_idx = len(self._history) - 1
            elif self._history_idx > 0:
                self._history_idx -= 1
        else:
            if self._history_idx == -1:
                return
            if self._history_idx < len(self._history) - 1:
                self._history_idx += 1
            else:
                self._history_idx = -1
                self._suppress_autocomplete = True
                inp.value = ""
                return
        self._suppress_autocomplete = True
        inp.value = self._history[self._history_idx]
        inp.cursor_position = len(inp.value)

    def on_key(self, event: events.Key) -> None:
        inp = self.query_one("#cmd-input", Input)
        if self.focused is not inp:
            return

        key = event.key

        if key == "escape":
            event.prevent_default()
            self._clear_suggestions()
            self._history_idx = -1
            return

        if key == "tab" and self._suggestions:
            event.prevent_default()
            if self._suggestion_idx < 0:
                self._suggestion_idx = 0
            cmd_tuple = self._suggestions[self._suggestion_idx]
            self._suppress_autocomplete = True
            inp.value = cmd_tuple[0] + " "
            inp.cursor_position = len(inp.value)
            self._suggestions    = []
            self._suggestion_idx = -1
            self.query_one("#suggestions-bar", Label).update("")
            self._show_hint(cmd_tuple)
            return

        if key == "up":
            if self._suggestions:
                event.prevent_default()
                n = len(self._suggestions)
                self._suggestion_idx = (n - 1) if self._suggestion_idx <= 0 else (self._suggestion_idx - 1)
                self._render_suggestions()
            elif self._mode is None:
                event.prevent_default()
                self._navigate_history(-1)
            return

        if key == "down":
            if self._suggestions:
                event.prevent_default()
                self._suggestion_idx = (self._suggestion_idx + 1) % len(self._suggestions)
                self._render_suggestions()
            elif self._mode is None:
                event.prevent_default()
                self._navigate_history(1)
            return

    # ── Live search filter ────────────────────────────────────────────────────

    @on(Input.Changed, "#cmd-input")
    def handle_input_changed(self, event: Input.Changed) -> None:
        if self._mode == "search":
            self._search_query = event.value.strip()
            self._populate_contacts_table(self._search_query)
            return
        if self._mode == "search_note":
            self._note_search_query = event.value.strip()
            self._populate_notes_table(self._note_search_query)
            return
        if self._suppress_autocomplete:
            self._suppress_autocomplete = False
            return
        self._history_idx = -1
        self._build_suggestions(event.value)

    # ── Command input (submit) ────────────────────────────────────────────────

    @on(Input.Submitted, "#cmd-input")
    def handle_input(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        inp = self.query_one("#cmd-input", Input)
        if not raw:
            inp.clear()
            return

        log = self.query_one("#output", RichLog)

        if self._mode == "search":
            table = self.query_one("#contacts-table", DataTable)
            if table.row_count == 1:
                try:
                    row_key = next(iter(table.rows))
                    name    = row_key.value
                    if name:
                        self._selected_contact = name
                        self._mode         = None
                        self._search_query = ""
                        inp.clear()
                        inp.placeholder = "type a command..."
                        self._show_contact_profile(name)
                        return
                except StopIteration:
                    pass
            self._mode         = None
            self._search_query = ""
            inp.placeholder    = "type a command..."
            inp.clear()
            return

        if self._mode == "search_note":
            table = self.query_one("#notes-table", DataTable)
            if table.row_count == 1:
                try:
                    row_key = next(iter(table.rows))
                    note_id = row_key.value
                    if note_id:
                        self._selected_note     = note_id
                        self._mode              = None
                        self._note_search_query = ""
                        inp.clear()
                        inp.placeholder = "type a command..."
                        self._update_note_label(self._note_service.notebook.find_note(note_id))
                        self.query_one("#note-actions").display = True
                        return
                except StopIteration:
                    pass
            self._mode              = None
            self._note_search_query = ""
            inp.placeholder         = "type a command..."
            inp.clear()
            self._populate_notes_table()
            return

        self._show_log_view()
        log.write(f"[bold {SAGE_MID}]>[/bold {SAGE_MID}] [{TEXT_PRIMARY}]{raw}[/{TEXT_PRIMARY}]")

        if self._mode == "add":
            if self._add_step == 1:
                if not raw:
                    log.write(f"[bold {RUST}]Name cannot be empty.[/bold {RUST}]")
                    inp.clear()
                    return
                existing = self._service.find_contact(raw)
                if existing:
                    log.write(
                        f"  [{TEXT_DIM}]Note:[/{TEXT_DIM}] [{TEXT_BRIGHT}]{raw}[/{TEXT_BRIGHT}]"
                        f" [{TEXT_DIM}]already exists — a phone will be added.[/{TEXT_DIM}]"
                    )
                self._add_name_buf = raw
                self._add_step     = 2
                log.write(
                    f"\n[bold {CLAY}]Add Contact[/bold {CLAY}]"
                    f"  [{TEXT_DIM}]step 2 / 2[/{TEXT_DIM}]\n"
                    f"  Name: [bold {TEXT_BRIGHT}]{self._add_name_buf}[/bold {TEXT_BRIGHT}]\n"
                    f"  Enter [bold {SAGE}]phone number[/bold {SAGE}]:"
                )
                inp.placeholder = "phone number"
                inp.clear()
                return
            elif self._add_step == 2:
                result = self._cmd_registry.execute(
                    "add", [self._add_name_buf, raw], self._service
                )
                log.write(f"[{MINT}]{result}[/{MINT}]")
                self._save()
                self._update_contact_count()
                self._reset_mode()
                return

        elif self._mode == "add_phone":
            result = self._cmd_registry.execute(
                "add", [self._selected_contact, raw], self._service
            )
            if "added" in result or "updated" in result:
                log.write(f"[{MINT}]{result}[/{MINT}]")
                self._save()
                self._update_contact_count()
                self.notify(result, severity="information")
                self._show_contact_after_change()
            else:
                log.write(f"[bold {RUST}]{result}[/bold {RUST}]")
                inp.clear()
                self._show_detail_actions(
                    "back_only",
                    f"[bold {CLAY}]Phone[/bold {CLAY}]  [{RUST}]{result}[/{RUST}]",
                )

        elif self._mode == "add_email":
            result = self._cmd_registry.execute(
                "add-email", [self._selected_contact, raw], self._service
            )
            if "added" in result:
                log.write(f"[{MINT}]{result}[/{MINT}]")
                self._save()
                self.notify(result, severity="information")
                self._show_contact_after_change()
            else:
                log.write(f"[bold {RUST}]{result}[/bold {RUST}]")
                inp.clear()
                self._show_detail_actions(
                    "back_only",
                    f"[bold {CLAY}]Email[/bold {CLAY}]  [{RUST}]{result}[/{RUST}]",
                )

        elif self._mode == "add_address":
            result = self._cmd_registry.execute(
                "add-address", [self._selected_contact, raw], self._service
            )
            if "added" in result:
                log.write(f"[{MINT}]{result}[/{MINT}]")
                self._save()
                self.notify(result, severity="information")
                self._show_contact_after_change()
            else:
                log.write(f"[bold {RUST}]{result}[/bold {RUST}]")
                inp.clear()
                self._show_detail_actions(
                    "back_only",
                    f"[bold {CLAY}]Address[/bold {CLAY}]  [{RUST}]{result}[/{RUST}]",
                )

        elif self._mode == "edit_phone":
            if self._edit_step == 1:
                record = self._service.find_contact(self._selected_contact)
                phones = list(record.phones)
                idx    = self._parse_item_index(raw, phones, log, inp)
                if idx is None:
                    return
                self._edit_old_val = str(phones[idx])
                self._edit_step    = 2
                log.write(
                    f"  [{TEXT_DIM}]selected:[/{TEXT_DIM}]  [{TEXT_SECONDARY}]{self._edit_old_val}[/{TEXT_SECONDARY}]\n"
                    f"  Enter [bold {SAGE}]new phone number[/bold {SAGE}]:"
                )
                inp.placeholder = "new phone number"
                inp.clear()
                return
            elif self._edit_step == 2:
                result = self._cmd_registry.execute(
                    "change-phone", [self._selected_contact, self._edit_old_val, raw], self._service
                )
                if "updated" in result:
                    log.write(f"[{MINT}]{result}[/{MINT}]")
                    self._save()
                    self.notify(result, severity="information")
                    self._show_contact_after_change()
                else:
                    log.write(f"[bold {RUST}]{result}[/bold {RUST}]")
                    inp.clear()
                    self._show_detail_actions(
                        "back_only",
                        f"[bold {CLAY}]Phone[/bold {CLAY}]  [{RUST}]{result}[/{RUST}]",
                    )

        elif self._mode == "edit_email":
            if self._edit_step == 1:
                record = self._service.find_contact(self._selected_contact)
                emails = list(record.emails)
                idx    = self._parse_item_index(raw, emails, log, inp)
                if idx is None:
                    return
                self._edit_old_val = str(emails[idx])
                self._edit_step    = 2
                log.write(
                    f"  [{TEXT_DIM}]selected:[/{TEXT_DIM}]  [{TEXT_SECONDARY}]{self._edit_old_val}[/{TEXT_SECONDARY}]\n"
                    f"  Enter [bold {SAGE}]new email address[/bold {SAGE}]:"
                )
                inp.placeholder = "new email address"
                inp.clear()
                return
            elif self._edit_step == 2:
                result = self._cmd_registry.execute(
                    "change-email", [self._selected_contact, self._edit_old_val, raw], self._service
                )
                if "updated" in result:
                    log.write(f"[{MINT}]{result}[/{MINT}]")
                    self._save()
                    self.notify(result, severity="information")
                    self._show_contact_after_change()
                else:
                    log.write(f"[bold {RUST}]{result}[/bold {RUST}]")
                    inp.clear()
                    self._show_detail_actions(
                        "back_only",
                        f"[bold {CLAY}]Email[/bold {CLAY}]  [{RUST}]{result}[/{RUST}]",
                    )

        elif self._mode == "edit_address":
            if self._edit_step == 1:
                record    = self._service.find_contact(self._selected_contact)
                addresses = list(record.addresses)
                idx       = self._parse_item_index(raw, addresses, log, inp)
                if idx is None:
                    return
                self._edit_old_val = str(addresses[idx])
                self._edit_step    = 2
                log.write(
                    f"  [{TEXT_DIM}]selected:[/{TEXT_DIM}]  [{TEXT_SECONDARY}]{self._edit_old_val}[/{TEXT_SECONDARY}]\n"
                    f"  Enter [bold {SAGE}]new address[/bold {SAGE}]:"
                )
                inp.placeholder = "new address"
                inp.clear()
                return
            elif self._edit_step == 2:
                result = self._cmd_registry.execute(
                    "change-address", [self._selected_contact, self._edit_old_val, raw], self._service
                )
                if "updated" in result:
                    log.write(f"[{MINT}]{result}[/{MINT}]")
                    self._save()
                    self.notify(result, severity="information")
                    self._show_contact_after_change()
                else:
                    log.write(f"[bold {RUST}]{result}[/bold {RUST}]")
                    inp.clear()
                    self._show_detail_actions(
                        "back_only",
                        f"[bold {CLAY}]Address[/bold {CLAY}]  [{RUST}]{result}[/{RUST}]",
                    )

        elif self._mode in ("delete_phone", "delete_email", "delete_address"):
            record = self._service.find_contact(self._selected_contact)
            if not record:
                self._reset_mode()
                return
            _del_cfg = {
                "delete_phone":   ("remove-phone",   list(record.phones)),
                "delete_email":   ("remove-email",   list(record.emails)),
                "delete_address": ("remove-address", list(record.addresses)),
            }
            cmd, items = _del_cfg[self._mode]
            idx = self._parse_item_index(raw, items, log, inp)
            if idx is None:
                return
            self._cmd_registry.execute(cmd, [self._selected_contact, str(items[idx])], self._service)
            self._save()
            self._reset_mode()
            self._show_contacts_view()
            self._show_contact_profile(self._selected_contact)

        elif self._mode == "add_birthday":
            contact_name = self._selected_contact
            result = self._cmd_registry.execute(
                "add-birthday", [contact_name, raw], self._service
            )
            success = "added" in result or "updated" in result
            if success:
                log.write(f"[{MINT}]{result}[/{MINT}]")
                self._save()
            else:
                log.write(f"[bold {RUST}]{result}[/bold {RUST}]")
            self._mode = None
            inp.placeholder = "type a command..."
            inp.clear()
            back_label = (
                f"[bold {CLAY}]Birthday[/bold {CLAY}]"
                f"  [{TEXT_DIM}]—[/{TEXT_DIM}]"
                f"  [{MINT if success else RUST}]{result}[/{MINT if success else RUST}]"
            )
            self._show_detail_actions("back_only", back_label)

        elif self._mode == "add_note":
            if raw.strip():
                result = self._note_registry.execute("add-note", raw.split(), self._note_service)
                if "added" in result:
                    self._save_notes()
                    self._update_note_count()
                    self._reset_mode()
                    self._populate_notes_table()
                    self._show_notes_view()
                else:
                    log.write(f"[bold {RUST}]{result}[/bold {RUST}]")
                    inp.clear()
            else:
                log.write(f"[bold {RUST}]Note content cannot be empty.[/bold {RUST}]")
                inp.clear()

        elif self._mode == "edit_note":
            if raw:
                result = self._note_registry.execute(
                    "change-note", [self._selected_note] + raw.split(), self._note_service
                )
                log.write(f"[{MINT}]{result}[/{MINT}]")
                self._save_notes()
                self._populate_notes_table()
            self._reset_mode()
            self._show_notes_view()

        elif self._mode == "add_note_tag":
            result = self._note_registry.execute(
                "add-tag", [self._selected_note, raw.strip()], self._note_service
            )
            if "added" in result:
                log.write(f"[{MINT}]{result}[/{MINT}]")
                self._save_notes()
                self._populate_notes_table()
                self._reset_mode()
                self._show_notes_view()
            else:
                log.write(f"[bold {RUST}]{result}[/bold {RUST}]")
                inp.clear()

        elif self._mode == "rm_note_tag":
            result = self._note_registry.execute(
                "remove-tag", [self._selected_note, raw.strip()], self._note_service
            )
            if "removed" in result:
                log.write(f"[{MINT}]{result}[/{MINT}]")
                self._save_notes()
                self._populate_notes_table()
                self._reset_mode()
                self._show_notes_view()
            else:
                log.write(f"[bold {RUST}]{result}[/bold {RUST}]")
                inp.clear()

        elif self._mode == "upcoming_birthdays":
            try:
                days = int(raw.strip())
                if days <= 0:
                    raise ValueError
            except ValueError:
                log.write(f"[bold {RUST}]Enter a positive number.[/bold {RUST}]")
                inp.clear()
                return
            upcoming = self._service.get_upcoming_birthdays(days)
            log.write(f"\n[bold {CLAY}]Upcoming Birthdays — next {days} days[/bold {CLAY}]")
            if not upcoming:
                log.write(f"  [{TEXT_DIM}]No birthdays in the next {days} days.[/{TEXT_DIM}]")
            else:
                for u in upcoming:
                    name  = u["name"]
                    bday  = u["birthday"]
                    try:
                        parts    = [int(x) for x in bday.split(".")]
                        bday_dt  = date(parts[2], parts[1], parts[0]).replace(year=date.today().year)
                        days_left = (bday_dt - date.today()).days
                        countdown = (
                            f"[bold {CLAY}]today[/bold {CLAY}]" if days_left == 0 else
                            f"[{CLAY}]tomorrow[/{CLAY}]"         if days_left == 1 else
                            ""
                        )
                    except Exception:
                        countdown = ""
                    log.write(
                        f"  [bold {TEXT_BRIGHT}]{name}[/bold {TEXT_BRIGHT}]"
                        f"  [{TEXT_DIM}]born[/{TEXT_DIM}] [{CLAY}]{bday}[/{CLAY}]"
                        + (f"  {countdown}" if countdown else "")
                    )
            self._reset_mode()

        else:
            if raw:
                self._history.append(raw)
                self._history_idx = -1
            self._clear_suggestions()
            self._dispatch(raw, log)
            inp.clear()

    # ── General command dispatcher ────────────────────────────────────────────

    def _dispatch(self, raw: str, log: RichLog) -> None:
        punctuation = string.punctuation.replace("-", "")
        parts = raw.split()
        cmd   = parts[0].lower().translate(str.maketrans("", "", punctuation)) if parts else ""
        args  = parts[1:]

        if cmd == "all-contacts":
            self._populate_contacts_table()
            self._show_contacts_view()
            return
        if cmd in ("exit", "close", "quit"):
            self.exit()
            return
        if cmd in ("hello", "help"):
            log.write(self._cmd_registry.help_text())
            log.write(
                self._note_registry.help_text("Note commands:")
                + f"\n\n  [dim]Tip: to get note ID, run[/dim] [cyan]all-notes[/cyan]"
            )
            return

        note_cmd = self._note_registry.get(cmd)
        if note_cmd:
            result = self._note_registry.execute(cmd, args, self._note_service)
            color = AMBER if result.startswith("No ") else MINT
            log.write(f"[{color}]{result}[/{color}]")
            if note_cmd.modifies_data:
                self._save_notes()
                self._update_note_count()
            return

        result  = self._cmd_registry.execute(cmd, args, self._service)
        cmd_obj = self._cmd_registry.get(cmd)
        if cmd_obj and cmd_obj.modifies_data:
            log.write(f"[{MINT}]{result}[/{MINT}]")
            self._save()
            self._update_contact_count()
        elif cmd_obj:
            log.write(result)
        else:
            log.write(f"[bold {RUST}]{result}[/bold {RUST}]")

    def on_unmount(self) -> None:
        self._save()
        self._save_notes()
