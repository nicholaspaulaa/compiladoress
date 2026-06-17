"""Handler WebSocket /ws/run (PRD §9.2)."""

import json
import logging
import threading

from flask import g
from flask_sock import Sock

from ws_auth import WS_CLOSE_POLICY, authenticate_ws_token, extract_ws_token_from_request
from ws_bridge import WsPtyBridge, start_pty_bridge
from ws_protocol import WsRunSession
from metrics import WEBSOCKET_CONNECTIONS

logger = logging.getLogger(__name__)

sock = Sock()
_send_lock = threading.Lock()


def _send_json(ws, payload: dict) -> None:
    with _send_lock:
        ws.send(json.dumps(payload, ensure_ascii=False))


def _reject_ws(ws, message: str) -> None:
    ws.close(WS_CLOSE_POLICY, message)


def begin_pty_execution(ws, binary_dir: str) -> tuple[WsPtyBridge, threading.Thread]:
    """Inicia execucao sandbox; usado por WsRunSession apos build ok."""
    return start_pty_bridge(lambda payload: _send_json(ws, payload), binary_dir)


@sock.route("/ws/run")
def ws_run(ws):
    """Canal autenticado compile+run com protocolo PRD §9.2 (issues #28/#30)."""
    token = extract_ws_token_from_request()
    payload, error = authenticate_ws_token(token)
    if error:
        _reject_ws(ws, error)
        return

    g.user_id = payload["sub"]
    g.user_email = payload.get("email")
    g.jwt_payload = payload

    logger.info("WebSocket /ws/run conectado user_id=%s", g.user_id)

    session = WsRunSession(g.user_id, lambda msg: _send_json(ws, msg))
    WEBSOCKET_CONNECTIONS.inc()

    try:
        while True:
            raw = ws.receive()
            if raw is None:
                session.cleanup()
                break

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("WS frame JSON invalido de user_id=%s", g.user_id)
                continue

            if not isinstance(message, dict):
                logger.warning("WS mensagem nao e objeto JSON user_id=%s", g.user_id)
                continue

            session.handle_message(message)
    finally:
        WEBSOCKET_CONNECTIONS.dec()
