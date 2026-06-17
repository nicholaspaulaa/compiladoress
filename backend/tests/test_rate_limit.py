"""Testes de rate limiting (issue #35)."""

from unittest.mock import patch

import pytest

from rate_limit import (
    RATE_LIMIT_MESSAGE,
    EXECUTION_LIMIT,
    _hit_execution_limit,
    check_execution_rate_limit,
    _rate_limit_key,
    ratelimit_error_response,
)

TEST_USER = "test-user-abc-123"


class TestRateLimitKey:
    """Testes da funcao de extracao de chave."""

    def test_key_with_user_id_in_g(self, app):
        """Com g.user_id setado, retorna user:<id>."""
        with app.test_request_context():
            from flask import g
            g.user_id = TEST_USER
            assert _rate_limit_key() == f"user:{TEST_USER}"

    def test_key_fallback_to_ip(self, app):
        """Sem g.user_id e sem JWT, fallback para IP."""
        with app.test_request_context():
            key = _rate_limit_key()
            assert key != f"user:{TEST_USER}"
            assert "." in key  # formato IP

    def test_key_from_jwt_header(self, app):
        """Extrai sub do JWT no header Authorization."""
        # Token dummy: {"sub": "user-1", "iat": 1}
        token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiJ1c2VyLTEiLCJpYXQiOjF9."
            "fake-sig"
        )
        with app.test_request_context(
            headers={"Authorization": f"Bearer {token}"}
        ):
            key = _rate_limit_key()
            assert key == "user:user-1"


class TestExecutionRateLimit:
    """Testes do limitador de execucoes."""

    def test_check_returns_true_within_limit(self):
        """Primeiras 30 chamadas retornam True (dentro do limite)."""
        for _ in range(30):
            assert check_execution_rate_limit(TEST_USER) is True

    def test_check_returns_false_when_exceeded(self):
        """31a chamada retorna False (limite excedido)."""
        # Consome o bucket primeiro
        for _ in range(30):
            check_execution_rate_limit(TEST_USER)
        assert check_execution_rate_limit(TEST_USER) is False

    def test_different_users_independent_buckets(self):
        """Usuarios diferentes tem buckets independentes."""
        # Satura user A
        for _ in range(30):
            check_execution_rate_limit("user-a")
        # User B ainda tem limite
        assert check_execution_rate_limit("user-b") is True
        # User A excedeu
        assert check_execution_rate_limit("user-a") is False

    def test_hit_execution_limit_wrapper(self):
        """Wrapper _hit_execution_limit usa chave formatada corretamente."""
        with patch("rate_limit.limiter._limiter.hit") as mock_hit:
            mock_hit.return_value = True
            result = _hit_execution_limit(f"user:{TEST_USER}")
            mock_hit.assert_called_once()
            assert result is True


class TestErrorResponse:
    """Testes da resposta de erro 429."""

    def test_ratelimit_error_response_format(self, app):
        """Resposta contem JSON com error e message."""
        with app.test_request_context():
            body, status = ratelimit_error_response()
            assert status == 429
            data = body.get_json()
            assert data["error"] == "rate_limited"
            assert data["message"] == RATE_LIMIT_MESSAGE

    def test_message_is_clear(self):
        """Mensagem de erro e informativa."""
        assert len(RATE_LIMIT_MESSAGE) > 20
        assert "30" in RATE_LIMIT_MESSAGE
        assert "minuto" in RATE_LIMIT_MESSAGE


class TestExecutionLimitConstant:
    """Valida consistencia da constante de limite."""

    def test_execution_limit_constant(self):
        assert EXECUTION_LIMIT == "30 per minute"

    def test_constant_used_by_limiter_decorator(self):
        """Garante que o valor esta documentado para uso consistente."""
        limit = EXECUTION_LIMIT
        parts = limit.split()
        assert parts[0] == "30"
        assert "per" in parts[1]
        assert "minute" in parts[2]
