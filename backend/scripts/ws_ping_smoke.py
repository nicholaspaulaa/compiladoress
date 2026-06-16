#!/usr/bin/env python3
"""Smoke test manual: /ws/run autenticado + ping/pong.

Uso (backend rodando em localhost:5000):
  cd backend
  pip install -r requirements-dev.txt
  # Com JWT real (copie do DevTools apos login):
  python scripts/ws_ping_smoke.py --token "eyJ..."
  # Ou com SUPABASE_JWT_SECRET no ambiente (gera JWT de teste HS256):
  set SUPABASE_JWT_SECRET=...   # PowerShell: $env:SUPABASE_JWT_SECRET="..."
  python scripts/ws_ping_smoke.py
  # Via nginx:
  python scripts/ws_ping_smoke.py --url ws://localhost/ws/run
"""

from __future__ import annotations

import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def _build_token(explicit: str | None) -> str:
    if explicit:
        return explicit.strip()
    secret = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
    if not secret:
        print(
            "Erro: passe --token ou defina SUPABASE_JWT_SECRET no ambiente.",
            file=sys.stderr,
        )
        sys.exit(1)
    import jwt

    return jwt.encode(
        {"sub": "ws-smoke-test", "aud": "authenticated"},
        secret,
        algorithm="HS256",
    )


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
    separator = "&" if "?" in args.url else "?"
    ws_url = f"{args.url}{separator}token={token}"

    print(f"Conectando: {args.url} ...")
    ws = create_connection(ws_url, timeout=10)
    try:
        ws.send(json.dumps({"type": "ping"}))
        raw = ws.recv()
        reply = json.loads(raw)
        if reply.get("type") != "pong":
            print(f"FAIL: esperado pong, recebeu {reply}", file=sys.stderr)
            return 1
        print("OK — ping/pong funcionou")
        return 0
    finally:
        ws.close()


if __name__ == "__main__":
    raise SystemExit(main())
