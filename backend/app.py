from flask import Flask, g, jsonify

from auth import verify_jwt
from config import Config

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
