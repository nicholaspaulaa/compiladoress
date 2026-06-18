"""Testes do protocolo WebSocket /ws/run (issue #30)."""

from unittest.mock import MagicMock, patch

from ws_protocol import WsRunSession, WsState, validate_compile_and_run, validate_stdin


def test_validate_compile_and_run_ok():
    code, error = validate_compile_and_run({"type": "compile_and_run", "code": "programa p\ninicio\nfim\n"})
    assert error is None
    assert code.startswith("programa")


def test_validate_compile_and_run_empty():
    code, error = validate_compile_and_run({"type": "compile_and_run", "code": "   "})
    assert code is None
    assert error is not None


def test_validate_stdin_ok():
    data, error = validate_stdin({"type": "stdin", "data": "42\n"})
    assert error is None
    assert data == "42\n"


def test_validate_stdin_invalid():
    data, error = validate_stdin({"type": "stdin", "data": 42})
    assert data is None
    assert error is not None


@patch("ws_protocol.start_pty_bridge")
@patch("ws_protocol.build_binary")
def test_compile_and_run_happy_path(mock_build, mock_start_bridge):
    sent: list[dict] = []
    mock_build.return_value = {
        "success": True,
        "asm": "section .text",
        "work_dir": "/tmp/sim-test",
    }
    bridge = MagicMock()
    bridge.active = True
    mock_start_bridge.return_value = (bridge, MagicMock())

    session = WsRunSession("user-1", sent.append)
    session.handle_message(
        {"type": "compile_and_run", "code": "programa p\ninicio\nfim\n"}
    )

    assert session.state == WsState.EXECUTING
    assert [msg["type"] for msg in sent[:2]] == ["compile_started", "asm_generated"]
    mock_start_bridge.assert_called_once()


@patch("ws_protocol.build_binary")
def test_compile_and_run_compile_error(mock_build):
    sent: list[dict] = []
    mock_build.return_value = {
        "success": False,
        "errors": [{"phase": "parser", "line": 1, "column": 1, "message": "erro"}],
    }

    session = WsRunSession("user-1", sent.append)
    session.handle_message(
        {"type": "compile_and_run", "code": "programa p\ninicio\nfim\n"}
    )

    assert session.state == WsState.IDLE
    assert sent[0]["type"] == "compile_started"
    assert sent[1]["type"] == "compile_error"
    assert sent[1]["phase"] == "parser"


@patch("ws_protocol.start_pty_bridge")
@patch("ws_protocol.build_binary")
def test_compile_and_run_ignored_while_executing(mock_build, mock_start_bridge):
    sent: list[dict] = []
    mock_build.return_value = {"success": True, "asm": "x", "work_dir": "/tmp/x"}
    bridge = MagicMock()
    bridge.active = True
    mock_start_bridge.return_value = (bridge, MagicMock())

    session = WsRunSession("user-1", sent.append)
    session.handle_message({"type": "compile_and_run", "code": "programa p\ninicio\nfim\n"})
    session.handle_message({"type": "compile_and_run", "code": "programa q\ninicio\nfim\n"})

    assert mock_build.call_count == 1


def test_stdin_ignored_in_idle():
    bridge = MagicMock()
    session = WsRunSession("user-1", lambda _msg: None)
    session.bridge = bridge
    session.state = WsState.IDLE
    session.handle_message({"type": "stdin", "data": "1\n"})
    bridge.enqueue.assert_not_called()


@patch("ws_protocol.start_pty_bridge")
@patch("ws_protocol.build_binary")
def test_stdin_forwarded_during_exec(mock_build, mock_start_bridge):
    mock_build.return_value = {"success": True, "asm": "x", "work_dir": "/tmp/x"}
    bridge = MagicMock()
    bridge.active = True
    mock_start_bridge.return_value = (bridge, MagicMock())

    session = WsRunSession("user-1", lambda _msg: None)
    session.handle_message({"type": "compile_and_run", "code": "programa p\ninicio\nfim\n"})
    session.handle_message({"type": "stdin", "data": "42\n"})

    bridge.enqueue.assert_called_once_with({"type": "stdin", "data": "42\n"})


@patch("ws_protocol.cleanup_work_dir")
def test_poll_exec_finished_returns_to_idle(mock_cleanup):
    thread = MagicMock()
    thread.is_alive.return_value = False

    session = WsRunSession("user-1", lambda _msg: None)
    session.state = WsState.EXECUTING
    session.work_dir = "/tmp/sim"
    session.exec_thread = thread
    session.poll_exec_finished()

    assert session.state == WsState.IDLE
    mock_cleanup.assert_called_once_with("/tmp/sim")


def test_ping_returns_pong():
    sent: list[dict] = []
    session = WsRunSession("user-1", sent.append)
    session.handle_message({"type": "ping"})
    assert sent == [{"type": "pong"}]


def test_validate_compile_and_run_oversized():
    from config import Config

    huge = "x" * (Config.max_code_bytes() + 1)
    code, error = validate_compile_and_run({"type": "compile_and_run", "code": huge})
    assert code is None
    assert "limite" in error


@patch("ws_protocol.start_pty_bridge")
@patch("ws_protocol.build_binary")
def test_stop_forwarded_during_exec(mock_build, mock_start_bridge):
    mock_build.return_value = {"success": True, "asm": "x", "work_dir": "/tmp/x"}
    bridge = MagicMock()
    bridge.active = True
    mock_start_bridge.return_value = (bridge, MagicMock())

    session = WsRunSession("user-1", lambda _msg: None)
    session.handle_message({"type": "compile_and_run", "code": "programa p\ninicio\nfim\n"})
    session.handle_message({"type": "stop"})

    bridge.enqueue.assert_called_with({"type": "stop"})


def test_stop_ignored_in_idle():
    session = WsRunSession("user-1", lambda _msg: None)
    session.handle_message({"type": "stop"})
    assert session.state == WsState.IDLE


def test_unknown_message_type_is_ignored():
    sent: list[dict] = []
    session = WsRunSession("user-1", sent.append)
    session.handle_message({"type": "not_supported"})
    assert sent == []


@patch("ws_protocol.check_execution_rate_limit", return_value=False)
def test_rate_limited_compile_and_run(_mock_limit):
    sent: list[dict] = []
    session = WsRunSession("user-1", sent.append)
    session.handle_message({"type": "compile_and_run", "code": "programa p\ninicio\nfim\n"})
    assert sent[0]["type"] == "rate_limited"


@patch("ws_protocol.start_pty_bridge", side_effect=RuntimeError("docker down"))
@patch("ws_protocol.build_binary")
@patch("ws_protocol.cleanup_work_dir")
def test_exec_start_failure_returns_internal_error(mock_cleanup, mock_build, _mock_start):
    sent: list[dict] = []
    mock_build.return_value = {"success": True, "asm": "x", "work_dir": "/tmp/sim"}

    session = WsRunSession("user-1", sent.append)
    session.handle_message({"type": "compile_and_run", "code": "programa p\ninicio\nfim\n"})

    assert session.state == WsState.IDLE
    assert sent[-1]["type"] == "internal_error"
    assert "docker down" in sent[-1]["message"]
    mock_cleanup.assert_called_once_with("/tmp/sim")


@patch("ws_protocol.cleanup_work_dir")
def test_cleanup_shuts_down_active_bridge(mock_cleanup):
    bridge = MagicMock()
    bridge.active = True
    thread = MagicMock()
    thread.is_alive.return_value = False

    session = WsRunSession("user-1", lambda _msg: None)
    session.bridge = bridge
    session.exec_thread = thread
    session.work_dir = "/tmp/sim"
    session.cleanup()

    bridge.shutdown.assert_called_once()
    mock_cleanup.assert_called_once_with("/tmp/sim")
    assert session.bridge is None


@patch("ws_protocol.build_binary")
def test_emit_build_failure_fallback_without_errors(mock_build):
    sent: list[dict] = []
    mock_build.return_value = {"success": False, "stderr": "linker failed"}

    session = WsRunSession("user-1", sent.append)
    session.handle_message({"type": "compile_and_run", "code": "programa p\ninicio\nfim\n"})

    assert sent[-1]["type"] == "internal_error"
    assert sent[-1]["message"] == "linker failed"
