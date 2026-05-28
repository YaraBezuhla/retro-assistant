from commands.registry import contact_registry
from helpers.error_handler import input_error


@contact_registry.command("add-email", "<name> <email>  — add email", modifies_data=True)
@input_error
def add_email(args, service):
    if len(args) < 2:
        raise ValueError("Usage: add-email <name> <email>")
    name, email, *_ = args
    return service.add_email(name, email)


@contact_registry.command("change-email", "<name> <old_email> <new_email>  — update email", modifies_data=True)
@input_error
def change_email(args, service):
    if len(args) < 3:
        raise ValueError("Usage: change-email <name> <old_email> <new_email>")
    name, old, new, *_ = args
    return service.change_email(name, old, new)


@contact_registry.command("remove-email", "<name> <email>  — remove email", modifies_data=True)
@input_error
def remove_email(args, service):
    if len(args) < 2:
        raise ValueError("Usage: remove-email <name> <email>")
    name, email, *_ = args
    return service.remove_email(name, email)


@contact_registry.command("show-email", "<name>  — show emails")
@input_error
def show_email(args, service):
    if not args:
        raise ValueError("Usage: show-email <name>")
    name, *_ = args
    return service.show_email(name)