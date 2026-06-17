"""Metricas Prometheus (PRD §16.2, issue #37)."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

if TYPE_CHECKING:
    from execution import ExecutionResult

COMPILE_DURATION = Histogram(
    "simples_compile_duration_seconds",
    "Duracao das etapas de compilacao",
    ["phase"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 15.0),
)
EXECUTION_DURATION = Histogram(
    "simples_execution_duration_seconds",
    "Duracao da execucao sandbox",
    ["outcome"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)
EXECUTIONS_TOTAL = Counter(
    "simples_executions_total",
    "Total de execucoes sandbox",
    ["outcome"],
)
COMPILE_ERRORS_TOTAL = Counter(
    "simples_compile_errors_total",
    "Total de erros de compilacao",
    ["phase"],
)
ACTIVE_SANDBOXES = Gauge(
    "simples_active_sandboxes",
    "Containers sandbox ativos",
)
WEBSOCKET_CONNECTIONS = Gauge(
    "simples_websocket_connections",
    "Conexoes WebSocket /ws/run abertas",
)


def normalize_compile_phase(phase: str | None) -> str:
    """Mapeia fases internas para labels do PRD."""
    if phase in ("lexer", "parser", "semantic", "nasm", "ld"):
        return phase
    if phase == "assemble":
        return "nasm"
    if phase == "link":
        return "ld"
    if phase in ("codegen", "compiler"):
        return "parser"
    return "unknown"


@contextmanager
def observe_compile_phase(phase: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        COMPILE_DURATION.labels(phase=normalize_compile_phase(phase)).observe(
            time.perf_counter() - start
        )


def record_compile_errors(errors: list[dict]) -> None:
    for err in errors:
        COMPILE_ERRORS_TOTAL.labels(phase=normalize_compile_phase(err.get("phase"))).inc()


def record_execution(result: ExecutionResult) -> None:
    if result.timed_out:
        outcome = "timeout"
    elif result.exit_code != 0:
        outcome = "runtime_error"
    else:
        outcome = "success"
    EXECUTION_DURATION.labels(outcome=outcome).observe(result.duration_ms / 1000.0)
    EXECUTIONS_TOTAL.labels(outcome=outcome).inc()


def metrics_response() -> tuple[bytes, int, dict[str, str]]:
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
