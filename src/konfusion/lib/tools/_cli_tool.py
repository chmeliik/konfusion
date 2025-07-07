from __future__ import annotations

import logging
import shutil
import subprocess
import threading
from pathlib import Path
from typing import IO, TYPE_CHECKING, Self

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from os import PathLike

log = logging.getLogger(__name__)


class CliTool:
    """Wrapper for calling CLI tools in a subprocess."""

    def __init__(self, executable_path: str | PathLike[str]) -> None:
        self._executable_path = executable_path

    @classmethod
    def find_by_name(cls, name: str) -> Self:
        """Find an executable in PATH and return a CliTool."""
        executable_path = shutil.which(name)
        if not executable_path:
            raise ValueError(f"Executable {name!r} not found in PATH")
        return cls(executable_path)

    def run(
        self,
        args: Sequence[str | PathLike[str]],
        *,
        check: bool = True,
        stdout_callback: Callable[[str], None] | None = None,
        stderr_callback: Callable[[str], None] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run a command while capturing the stdout and stderr.

        By default, behaves the same as
        subprocess.run(..., check=True, capture_output=True, text=True)

        Unlike subprocess.run, allows passing callbacks to react on stdout and stderr
        lines in real time. The callbacks, if specified, should be functions that
        take a line as input (includes the trailing newline) and perform some side effect
        (e.g. logging the line).
        """
        cmd = [self._executable_path, *args]
        log.debug("Running %s", cmd)

        process = subprocess.Popen(  # noqa: S603
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout_pipe = _cannot_be_none(process.stdout)
        stderr_pipe = _cannot_be_none(process.stderr)

        stdout_handler = _PipeHandler(stdout_pipe, stdout_callback)
        stderr_handler = _PipeHandler(stderr_pipe, stderr_callback)

        # Thread-based approach, inspired by:
        #   * a suggestion from Gemini
        #   * the CPython stdlib: https://github.com/python/cpython/blob/cb99d992774b67761441e122965ed056bac09241/Lib/subprocess.py#L1617
        _run_handlers([stdout_handler, stderr_handler])

        returncode = process.wait()
        completed_process = subprocess.CompletedProcess(
            cmd, returncode, stdout_handler.output, stderr_handler.output
        )

        if check:
            completed_process.check_returncode()

        return completed_process

    def run_with_logging(
        self,
        args: Sequence[str | PathLike[str]],
        *,
        check: bool = True,
        stdout_at_level: int | None = logging.DEBUG,
        stderr_at_level: int | None = logging.ERROR,
    ) -> subprocess.CompletedProcess[str]:
        """Same as run() but special-cased for the common use case of log+collect.

        Logs each line of stdout and stderr in real time while also collecting them
        for later use.

        To disable the logging for stdout or stderr, set <stdout|stderr>_at_level=None.
        """
        tool_name = Path(self._executable_path).name
        stdout_format = f"{tool_name} stdout> %s"
        stderr_format = f"{tool_name} stderr> %s"

        def log_line(level: int | None, log_format: str, line: str) -> None:
            if level is not None:
                log.log(level, log_format, line.rstrip("\n"))

        return self.run(
            args,
            check=check,
            stdout_callback=lambda line: log_line(stdout_at_level, stdout_format, line),
            stderr_callback=lambda line: log_line(stderr_at_level, stderr_format, line),
        )


def _cannot_be_none[T](obj: T | None) -> T:
    """Assert that obj is not None (mainly for typecheckers).

    For cases where the subprocess module type hints are not good enough.
    """
    if obj is None:
        raise AssertionError("against all odds, object was None")
    return obj


class _PipeHandler:
    def __init__(
        self, pipe: IO[str], line_callback: Callable[[str], None] | None = None
    ) -> None:
        self._pipe = pipe
        self._lines: list[str] = []
        self._line_callback = line_callback

    def run(self) -> None:
        with self._pipe:
            for line in self._pipe:
                self.handle(line)

    def handle(self, line: str) -> None:
        self._lines.append(line)
        if self._line_callback:
            self._line_callback(line)

    @property
    def output(self) -> str:
        return "".join(self._lines)


def _run_handlers(handlers: Iterable[_PipeHandler]) -> None:
    threads = [threading.Thread(target=handler.run) for handler in handlers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
