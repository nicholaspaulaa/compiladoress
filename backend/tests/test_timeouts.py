"""Testes para timeouts de execucao (issue #33, PRD §11.3)."""

from config import Config


def test_docker_stop_timeout_default():
    """DOCKER_STOP_TIMEOUT_S deve ser 12 por padrao (PRD §11.3 camada [3])."""
    assert Config.DOCKER_STOP_TIMEOUT_S == 12


def test_exec_timeout_default():
    """EXEC_TIMEOUT_S deve ser 10 por padrao (PRD §11.3 camada [2])."""
    assert Config.EXEC_TIMEOUT_S == 10


def test_compile_timeout_default():
    """COMPILE_TIMEOUT_S deve ser 15 por padrao (PRD §11.3 camada [1])."""
    assert Config.COMPILE_TIMEOUT_S == 15
