"""Pipeline simplesc -> nasm -> ld para execucao sandbox (PRD §7.3)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid

from compile import SIMPLESC_BIN
from config import Config
from error_parser import CompileError, make_error, parse_errors
from metrics import observe_compile_phase, record_compile_errors

NASM_BIN = os.environ.get("NASM_BIN", "nasm")
LD_BIN = os.environ.get("LD_BIN", "i686-linux-gnu-ld")
PROGRAM = "programa"


def cleanup_work_dir(work_dir: str | None) -> None:
    if work_dir and os.path.isdir(work_dir):
        shutil.rmtree(work_dir, ignore_errors=True)


def create_work_dir() -> str:
    base = tempfile.gettempdir()
    path = os.path.join(base, f"sim-{uuid.uuid4().hex}")
    os.makedirs(path, mode=0o700)
    return path


def _run_step(
    cmd: list[str],
    *,
    cwd: str,
    timeout_s: int,
    timeout_phase: str,
) -> subprocess.CompletedProcess[str] | dict:
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "errors": [
                make_error(
                    "compile_timeout",
                    f"Etapa excedeu o tempo limite de {timeout_s} segundos",
                    limit_s=timeout_s,
                )
            ],
        }
    except FileNotFoundError:
        return {
            "success": False,
            "errors": [
                make_error(
                    "server",
                    f"Ferramenta nao encontrada: {cmd[0]}",
                )
            ],
        }


def build_binary(code: str) -> dict:
    """Compila, monta e linka codigo SIMPLES. Retorna work_dir em sucesso."""
    max_bytes = Config.max_code_bytes()
    encoded = code.encode("utf-8")
    if len(encoded) > max_bytes:
        return {
            "success": False,
            "errors": [
                make_error(
                    "server",
                    f"Codigo excede o limite de {Config.MAX_CODE_KB} KB",
                )
            ],
        }

    work_dir = create_work_dir()
    timeout_s = Config.COMPILE_TIMEOUT_S
    src_path = os.path.join(work_dir, f"{PROGRAM}.simples")
    asm_path = os.path.join(work_dir, f"{PROGRAM}.asm")
    obj_path = os.path.join(work_dir, f"{PROGRAM}.o")
    bin_path = os.path.join(work_dir, PROGRAM)

    try:
        with open(src_path, "w", encoding="utf-8") as handle:
            handle.write(code)

        with observe_compile_phase("parser"):
            compile_result = _run_step(
                [SIMPLESC_BIN, src_path, "-o", asm_path],
                cwd=work_dir,
                timeout_s=timeout_s,
                timeout_phase="compile",
            )
        if isinstance(compile_result, dict):
            cleanup_work_dir(work_dir)
            return compile_result

        if compile_result.returncode != 0 or not os.path.isfile(asm_path):
            errors = parse_errors(compile_result.stderr)
            if not errors and compile_result.stderr.strip():
                errors = [make_error("unknown", compile_result.stderr.strip())]
            if not errors:
                errors = [make_error("compiler", "Falha na compilacao SIMPLES")]
            record_compile_errors(errors)
            cleanup_work_dir(work_dir)
            return {"success": False, "errors": errors}

        with open(asm_path, encoding="utf-8") as handle:
            asm = handle.read()

        with observe_compile_phase("nasm"):
            nasm_result = _run_step(
                [NASM_BIN, "-f", "elf32", asm_path, "-o", obj_path],
                cwd=work_dir,
                timeout_s=timeout_s,
                timeout_phase="assemble",
            )
        if isinstance(nasm_result, dict):
            cleanup_work_dir(work_dir)
            return nasm_result

        if nasm_result.returncode != 0 or not os.path.isfile(obj_path):
            cleanup_work_dir(work_dir)
            return {
                "success": False,
                "stage": "assemble",
                "stderr": nasm_result.stderr.strip() or "Falha ao montar NASM",
            }

        with observe_compile_phase("ld"):
            link_result = _run_step(
                [LD_BIN, "-m", "elf_i386", obj_path, "-o", bin_path],
                cwd=work_dir,
                timeout_s=timeout_s,
                timeout_phase="link",
            )
        if isinstance(link_result, dict):
            cleanup_work_dir(work_dir)
            return link_result

        if link_result.returncode != 0 or not os.path.isfile(bin_path):
            cleanup_work_dir(work_dir)
            return {
                "success": False,
                "stage": "link",
                "stderr": link_result.stderr.strip() or "Falha ao linkar binario",
            }

        return {"success": True, "asm": asm, "work_dir": work_dir}
    except OSError as exc:
        cleanup_work_dir(work_dir)
        return {
            "success": False,
            "errors": [make_error("server", f"Erro ao preparar build: {exc}")],
        }


def compile_error_payload(error: CompileError) -> dict:
    payload: dict = {
        "type": "compile_error",
        "message": error["message"],
    }
    phase = error.get("phase")
    if phase:
        payload["phase"] = phase
    line = error.get("line")
    if line is not None:
        payload["line"] = line
    column = error.get("column")
    if column is not None:
        payload["column"] = column
    return payload
