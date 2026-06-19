import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    "Supabase nao configurado: defina VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY",
  );
}

export const supabase = createClient(
  supabaseUrl || "https://placeholder.supabase.co",
  supabaseAnonKey || "placeholder",
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  },
);

export function isSupabaseConfigured(): boolean {
  return Boolean(supabaseUrl && supabaseAnonKey);
}

/** Renova proativamente quando faltam <=5 min para expirar (PRD §12). */
const REFRESH_MARGIN_S = 300;

function accessTokenExpiresAt(session: {
  expires_at?: number;
  access_token: string;
}): number {
  if (session.expires_at && session.expires_at > 0) {
    return session.expires_at;
  }

  try {
    const payload = JSON.parse(
      atob(
        session.access_token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"),
      ),
    ) as { exp?: number };
    return payload.exp ?? 0;
  } catch {
    return 0;
  }
}

/** Retorna access_token valido; renova antes de expirar. Nunca devolve token expirado. */
export async function getFreshAccessToken(): Promise<string | null> {
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error || !session?.access_token) {
    return null;
  }

  const now = Math.floor(Date.now() / 1000);
  const expiresAt = accessTokenExpiresAt(session);

  if (expiresAt > now + REFRESH_MARGIN_S) {
    return session.access_token;
  }

  const { data: refreshed, error: refreshError } =
    await supabase.auth.refreshSession();
  const nextToken = refreshed.session?.access_token;
  if (nextToken) {
    return nextToken;
  }

  if (refreshError) {
    console.warn("Supabase refreshSession:", refreshError.message);
  }

  // Rede falhou mas o token ainda nao expirou — tenta usar uma vez
  if (expiresAt > now) {
    return session.access_token;
  }

  return null;
}

export async function getAccessToken(): Promise<string | null> {
  return getFreshAccessToken();
}
