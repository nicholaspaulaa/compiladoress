import { getFreshAccessToken } from "./supabase";

export async function apiFetch(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<Response> {
  const accessToken = token ?? (await getFreshAccessToken());
  if (!accessToken) {
    throw new Error("Nao autenticado");
  }

  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${accessToken}`);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  return fetch(path, { ...options, headers });
}

export async function verifyAuth(): Promise<{
  valid: boolean;
  user_id: string;
  email: string | null;
}> {
  const token = await getFreshAccessToken();
  if (!token) {
    throw new Error("Sessao expirada — faca login novamente");
  }

  const response = await apiFetch("/api/auth/verify", { method: "POST" }, token);

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message =
      (body as { message?: string }).message ?? "Falha ao verificar token";
    if (message.toLowerCase().includes("expirad")) {
      throw new Error("Sessao expirada — faca login novamente");
    }
    if (message.toLowerCase().includes("invalid")) {
      throw new Error("Sessao invalida — clique SAIR e entre de novo");
    }
    throw new Error(message);
  }
  return response.json();
}
