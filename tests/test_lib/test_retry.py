from __future__ import annotations

import time

import pytest

from konfusion.lib.retry import retry


@pytest.fixture(scope="function", autouse=True)
def disable_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_sleep(_: float) -> None:
        pass

    monkeypatch.setattr(time, "sleep", no_sleep)


def test_retry_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Test that functions decorated with @retry log useful messages."""

    @retry(on=ValueError, wait_jitter=0.0)
    def always_fail() -> None:
        raise ValueError("oh no")

    with pytest.raises(ValueError):
        always_fail()

    expected_messages = [
        "test_retry.test_retry_logging.<locals>.always_fail: attempt 1 failed, retrying in 1.000000 seconds: ValueError: oh no",
        "test_retry.test_retry_logging.<locals>.always_fail: attempt 2 failed, retrying in 2.000000 seconds: ValueError: oh no",
        "test_retry.test_retry_logging.<locals>.always_fail: attempt 3 failed, retrying in 4.000000 seconds: ValueError: oh no",
        "test_retry.test_retry_logging.<locals>.always_fail: attempt 4 failed, retrying in 8.000000 seconds: ValueError: oh no",
        "test_retry.test_retry_logging.<locals>.always_fail: attempt 5 failed, retrying in 16.000000 seconds: ValueError: oh no",
        "test_retry.test_retry_logging.<locals>.always_fail: attempt 6 failed, retrying in 32.000000 seconds: ValueError: oh no",
        "test_retry.test_retry_logging.<locals>.always_fail: attempt 7 failed, retrying in 64.000000 seconds: ValueError: oh no",
        "test_retry.test_retry_logging.<locals>.always_fail: attempt 8 failed, retrying in 120.000000 seconds: ValueError: oh no",
        "test_retry.test_retry_logging.<locals>.always_fail: attempt 9 failed, retrying in 120.000000 seconds: ValueError: oh no",
    ]
    assert caplog.messages == expected_messages
