from __future__ import annotations

import argparse
import importlib.metadata
import io
import logging
import sys
from types import ModuleType
from typing import Any, TypeGuard

from konfusion.cli import CliCommand
from konfusion.logs import setup_logging

log = logging.getLogger(__name__)


def load_commands() -> dict[str, type[CliCommand]]:
    """Load CLI commands from packages that provide 'konfusion.commands' entrypoints."""

    def is_cli_command(obj: Any) -> TypeGuard[type[CliCommand]]:  # noqa: ANN401
        return (
            isinstance(obj, type)
            and issubclass(obj, CliCommand)
            and obj is not CliCommand
        )

    def get_command(entrypoint: importlib.metadata.EntryPoint) -> type[CliCommand]:
        obj = entrypoint.load()

        if is_cli_command(obj):
            return obj
        elif isinstance(obj, ModuleType):
            commands = [attr for attr in vars(obj).values() if is_cli_command(attr)]
            if len(commands) == 1:
                return commands[0]
            else:
                msg = f"Expected to find 1 CliCommand subclass, found {len(commands)}"
                raise ValueError(msg)
        else:
            raise ValueError(f"Unsupported object type: {obj!r}")

    commands: dict[str, type[CliCommand]] = {}
    for entrypoint in importlib.metadata.entry_points(group="konfusion.commands"):
        try:
            commands[entrypoint.name] = get_command(entrypoint)
        except Exception as e:
            log.warning(
                "Failed to load command %s from %s: %r",
                entrypoint.name,
                entrypoint.value,
                e,
            )

    return commands


def version_str(loaded_commands: dict[str, type[CliCommand]]) -> str:
    f = io.StringIO()
    print("konfusion", importlib.metadata.version("konfusion"), file=f)
    print("\nsubcommands:", file=f)

    if loaded_commands:
        for cmd_name, cmd_type in loaded_commands.items():
            module, _, _ = cmd_type.__module__.partition(".")
            version = importlib.metadata.version(module)
            print(f"  {cmd_name} ({module} {version})", file=f)
    else:
        print("  <none loaded>", file=f)

    return f.getvalue()


def get_parser(loaded_commands: dict[str, type[CliCommand]]) -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser()
    parser.formatter_class = argparse.RawDescriptionHelpFormatter

    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
    )
    parser.add_argument(
        "--version", action="version", version=version_str(loaded_commands)
    )

    def add_subcommand(name: str, cmd: type[CliCommand]) -> None:
        cmd.setup_parser(subcommands.add_parser(name, help=cmd.help()))

    if loaded_commands:
        subcommands = parser.add_subparsers(title="subcommands", required=True)
        for name, cmd_type in loaded_commands.items():
            add_subcommand(name, cmd_type)

    return parser


def main() -> None:
    """Run Konfusion."""
    # Setup logging first so that we can log messages when we fail to load a command
    setup_logging(logging.INFO, ["konfusion"])
    loaded_commands = load_commands()

    parser = get_parser(loaded_commands)
    args = parser.parse_args()

    if not loaded_commands:
        sys.exit("No subcommands loaded")

    # Re-setup logging for konfusion and all loaded modules after parsing args
    setup_logging(
        args.log_level,
        ["konfusion", *(cmd.__module__ for cmd in loaded_commands.values())],
    )

    cmd_type: type[CliCommand] = args.__konfusion_cmd__
    cmd = cmd_type.from_parsed_args(args)
    cmd.run()
