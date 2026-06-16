"""Testes para o timeout de compilacao (issue #23, PRD RF15)."""

from error_parser import make_error, _VALID_PHASES


def test_compile_timeout_phase_is_valid():
    """compile_timeout deve estar na lista de fases validas."""
    assert "compile_timeout" in _VALID_PHASES


def test_make_error_compile_timeout():
    """make_error com phase=compile_timeout deve incluir limit_s."""
    err = make_error("compile_timeout", "Compilacao excedeu 15s", limit_s=15)
    assert err["phase"] == "compile_timeout"
    assert err["message"] == "Compilacao excedeu 15s"
    assert err["limit_s"] == 15
    assert err["line"] == 0
    assert err["column"] == 0


def test_make_error_compile_timeout_sem_limit_s():
    """make_error com compile_timeout sem limit_s nao inclui o campo."""
    err = make_error("compile_timeout", "timeout")
    assert err["phase"] == "compile_timeout"
    assert "limit_s" not in err


def test_make_error_compile_timeout_preserva_campos_padrao():
    """line e column devem ser preservadas mesmo com limit_s."""
    err = make_error("compile_timeout", "msg", line=10, column=5, limit_s=30)
    assert err["line"] == 10
    assert err["column"] == 5
    assert err["limit_s"] == 30
