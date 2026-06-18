"""Testes do handler WebSocket /ws/run (issue #41)."""

import json
from unittest.mock import MagicMock, patch

from simple_websocket import ConnectionClosed

from config import Config
from ws_auth import WS_CLOSE_POLICY
from ws_run import begin_pty_execution, handle_ws_run_connection


def _configure_auth(monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(Config, "SUPABASE_JWT_SECRET", "test-secret")


@patch("ws_run.authenticate_ws_token")
def test_ws_run_rejects_unauthenticated(mock_auth, app):
    mock_auth.return_value = (None, "Token ausente")
    ws = MagicMock()
    ws.connected = True

    with app.test_request_context("/ws/run"):
        handle_ws_run_connection(ws)

    ws.close.assert_called_once_with(WS_CLOSE_POLICY, "Token ausente")
    assert ws.send.called


@patch("ws_run.WsRunSession")
@patch("ws_run.authenticate_ws_token")
def test_ws_run_authenticated_session_lifecycle(mock_auth, mock_session_cls, app, monkeypatch):
    _configure_auth(monkeypatch)
    mock_auth.return_value = ({"sub": "user-1", "email": "a@b.com"}, None)
    session = MagicMock()
    mock_session_cls.return_value = session

    ws = MagicMock()
    ws.connected = True

    def receive_side(_timeout=None, **_kwargs):
        if receive_side.calls == 0:
            receive_side.calls += 1
            return json.dumps({"type": "ping"})
        ws.connected = False
        return None

    receive_side.calls = 0
    ws.receive.side_effect = receive_side

    with app.test_request_context("/ws/run?token=abc"):
        handle_ws_run_connection(ws)

    session.handle_message.assert_called_once()
    session.cleanup.assert_called_once()


@patch("ws_run.WsRunSession")
@patch("ws_run.authenticate_ws_token")
def test_ws_run_ignores_invalid_json(mock_auth, mock_session_cls, app, monkeypatch):
    _configure_auth(monkeypatch)
    mock_auth.return_value = ({"sub": "user-1"}, None)
    session = MagicMock()
    mock_session_cls.return_value = session

    ws = MagicMock()
    ws.connected = True
    ws.receive.side_effect = ["not-json", ConnectionClosed()]

    with app.test_request_context("/ws/run?token=abc"):
        handle_ws_run_connection(ws)

    session.handle_message.assert_not_called()
    session.cleanup.assert_called_once()


@patch("ws_run.WsRunSession")
@patch("ws_run.authenticate_ws_token")
def test_ws_run_ignores_non_object_json(mock_auth, mock_session_cls, app, monkeypatch):
    _configure_auth(monkeypatch)
    mock_auth.return_value = ({"sub": "user-1"}, None)
    session = MagicMock()
    mock_session_cls.return_value = session

    ws = MagicMock()
    ws.connected = True
    ws.receive.side_effect = [json.dumps([1, 2, 3]), ConnectionClosed()]

    with app.test_request_context("/ws/run?token=abc"):
        handle_ws_run_connection(ws)

    session.handle_message.assert_not_called()


@patch("ws_run.start_pty_bridge")
def test_begin_pty_execution_delegates(mock_start):
    outbound = MagicMock()
    mock_start.return_value = (MagicMock(), MagicMock())

    bridge, thread = begin_pty_execution(outbound, "/tmp/work")

    mock_start.assert_called_once_with(outbound.enqueue, "/tmp/work")
    assert bridge is mock_start.return_value[0]
    assert thread is mock_start.return_value[1]
