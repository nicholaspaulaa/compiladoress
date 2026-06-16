import { useState, type FormEvent } from "react";
import { Link, Navigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { isSupabaseConfigured } from "../lib/supabase";

export function LoginPage() {
  const { session, loading, signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!loading && session) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await signIn(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao entrar");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="retro-screen flex items-center justify-center px-4 py-10">
      <div className="retro-panel w-full max-w-md p-8">
        <div className="mb-8 text-center">
          <p className="retro-subtitle mb-3 text-sm tracking-widest">
            &gt; SISTEMA SIMPLES v1.0
          </p>
          <h1 className="retro-title">SIMPLES EDITOR</h1>
          <p className="retro-blink mt-4 text-lg text-[var(--retro-text-dim)]">
            aguardando credenciais
          </p>
        </div>

        {!isSupabaseConfigured() && (
          <div className="retro-alert retro-alert-warn mb-4" role="alert">
            Supabase nao configurado. Defina{" "}
            <code className="retro-code">VITE_SUPABASE_URL</code> e{" "}
            <code className="retro-code">VITE_SUPABASE_ANON_KEY</code>.
          </div>
        )}

        {error && (
          <div className="retro-alert retro-alert-error mb-4" role="alert">
            &gt; ERRO: {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="email" className="retro-label">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="retro-input"
              placeholder="usuario@dominio.com"
              disabled={submitting}
            />
          </div>

          <div>
            <label htmlFor="password" className="retro-label">
              Senha
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="retro-input"
              placeholder="********"
              disabled={submitting}
            />
          </div>

          <button
            type="submit"
            disabled={submitting || !isSupabaseConfigured()}
            className="retro-btn"
          >
            {submitting ? "CONECTANDO..." : "[ ENTRAR ]"}
          </button>
        </form>

        <p className="mt-6 text-center text-lg">
          <Link to="/api/health" className="retro-link">
            &gt; health_check
          </Link>
        </p>
      </div>
    </div>
  );
}
