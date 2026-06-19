from functools import lru_cache, wraps

import jwt
from flask import g, jsonify, request
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from config import Config

# Tolerancia de relogio entre cliente, Supabase e Docker (segundos).
# Docker Desktop no Windows costuma ficar ~1-2 min atrasado vs o host.
_JWT_LEEWAY_S = 120


def _unauthorized(message: str):
    return jsonify({"error": "unauthorized", "message": message}), 401


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient | None:
    if not Config.SUPABASE_URL:
        return None
    jwks_url = f"{Config.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(jwks_url, cache_keys=True)


def _decode_via_jwks(token: str, algorithm: str) -> dict:
    client = _jwks_client()
    if client is None:
        raise InvalidTokenError("SUPABASE_URL nao configurado para JWKS")
    signing_key = client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=[algorithm],
        audience="authenticated",
        leeway=_JWT_LEEWAY_S,
    )


def _decode_via_hs256(token: str) -> dict:
    if not Config.SUPABASE_JWT_SECRET:
        raise InvalidTokenError("SUPABASE_JWT_SECRET nao configurado")
    return jwt.decode(
        token,
        Config.SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience="authenticated",
        leeway=_JWT_LEEWAY_S,
    )


def _decode_supabase_token(token: str) -> dict:
    """Valida JWT do Supabase (ES256/RS256 via JWKS ou HS256 legado)."""
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg", "HS256")
    errors: list[InvalidTokenError] = []

    if algorithm in ("ES256", "RS256"):
        try:
            return _decode_via_jwks(token, algorithm)
        except InvalidTokenError as exc:
            errors.append(exc)

    if Config.SUPABASE_JWT_SECRET:
        try:
            return _decode_via_hs256(token)
        except InvalidTokenError as exc:
            errors.append(exc)

    if errors:
        raise errors[-1]
    raise InvalidTokenError("Token invalido")


def verify_jwt(f):
    """Valida JWT do Supabase (Authorization: Bearer <token>)."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return _unauthorized("Token ausente ou formato invalido")

        token = auth_header[7:].strip()
        if not token:
            return _unauthorized("Token ausente ou formato invalido")

        if not Config.SUPABASE_URL:
            return (
                jsonify(
                    {
                        "error": "server_error",
                        "message": "SUPABASE_URL nao configurado no servidor",
                    }
                ),
                503,
            )

        try:
            payload = _decode_supabase_token(token)
        except jwt.ExpiredSignatureError:
            return _unauthorized("Token expirado")
        except InvalidTokenError:
            return _unauthorized("Token invalido")

        g.user_id = payload["sub"]
        g.user_email = payload.get("email")
        g.jwt_payload = payload
        return f(*args, **kwargs)

    return decorated
