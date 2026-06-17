"""Protocolo WebSocket /ws/run e maquina de estados (PRD §9.2, issue #30)."""

from __future__ import annotations

import logging
import threading
from enum import Enum
from typing import Callable

from config import Config
from pipeline import build_binary, cleanup_work_dir, compile_error_payload
from ws_bridge import WsPtyBridge, start_pty_bridge

logger = logging.getLogger(__name__)

SendJson = Callable[[dict], None]


class WsState(str, Enum):
    IDLE = "idle"
    COMPILING = "compiling"
    EXECUTING = "executing"


def validate_compile_and_run(message: dict) -> tuple[str | None, str | None]:
    code = message.get("code")
    if not isinstance(code, str) or not code.strip():
        return None, "Campo 'code' obrigatorio e nao vazio"
    stripped = code.strip()
    if len(stripped.encode("utf-8")) > Config.max_code_bytes():
        return None, f"Codigo excede o limite de {Config.MAX_CODE_KB} KB"
    return stripped, None


def validate_stdin(message: dict) -> tuple[str | None, str | None]:
    data = message.get("data")
    if not isinstance(data, str):
        return None, "Campo 'data' obrigatorio (string UTF-8)"
    return data, None


class WsRunSession:
    """Estado por conexao WebSocket: compile_and_run -> bridge PTY (PRD §9.2.3)."""

    def __init__(self, user_id: str, send_json: SendJson):
        self.user_id = user_id
        self._send_json = send_json
        self.state = WsState.IDLE
        self.bridge: WsPtyBridge | None = None
        self.exec_thread: threading.Thread | None = None
        self.work_dir: str | None = None

    def cleanup(self) -> None:
        if self.bridge is not None and self.bridge.active:
            self.bridge.shutdown()
        if self.exec_thread is not None and self.exec_thread.is_alive():
            self.exec_thread.join(
                timeout=Config.EXEC_TIMEOUT_S + Config.DOCKER_STOP_TIMEOUT_S + 5
            )
        cleanup_work_dir(self.work_dir)
        self.work_dir = None
        self.bridge = None
        self.exec_thread = None
        self.state = WsState.IDLE

    def poll_exec_finished(self) -> None:
        if self.state != WsState.EXECUTING or self.exec_thread is None:
            return
        if self.exec_thread.is_alive():
            return
        self.exec_thread.join(timeout=1)
        cleanup_work_dir(self.work_dir)
        self.work_dir = None
        self.bridge = None
        self.exec_thread = None
        self.state = WsState.IDLE

    def handle_message(self, message: dict) -> None:
        self.poll_exec_finished()

        msg_type = message.get("type")
        if msg_type == "ping":
            self._send_json({"type": "pong"})
            return

        if msg_type == "compile_and_run":
            self._handle_compile_and_run(message)
            return

        if msg_type == "stdin":
            data, error = validate_stdin(message)
            if error:
                logger.warning("WS stdin invalido user_id=%s: %s", self.user_id, error)
                return
            if self.state != WsState.EXECUTING or self.bridge is None or not self.bridge.active:
                logger.warning("WS stdin ignorado em %s user_id=%s", self.state.value, self.user_id)
                return
            self.bridge.enqueue({"type": "stdin", "data": data})
            return

        if msg_type == "stop":
            if self.state != WsState.EXECUTING or self.bridge is None or not self.bridge.active:
                logger.warning("WS stop ignorado em %s user_id=%s", self.state.value, self.user_id)
                return
            self.bridge.enqueue({"type": "stop"})
            return

        logger.warning(
            "WS mensagem desconhecida: type=%s user_id=%s",
            msg_type,
            self.user_id,
        )

    def _handle_compile_and_run(self, message: dict) -> None:
        if self.state != WsState.IDLE:
            logger.warning(
                "compile_and_run ignorado em %s user_id=%s",
                self.state.value,
                self.user_id,
            )
            return

        code, error = validate_compile_and_run(message)
        if error:
            logger.warning("compile_and_run invalido user_id=%s: %s", self.user_id, error)
            self._send_json({"type": "internal_error", "message": error})
            return

        self.state = WsState.COMPILING
        self._send_json({"type": "compile_started"})

        result = build_binary(code)
        if not result.get("success"):
            self._emit_build_failure(result)
            self.state = WsState.IDLE
            return

        self._send_json({"type": "asm_generated", "asm": result["asm"]})
        self.work_dir = result["work_dir"]
        self.state = WsState.EXECUTING
        try:
            self.bridge, self.exec_thread = start_pty_bridge(
                self._send_json,
                self.work_dir,
            )
        except Exception as exc:
            logger.exception("Falha ao iniciar execucao user_id=%s", self.user_id)
            self._send_json(
                {
                    "type": "internal_error",
                    "message": (
                        f"Falha ao iniciar sandbox: {exc}. "
                        "Verifique Docker Desktop e a imagem simples-runner:latest."
                    ),
                }
            )
            cleanup_work_dir(self.work_dir)
            self.work_dir = None
            self.state = WsState.IDLE
            return
        logger.info("Execucao iniciada user_id=%s work_dir=%s", self.user_id, self.work_dir)

    def _emit_build_failure(self, result: dict) -> None:
        errors = result.get("errors")
        if errors:
            for err in errors:
                self._send_json(compile_error_payload(err))
            return

        # Safety net — fallback for callers that don't use the errors format
        stderr = result.get("stderr", "")
        self._send_json(
            {
                "type": "internal_error",
                "message": stderr or "Falha desconhecida no build",
            }
        )
