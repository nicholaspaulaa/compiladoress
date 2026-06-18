"""Testes para timeouts de execucao (issue #32, #33, PRD §11.3)."""

from config import Config


def test_docker_stop_timeout_default():
    assert Config.DOCKER_STOP_TIMEOUT_S == 12


def test_exec_timeout_default():
    assert Config.EXEC_TIMEOUT_S == 10


def test_compile_timeout_default():
    assert Config.COMPILE_TIMEOUT_S == 15


def test_exec_timeout_uses_asyncio_module():
    """Issue #32: camada wall-clock exposta via exec_timeout."""
    import exec_timeout

    assert hasattr(exec_timeout, "run_with_wall_clock_timeout")
