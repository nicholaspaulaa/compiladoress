"""Testes do middleware JWT HTTP (issue #41)."""

import time

import jwt
import pytest
from flask import Flask, g, jsonify

from auth import _decode_supabase_token, _unauthorized, verify_jwt
from config import Config
from jwt.exceptions import InvalidTokenError


@pytest.fixture
def jwt_app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route("/protected")
    @verify_jwt
    def protected():
        return jsonify({"user_id": g.user_id, "email": g.user_email})

    return app


@pytest.fixture
def jwt_client(jwt_app):
    return jwt_app.test_client()


def _configure_supabase(monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(Config, "SUPABASE_JWT_SECRET", "test-secret")


def test_unauthorized_response_format():
    app = Flask(__name__)
    with app.app_context():
        body, status = _unauthorized("Token invalido")
    assert status == 401
    assert body.get_json()["error"] == "unauthorized"


def test_verify_jwt_missing_header(jwt_client, monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://example.supabase.co")

    response = jwt_client.get("/protected")

    assert response.status_code == 401


def test_verify_jwt_empty_bearer(jwt_client, monkeypatch):
    _configure_supabase(monkeypatch)

    response = jwt_client.get("/protected", headers={"Authorization": "Bearer "})

    assert response.status_code == 401


def test_verify_jwt_server_misconfigured(jwt_client, monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "")

    response = jwt_client.get(
        "/protected",
        headers={"Authorization": "Bearer some-token"},
    )

    assert response.status_code == 503
    assert response.get_json()["error"] == "server_error"


def test_verify_jwt_valid_hs256(jwt_client, monkeypatch):
    _configure_supabase(monkeypatch)
    token = jwt.encode(
        {"sub": "user-123", "email": "dev@test.com", "aud": "authenticated"},
        "test-secret",
        algorithm="HS256",
    )

    response = jwt_client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["user_id"] == "user-123"
    assert body["email"] == "dev@test.com"


def test_verify_jwt_expired(jwt_client, monkeypatch):
    _configure_supabase(monkeypatch)
    token = jwt.encode(
        {
            "sub": "user-123",
            "aud": "authenticated",
            "exp": int(time.time()) - 120,
        },
        "test-secret",
        algorithm="HS256",
    )

    response = jwt_client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert "expirado" in response.get_json()["message"]


def test_verify_jwt_invalid_token(jwt_client, monkeypatch):
    _configure_supabase(monkeypatch)

    response = jwt_client.get(
        "/protected",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )

    assert response.status_code == 401


def test_decode_supabase_token_without_secret(monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "")
    monkeypatch.setattr(Config, "SUPABASE_JWT_SECRET", "")

    with pytest.raises(InvalidTokenError):
        _decode_supabase_token("invalid.token.value")
