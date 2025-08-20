from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import stamina

if TYPE_CHECKING:
    import datetime as dt

type ExcOrPredicate = (
    type[Exception] | tuple[type[Exception], ...] | Callable[[Exception], bool]
)


def retry[**P, T](
    *,
    on: ExcOrPredicate,
    attempts: int | None = 10,
    timeout: float | dt.timedelta | None = None,
    wait_initial: float | dt.timedelta = 1.0,
    wait_max: float | dt.timedelta = 120.0,
    wait_jitter: float | dt.timedelta = 1.0,
    wait_exp_base: float = 2.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Wrapper around stamina.retry with different defaults.

    | stamina.retry    | this retry       |
    |------------------|------------------|
    | timeout=45.0     | timeout=None     |
    | wait_initial=0.1 | wait_initial=1.0 |
    | wait_max=5.0     | wait_max=120.0   |

    The stamina.retry defaults seem geared more towards a high-throughput service
    where we would still want operations to finish reasonably fast. Our use case
    is retrying operations in long-running CI pipelines, where we don't care as
    much about waiting a long time as long as we can avoid the whole pipeline failing.

    By default, the retry sequence will be (ignoring jitter):

        [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 120.0, 120.0]
        sum(above) = 367.0 = 6m7s
    """
    return stamina.retry(
        on=on,
        attempts=attempts,
        timeout=timeout,
        wait_initial=wait_initial,
        wait_max=wait_max,
        wait_jitter=wait_jitter,
        wait_exp_base=wait_exp_base,
    )
