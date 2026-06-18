"""Wall-clock execution timeout via asyncio (PRD RF14, issue #32).

Camada 1 de timeout (PRD §4.1): limite de 10s wall-clock na sessao de execucao.
Camadas 2/3 permanecem em execution.py (kill loop) e Docker stop-timeout.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def _complete_future(future: asyncio.Future, loop: asyncio.AbstractEventLoop, result: T) -> None:
    if future.done() or loop.is_closed():
        return
    try:
        loop.call_soon_threadsafe(future.set_result, result)
    except RuntimeError:
        pass


def _fail_future(
    future: asyncio.Future, loop: asyncio.AbstractEventLoop, exc: BaseException
) -> None:
    if future.done() or loop.is_closed():
        return
    try:
        loop.call_soon_threadsafe(future.set_exception, exc)
    except RuntimeError:
        pass


async def run_with_wall_clock_timeout(
    fn: Callable[[], T],
    *,
    timeout_s: float,
    on_timeout: Callable[[], None] | None = None,
    cleanup_grace_s: float = 2.0,
) -> tuple[T | None, bool]:
    """Executa fn em thread daemon com limite wall-clock (asyncio.wait).

    Retorna ao caller quando o limite estoura, sem bloquear na thread de cleanup
    (PTY/container continua finalizando em background via stop/timeout interno).
    """
    loop = asyncio.get_running_loop()
    future: asyncio.Future[T] = loop.create_future()

    def worker() -> None:
        try:
            result = fn()
        except BaseException as exc:
            _fail_future(future, loop, exc)
            return
        _complete_future(future, loop, result)

    thread = threading.Thread(target=worker, daemon=True, name="exec-wall-clock")
    thread.start()

    done, _pending = await asyncio.wait({future}, timeout=timeout_s)
    if future in done:
        return future.result(), False

    if on_timeout is not None:
        on_timeout()

    done, _pending = await asyncio.wait({future}, timeout=cleanup_grace_s)
    if future in done:
        return future.result(), True
    return None, True
