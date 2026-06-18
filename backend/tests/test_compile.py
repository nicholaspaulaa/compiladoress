"""Testes unitarios de compile_code (issue #41)."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from compile import _kill_process_tree, compile_code


@patch("compile.os.unlink")
@patch("compile.os.path.isfile", return_value=True)
@patch("builtins.open", create=True)
@patch("compile.subprocess.Popen")
def test_compile_code_success(mock_popen, mock_open, _mock_isfile, _mock_unlink):
    proc = MagicMock()
    proc.returncode = 0
    proc.communicate.return_value = ("", "")
    mock_popen.return_value = proc
    mock_open.return_value.__enter__.return_value.read.return_value = "section .text\n"

    result = compile_code("programa p\ninicio\nfim\n")

    assert result["success"] is True
    assert result["asm"] == "section .text\n"


@patch("compile.os.unlink")
@patch("compile.os.path.isfile", return_value=False)
@patch("compile.subprocess.Popen")
def test_compile_code_parsed_error(mock_popen, _mock_isfile, _mock_unlink):
    proc = MagicMock()
    proc.returncode = 1
    proc.communicate.return_value = ("", "semantic:2:1: variavel nao declarada")
    mock_popen.return_value = proc

    result = compile_code("programa p\ninicio\nfim\n")

    assert result["success"] is False
    assert result["errors"][0]["phase"] == "semantic"


@patch("compile.os.unlink")
@patch("compile.os.path.isfile", return_value=False)
@patch("compile.subprocess.Popen")
def test_compile_code_unknown_stderr(mock_popen, _mock_isfile, _mock_unlink):
    proc = MagicMock()
    proc.returncode = 1
    proc.communicate.return_value = ("", "erro interno do compilador")
    mock_popen.return_value = proc

    result = compile_code("x")

    assert result["success"] is False
    assert result["errors"][0]["phase"] == "unknown"


@patch("compile.record_compile_errors")
@patch("compile._kill_process_tree")
@patch("compile.os.unlink")
@patch("compile.subprocess.Popen")
def test_compile_code_timeout(mock_popen, _mock_unlink, mock_kill, _mock_record):
    proc = MagicMock()
    mock_popen.return_value = proc
    proc.communicate.side_effect = [
        subprocess.TimeoutExpired(cmd="simplesc", timeout=15),
        ("", ""),
    ]

    result = compile_code("programa p\ninicio\nfim\n")

    assert result["success"] is False
    assert result["errors"][0]["phase"] == "compile_timeout"
    mock_kill.assert_called_once_with(proc)


@patch("compile.record_compile_errors")
@patch("compile.os.unlink")
@patch("compile.subprocess.Popen", side_effect=FileNotFoundError)
def test_compile_code_binary_missing(_mock_popen, _mock_unlink, _mock_record):
    result = compile_code("programa p\ninicio\nfim\n")

    assert result["success"] is False
    assert result["errors"][0]["phase"] == "server"
    assert "nao encontrado" in result["errors"][0]["message"]


def test_kill_process_tree_terminate_success():
    proc = MagicMock()
    proc.wait.return_value = 0

    _kill_process_tree(proc)

    proc.terminate.assert_called_once()
    proc.kill.assert_not_called()


def test_kill_process_tree_escalates_to_kill():
    proc = MagicMock()
    proc.pid = 999
    proc.wait.side_effect = [subprocess.TimeoutExpired(cmd="simplesc", timeout=2), 0]

    _kill_process_tree(proc)

    proc.terminate.assert_called_once()
    proc.kill.assert_called_once()


def test_kill_process_tree_process_already_gone():
    proc = MagicMock()
    proc.terminate.side_effect = ProcessLookupError()

    _kill_process_tree(proc)
