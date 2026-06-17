"""Testes do endpoint /metrics (issue #37)."""

import os
import re
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


def _metric_value(body: str, metric_name: str, labels: dict[str, str] | None = None) -> float | None:
    """Extrai o valor de uma metrica do formato text/plain do Prometheus.

    Exemplo de linha: simples_compile_errors_total{phase="semantic"} 3.0
    """
    for line in body.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if not line.startswith(metric_name):
            continue
        if labels:
            if not all(f'{k}="{v}"' in line for k, v in labels.items()):
                continue
        # Pega o ultimo token (valor numerico)
        parts = line.rsplit(" ", 1)
        if len(parts) == 2:
            try:
                return float(parts[1])
            except ValueError:
                continue
    return None


def _metric_present(body: str, metric_name: str) -> bool:
    """Verifica se a metrica aparece no corpo (linha de dados ou HELP/TYPE)."""
    return metric_name in body


@pytest.fixture
def client():
    return app.test_client()


def test_metrics_returns_prometheus_text(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.content_type
    body = resp.get_data(as_text=True)
    assert _metric_present(body, "simples_executions_total")
    assert _metric_present(body, "simples_active_sandboxes")
    assert _metric_present(body, "simples_websocket_connections")
    assert _metric_present(body, "simples_compile_duration_seconds")
    assert _metric_present(body, "simples_execution_duration_seconds")
    assert _metric_present(body, "simples_compile_errors_total")


def test_metrics_no_auth_required(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200


@patch("compile.subprocess.Popen")
def test_compile_records_duration_and_errors(mock_popen, client):
    proc = mock_popen.return_value
    proc.communicate.return_value = ("", "semantic:2:1: variavel nao declarada")
    proc.returncode = 1

    # Captura valores antes via /metrics
    resp_before = client.get("/metrics")
    body_before = resp_before.get_data(as_text=True)
    before_duration = _metric_value(body_before, "simples_compile_duration_seconds_count", {"phase": "parser"}) or 0
    before_errors = _metric_value(body_before, "simples_compile_errors_total", {"phase": "semantic"}) or 0

    from compile import compile_code

    result = compile_code("programa p\ninicio\nfim\n")

    assert result["success"] is False

    # Captura valores depois via /metrics
    resp_after = client.get("/metrics")
    body_after = resp_after.get_data(as_text=True)
    after_duration = _metric_value(body_after, "simples_compile_duration_seconds_count", {"phase": "parser"}) or 0
    after_errors = _metric_value(body_after, "simples_compile_errors_total", {"phase": "semantic"}) or 0

    assert after_duration > before_duration, "compile duration count should increase"
    assert after_errors == before_errors + 1, f"compile errors should increment by 1 (was {before_errors}, now {after_errors})"


@patch("pipeline._run_step")
def test_build_binary_records_nasm_and_ld_phases(mock_run_step, client):
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

    # Captura valores antes via /metrics
    resp_before = client.get("/metrics")
    body_before = resp_before.get_data(as_text=True)
    before_nasm = _metric_value(body_before, "simples_compile_duration_seconds_count", {"phase": "nasm"}) or 0
    before_ld = _metric_value(body_before, "simples_compile_duration_seconds_count", {"phase": "ld"}) or 0

    from pipeline import build_binary, cleanup_work_dir

    result = build_binary("programa p\ninicio\nfim\n")

    try:
        assert result["success"] is True
        # Captura valores depois via /metrics
        resp_after = client.get("/metrics")
        body_after = resp_after.get_data(as_text=True)
        after_nasm = _metric_value(body_after, "simples_compile_duration_seconds_count", {"phase": "nasm"}) or 0
        after_ld = _metric_value(body_after, "simples_compile_duration_seconds_count", {"phase": "ld"}) or 0
        assert after_nasm > before_nasm, "nasm duration count should increase"
        assert after_ld > before_ld, "ld duration count should increase"
    finally:
        cleanup_work_dir(result.get("work_dir"))


def test_record_execution_increments_counter(client):
    from execution import ExecutionResult
    from metrics import record_execution

    resp_before = client.get("/metrics")
    body_before = resp_before.get_data(as_text=True)
    before = _metric_value(body_before, "simples_executions_total", {"outcome": "success"}) or 0

    record_execution(ExecutionResult(exit_code=0, duration_ms=100, timed_out=False))

    resp_after = client.get("/metrics")
    body_after = resp_after.get_data(as_text=True)
    after = _metric_value(body_after, "simples_executions_total", {"outcome": "success"}) or 0

    assert after == before + 1, f"executions_total should increment by 1 (was {before}, now {after})"


def test_gauges_start_at_zero(client):
    resp = client.get("/metrics")
    body = resp.get_data(as_text=True)
    assert _metric_value(body, "simples_active_sandboxes") == 0.0
    assert _metric_value(body, "simples_websocket_connections") == 0.0
