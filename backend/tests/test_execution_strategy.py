"""Testes de PtyExecutionStrategy (issue #27)."""

from unittest.mock import MagicMock, patch

import pytest

from config import Config
from execution import (
    ExecutionResult,
    PtyExecutionStrategy,
    sandbox_run_kwargs,
    sandbox_staging_kwargs,
)


@pytest.fixture
def mock_docker_client():
    client = MagicMock()
    container = MagicMock()
    container.status = "running"
    container.wait.return_value = {"StatusCode": 0}

    attach = MagicMock()
    sock = MagicMock()
    sock.fileno.return_value = 1
    attach._sock = sock
    container.attach_socket.return_value = attach

    client.containers.create.return_value = container
    return client, container, attach, sock


def test_sandbox_run_kwargs_from_config():
    kwargs = sandbox_run_kwargs()
    assert kwargs["read_only"] is True
    assert kwargs["mem_limit"] == Config.sandbox_mem_limit()
    assert kwargs["pids_limit"] == Config.SANDBOX_PIDS_LIMIT
    assert kwargs["user"] == Config.SANDBOX_USER
    assert kwargs["stdin_open"] is True
    assert kwargs["tty"] is True
    assert kwargs["detach"] is True


def test_sandbox_staging_kwargs_allows_put_archive():
    kwargs = sandbox_staging_kwargs()
    assert kwargs["read_only"] is False


@patch("execution._build_dir_tar", return_value=b"")
@patch("execution.select.select")
def test_execute_spawns_runner_container(mock_select, _mock_tar, mock_docker_client):
    client, container, attach, sock = mock_docker_client
    mock_select.side_effect = [([sock], [], []), ([], [], [])]
    sock.recv.return_value = b"hello\n"
    container.reload.side_effect = lambda: setattr(container, "status", "exited")

    strategy = PtyExecutionStrategy(client=client)
    outputs: list[str] = []

    result = strategy.execute("/tmp/sim", outputs.append, lambda: None)

    client.containers.create.assert_called_once()
    call_kwargs = client.containers.create.call_args.kwargs
    assert call_kwargs["image"] == Config.SANDBOX_IMAGE
    assert call_kwargs["command"] == PtyExecutionStrategy.QEMU_COMMAND
    assert call_kwargs["read_only"] is False
    container.put_archive.assert_called_once()
    assert container.put_archive.call_args.args[0] == "/"
    container.start.assert_called_once()
    container.attach_socket.assert_called_once_with(
        params=PtyExecutionStrategy.ATTACH_PARAMS
    )

    assert outputs == ["hello\n"]
    assert isinstance(result, ExecutionResult)
    assert result.exit_code == 0
    assert result.timed_out is False
    container.remove.assert_called_once_with(force=True)
    attach.close.assert_called_once()


@patch("execution._build_dir_tar", return_value=b"")
@patch("execution.select.select", return_value=([], [], []))
def test_execute_forwards_stdin_to_attach_socket(_mock_select, _mock_tar, mock_docker_client):
    client, container, attach, sock = mock_docker_client
    sock.fileno.return_value = 1
    container.reload.side_effect = lambda: setattr(container, "status", "exited")
    messages = [{"type": "stdin", "data": "42\n"}]

    def poll():
        return messages.pop(0) if messages else None

    strategy = PtyExecutionStrategy(client=client)
    strategy.execute("/tmp/sim", lambda _data: None, poll)

    attach._sock.sendall.assert_called_once_with(b"42\n")


@patch("execution._build_dir_tar", return_value=b"")
@patch("execution.select.select", return_value=([], [], []))
def test_execute_stop_kills_container(_mock_select, _mock_tar, mock_docker_client):
    client, container, attach, sock = mock_docker_client
    sock.fileno.return_value = 1

    strategy = PtyExecutionStrategy(client=client)
    result = strategy.execute(
        "/tmp/sim",
        lambda _data: None,
        lambda: {"type": "stop"},
        timeout_s=5,
    )

    container.kill.assert_called_with(signal="SIGTERM")
    assert result.stopped is True
    container.remove.assert_called_once_with(force=True)


@patch("execution._build_dir_tar", return_value=b"")
@patch("execution.select.select", return_value=([], [], []))
@patch("execution.time.monotonic")
def test_execute_timeout_kills_container(mock_monotonic, _mock_select, _mock_tar, mock_docker_client):
    client, container, _attach, _sock = mock_docker_client
    mock_monotonic.side_effect = [0.0, 0.0, 11.0, 11.0, 12.0, 12.0]

    strategy = PtyExecutionStrategy(client=client)
    result = strategy.execute(
        "/tmp/sim",
        lambda _data: None,
        lambda: None,
        timeout_s=10,
    )

    assert result.timed_out is True
    assert container.kill.call_count >= 1
    container.remove.assert_called_once_with(force=True)
