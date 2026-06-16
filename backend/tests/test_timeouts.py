"""Testes para timeouts de execucao (issue #33, PRD §11.3)."""

from config import Config


def test_docker_stop_timeout_default():
    assert Config.DOCKER_STOP_TIMEOUT_S == 12


def test_exec_timeout_default():
    assert Config.EXEC_TIMEOUT_S == 10


def test_compile_timeout_default():
    assert Config.COMPILE_TIMEOUT_S == 15
