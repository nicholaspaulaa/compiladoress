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

/** Retorna access_token da sessao atual; renova so se ja expirou. */
export async function getFreshAccessToken(): Promise<string | null> {
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error || !session?.access_token) {
    return null;
  }

  const now = Math.floor(Date.now() / 1000);
  const expiresAt = session.expires_at ?? 0;

  // Token ainda valido — usa direto (autoRefreshToken cuida da renovacao em background)
  if (expiresAt <= 0 || expiresAt > now + 30) {
    return session.access_token;
  }

  // Expirando em breve ou ja expirou — tenta renovar uma vez, sem deslogar
  const { data: refreshed } = await supabase.auth.refreshSession();
  return refreshed.session?.access_token ?? session.access_token;
}

export async function getAccessToken(): Promise<string | null> {
  return getFreshAccessToken();
}
