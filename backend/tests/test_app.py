"""Testes dos endpoints HTTP Flask (issue #41)."""

from unittest.mock import patch

import jwt

from config import Config


def _auth_headers(monkeypatch, sub: str = "user-1", email: str = "a@b.com") -> dict[str, str]:
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(Config, "SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.setattr(Config, "SUPABASE_JWT_SECRET", "test-secret")
    token = jwt.encode(
        {"sub": sub, "email": email, "aud": "authenticated"},
        "test-secret",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_health_supabase_ok(client, monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(Config, "SUPABASE_ANON_KEY", "anon")
    monkeypatch.setattr(Config, "SUPABASE_JWT_SECRET", "secret")

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["components"]["supabase"]["status"] == "ok"


def test_health_supabase_unconfigured(client, monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "")
    monkeypatch.setattr(Config, "SUPABASE_ANON_KEY", "")
    monkeypatch.setattr(Config, "SUPABASE_JWT_SECRET", "")

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["components"]["supabase"]["status"] == "unconfigured"


def test_metrics_endpoint(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert b"simples_" in response.data or response.data


def test_auth_verify_success(client, monkeypatch):
    headers = _auth_headers(monkeypatch, sub="user-abc", email="dev@test.com")

    response = client.post("/api/auth/verify", headers=headers)

    assert response.status_code == 200
    body = response.get_json()
    assert body["valid"] is True
    assert body["user_id"] == "user-abc"
    assert body["email"] == "dev@test.com"


def test_compile_requires_json_body(client, monkeypatch):
    headers = _auth_headers(monkeypatch)

    response = client.post(
        "/api/compile",
        headers=headers,
        data="not-json",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "bad_request"


def test_compile_requires_non_empty_code(client, monkeypatch):
    headers = _auth_headers(monkeypatch)

    response = client.post("/api/compile", json={"code": "   "}, headers=headers)

    assert response.status_code == 400


def test_compile_requires_code_field(client, monkeypatch):
    headers = _auth_headers(monkeypatch)

    response = client.post("/api/compile", json={}, headers=headers)

    assert response.status_code == 400


@patch("app.compile_code")
def test_compile_success(mock_compile, client, monkeypatch):
    mock_compile.return_value = {"success": True, "asm": "section .text\n"}
    headers = _auth_headers(monkeypatch)

    response = client.post(
        "/api/compile",
        json={"code": "programa p\ninicio\nfim\n"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.get_json()["asm"] == "section .text\n"
    mock_compile.assert_called_once_with("programa p\ninicio\nfim")


@patch("app.compile_code")
def test_compile_returns_structured_errors(mock_compile, client, monkeypatch):
    mock_compile.return_value = {
        "success": False,
        "errors": [
            {"phase": "semantic", "line": 2, "column": 1, "message": "variavel nao declarada"},
        ],
    }
    headers = _auth_headers(monkeypatch)

    response = client.post(
        "/api/compile",
        json={"code": "programa p\ninicio\nfim\n"},
        headers=headers,
    )

    assert response.status_code == 422
    errors = response.get_json()["errors"]
    assert errors[0]["phase"] == "semantic"


def test_compile_requires_authentication(client, monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://example.supabase.co")

    response = client.post("/api/compile", json={"code": "programa p\ninicio\nfim\n"})

    assert response.status_code == 401
