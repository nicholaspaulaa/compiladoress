"""Autenticacao JWT para handshake WebSocket (PRD §9.2)."""

from flask import request
import jwt
from jwt.exceptions import InvalidTokenError

from auth import _decode_supabase_token
from config import Config

WS_CLOSE_POLICY = 4403


def extract_ws_token_from_request() -> str | None:
    """Extrai JWT de ?token= ou Sec-WebSocket-Protocol: bearer.<jwt>."""
    query_token = request.args.get("token", "").strip()
    if query_token:
        return query_token

    protocol_header = request.headers.get("Sec-WebSocket-Protocol", "")
    for entry in protocol_header.split(","):
        entry = entry.strip()
        if entry.startswith("bearer."):
            token = entry[7:].strip()
            if token:
                return token
    return None


def authenticate_ws_token(token: str | None) -> tuple[dict | None, str | None]:
    """Valida token Supabase. Retorna (payload, mensagem_erro)."""
    if not token:
        return None, "Token ausente"

    if not Config.SUPABASE_URL:
        return None, "SUPABASE_URL nao configurado no servidor"

    try:
        payload = _decode_supabase_token(token)
    except jwt.ExpiredSignatureError:
        return None, "Token expirado"
    except InvalidTokenError:
        return None, "Token invalido"

    return payload, None
