from functools import wraps

import jwt
from flask import g, jsonify, request
from jwt.exceptions import InvalidTokenError

from config import Config


def _unauthorized(message: str):
    return jsonify({"error": "unauthorized", "message": message}), 401


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

        if not Config.SUPABASE_JWT_SECRET:
            return (
                jsonify(
                    {
                        "error": "server_error",
                        "message": "SUPABASE_JWT_SECRET nao configurado no servidor",
                    }
                ),
                503,
            )

        try:
            payload = jwt.decode(
                token,
                Config.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except jwt.ExpiredSignatureError:
            return _unauthorized("Token expirado")
        except InvalidTokenError:
            return _unauthorized("Token invalido")

        g.user_id = payload["sub"]
        g.user_email = payload.get("email")
        g.jwt_payload = payload
        return f(*args, **kwargs)

    return decorated
