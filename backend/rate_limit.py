"""Rate limiting por usuario autenticado (PRD RF18, issue #35).

30 execucoes/minuto por user_id do JWT, compartilhado entre
HTTP /api/compile e WebSocket /ws/run (cada compile_and_run conta como 1 hit).

Define "execucao" como: POST /api/compile (REST) OU mensagem compile_and_run (WS).
Ambos compartilham o mesmo bucket de 30/min por usuario.
"""

import jwt
from flask import g, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from limits import parse

RATE_LIMIT_MESSAGE = (
    "Limite de 30 execucoes por minuto excedido. Aguarde e tente novamente."
)
EXECUTION_LIMIT = "30 per minute"


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

# ── API pública para WS (mesmo bucket do flask-limiter) ────────────────────

# Cache do objeto parseado para evitar re-parse a cada chamada
_execution_limit = parse(EXECUTION_LIMIT)


def _hit_execution_limit(key: str) -> bool:
    """Wrapper sobre o RateLimiter interno (limits) — unico ponto de acesso.

    Encapsula o acesso ao atributo privado para facilitar testes e upgrades.
    Retorna True se dentro do limite, False se excedido.
    """
    return limiter._limiter.hit(_execution_limit, key)


def check_execution_rate_limit(user_id: str) -> bool:
    """Verifica rate limit de execucao para o usuario.

    Chamado no WS a cada compile_and_run (nao no handshake).
    Compartilha o mesmo bucket do decorator HTTP @limiter.limit.

    Retorna True se dentro do limite, False se excedido.
    """
    key = f"user:{user_id}"
    return _hit_execution_limit(key)


def ratelimit_error_response() -> tuple:
    """Resposta 429 padronizada (PRD §6.2)."""
    return (
        jsonify({"error": "rate_limited", "message": RATE_LIMIT_MESSAGE}),
        429,
    )

