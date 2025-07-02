from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from konfusion.cmd.apply_tags import ApplyTags

if TYPE_CHECKING:
    from konfusion.cli import CliCommand


def get_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(title="subcommands", required=True)

    def add_subcommand(name: str, cmd: type[CliCommand]) -> None:
        cmd.setup_parser(subcommands.add_parser(name, help=cmd.help()))

    add_subcommand("apply-tags", ApplyTags)
    return parser


def main() -> None:
    """Run Konfusion."""
    parser = get_parser()
    args = parser.parse_args()

    cmd_type: type[CliCommand] = args.cmd
    cmd = cmd_type.from_parsed_args(args)
    cmd.run()
