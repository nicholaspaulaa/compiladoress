"""Compila codigo SIMPLES invocando o binario simplesc como subprocesso."""

import os
import signal
import subprocess
import tempfile

from config import Config
from error_parser import make_error, parse_errors
from metrics import observe_compile_phase, record_compile_errors

SIMPLESC_BIN = os.environ.get("SIMPLESC_BIN", "/usr/local/bin/simplesc")


# ---------- helpers ----------

def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Mata o processo e toda sua arvore de filhos, depois faz reap (PRD RF15)."""
    try:
        # SIGTERM primeiro para dar chance de cleanup
        proc.terminate()
        try:
            proc.wait(timeout=2)
            return
        except subprocess.TimeoutExpired:
            pass

        # SIGKILL como fallback hard
        proc.kill()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            # Se nem SIGKILL funcionar, enviamos novamente
            try:
                os.kill(proc.pid, signal.SIGKILL)
                proc.wait(timeout=1)
            except (ProcessLookupError, subprocess.TimeoutExpired, OSError):
                pass
    except ProcessLookupError:
        pass


def compile_code(code: str) -> dict:
    """Compila codigo SIMPLES e retorna dict com 'asm' (sucesso) ou 'errors' (falha)."""
    timeout_s = Config.COMPILE_TIMEOUT_S

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".simples", delete=False, encoding="utf-8"
    ) as src:
        src.write(code)
        src_path = src.name

    asm_path = src_path + ".asm"
    proc = None

    try:
        with observe_compile_phase("parser"):
            proc = subprocess.Popen(
                [SIMPLESC_BIN, src_path, "-o", asm_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = proc.communicate(timeout=timeout_s)

        if proc.returncode == 0 and os.path.isfile(asm_path):
            with open(asm_path, encoding="utf-8") as f:
                asm = f.read()
            return {"success": True, "asm": asm}

        errors = parse_errors(stderr)
        if not errors and stderr.strip():
            errors = [make_error("unknown", stderr.strip())]

        record_compile_errors(errors)
        return {"success": False, "errors": errors}

    except subprocess.TimeoutExpired:
        if proc is not None:
            _kill_process_tree(proc)
            try:
                proc.communicate()
            except (OSError, ValueError):
                pass
        errors = [
            make_error(
                "compile_timeout",
                f"Compilacao excedeu o tempo limite de {timeout_s} segundos",
                limit_s=timeout_s,
            )
        ]
        record_compile_errors(errors)
        return {"success": False, "errors": errors}
    except FileNotFoundError:
        errors = [
            make_error(
                "server",
                f"Binario do compilador nao encontrado: {SIMPLESC_BIN}",
            )
        ]
        record_compile_errors(errors)
        return {"success": False, "errors": errors}
    finally:
        for path in (src_path, asm_path):
            try:
                os.unlink(path)
            except OSError:
                pass
