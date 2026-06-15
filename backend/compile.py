"""Compila codigo SIMPLES invocando o binario simplesc como subprocesso."""

import os
import re
import subprocess
import tempfile

SIMPLESC_BIN = os.environ.get("SIMPLESC_BIN", "/usr/local/bin/simplesc")

# Formato de erro do simplesc: phase:line:col: message
_ERROR_RE = re.compile(r"^(\w+):(\d+):(\d+):\s*(.+)$")


def _parse_error(line: str) -> dict | None:
    """Converte uma linha de stderr do simplesc em dict estruturado."""
    match = _ERROR_RE.match(line.strip())
    if not match:
        return None
    return {
        "phase": match.group(1),
        "line": int(match.group(2)),
        "column": int(match.group(3)),
        "message": match.group(4),
    }


def compile_code(code: str) -> dict:
    """Compila codigo SIMPLES e retorna dict com 'asm' (sucesso) ou 'errors' (falha).

    Returns:
        {"success": True, "asm": "<nasm assembly>"}  ou
        {"success": False, "errors": [{"phase": ..., "line": ..., "column": ..., "message": ...}]}
    """
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
            timeout=30,
        )

        if proc.returncode == 0 and os.path.isfile(asm_path):
            with open(asm_path, encoding="utf-8") as f:
                asm = f.read()
            return {"success": True, "asm": asm}

        # Compilacao falhou — parse stderr
        errors: list[dict] = []
        for line in proc.stderr.splitlines():
            parsed = _parse_error(line)
            if parsed:
                errors.append(parsed)

        # Fallback: se nenhum erro parseavel, retorna stderr bruto
        if not errors and proc.stderr.strip():
            errors.append(
                {
                    "phase": "unknown",
                    "line": 0,
                    "column": 0,
                    "message": proc.stderr.strip(),
                }
            )

        return {"success": False, "errors": errors}

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "errors": [
                {
                    "phase": "compiler",
                    "line": 0,
                    "column": 0,
                    "message": "Compilacao excedeu o tempo limite de 30 segundos",
                }
            ],
        }
    except FileNotFoundError:
        return {
            "success": False,
            "errors": [
                {
                    "phase": "server",
                    "line": 0,
                    "column": 0,
                    "message": f"Binario do compilador nao encontrado: {SIMPLESC_BIN}",
                }
            ],
        }
    finally:
        # Limpeza dos arquivos temporarios
        for path in (src_path, asm_path):
            try:
                os.unlink(path)
            except OSError:
                pass
