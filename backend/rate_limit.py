"""Rate limiting por usuario autenticado (PRD RF18, issue #35).

30 execucoes/minuto por user_id do JWT, compartilhado entre
HTTP /api/compile e WebSocket /ws/run.
"""

import jwt
from flask import g, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from limits import parse

RATE_LIMIT_MESSAGE = (
    "Limite de 30 execucoes por minuto excedido. Aguarde e tente novamente."
)


def _rate_limit_key() -> str:
    """Extrai chave de rate limit do JWT (user_id) ou fallback para IP."""
    # g.user_id ja foi setado por verify_jwt antes do limiter rodar
    user_id = getattr(g, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fallback: extrai sub do JWT sem verificar assinatura
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                sub = payload.get("sub")
                if sub:
                    return f"user:{sub}"
            except Exception:
                pass

    return get_remote_address()


limiter = Limiter(key_func=_rate_limit_key, storage_uri="memory://")


def ws_check_rate_limit(user_id: str) -> bool:
    """Verifica rate limit para conexao WebSocket.

    Retorna True se dentro do limite, False se excedido.
    Usa o mesmo bucket do flask-limiter para consistencia HTTP/WS.
    """
    key = f"user:{user_id}"
    limit = parse("30 per minute")
    # Acessa o RateLimiter interno do limits (flask-limiter o expoe como _limiter)
    return limiter._limiter.hit(limit, key)


def ratelimit_error_response() -> tuple:
    """Resposta 429 padronizada (PRD §6.2)."""
    return (
        jsonify({"error": "rate_limited", "message": RATE_LIMIT_MESSAGE}),
        429,
    )
