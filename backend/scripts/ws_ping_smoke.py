#!/usr/bin/env python3
"""Smoke test manual: /ws/run autenticado + ping/pong."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
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


def _build_token(explicit: str | None) -> str:
    if explicit:
        return explicit.strip()
    _load_dotenv()
    secret = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
    if not secret:
        print(
            "Erro: passe --token ou defina SUPABASE_JWT_SECRET (repo/.env).",
            file=sys.stderr,
        )
        sys.exit(1)
    import jwt

    return jwt.encode(
        {"sub": "ws-smoke-test", "aud": "authenticated"},
        secret,
        algorithm="HS256",
    )


def _check_server_supabase(ws_url: str) -> bool:
    """Confere se o processo em localhost carregou repo/.env."""
    if not ws_url.startswith("ws://localhost") and not ws_url.startswith("ws://127.0.0.1"):
        return True
    http_base = ws_url.replace("ws://", "http://", 1).split("/ws/")[0]
    try:
        with urllib.request.urlopen(f"{http_base}/api/health", timeout=3) as resp:
            data = json.loads(resp.read().decode())
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"FAIL: servidor inacessivel em {http_base} ({exc})", file=sys.stderr)
        print("  -> Terminal A: cd backend && python app.py", file=sys.stderr)
        return False
    status = data.get("components", {}).get("supabase", {}).get("status")
    if status != "ok":
        print(
            "FAIL: Terminal A rodando SEM Supabase (.env nao carregado).\n"
            "  1. Ctrl+C no Terminal A\n"
            "  2. cd compiladoress\\backend && python app.py\n"
            "  3. Confirme compiladoress\\.env (SUPABASE_URL + SUPABASE_JWT_SECRET)",
            file=sys.stderr,
        )
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test WebSocket /ws/run")
    parser.add_argument(
        "--url",
        default="ws://localhost:5000/ws/run",
        help="URL do WebSocket (default: backend direto)",
    )
    parser.add_argument("--token", help="JWT Supabase (Bearer)")
    args = parser.parse_args()

    try:
        from websocket import create_connection
    except ImportError:
        print("Instale: pip install websocket-client", file=sys.stderr)
        return 1

    token = _build_token(args.token)
    query = urlencode({"token": token})
    separator = "&" if "?" in args.url else "?"
    ws_url = f"{args.url}{separator}{query}"

    if not _check_server_supabase(args.url):
        return 1

    print(f"Conectando: {args.url} ...")
    try:
        ws = create_connection(ws_url, timeout=10)
    except OSError as exc:
        print(f"FAIL: nao conectou ({exc}). Terminal A rodando python app.py?", file=sys.stderr)
        return 1

    try:
        ws.send(json.dumps({"type": "ping"}))
        raw = ws.recv()
        if not raw:
            print(
                "FAIL: servidor fechou a conexao sem responder.\n"
                "  - Reinicie Terminal A: cd backend && python app.py\n"
                "  - Confirme repo/.env com SUPABASE_URL e SUPABASE_JWT_SECRET\n"
                "  - Ou use JWT real: --token \"eyJ...\"",
                file=sys.stderr,
            )
            return 1
        try:
            reply = json.loads(raw)
        except json.JSONDecodeError:
            print(f"FAIL: resposta nao-JSON: {raw!r}", file=sys.stderr)
            return 1
        if reply.get("type") != "pong":
            print(f"FAIL: esperado pong, recebeu {reply}", file=sys.stderr)
            return 1
        print("OK — ping/pong funcionou")
        return 0
    finally:
        ws.close()


if __name__ == "__main__":
    raise SystemExit(main())
