from flask import Flask, g, jsonify, request

from auth import verify_jwt
from compile import compile_code
from config import Config
from ws_run import sock, ws_run  # noqa: F401 — registra rota via decorator

app = Flask(__name__)
sock.init_app(app)


@app.route("/api/health")
def health():
    """Publico — sem JWT (PRD RF20)."""
    supabase_status = "ok" if Config.supabase_configured() else "unconfigured"
    return jsonify(
        {
            "status": "ok",
            "service": "backend",
            "components": {
                "supabase": {"status": supabase_status},
            },
        }
    )


@app.route("/api/auth/verify", methods=["POST"])
@verify_jwt
def auth_verify():
    """Valida JWT; usado pelo frontend apos login (PRD §9.1)."""
    return jsonify(
        {
            "valid": True,
            "user_id": g.user_id,
            "email": g.user_email,
        }
    )


@app.route("/api/compile", methods=["POST"])
@verify_jwt
def compile_endpoint():
    """Compila codigo SIMPLES e retorna NASM ou erros estruturados (PRD §9.1, RF05)."""
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "bad_request", "message": "Corpo JSON obrigatorio"}), 400

    code = body.get("code")
    if not code or not isinstance(code, str) or not code.strip():
        return jsonify({"error": "bad_request", "message": "Campo 'code' obrigatorio e nao vazio"}), 400

    result = compile_code(code.strip())

    if result.get("success"):
        return jsonify({"asm": result["asm"]}), 200

    return jsonify({"errors": result["errors"]}), 422


if __name__ == "__main__":
    if not Config.supabase_configured():
        print(
            "AVISO: Supabase nao configurado (repo/.env). "
            "WebSocket /ws/run e endpoints protegidos vao rejeitar tokens.",
            flush=True,
        )
    # Dev: Werkzeug + flask-sock. Producao: gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker
    app.run(host="0.0.0.0", port=5000)
