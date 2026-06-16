"""Estrategia de execucao em sandbox Docker com PTY bridge (PRD §7.3 e §11)."""

import asyncio
import json

from config import Config

try:
    import docker  # type: ignore

    _DOCKER_AVAILABLE = True
except ImportError:
    _DOCKER_AVAILABLE = False


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


def _sandbox_run_kwargs() -> dict:
    """Parametros de containers.run derivados de Config (DRY)."""
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
        "stop_timeout": Config.DOCKER_STOP_TIMEOUT_S,
        "stdin_open": True,
        "tty": True,
        "detach": True,
    }


class PtyExecutionStrategy:
    """Spawna container Docker com TTY e faz bridge bidirecional stdio ↔ WebSocket."""

    def __init__(self, image: str | None = None):
        if not _DOCKER_AVAILABLE:
            raise RuntimeError("docker-py nao instalado (pip install docker)")
        self.image = image or Config.SANDBOX_IMAGE
        self.client = docker.from_env()

    async def execute(self, binary_dir: str, ws, timeout_s: int | None = None) -> dict:
        """Executa binario no sandbox. Integracao WS sera ligada no sprint correspondente."""
        exec_timeout = timeout_s if timeout_s is not None else Config.EXEC_TIMEOUT_S
        stop_timeout = Config.DOCKER_STOP_TIMEOUT_S
        container = None

        try:
            container = self.client.containers.run(
                image=self.image,
                command=["/usr/bin/qemu-i386-static", "/sandbox/programa"],
                volumes={binary_dir: {"bind": "/sandbox", "mode": "ro"}},
                **_sandbox_run_kwargs(),
            )

            sock = container.attach_socket(
                params={"stdin": 1, "stdout": 1, "stderr": 1, "stream": 1}
            )
            sock._sock.setblocking(False)

            loop = asyncio.get_running_loop()
            start = loop.time()

            async def pty_to_ws():
                while True:
                    try:
                        data = await loop.run_in_executor(None, sock._sock.recv, 4096)
                        if not data:
                            break
                        await ws.send(
                            json.dumps(
                                {
                                    "type": "stdout",
                                    "data": data.decode("utf-8", errors="replace"),
                                }
                            )
                        )
                    except BlockingIOError:
                        await asyncio.sleep(0.01)

            async def ws_to_pty():
                async for message in ws:
                    msg = json.loads(message)
                    if msg["type"] == "stdin":
                        sock._sock.sendall(msg["data"].encode("utf-8"))
                    elif msg["type"] == "stop":
                        container.kill(signal="SIGTERM")
                        break

            try:
                await asyncio.wait_for(
                    asyncio.gather(pty_to_ws(), ws_to_pty()),
                    timeout=exec_timeout,
                )
                timed_out = False
            except asyncio.TimeoutError:
                container.kill(signal="SIGTERM")
                await asyncio.sleep(1)
                container.kill(signal="SIGKILL")
                timed_out = True

            result = container.wait(timeout=stop_timeout + 2)
            return {
                "exit_code": result["StatusCode"],
                "duration_ms": int((loop.time() - start) * 1000),
                "timed_out": timed_out,
            }
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
