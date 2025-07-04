from __future__ import annotations

import logging
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from konfusion.lib.tools._cli_tool import CliTool


def test_run() -> None:
    python_cli = CliTool(sys.executable)
    script_to_run = textwrap.dedent(
        r"""
        import sys

        # let's also check that we handle missing newlines correctly
        print("hello\nthere", end="")
        print("general\nkenobi", end="", file=sys.stderr)
        """
    )

    proc = python_cli.run(["-c", script_to_run])
    assert proc.returncode == 0
    assert proc.stdout == "hello\nthere"
    assert proc.stderr == "general\nkenobi"


def test_run_a_failing_process() -> None:
    python_cli = CliTool(sys.executable)
    script_to_run = "import sys; sys.exit('goodbye world')"

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        python_cli.run(["-c", script_to_run])

    e = exc_info.value
    assert e.returncode == 1
    assert e.stdout == ""
    assert e.stderr == "goodbye world\n"


def test_run_a_failing_process_with_check_false() -> None:
    python_cli = CliTool(sys.executable)
    script_to_run = "import sys; sys.exit('goodbye world')"

    proc = python_cli.run(["-c", script_to_run], check=False)
    assert proc.returncode == 1
    assert proc.stdout == ""
    assert proc.stderr == "goodbye world\n"


def test_run_with_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Test that run_with_logging captures output and logs it in real time."""
    python_cli = CliTool(sys.executable)
    script_to_run = textwrap.dedent(
        """
        import sys
        import time

        print("stdout line #1", flush=True)
        # add a tiny delay to make sure CliTool receives the lines in the expected order
        time.sleep(0.001)
        print("stderr line #1", flush=True, file=sys.stderr)
        time.sleep(0.001)
        print("stdout line #2", flush=True)
        """
    )

    caplog.set_level(logging.INFO)

    proc = python_cli.run_with_logging(
        ["-c", script_to_run],
        stdout_at_level=logging.INFO,
        stderr_at_level=logging.WARNING,
    )
    assert proc.returncode == 0
    assert proc.stdout == "stdout line #1\nstdout line #2\n"
    assert proc.stderr == "stderr line #1\n"

    python_name = Path(sys.executable).name
    log_records = [(record.levelname, record.message) for record in caplog.records]
    assert log_records == [
        ("INFO", f"{python_name} stdout> stdout line #1"),
        ("WARNING", f"{python_name} stderr> stderr line #1"),
        ("INFO", f"{python_name} stdout> stdout line #2"),
    ]
