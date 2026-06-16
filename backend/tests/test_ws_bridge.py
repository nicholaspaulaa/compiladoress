"""Testes do bridge PTY <-> WebSocket (issue #28)."""

from unittest.mock import MagicMock

import pytest

from execution import ExecutionResult
from ws_bridge import WsPtyBridge, start_pty_bridge


@pytest.fixture
def mock_strategy():
    strategy = MagicMock()
    strategy.execute.return_value = ExecutionResult(
        exit_code=0,
        duration_ms=100,
        timed_out=False,
    )
    return strategy


def test_run_emits_exec_started_stdout_and_exit(mock_strategy):
    sent: list[dict] = []

    def fake_execute(_binary_dir, on_stdout, _poll_message, timeout_s=None):
        on_stdout("hello\n")
        return ExecutionResult(exit_code=0, duration_ms=50, timed_out=False)

    mock_strategy.execute.side_effect = fake_execute

    bridge = WsPtyBridge(sent.append, strategy=mock_strategy)
    result = bridge.run("/tmp/sim")

    assert result.exit_code == 0
    assert [msg["type"] for msg in sent] == ["exec_started", "stdout", "exit"]
    assert sent[1]["data"] == "hello\n"
    assert sent[2]["code"] == 0
    assert sent[2]["duration_ms"] == 50
    mock_strategy.execute.assert_called_once()


def test_enqueue_forwards_stdin_to_strategy(mock_strategy):
    captured_poll = []

    def fake_execute(_binary_dir, _on_stdout, poll_message, timeout_s=None):
        while True:
            msg = poll_message()
            captured_poll.append(msg)
            if msg and msg.get("type") == "stop":
                return ExecutionResult(exit_code=0, duration_ms=10, timed_out=False, stopped=True)
            if len(captured_poll) >= 3:
                return ExecutionResult(exit_code=0, duration_ms=10, timed_out=False)

    mock_strategy.execute.side_effect = fake_execute

    bridge = WsPtyBridge(lambda _payload: None, strategy=mock_strategy)
    thread = __import__("threading").Thread(target=bridge.run, args=("/tmp/sim",))
    thread.start()

    import time

    deadline = time.monotonic() + 2
    while not bridge.active and time.monotonic() < deadline:
        time.sleep(0.01)

    bridge.enqueue({"type": "stdin", "data": "42\n"})
    bridge.enqueue({"type": "stop"})
    thread.join(timeout=3)

    assert {"type": "stdin", "data": "42\n"} in captured_poll
    assert {"type": "stop"} in captured_poll


def test_enqueue_ignored_when_idle(mock_strategy):
    bridge = WsPtyBridge(lambda _payload: None, strategy=mock_strategy)
    bridge.enqueue({"type": "stdin", "data": "x"})
    mock_strategy.execute.assert_not_called()


def test_run_timeout_emits_timeout_message(mock_strategy):
    sent: list[dict] = []
    mock_strategy.execute.return_value = ExecutionResult(
        exit_code=137,
        duration_ms=10000,
        timed_out=True,
    )

    bridge = WsPtyBridge(sent.append, strategy=mock_strategy)
    bridge.run("/tmp/sim", timeout_s=10)

    assert sent[-1] == {"type": "timeout", "limit_s": 10}


def test_run_internal_error_on_strategy_failure(mock_strategy):
    sent: list[dict] = []
    mock_strategy.execute.side_effect = RuntimeError("docker down")

    bridge = WsPtyBridge(sent.append, strategy=mock_strategy)
    with pytest.raises(RuntimeError, match="docker down"):
        bridge.run("/tmp/sim")

    assert sent[0]["type"] == "exec_started"
    assert sent[1]["type"] == "internal_error"
    assert "docker down" in sent[1]["message"]


def test_start_pty_bridge_runs_in_background(mock_strategy):
    sent: list[dict] = []
    bridge, thread = start_pty_bridge(sent.append, "/tmp/sim", strategy=mock_strategy)
    thread.join(timeout=3)

    assert not bridge.active
    assert sent[0]["type"] == "exec_started"
    assert sent[-1]["type"] == "exit"
    mock_strategy.execute.assert_called_once()
