"""Testes de autenticacao WebSocket (issue #24)."""

import jwt
import pytest
from flask import Flask

from config import Config
from ws_auth import authenticate_ws_token, extract_ws_token_from_request


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    return flask_app


def test_extract_token_from_query(app):
    with app.test_request_context("/ws/run?token=abc123"):
        assert extract_ws_token_from_request() == "abc123"


def test_extract_token_from_websocket_protocol(app):
    with app.test_request_context(
        "/ws/run",
        headers={"Sec-WebSocket-Protocol": "bearer.jwt.token.here, json"},
    ):
        assert extract_ws_token_from_request() == "jwt.token.here"


def test_extract_token_missing(app):
    with app.test_request_context("/ws/run"):
        assert extract_ws_token_from_request() is None


def test_authenticate_ws_token_missing():
    payload, error = authenticate_ws_token(None)
    assert payload is None
    assert error == "Token ausente"


def test_authenticate_ws_token_valid_hs256(monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(Config, "SUPABASE_JWT_SECRET", "test-secret")
    token = jwt.encode(
        {"sub": "user-123", "email": "a@b.com", "aud": "authenticated"},
        "test-secret",
        algorithm="HS256",
    )
    payload, error = authenticate_ws_token(token)
    assert error is None
    assert payload["sub"] == "user-123"


def test_authenticate_ws_token_expired(monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(Config, "SUPABASE_JWT_SECRET", "test-secret")
    token = jwt.encode(
        {"sub": "user-123", "aud": "authenticated"},
        "test-secret",
        algorithm="HS256",
        headers={"alg": "HS256"},
    )
    # Force expired by decoding with wrong secret simulation - use expired token
    import time

    token = jwt.encode(
        {"sub": "user-123", "aud": "authenticated", "exp": int(time.time()) - 60},
        "test-secret",
        algorithm="HS256",
    )
    payload, error = authenticate_ws_token(token)
    assert payload is None
    assert error == "Token expirado"
