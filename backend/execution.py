"""Estrategia de execucao em sandbox Docker com PTY bridge (PRD §7.3 e §11).

Sandbox hardening — 9 camadas de defesa (PRD §11.2):
  1. Container descartavel   — container.remove(force=True) ao final
  2. Network isolation        — network_mode="none"
  3. Filesystem read-only     — read_only=True + tmpfs:/tmp (8 MB)
  4. Memoria limitada         — mem_limit="128m", sem swap
  5. CPU limitada             — cpu_quota=50000 (0.5 CPU)
  6. PID limit                — pids_limit=64 (bloqueia fork bomb)
  7. Usuario non-root         — user="65534:65534" (nobody)
  8. Capabilities drop        — cap_drop=["ALL"]
  9. Seccomp                  — perfil padrao do Docker

Timeouts em tres camadas (defense in depth, PRD §11.3):
  [1] Compile timeout     — subprocess.run(timeout=COMPILE_TIMEOUT_S)        (compile.py)
  [2] Wall-clock timeout  — asyncio.wait_for(exec, timeout=EXEC_TIMEOUT_S)   (este modulo)
  [3] Hard limit Docker   — stop_timeout=DOCKER_STOP_TIMEOUT_S               (este modulo)
"""

import asyncio
import json

from config import Config

# docker e opcional — so importa se disponivel (backend final tem o pacote)
try:
    import docker  # type: ignore

    _DOCKER_AVAILABLE = True
except ImportError:
    _DOCKER_AVAILABLE = False


def get_sandbox_security_config() -> dict:
    """Retorna a configuracao de seguranca do sandbox documentada.

    Usada para auditoria e verificacao de que todas as camadas de defesa
    estao configuradas corretamente (PRD §11.2). Cada chave inclui o valor
    e a justificativa de seguranca.

    Returns:
        dict mapeando nome do parametro -> {value, rationale}.
    """
    return {
        "network_mode": {
            "value": "none",
            "rationale": "Camada 2: isola o container de qualquer rede — "
            "impede exfiltracao de dados e ataques de rede (PRD §11.2).",
        },
        "read_only": {
            "value": True,
            "rationale": "Camada 3: filesystem imutavel — impede escrita "
            "maliciosa no sistema de arquivos do container.",
        },
        "tmpfs": {
            "value": {"/tmp": "size=8m"},
            "rationale": "Camada 3: unica area gravavel e em RAM com "
            "limite de 8 MB — evita DoS por preenchimento de disco.",
        },
        "mem_limit": {
            "value": "128m",
            "rationale": "Camada 4: limite rigido de memoria — OOM kill "
            "rapido se o codigo do aluno alocar demais.",
        },
        "memswap_limit": {
            "value": "128m",
            "rationale": "Camada 4: sem swap — evita que o container "
            "contorne o limite de memoria via paginacao.",
        },
        "cpu_quota": {
            "value": 50000,
            "rationale": "Camada 5: 50% de uma CPU (cgroups v1) — "
            "impede que um unico aluno monopolize o host.",
        },
        "pids_limit": {
            "value": 64,
            "rationale": "Camada 6: limite de processos — bloqueia "
            "fork bombs que esgotariam os PIDs do host.",
        },
        "user": {
            "value": "65534:65534",
            "rationale": "Camada 7: usuario nobody (UID/GID 65534) — "
            "sem privilegios de root dentro do container.",
        },
        "cap_drop": {
            "value": ["ALL"],
            "rationale": "Camada 8: remove todas as capabilities Linux — "
            "impede operacoes privilegiadas mesmo se o usuario for root.",
        },
        "stop_timeout": {
            "value": Config.DOCKER_STOP_TIMEOUT_S,
            "rationale": "Camada [3] de timeout: rede de seguranca — "
            "Docker envia SIGKILL apos N segundos se o container nao parar.",
        },
    }


class PtyExecutionStrategy:
    """Spawna container Docker com TTY e faz bridge bidirecional stdio ↔ WebSocket.

    Todas as 9 camadas de hardening do PRD §11.2 sao aplicadas na criacao
    do container. Consulte `get_sandbox_security_config()` para auditoria.
    """

    def __init__(self, image: str = "simples-runner:latest"):
        if not _DOCKER_AVAILABLE:
            raise RuntimeError("docker-py nao instalado (pip install docker)")
        self.image = image
        self.client = docker.from_env()

    async def execute(self, binary_dir: str, ws, timeout_s: int) -> dict:
        """Executa o binario no container sandbox e retorna resultado.

        Args:
            binary_dir: diretorio com o binario compilado (montado em /sandbox).
            ws: conexao WebSocket para bridge stdin/stdout.
            timeout_s: wall-clock timeout (camada [2]).

        Returns:
            dict com exit_code, duration_ms, timed_out.
        """
        stop_timeout = Config.DOCKER_STOP_TIMEOUT_S

        # Container criado com todas as 9 camadas de hardening (PRD §11.2).
        # Cada parametro abaixo tem justificativa de seguranca documentada
        # em `get_sandbox_security_config()`.
        container = self.client.containers.run(
            image=self.image,
            command=["/usr/bin/qemu-i386-static", "/sandbox/programa"],
            volumes={binary_dir: {"bind": "/sandbox", "mode": "ro"}},
            # --- hardening layers ---
            network_mode="none",          # layer 2: network isolation
            read_only=True,               # layer 3: immutable filesystem
            tmpfs={"/tmp": "size=8m"},    # layer 3: writable RAM only, 8 MB cap
            mem_limit="128m",             # layer 4: hard memory cap, no swap
            memswap_limit="128m",         # layer 4: swap disabled
            cpu_quota=50000,              # layer 5: 50% of 1 CPU
            pids_limit=64,                # layer 6: fork-bomb protection
            user="65534:65534",           # layer 7: nobody (non-root)
            cap_drop=["ALL"],             # layer 8: drop all capabilities
            # layer 9: seccomp — Docker default profile
            # --- timeout layer [3] ---
            stop_timeout=stop_timeout,
            # --- I/O config ---
            stdin_open=True,
            tty=True,
            detach=True,
        )

        sock = container.attach_socket(
            params={"stdin": 1, "stdout": 1, "stderr": 1, "stream": 1}
        )
        sock._sock.setblocking(False)

        loop = asyncio.get_event_loop()
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
                timeout=timeout_s,
            )
            timed_out = False
        except asyncio.TimeoutError:
            container.kill(signal="SIGTERM")
            await asyncio.sleep(1)
            container.kill(signal="SIGKILL")
            timed_out = True

        result = container.wait(timeout=stop_timeout + 2)
        container.remove(force=True)  # layer 1: disposable container

        return {
            "exit_code": result["StatusCode"],
            "duration_ms": int((loop.time() - start) * 1000),
            "timed_out": timed_out,
        }
