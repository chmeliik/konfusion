from __future__ import annotations

import argparse
import importlib.metadata
from types import ModuleType
from typing import Any, TypeGuard

from konfusion.cli import CliCommand
from konfusion.cmd.apply_tags import ApplyTags


def load_commands() -> dict[str, type[CliCommand]]:
    """Load CLI commands from packages that provide 'konfusion.commands' entrypoints."""
    entrypoints = importlib.metadata.entry_points(group="konfusion.commands")

    def is_cli_command(obj: Any) -> TypeGuard[type[CliCommand]]:  # noqa: ANN401
        return (
            isinstance(obj, type)
            and issubclass(obj, CliCommand)
            and obj is not CliCommand
        )

    def get_command(
        entrypoint: importlib.metadata.EntryPoint,
    ) -> type[CliCommand] | None:
        try:
            obj = entrypoint.load()
        except ImportError:
            return None

        if is_cli_command(obj):
            return obj
        elif isinstance(obj, ModuleType):
            commands = [attr for attr in vars(obj).values() if is_cli_command(attr)]
            if len(commands) == 1:
                return commands[0]

        # TODO: log unsuccessful cmd loading
        return None

    return {
        entrypoint.name: cmd
        for entrypoint in entrypoints
        if (cmd := get_command(entrypoint)) is not None
    }


def get_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(title="subcommands", required=True)

    def add_subcommand(name: str, cmd: type[CliCommand]) -> None:
        cmd.setup_parser(subcommands.add_parser(name, help=cmd.help()))

    add_subcommand("apply-tags", ApplyTags)

    for name, cmd_type in load_commands().items():
        add_subcommand(name, cmd_type)

    return parser


def main() -> None:
    """Run Konfusion."""
    parser = get_parser()
    args = parser.parse_args()

    cmd_type: type[CliCommand] = args.cmd
    cmd = cmd_type.from_parsed_args(args)
    cmd.run()
