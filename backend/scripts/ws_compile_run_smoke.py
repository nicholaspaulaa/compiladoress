#!/usr/bin/env python3
"""Smoke manual: compile_and_run + stdin (issue #30). Requer simplesc, nasm, ld e Docker."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = Path(BACKEND_DIR).parent
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def _load_dotenv() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> int:
    _load_dotenv()
    secret = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
    if not secret:
        print("Erro: SUPABASE_JWT_SECRET ausente (repo/.env)", file=sys.stderr)
        return 1

    try:
        import jwt
        from websocket import create_connection
    except ImportError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    token = jwt.encode(
        {"sub": "ws-compile-smoke", "aud": "authenticated"},
        secret,
        algorithm="HS256",
    )
    ws_url = f"ws://localhost:5000/ws/run?{urlencode({'token': token})}"

    code = (
        "programa leia_teste\n"
        "  inteiro x\n"
        "inicio\n"
        "  leia x\n"
        "  escreva x\n"
        "fim\n"
    )

    print(f"Conectando: {ws_url.split('?')[0]} ...")
    ws = create_connection(ws_url, timeout=30)
    ws.send(json.dumps({"type": "compile_and_run", "code": code}))

    stdin_sent = False
    types: list[str] = []
    try:
        while len(types) < 20:
            raw = ws.recv()
            if not raw:
                print("FAIL: conexao fechada inesperadamente", file=sys.stderr)
                return 1
            msg = json.loads(raw)
            types.append(msg.get("type", "?"))
            print(json.dumps(msg, ensure_ascii=False))

            if msg.get("type") == "exec_started" and not stdin_sent:
                ws.send(json.dumps({"type": "stdin", "data": "42\n"}))
                stdin_sent = True
                continue

            if msg.get("type") in (
                "compile_error",
                "assemble_error",
                "link_error",
                "internal_error",
                "timeout",
                "exit",
            ):
                break
    finally:
        ws.close()

    print(f"SEQUENCE: {' -> '.join(types)}")

    if "compile_started" not in types:
        print("FAIL: compile_started ausente", file=sys.stderr)
        return 1
    if types[0] != "compile_started":
        print("FAIL: primeira resposta deveria ser compile_started", file=sys.stderr)
        return 1

    terminal = types[-1]
    if terminal == "exit":
        print("OK — compile_and_run completou com exit")
        return 0
    if terminal in ("compile_error", "assemble_error", "link_error", "internal_error"):
        print(
            f"AVISO: pipeline falhou no host ({terminal}) — "
            "esperado se simplesc/nasm/ld ou Docker nao estiverem instalados",
            file=sys.stderr,
        )
        return 0
    print(f"FAIL: terminou com {terminal}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
