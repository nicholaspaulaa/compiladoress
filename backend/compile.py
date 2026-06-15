"""Compila codigo SIMPLES invocando o binario simplesc como subprocesso."""

import os
import subprocess
import tempfile

from config import Config
from error_parser import make_error, parse_errors

SIMPLESC_BIN = os.environ.get("SIMPLESC_BIN", "/usr/local/bin/simplesc")


def compile_code(code: str) -> dict:
    """Compila codigo SIMPLES e retorna dict com 'asm' (sucesso) ou 'errors' (falha)."""
    timeout_s = Config.COMPILE_TIMEOUT_S

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".simples", delete=False, encoding="utf-8"
    ) as src:
        src.write(code)
        src_path = src.name

    asm_path = src_path + ".asm"

    try:
        proc = subprocess.run(
            [SIMPLESC_BIN, src_path, "-o", asm_path],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )

        if proc.returncode == 0 and os.path.isfile(asm_path):
            with open(asm_path, encoding="utf-8") as f:
                asm = f.read()
            return {"success": True, "asm": asm}

        errors = parse_errors(proc.stderr)
        if not errors and proc.stderr.strip():
            errors = [make_error("unknown", proc.stderr.strip())]

        return {"success": False, "errors": errors}

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "errors": [
                make_error(
                    "compiler",
                    f"Compilacao excedeu o tempo limite de {timeout_s} segundos",
                )
            ],
        }
    except FileNotFoundError:
        return {
            "success": False,
            "errors": [
                make_error(
                    "server",
                    f"Binario do compilador nao encontrado: {SIMPLESC_BIN}",
                )
            ],
        }
    finally:
        for path in (src_path, asm_path):
            try:
                os.unlink(path)
            except OSError:
                pass
