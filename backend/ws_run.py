"""Handler WebSocket /ws/run (PRD §9.2)."""

import json
import logging
import threading

from flask import g
from flask_sock import Sock

from config import Config
from ws_auth import WS_CLOSE_POLICY, authenticate_ws_token, extract_ws_token_from_request
from ws_bridge import WsPtyBridge, start_pty_bridge

logger = logging.getLogger(__name__)

sock = Sock()
_send_lock = threading.Lock()


def _send_json(ws, payload: dict) -> None:
    with _send_lock:
        ws.send(json.dumps(payload, ensure_ascii=False))


def _reject_ws(ws, message: str) -> None:
    ws.close(WS_CLOSE_POLICY, message)


def _cleanup_execution(
    bridge: WsPtyBridge | None,
    exec_thread: threading.Thread | None,
) -> None:
    if bridge is not None and bridge.active:
        bridge.shutdown()
    if exec_thread is not None and exec_thread.is_alive():
        exec_thread.join(timeout=Config.EXEC_TIMEOUT_S + Config.DOCKER_STOP_TIMEOUT_S + 5)


def begin_pty_execution(ws, binary_dir: str) -> tuple[WsPtyBridge, threading.Thread]:
    """Inicia execucao sandbox; chamado pelo pipeline compile+run (issue #30)."""
    return start_pty_bridge(lambda payload: _send_json(ws, payload), binary_dir)


@sock.route("/ws/run")
def ws_run(ws):
    """Canal autenticado compile+run. Bridge PTY<->WS (issue #28); protocolo completo #30."""
    token = extract_ws_token_from_request()
    payload, error = authenticate_ws_token(token)
    if error:
        _reject_ws(ws, error)
        return

    g.user_id = payload["sub"]
    g.user_email = payload.get("email")
    g.jwt_payload = payload

    logger.info("WebSocket /ws/run conectado user_id=%s", g.user_id)

    bridge: WsPtyBridge | None = None
    exec_thread: threading.Thread | None = None

    while True:
        raw = ws.receive()
        if raw is None:
            _cleanup_execution(bridge, exec_thread)
            break

        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("WS frame JSON invalido de user_id=%s", g.user_id)
            continue

        msg_type = message.get("type")
        if msg_type == "ping":
            _send_json(ws, {"type": "pong"})
            continue

        if msg_type in ("stdin", "stop"):
            if bridge is not None and bridge.active:
                bridge.enqueue(message)
            else:
                logger.warning(
                    "WS %s ignorado em IDLE user_id=%s",
                    msg_type,
                    g.user_id,
                )
            continue

        if msg_type == "compile_and_run":
            logger.warning(
                "compile_and_run ainda nao implementado (issue #30) user_id=%s",
                g.user_id,
            )
            continue

        logger.warning(
            "WS mensagem desconhecida: type=%s user_id=%s",
            msg_type,
            g.user_id,
        )
