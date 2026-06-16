import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { verifyAuth } from "../lib/api";

export function HomePage() {
  const { user, signOut, getAccessToken } = useAuth();
  const navigate = useNavigate();
  const [verifyResult, setVerifyResult] = useState<string | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  async function handleSignOut() {
    await signOut();
    navigate("/login", { replace: true });
  }

  async function handleVerifyToken() {
    setVerifyResult(null);
    setVerifyError(null);
    setChecking(true);

    try {
      const token = await getAccessToken();
      if (!token) {
        setVerifyError("Nenhum token JWT disponivel na sessao.");
        return;
      }

      const result = await verifyAuth();
      setVerifyResult(
        `JWT OK — user_id: ${result.user_id}, email: ${result.email ?? "—"}`,
      );
    } catch (err) {
      setVerifyError(
        err instanceof Error ? err.message : "Falha ao verificar JWT",
      );
    } finally {
      setChecking(false);
    }
  }

  return (
    <div className="retro-screen min-h-screen">
      <header className="retro-header">
        <h1 className="retro-title text-[0.65rem] sm:text-[0.75rem]">
          SIMPLES EDITOR
        </h1>
        <div className="flex items-center gap-4">
          <span className="hidden text-lg text-[var(--retro-text-dim)] sm:inline">
            {user?.email}
          </span>
          <button
            type="button"
            onClick={handleSignOut}
            className="retro-btn retro-btn-sm retro-btn-outline"
          >
            SAIR
          </button>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-2xl px-6 py-12">
        <div className="retro-panel p-8">
          <p className="retro-subtitle mb-2 text-sm tracking-widest">
            &gt; SESSAO ATIVA
          </p>
          <h2 className="retro-title text-[0.7rem] sm:text-[0.85rem]">
            IDE — PLACEHOLDER
          </h2>
          <p className="mt-4 text-xl leading-relaxed text-[var(--retro-text-dim)]">
            Login realizado com sucesso. O editor Monaco, painel NASM e terminal
            serao integrados nas proximas sprints.
          </p>

          <div className="mt-8 space-y-4 border-t-2 border-[var(--retro-purple)] pt-6">
            <p className="text-lg text-[var(--retro-text-dim)]">
              JWT disponivel via{" "}
              <code className="retro-code">getAccessToken()</code> para chamadas
              autenticadas.
            </p>
            <button
              type="button"
              onClick={handleVerifyToken}
              disabled={checking}
              className="retro-btn retro-btn-sm"
            >
              {checking ? "VERIFICANDO..." : "[ TESTAR JWT ]"}
            </button>

            {verifyResult && (
              <p className="retro-alert retro-alert-success">{verifyResult}</p>
            )}
            {verifyError && (
              <p className="retro-alert retro-alert-error" role="alert">
                &gt; ERRO: {verifyError}
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
