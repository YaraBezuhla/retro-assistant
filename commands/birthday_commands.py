from commands.registry import contact_registry
from helpers.error_handler import input_error


@contact_registry.command("add-birthday", "<name> <DD.MM.YYYY>  — set birthday",
                          modifies_data=True)
@input_error
def add_birthday(args, service):
    if len(args) < 2:
        raise ValueError("Usage: add-birthday <name> <DD.MM.YYYY>")
    name, birthday, *_ = args
    return service.add_birthday(name, birthday)


@contact_registry.command("show-birthday", "<name>  — show birthday")
@input_error
def show_birthday(args, service):
    if not args:
        raise ValueError("Usage: show-birthday <name>")
    name, *_ = args
    return service.show_birthday(name)


@contact_registry.command("birthdays", "<days>  — upcoming birthdays")
@input_error
def show_upcoming_birthdays(args, service):
    if not args:
        raise ValueError("Usage: birthdays <days>")
    days = int(args[0])
    if days <= 0:
        raise ValueError("Number of days must be positive.")
    upcoming = service.get_upcoming_birthdays(days)
    if not upcoming:
        return "No upcoming birthdays yet."
    lines = [f"  {u['name']}: {u['birthday']}" for u in upcoming]
    return "Upcoming birthdays:\n" + "\n".join(lines)