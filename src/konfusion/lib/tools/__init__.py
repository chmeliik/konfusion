from __future__ import annotations

import logging
import shutil
import subprocess
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from collections.abc import Sequence
    from os import PathLike

log = logging.getLogger(__name__)


class CliTool:
    """Wrapper for calling CLI tools in a subprocess.

    Essentially an opinionated way to call subprocess.run().
    """

    def __init__(self, executable_path: str | PathLike[str]) -> None:
        self._executable_path = executable_path

    @classmethod
    def find_by_name(cls, name: str) -> Self:
        """Find an executable in PATH and return a CliTool."""
        executable_path = shutil.which(name)
        if not executable_path:
            raise ValueError(f"Executable {name!r} not found in PATH")
        return cls(executable_path)

    def run(self, args: Sequence[str | PathLike[str]]) -> None:
        """Run a command without capturing stdout or stderr.

        Best used for commands that take longer and/or print progress messages.
        """
        cmd = [self._executable_path, *args]
        log.debug("Running %s", cmd)
        subprocess.run(cmd, check=True)  # noqa: S603

    def get_output(self, args: Sequence[str | PathLike[str]]) -> str:
        """Run a command while capturing both stdout and stderr, return stdout.

        Best used when you need the stdout of a quick command.
        """
        cmd = [self._executable_path, *args]
        log.debug("Running %s", cmd)
        proc = subprocess.run(  # noqa: S603
            cmd, check=True, capture_output=True, text=True
        )
        return proc.stdout
