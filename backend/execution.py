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


def create_docker_client():
    """Cliente docker-py com timeout maior (Docker Desktop no Windows pode demorar)."""
    if not _DOCKER_AVAILABLE:
        raise RuntimeError("docker-py nao instalado (pip install docker)")
    return docker.from_env(timeout=Config.DOCKER_API_TIMEOUT_S)


def format_docker_error(exc: BaseException) -> str:
    """Traduz erros comuns do docker-py para mensagem acionavel."""
    msg = str(exc)
    lowered = msg.lower()
    if "read timed out" in lowered or "unixhttpconnectionpool" in lowered:
        return (
            "Falha ao finalizar container (bug conhecido do Docker no Windows). "
            "Clique Run novamente — o programa pode ter executado mesmo assim."
        )
    if "connection refused" in lowered or "no such file" in lowered:
        return "Docker nao esta rodando — abra o Docker Desktop"
    if "not found" in lowered and ("image" in lowered or "pull" in lowered):
        return (
            f"Imagem {Config.SANDBOX_IMAGE} ausente — rode na raiz do projeto: "
            "docker compose build runner_image_build"
        )
    return msg


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
    _DOCKER_RETRIES = 3

    def __init__(self, image: str | None = None, client=None):
        if client is None and not _DOCKER_AVAILABLE:
            raise RuntimeError("docker-py nao instalado (pip install docker)")
        self.image = image or Config.SANDBOX_IMAGE
        self.client = client if client is not None else create_docker_client()

    def _retry_docker(self, operation: str, fn):
        last_exc: BaseException | None = None
        for attempt in range(self._DOCKER_RETRIES):
            try:
                return fn()
            except Exception as exc:
                last_exc = exc
                retryable = "timed out" in str(exc).lower()
                if not retryable or attempt == self._DOCKER_RETRIES - 1:
                    raise
                logger.warning(
                    "Docker %s timeout (tentativa %s/%s), repetindo...",
                    operation,
                    attempt + 1,
                    self._DOCKER_RETRIES,
                )
                time.sleep(0.5 * (attempt + 1))
        if last_exc:
            raise last_exc
        raise RuntimeError(f"Falha em {operation}")

    @staticmethod
    def _drain_stop_messages(poll_message: MessagePoll, pending: list[dict]) -> bool:
        """Drena stops disponiveis; stdin e demais mensagens vao para pending."""
        while True:
            message = poll_message()
            if message is None:
                return False
            if message.get("type") == "stop":
                return True
            pending.append(message)

    @staticmethod
    def _next_message(poll_message: MessagePoll, pending: list[dict]) -> dict | None:
        if pending:
            return pending.pop(0)
        return poll_message()

    @staticmethod
    def _resolve_exit_code(
        container,
        *,
        stop_timeout: int,
        stopped: bool,
        timed_out: bool,
    ) -> int:
        """Obtem exit code sem bloquear varios segundos (Docker Desktop no Windows)."""
        wait_s = 2 if stopped else stop_timeout + 2

        try:
            wait_result = container.wait(timeout=wait_s)
            return int(wait_result.get("StatusCode", 130 if stopped else 1))
        except Exception as exc:
            logger.warning("container.wait falhou, usando State.ExitCode: %s", exc)

        try:
            container.reload()
            state = container.attrs.get("State", {})
            if state.get("Status") == "exited":
                code = state.get("ExitCode")
                return 130 if stopped else (0 if code is None else int(code))
        except Exception as exc:
            logger.warning("container.reload falhou ao ler exit code: %s", exc)

        if stopped:
            return 130
        if timed_out:
            return 1
        return 0

    @staticmethod
    def _kill_container(container, *, force: bool = False) -> None:
        signal = "SIGKILL" if force else "SIGTERM"
        try:
            container.kill(signal=signal)
        except Exception as exc:
            logger.debug("container.kill(%s) falhou: %s", signal, exc)
            if not force:
                try:
                    container.kill(signal="SIGKILL")
                except Exception:
                    pass

    def execute(
        self,
        binary_dir: str,
        on_stdout: StdoutHandler,
        poll_message: MessagePoll,
        timeout_s: int | None = None,
    ) -> ExecutionResult:
        exec_timeout = timeout_s if timeout_s is not None else Config.EXEC_TIMEOUT_S
        stop_timeout = Config.DOCKER_STOP_TIMEOUT_S
        # Camada 2 (PRD §4.1): deadline no loop PTY — backup do asyncio.wait_for no ws_bridge (#32)
        container = None
        attach = None
        start = time.monotonic()
        timed_out = False
        stopped = False
        active_counted = False
        pending: list[dict] = []

        if self._drain_stop_messages(poll_message, pending):
            return ExecutionResult(
                exit_code=130,
                duration_ms=0,
                timed_out=False,
                stopped=True,
            )

        try:
            container = self._retry_docker(
                "create",
                lambda: self.client.containers.create(
                    image=self.image,
                    command=self.QEMU_COMMAND,
                    **sandbox_staging_kwargs(),
                ),
            )

            if self._drain_stop_messages(poll_message, pending):
                container.remove(force=True)
                return ExecutionResult(
                    exit_code=130,
                    duration_ms=int((time.monotonic() - start) * 1000),
                    timed_out=False,
                    stopped=True,
                )

            self._retry_docker(
                "put_archive",
                lambda: container.put_archive(
                    "/", _build_dir_tar(binary_dir, dest_prefix="sandbox")
                ),
            )
            self._retry_docker("start", container.start)
            ACTIVE_SANDBOXES.inc()
            active_counted = True

            attach = container.attach_socket(params=self.ATTACH_PARAMS)
            attach._sock.setblocking(False)

            deadline = start + exec_timeout
            while True:
                if time.monotonic() >= deadline:
                    timed_out = True
                    self._kill_container(container)
                    time.sleep(0.3)
                    self._kill_container(container, force=True)
                    break

                message = self._next_message(poll_message, pending)
                if message:
                    msg_type = message.get("type")
                    if msg_type == "stdin":
                        data = message.get("data", "")
                        if isinstance(data, str):
                            attach._sock.sendall(data.encode("utf-8"))
                    elif msg_type == "stop":
                        stopped = True
                        self._kill_container(container, force=True)
                        break

                readable, _, _ = select.select([attach._sock], [], [], 0.05)
                if readable:
                    chunk = attach._sock.recv(4096)
                    if not chunk:
                        break
                    on_stdout(chunk.decode("utf-8", errors="replace"))

            exit_code = self._resolve_exit_code(
                container,
                stop_timeout=stop_timeout,
                stopped=stopped,
                timed_out=timed_out,
            )
            return ExecutionResult(
                exit_code=exit_code,
                duration_ms=int((time.monotonic() - start) * 1000),
                timed_out=timed_out,
                stopped=stopped,
            )
        except Exception as exc:
            if container is not None and attach is not None:
                try:
                    exit_code = self._resolve_exit_code(
                        container,
                        stop_timeout=stop_timeout,
                        stopped=stopped,
                        timed_out=timed_out,
                    )
                    return ExecutionResult(
                        exit_code=exit_code,
                        duration_ms=int((time.monotonic() - start) * 1000),
                        timed_out=timed_out,
                        stopped=stopped,
                    )
                except Exception:
                    pass
            raise RuntimeError(format_docker_error(exc)) from exc
        finally:
            if active_counted:
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
