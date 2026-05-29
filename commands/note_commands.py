from commands.registry import note_registry
from helpers.error_handler import input_error


@note_registry.command("add-note", "<content…>  — create a new note", modifies_data=True)
@input_error
def add_note(args, service):
    if not args:
        raise ValueError("Note content cannot be empty.")
    content = " ".join(args)
    return service.add_note(content)


@note_registry.command("change-note", "<id> <new_content…>  — update note content (Call ‘all-notes’ to find out the ID)", modifies_data=True)
@input_error
def edit_note(args, service):
    if len(args) < 2:
        raise ValueError("Usage: change-note <id> <new content…>")
    note_id, *rest = args
    content = " ".join(rest)
    return service.edit_note(note_id, content)


@note_registry.command("delete-note", "<id>  — delete a note (Call ‘all-notes’ to find out the ID)", modifies_data=True)
@input_error
def delete_note(args, service):
    if not args:
        raise ValueError("Usage: delete-note <id>")
    note_id, *_ = args
    return service.delete_note(note_id)


@note_registry.command("show-note", "<id>  — display a note (Call ‘all-notes’ to find out the ID)")
@input_error
def show_note(args, service):
    if not args:
        raise ValueError("Usage: show-note <id>")
    note_id, *_ = args
    return service.show_note(note_id)


@note_registry.command("all-notes", "— list all notes")
def show_all_notes(args, service):
    return service.show_all()


@note_registry.command("find-note", "<query>  — search notes by content/tag")
@input_error
def find_note(args, service):
    if not args:
        raise ValueError("Usage: find-note <query>")
    return service.format_find(" ".join(args))


@note_registry.command("add-tag", "<id> <tag>  — add tag to a note (Call ‘all-notes’ to find out the ID)", modifies_data=True)
@input_error
def add_tag(args, service):
    if len(args) < 2:
        raise ValueError("Usage: add-tag <id> <tag>")
    note_id, tag, *_ = args
    return service.add_tag(note_id, tag)


@note_registry.command("remove-tag", "<id> <tag>  — remove tag from a note (Call ‘all-notes’ to find out the ID)", modifies_data=True)
@input_error
def remove_tag(args, service):
    if len(args) < 2:
        raise ValueError("Usage: remove-tag <id> <tag>")
    note_id, tag, *_ = args
    return service.remove_tag(note_id, tag)


@note_registry.command("notes-by-tag", "<tag>  — find notes by tag, sorted")
@input_error
def find_by_tag(args, service):
    if not args:
        raise ValueError("Usage: notes-by-tag <tag>")
    tag, *_ = args
    return service.format_by_tag(tag)