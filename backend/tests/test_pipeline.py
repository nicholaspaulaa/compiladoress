"""Testes do pipeline simplesc -> nasm -> ld (issue #30)."""

import os
from unittest.mock import patch

import pytest

from config import Config
from pipeline import build_binary, cleanup_work_dir, compile_error_payload


def test_compile_error_payload_includes_fields():
    payload = compile_error_payload(
        {
            "phase": "semantic",
            "line": 4,
            "column": 7,
            "message": "variavel nao declarada",
        }
    )
    assert payload == {
        "type": "compile_error",
        "phase": "semantic",
        "line": 4,
        "column": 7,
        "message": "variavel nao declarada",
    }


def test_build_binary_rejects_oversized_code():
    huge = "x" * (Config.max_code_bytes() + 1)
    result = build_binary(huge)
    assert result["success"] is False
    assert result["errors"][0]["phase"] == "server"


@patch("pipeline._run_step")
def test_build_binary_success(mock_run_step):
    def fake_run(cmd, *, cwd, timeout_s, timeout_phase):
        asm_path = os.path.join(cwd, "programa.asm")
        obj_path = os.path.join(cwd, "programa.o")
        bin_path = os.path.join(cwd, "programa")
        if "simplesc" in os.path.basename(cmd[0]) or cmd[0].endswith("simplesc"):
            with open(asm_path, "w", encoding="utf-8") as handle:
                handle.write("section .text\n")
            return type("R", (), {"returncode": 0, "stderr": ""})()
        if "nasm" in cmd[0]:
            open(obj_path, "wb").close()
            return type("R", (), {"returncode": 0, "stderr": ""})()
        open(bin_path, "wb").close()
        return type("R", (), {"returncode": 0, "stderr": ""})()

    mock_run_step.side_effect = fake_run

    code = "programa p\ninicio\nfim\n"
    result = build_binary(code)

    try:
        assert result["success"] is True
        assert "section .text" in result["asm"]
        assert os.path.isdir(result["work_dir"])
        assert mock_run_step.call_count == 3
    finally:
        cleanup_work_dir(result.get("work_dir"))


@patch("pipeline._run_step")
def test_build_binary_compile_error(mock_run_step):
    mock_run_step.return_value = type(
        "R",
        (),
        {"returncode": 1, "stderr": "semantic:2:1: erro de teste"},
    )()

    result = build_binary("programa p\ninicio\nfim\n")
    assert result["success"] is False
    assert result["errors"][0]["phase"] == "semantic"


@patch("pipeline._run_step")
def test_build_binary_assemble_error(mock_run_step):
    def fake_run(cmd, *, cwd, timeout_s, timeout_phase):
        if "simplesc" in os.path.basename(cmd[0]) or cmd[0].endswith("simplesc"):
            with open(os.path.join(cwd, "programa.asm"), "w", encoding="utf-8") as handle:
                handle.write("bad asm")
            return type("R", (), {"returncode": 0, "stderr": ""})()
        return type("R", (), {"returncode": 1, "stderr": "invalid instruction"})()

    mock_run_step.side_effect = fake_run

    result = build_binary("programa p\ninicio\nfim\n")
    assert result["success"] is False
    assert result["stage"] == "assemble"
    assert "invalid instruction" in result["stderr"]
