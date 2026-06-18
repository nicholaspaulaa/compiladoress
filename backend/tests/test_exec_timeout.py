"""Testes de timeout wall-clock com asyncio (issue #32)."""

import asyncio
import time

from exec_timeout import run_with_wall_clock_timeout


def test_run_with_wall_clock_timeout_completes_within_limit():
    async def run():
        return await run_with_wall_clock_timeout(lambda: 42, timeout_s=1.0)

    result, timed_out = asyncio.run(run())
    assert result == 42
    assert timed_out is False


def test_run_with_wall_clock_timeout_fires_on_slow_fn():
    calls: list[str] = []

    def slow():
        time.sleep(0.3)
        return "late"

    async def run():
        return await run_with_wall_clock_timeout(
            slow,
            timeout_s=0.05,
            on_timeout=lambda: calls.append("timeout"),
            cleanup_grace_s=0.5,
        )

    result, timed_out = asyncio.run(run())
    assert timed_out is True
    assert calls == ["timeout"]
    assert result == "late"


def test_run_with_wall_clock_timeout_returns_none_when_stuck():
    def stuck():
        time.sleep(2.0)
        return "never"

    async def run():
        return await run_with_wall_clock_timeout(
            stuck,
            timeout_s=0.05,
            cleanup_grace_s=0.05,
        )

    result, timed_out = asyncio.run(run())
    assert timed_out is True
    assert result is None


def test_run_with_wall_clock_timeout_interrupted_within_11s():
    """DoD Sprint 5: sessao lenta interrompida em <=11s (wall-clock)."""

    def hangs_past_limit():
        time.sleep(10.5)
        return "late"

    async def run():
        return await run_with_wall_clock_timeout(
            hangs_past_limit,
            timeout_s=10.0,
            cleanup_grace_s=0.2,
        )

    started = time.monotonic()
    _, timed_out = asyncio.run(run())
    elapsed = time.monotonic() - started

    assert timed_out is True
    assert elapsed <= 11.0
