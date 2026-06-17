"""Estrategia de execucao em sandbox Docker com PTY (PRD §7.3 e §11)."""

from __future__ import annotations

import io
import logging
import os
import select
import tarfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from config import Config
from metrics import ACTIVE_SANDBOXES

try:
    import docker  # type: ignore

    _DOCKER_AVAILABLE = True
except ImportError:
    _DOCKER_AVAILABLE = False

logger = logging.getLogger(__name__)

MessagePoll = Callable[[], dict | None]
StdoutHandler = Callable[[str], None]


@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int
    duration_ms: int
    timed_out: bool
    stopped: bool = False


def docker_available() -> bool:
    return _DOCKER_AVAILABLE


def get_sandbox_security_config() -> dict:
    """Retorna configuracao de hardening do sandbox para auditoria (PRD §11.2)."""
    return {
        "network_mode": {
            "value": "none",
            "rationale": "Camada 2: isola o container de qualquer rede.",
        },
        "read_only": {
            "value": True,
            "rationale": "Camada 3: filesystem imutavel no container.",
        },
        "tmpfs": {
            "value": Config.sandbox_tmpfs(),
            "rationale": "Camada 3: unica area gravavel em RAM com limite configuravel.",
        },
        "mem_limit": {
            "value": Config.sandbox_mem_limit(),
            "rationale": "Camada 4: limite rigido de memoria.",
        },
        "memswap_limit": {
            "value": Config.sandbox_mem_limit(),
            "rationale": "Camada 4: swap desabilitado.",
        },
        "cpu_quota": {
            "value": Config.SANDBOX_CPU_QUOTA,
            "rationale": "Camada 5: quota de CPU via cgroups.",
        },
        "pids_limit": {
            "value": Config.SANDBOX_PIDS_LIMIT,
            "rationale": "Camada 6: protecao contra fork bomb.",
        },
        "user": {
            "value": Config.SANDBOX_USER,
            "rationale": "Camada 7: execucao non-root.",
        },
        "cap_drop": {
            "value": ["ALL"],
            "rationale": "Camada 8: remove todas as capabilities Linux.",
        },
        "stop_timeout": {
            "value": Config.DOCKER_STOP_TIMEOUT_S,
            "rationale": "Camada [3] de timeout: hard limit do Docker daemon.",
        },
    }


def sandbox_run_kwargs() -> dict:
    """Parametros de containers.create/run derivados de Config (DRY)."""
    return {
        "network_mode": "none",
        "read_only": True,
        "tmpfs": Config.sandbox_tmpfs(),
        "mem_limit": Config.sandbox_mem_limit(),
        "memswap_limit": Config.sandbox_mem_limit(),
        "cpu_quota": Config.SANDBOX_CPU_QUOTA,
        "pids_limit": Config.SANDBOX_PIDS_LIMIT,
        "user": Config.SANDBOX_USER,
        "cap_drop": ["ALL"],
        "stdin_open": True,
        "tty": True,
        "detach": True,
    }


def _build_dir_tar(dir_path: str, *, dest_prefix: str = "") -> bytes:
    """Empacota arquivos do build para put_archive no runner (sem bind mount do host)."""
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as tar:
        for name in os.listdir(dir_path):
            full = os.path.join(dir_path, name)
            arcname = f"{dest_prefix}/{name}" if dest_prefix else name
            info = tar.gettarinfo(full, arcname=arcname)
            # Runner executa como nobody (65534) — arquivos precisam ser legiveis
            info.uid = 65534
            info.gid = 65534
            info.mode = 0o755
            with open(full, "rb") as handle:
                tar.addfile(info, handle)
    stream.seek(0)
    return stream.read()


def sandbox_staging_kwargs() -> dict:
    """Kwargs do runner: rootfs gravavel para put_archive em /sandbox (WORKDIR da imagem)."""
    return {**sandbox_run_kwargs(), "read_only": False}


class ExecutionStrategy(ABC):
    """Interface Strategy para execucao sandbox (PRD §7.4)."""

    @abstractmethod
    def execute(
        self,
        binary_dir: str,
        on_stdout: StdoutHandler,
        poll_message: MessagePoll,
        timeout_s: int | None = None,
    ) -> ExecutionResult:
        raise NotImplementedError


class PtyExecutionStrategy(ExecutionStrategy):
    """Executa binario i386 no simples-runner via qemu + attach_socket PTY."""

    QEMU_COMMAND = ["/usr/bin/qemu-i386-static", "/sandbox/programa"]
    SANDBOX_DIR = "/sandbox"
    ATTACH_PARAMS = {"stdin": 1, "stdout": 1, "stderr": 1, "stream": 1}

    def __init__(self, image: str | None = None, client=None):
        if client is None and not _DOCKER_AVAILABLE:
            raise RuntimeError("docker-py nao instalado (pip install docker)")
        self.image = image or Config.SANDBOX_IMAGE
        self.client = client if client is not None else docker.from_env()

    def execute(
        self,
        binary_dir: str,
        on_stdout: StdoutHandler,
        poll_message: MessagePoll,
        timeout_s: int | None = None,
    ) -> ExecutionResult:
        exec_timeout = timeout_s if timeout_s is not None else Config.EXEC_TIMEOUT_S
        stop_timeout = Config.DOCKER_STOP_TIMEOUT_S
        container = None
        attach = None
        start = time.monotonic()
        timed_out = False
        stopped = False

        try:
            container = self.client.containers.create(
                image=self.image,
                command=self.QEMU_COMMAND,
                **sandbox_staging_kwargs(),
            )
            container.put_archive("/", _build_dir_tar(binary_dir, dest_prefix="sandbox"))
            container.start()
            ACTIVE_SANDBOXES.inc()

            attach = container.attach_socket(params=self.ATTACH_PARAMS)
            attach._sock.setblocking(False)

            deadline = start + exec_timeout
            while True:
                if time.monotonic() >= deadline:
                    timed_out = True
                    container.kill(signal="SIGTERM")
                    time.sleep(1)
                    container.kill(signal="SIGKILL")
                    break

                message = poll_message()
                if message:
                    msg_type = message.get("type")
                    if msg_type == "stdin":
                        data = message.get("data", "")
                        if isinstance(data, str):
                            attach._sock.sendall(data.encode("utf-8"))
                    elif msg_type == "stop":
                        stopped = True
                        container.kill(signal="SIGTERM")
                        break

                readable, _, _ = select.select([attach._sock], [], [], 0.05)
                if readable:
                    chunk = attach._sock.recv(4096)
                    if not chunk:
                        break
                    on_stdout(chunk.decode("utf-8", errors="replace"))

                container.reload()
                if container.status != "running":
                    break

            wait_result = container.wait(timeout=stop_timeout + 2)
            exit_code = wait_result.get("StatusCode", 1)
            return ExecutionResult(
                exit_code=exit_code,
                duration_ms=int((time.monotonic() - start) * 1000),
                timed_out=timed_out,
                stopped=stopped,
            )
        finally:
            if container is not None:
                ACTIVE_SANDBOXES.dec()
            if attach is not None:
                try:
                    attach.close()
                except Exception:
                    logger.debug("Falha ao fechar attach_socket", exc_info=True)
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    logger.debug("Falha ao remover container sandbox", exc_info=True)
