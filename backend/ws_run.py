"""Handler WebSocket /ws/run (PRD §9.2)."""

import json
import logging
import queue
import threading

from flask import g
from flask_sock import Sock
from simple_websocket import ConnectionClosed

from ws_auth import WS_CLOSE_POLICY, authenticate_ws_token, extract_ws_token_from_request
from ws_bridge import WsPtyBridge, start_pty_bridge
from ws_protocol import WsRunSession
from metrics import WEBSOCKET_CONNECTIONS

logger = logging.getLogger(__name__)

sock = Sock()
_RECEIVE_TIMEOUT_S = 0.05


class WsOutbound:
    """Fila de envio — ws.send so na thread do handler (Werkzeug nao e thread-safe)."""

    def __init__(self, ws):
        self._ws = ws
        self._queue: queue.Queue[dict] = queue.Queue()
        self._owner_thread = threading.current_thread()

    def enqueue(self, payload: dict) -> None:
        self._queue.put(payload)
        if threading.current_thread() is self._owner_thread:
            self.flush()

    def flush(self) -> None:
        while True:
            try:
                payload = self._queue.get_nowait()
            except queue.Empty:
                break
            self._ws.send(json.dumps(payload, ensure_ascii=False))


def _reject_ws(ws, message: str) -> None:
    ws.close(WS_CLOSE_POLICY, message)


def begin_pty_execution(
    outbound: WsOutbound,
    binary_dir: str,
) -> tuple[WsPtyBridge, threading.Thread]:
    """Inicia execucao sandbox; usado por WsRunSession apos build ok."""
    return start_pty_bridge(outbound.enqueue, binary_dir)


@sock.route("/ws/run")
def ws_run(ws):
    """Canal autenticado compile+run com protocolo PRD §9.2 (issues #28/#30)."""
    outbound = WsOutbound(ws)

    token = extract_ws_token_from_request()
    payload, error = authenticate_ws_token(token)
    if error:
        outbound.enqueue({"type": "internal_error", "message": error})
        try:
            outbound.flush()
        except Exception:
            logger.debug("Nao foi possivel enviar internal_error antes do close WS")
        _reject_ws(ws, error)
        return

    g.user_id = payload["sub"]
    g.user_email = payload.get("email")
    g.jwt_payload = payload

    logger.info("WebSocket /ws/run conectado user_id=%s", g.user_id)

    session = WsRunSession(g.user_id, outbound.enqueue)
    WEBSOCKET_CONNECTIONS.inc()

    try:
        while ws.connected:
            outbound.flush()
            session.poll_exec_finished()

            try:
                raw = ws.receive(timeout=_RECEIVE_TIMEOUT_S)
            except ConnectionClosed:
                break

            if raw is None:
                continue

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
        session.cleanup()
        WEBSOCKET_CONNECTIONS.dec()
