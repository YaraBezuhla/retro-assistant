from dataclasses import dataclass
from typing import Callable, Iterator


@dataclass
class CommandDef:
    name: str
    description: str
    handler: Callable
    modifies_data: bool = False


class CommandRegistry:
    def __init__(self):
        self._commands: dict[str, CommandDef] = {}

    def command(self, name: str, description: str, modifies_data: bool = False):
        def decorator(func: Callable) -> Callable:
            self._commands[name] = CommandDef(
                name=name,
                description=description,
                handler=func,
                modifies_data=modifies_data,
            )
            return func
        return decorator

    def get(self, name: str) -> CommandDef | None:
        return self._commands.get(name)

    def execute(self, name: str, args: list[str], service) -> str:
        cmd = self._commands.get(name)
        if cmd is None:
            return f"Unknown command '{name}'. Type 'help'."
        return cmd.handler(args, service)

    def commands(self) -> Iterator[CommandDef]:
        return iter(self._commands.values())

    def help_text(self, title: str = "Commands:") -> str:
        lines = [f"[bold]{title}[/bold]"]
        for cmd in self.commands():
            lines.append(f"  [cyan]{cmd.name:<22}[/cyan] {cmd.description}")
        return "\n".join(lines)


contact_registry = CommandRegistry()
note_registry = CommandRegistry()
