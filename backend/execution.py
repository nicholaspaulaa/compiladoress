"""Estrategia de execucao em sandbox Docker com PTY bridge (PRD §7.3 e §11).

Timeouts em tres camadas (defense in depth, PRD §11.3):
  [1] Compile timeout     — subprocess.run(timeout=COMPILE_TIMEOUT_S)        (compile.py)
  [2] Wall-clock timeout  — asyncio.wait_for(exec, timeout=EXEC_TIMEOUT_S)   (este modulo)
  [3] Hard limit Docker   — stop_timeout=DOCKER_STOP_TIMEOUT_S               (este modulo)

A camada [3] e a rede de seguranca: mesmo que [2] falhe (ex.: o loop asyncio
trave), o Docker forcara SIGKILL apos stop_timeout segundos, garantindo que
o container nao sobreviva indefinidamente.
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


class ExecutionStrategy:
    """Interface base para estrategias de execucao (Strategy pattern — PRD §7.4)."""

    async def execute(self, binary_dir: str, ws, timeout_s: int) -> dict:
        raise NotImplementedError


class PtyExecutionStrategy:
    """Spawna container Docker com TTY e faz bridge bidirecional stdio ↔ WebSocket.

    O container e criado com stop_timeout = DOCKER_STOP_TIMEOUT_S (default 12s).
    Esse e o hard limit do Docker — se o container nao parar com SIGTERM dentro
    desse prazo, o daemon envia SIGKILL automaticamente (PRD §11.3, camada [3]).
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

        # --- Camada [3]: hard limit Docker ---
        # stop_timeout garante que, mesmo que o orchestrator perca o controle
        # do container, o daemon Docker forcara o encerramento apos N segundos.
        container = self.client.containers.run(
            image=self.image,
            command=["/usr/bin/qemu-i386-static", "/sandbox/programa"],
            volumes={binary_dir: {"bind": "/sandbox", "mode": "ro"}},
            network_mode="none",
            mem_limit="128m",
            memswap_limit="128m",
            cpu_quota=50000,
            pids_limit=64,
            read_only=True,
            tmpfs={"/tmp": "size=8m"},
            user="65534:65534",
            cap_drop=["ALL"],
            stop_timeout=stop_timeout,       # <-- hard limit (PRD §11.3)
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

        # --- Camada [2]: wall-clock timeout ---
        try:
            await asyncio.wait_for(
                asyncio.gather(pty_to_ws(), ws_to_pty()),
                timeout=timeout_s,
            )
            timed_out = False
        except asyncio.TimeoutError:
            # Soft kill: SIGTERM → 1s → SIGKILL
            container.kill(signal="SIGTERM")
            await asyncio.sleep(1)
            container.kill(signal="SIGKILL")
            timed_out = True

        result = container.wait(timeout=stop_timeout + 2)
        container.remove(force=True)

        return {
            "exit_code": result["StatusCode"],
            "duration_ms": int((loop.time() - start) * 1000),
            "timed_out": timed_out,
        }
