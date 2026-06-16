"""Handler WebSocket /ws/run (PRD §9.2)."""

import json
import logging

from flask import g
from flask_sock import Sock

from ws_auth import WS_CLOSE_POLICY, authenticate_ws_token, extract_ws_token_from_request

logger = logging.getLogger(__name__)

sock = Sock()


def _send_json(ws, payload: dict) -> None:
    ws.send(json.dumps(payload, ensure_ascii=False))


def _reject_ws(ws, message: str) -> None:
    ws.close(WS_CLOSE_POLICY, message)


@sock.route("/ws/run")
def ws_run(ws):
    """Canal autenticado compile+run. Protocolo completo nas issues #28/#30."""
    token = extract_ws_token_from_request()
    payload, error = authenticate_ws_token(token)
    if error:
        _reject_ws(ws, error)
        return

    g.user_id = payload["sub"]
    g.user_email = payload.get("email")
    g.jwt_payload = payload

    logger.info("WebSocket /ws/run conectado user_id=%s", g.user_id)

    while True:
        raw = ws.receive()
        if raw is None:
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

        logger.warning(
            "WS mensagem ignorada (handler completo em sprint 4): type=%s user_id=%s",
            msg_type,
            g.user_id,
        )
