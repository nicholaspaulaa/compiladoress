from functools import lru_cache, wraps

import jwt
from flask import g, jsonify, request
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from config import Config


def _unauthorized(message: str):
    return jsonify({"error": "unauthorized", "message": message}), 401


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient | None:
    if not Config.SUPABASE_URL:
        return None
    jwks_url = f"{Config.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(jwks_url, cache_keys=True)


def _decode_supabase_token(token: str) -> dict:
    """Valida JWT do Supabase (HS256 legado ou ES256/RS256 via JWKS)."""
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg", "HS256")

    if algorithm in ("ES256", "RS256"):
        client = _jwks_client()
        if client is None:
            raise InvalidTokenError("SUPABASE_URL nao configurado para JWKS")
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            audience="authenticated",
        )

    if not Config.SUPABASE_JWT_SECRET:
        raise InvalidTokenError("SUPABASE_JWT_SECRET nao configurado")

    return jwt.decode(
        token,
        Config.SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience="authenticated",
    )


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
