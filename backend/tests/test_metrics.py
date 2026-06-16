"""Testes do endpoint /metrics (issue #37)."""

import os
from unittest.mock import patch

import pytest

from app import app
from metrics import (
    ACTIVE_SANDBOXES,
    COMPILE_DURATION,
    COMPILE_ERRORS_TOTAL,
    EXECUTIONS_TOTAL,
    WEBSOCKET_CONNECTIONS,
)


@pytest.fixture
def client():
    return app.test_client()


def test_metrics_returns_prometheus_text(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.content_type
    body = resp.get_data(as_text=True)
    assert "simples_executions_total" in body
    assert "simples_active_sandboxes" in body
    assert "simples_websocket_connections" in body
    assert "simples_compile_duration_seconds" in body
    assert "simples_execution_duration_seconds" in body
    assert "simples_compile_errors_total" in body


def test_metrics_no_auth_required(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200


@patch("compile.subprocess.Popen")
def test_compile_records_duration_and_errors(mock_popen, client):
    proc = mock_popen.return_value
    proc.communicate.return_value = ("", "semantic:2:1: variavel nao declarada")
    proc.returncode = 1

    before = COMPILE_DURATION.labels(phase="parser")._sum.get()
    before_errors = COMPILE_ERRORS_TOTAL.labels(phase="semantic")._value.get()

    from compile import compile_code

    result = compile_code("programa p\ninicio\nfim\n")

    assert result["success"] is False
    assert COMPILE_DURATION.labels(phase="parser")._sum.get() >= before
    assert COMPILE_ERRORS_TOTAL.labels(phase="semantic")._value.get() == before_errors + 1


@patch("pipeline._run_step")
def test_build_binary_records_nasm_and_ld_phases(mock_run_step):
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

    from pipeline import build_binary, cleanup_work_dir

    before_nasm = COMPILE_DURATION.labels(phase="nasm")._sum.get()
    before_ld = COMPILE_DURATION.labels(phase="ld")._sum.get()

    result = build_binary("programa p\ninicio\nfim\n")

    try:
        assert result["success"] is True
        assert COMPILE_DURATION.labels(phase="nasm")._sum.get() >= before_nasm
        assert COMPILE_DURATION.labels(phase="ld")._sum.get() >= before_ld
    finally:
        cleanup_work_dir(result.get("work_dir"))


def test_record_execution_increments_counter():
    from execution import ExecutionResult
    from metrics import record_execution

    before = EXECUTIONS_TOTAL.labels(outcome="success")._value.get()
    record_execution(ExecutionResult(exit_code=0, duration_ms=100, timed_out=False))
    assert EXECUTIONS_TOTAL.labels(outcome="success")._value.get() == before + 1


def test_gauges_start_at_zero(client):
    resp = client.get("/metrics")
    body = resp.get_data(as_text=True)
    assert "simples_active_sandboxes 0.0" in body or "simples_active_sandboxes 0" in body
    assert WEBSOCKET_CONNECTIONS._value.get() == 0
