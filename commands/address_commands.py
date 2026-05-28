from commands.registry import contact_registry
from helpers.error_handler import input_error


@contact_registry.command("add-address", "<name> <address>  — add address", modifies_data=True)
@input_error
def add_address(args, service):
    if len(args) < 2:
        raise ValueError("Usage: add-address <name> <address>")
    name, *addr_parts = args
    return service.add_address(name, " ".join(addr_parts))


@contact_registry.command("change-address", "<name> <old_address> <new_address>  — update address", modifies_data=True)
@input_error
def change_address(args, service):
    if len(args) < 3:
        raise ValueError("Usage: change-address <name> <old_address> <new_address>")
    name, old, new, *_ = args
    return service.change_address(name, old, new)


@contact_registry.command("remove-address", "<name> <address>  — remove address", modifies_data=True)
@input_error
def remove_address(args, service):
    if len(args) < 2:
        raise ValueError("Usage: remove-address <name> <address>")
    name, *addr_parts = args
    return service.remove_address(name, " ".join(addr_parts))


@contact_registry.command("show-address", "<name>  — show addresses")
@input_error
def show_address(args, service):
    if not args:
        raise ValueError("Usage: show-address <name>")
    name, *_ = args
    return service.show_address(name)