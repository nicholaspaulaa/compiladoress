"""Bridge bidirecional PTY (docker attach) <-> WebSocket xterm (PRD §7.3, issue #28)."""

from __future__ import annotations

import asyncio
import logging
import queue
import threading
import time
from typing import Callable

from config import Config
from exec_timeout import run_with_wall_clock_timeout
from execution import ExecutionResult, ExecutionStrategy, PtyExecutionStrategy, format_docker_error
from metrics import record_execution

logger = logging.getLogger(__name__)

SendJson = Callable[[dict], None]


class WsPtyBridge:
    """Conecta PtyExecutionStrategy ao protocolo WS (stdout/stdin/stop)."""

    def __init__(
        self,
        send_json: SendJson,
        strategy: ExecutionStrategy | None = None,
    ):
        self._send_json = send_json
        self._strategy = strategy or PtyExecutionStrategy()
        self._inbound: queue.Queue[dict | None] = queue.Queue()
        self._active = threading.Event()

    @property
    def active(self) -> bool:
        return self._active.is_set()

    def enqueue(self, message: dict) -> None:
        """ws_to_pty: enfileira mensagens do cliente (stdin, stop)."""
        msg_type = message.get("type")
        if not self.active and msg_type != "stop":
            logger.warning(
                "WS mensagem ignorada fora de EXECUTING: type=%s",
                msg_type,
            )
            return
        self._inbound.put(message)

    def shutdown(self) -> None:
        """Encerra sessao e libera recursos do bridge."""
        self._inbound.put(None)

    def run(self, binary_dir: str, timeout_s: int | None = None) -> ExecutionResult:
        """pty_to_ws + ws_to_pty; asyncio.wait_for aplica timeout wall-clock (issue #32)."""
        self._active.set()
        try:
            return asyncio.run(self._run_session_async(binary_dir, timeout_s))
        finally:
            self._active.clear()
            self._drain_inbound()

    def _drain_inbound(self) -> None:
        while True:
            try:
                self._inbound.get_nowait()
            except queue.Empty:
                break

    async def _run_session_async(
        self, binary_dir: str, timeout_s: int | None
    ) -> ExecutionResult:
        limit = timeout_s if timeout_s is not None else Config.EXEC_TIMEOUT_S
        self._send_json({"type": "exec_started"})
        started = time.monotonic()

        def poll_message() -> dict | None:
            try:
                msg = self._inbound.get(timeout=0.05)
            except queue.Empty:
                return None
            if msg is None:
                return {"type": "stop"}
            return msg

        def pty_to_ws(data: str) -> None:
            if not data:
                return
            self._send_json({"type": "stdout", "data": data})

        def run_execute() -> ExecutionResult:
            return self._strategy.execute(
                binary_dir,
                pty_to_ws,
                poll_message,
                timeout_s=timeout_s,
            )

        try:
            result, asyncio_timed_out = await run_with_wall_clock_timeout(
                run_execute,
                timeout_s=float(limit),
                on_timeout=self.shutdown,
                cleanup_grace_s=0.5,
            )
        except Exception as exc:
            logger.exception("Falha na execucao PTY user-facing")
            message = format_docker_error(exc)
            self._send_json({"type": "internal_error", "message": message})
            record_execution(
                ExecutionResult(exit_code=-1, duration_ms=0, timed_out=False)
            )
            raise

        duration_ms = int((time.monotonic() - started) * 1000)
        if asyncio_timed_out and result is None:
            result = ExecutionResult(
                exit_code=1,
                duration_ms=duration_ms,
                timed_out=True,
            )
        elif asyncio_timed_out and result is not None:
            result = ExecutionResult(
                exit_code=result.exit_code,
                duration_ms=result.duration_ms,
                timed_out=True,
                stopped=result.stopped,
            )

        if result.timed_out:
            self._send_json({"type": "timeout", "limit_s": limit})
        else:
            payload: dict = {
                "type": "exit",
                "code": result.exit_code,
                "duration_ms": result.duration_ms,
            }
            if result.stopped:
                payload["stopped"] = True
            self._send_json(payload)

        record_execution(result)
        return result


def start_pty_bridge(
    send_json: SendJson,
    binary_dir: str,
    *,
    strategy: ExecutionStrategy | None = None,
    timeout_s: int | None = None,
) -> tuple[WsPtyBridge, threading.Thread]:
    """Inicia bridge em background; handler WS continua recebendo stdin/stop."""
    bridge = WsPtyBridge(send_json, strategy=strategy)
    bridge._active.set()
    thread = threading.Thread(
        target=bridge.run,
        args=(binary_dir,),
        kwargs={"timeout_s": timeout_s},
        daemon=True,
        name="ws-pty-bridge",
    )
    thread.start()
    return bridge, thread
