from __future__ import annotations

import abc
import argparse
import dataclasses
import textwrap
from typing import Self


@dataclasses.dataclass(frozen=True, kw_only=True)
class CliCommand(abc.ABC):
    """Base class for CLI commands.

    Example usage:

    >>> @dataclasses.dataclass(frozen=True, kw_only=True)
    ... class MyCommand(CliCommand):
    ...     flag: bool
    ...     maybe_string: str | None
    ...     a_list: list[int]
    ...
    ...     @classmethod
    ...     def setup_parser(cls, parser: argparse.ArgumentParser) -> None:
    ...         super().setup_parser(parser)
    ...         parser.add_argument("--flag", action="store_true")
    ...         parser.add_argument("--maybe-string")
    ...         parser.add_argument("--a-list", type=int, nargs="*", default=[])
    ...
    ...     def run(self) -> None:
    ...         print("Got arguments:")
    ...         print(f"    {self.flag = }")
    ...         print(f"    {self.maybe_string = }")
    ...         print(f"    {self.a_list = }")

    >>> ap = argparse.ArgumentParser()
    >>> subcommands = ap.add_subparsers()
    >>> MyCommand.setup_parser(subcommands.add_parser("my-command"))

    >>> args = ap.parse_args(["my-command"])
    >>> assert args.__konfusion_cmd__ is MyCommand

    >>> args.__konfusion_cmd__.from_parsed_args(args).run()
    Got arguments:
        self.flag = False
        self.maybe_string = None
        self.a_list = []

    >>> args = ap.parse_args(
    ...     ["my-command", "--flag", "--maybe-string=foo", "--a-list", "1", "2"]
    ... )

    >>> args.__konfusion_cmd__.from_parsed_args(args).run()
    Got arguments:
        self.flag = True
        self.maybe_string = 'foo'
        self.a_list = [1, 2]
    """

    @classmethod
    def help(cls) -> str | None:
        """Return the help text for this command. Should be a short sentence.

        By default, returns the first line of the docstring.

        >>> CliCommand.help()
        'Base class for CLI commands.'

        >>> class NoHelp(CliCommand):
        ...     pass

        >>> assert NoHelp.help() is None
        """
        if cls.__doc__ and (doc := cls.__doc__.lstrip()):
            return doc.split("\n", maxsplit=1)[0]
        else:
            return None

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser) -> None:
        """Set up an argparse parser for this command.

        After the setup is done, the return value of parser.parse_args() must be a valid
        set of arguments to instantiate this command (using the 'from_parsed_args' method).

        Subclasses should override this method and call super().setup_parser(parser).
        See the class docstring for a complete example.
        """
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        if cls.__doc__:
            parser.description = _dedent_docstring(cls.__doc__)
        parser.set_defaults(__konfusion_cmd__=cls)

    @classmethod
    def from_parsed_args(cls, args: argparse.Namespace) -> Self:
        """Instantiate this command from a "Namespace" of parsed arguments."""
        known_args = {field.name for field in dataclasses.fields(cls)}
        kwargs = {k: v for k, v in vars(args).items() if k in known_args}
        return cls(**kwargs)

    @abc.abstractmethod
    def run(self) -> None:
        """Run this command."""


def _dedent_docstring(docstring: str) -> str:
    """Dedent a docstring that follows the style of <this docstring>.

    I.e. the docstring immediately starts with the first line, but the rest
    of the docstring is indented by a consistent amount.

    Example:

    >>> docstring = '''This is the first line.
    ...
    ...     This is a second, indented line.
    ...
    ...     A third line, indented consistently with the second
    ...
    ...         A fourth line, indented more deeply.
    ... '''

    >>> print(_dedent_docstring(docstring))
    This is the first line.
    <BLANKLINE>
    This is a second, indented line.
    <BLANKLINE>
    A third line, indented consistently with the second
    <BLANKLINE>
        A fourth line, indented more deeply.
    <BLANKLINE>

    >>> docstring2 = "Nothing to dedent."
    >>> assert _dedent_docstring(docstring2) == docstring2
    """
    first_line, maybe_newline, rest = docstring.partition("\n")
    return first_line + maybe_newline + textwrap.dedent(rest)
