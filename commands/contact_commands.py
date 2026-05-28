from commands.registry import contact_registry
from helpers.error_handler import input_error


@contact_registry.command("add", "<name> <phone>  — add or update a contact", modifies_data=True)
@input_error
def add_contact(args, service):
    if len(args) < 2:
        raise ValueError("Usage: add <name> <phone>")
    name, phone, *_ = args
    return service.add_contact(name, phone)


@contact_registry.command("change", "<name> <old_phone> <new_phone>  — update phone", modifies_data=True)
@input_error
def change_phone(args, service):
    if len(args) < 3:
        raise ValueError("Usage: change <name> <old_phone> <new_phone>")
    name, old, new, *_ = args
    return service.change_phone(name, old, new)


@contact_registry.command("delete", "<name>  — remove a contact", modifies_data=True)
@input_error
def delete_contact(args, service):
    if not args:
        raise ValueError("Usage: delete <name>")
    name, *_ = args
    return service.delete_contact(name)


@contact_registry.command("remove-phone", "<name> <phone>  — remove phone", modifies_data=True)
@input_error
def remove_phone(args, service):
    if len(args) < 2:
        raise ValueError("Usage: remove-phone <name> <phone>")
    name, phone, *_ = args
    return service.remove_phone(name, phone)


@contact_registry.command("phone", "<name>  — show phone numbers")
@input_error
def show_phone(args, service):
    if not args:
        raise ValueError("Usage: phone <name>")
    name, *_ = args
    return service.show_phone(name)


@contact_registry.command("all", "— list all contacts")
def show_all(args, service):
    return service.show_all()