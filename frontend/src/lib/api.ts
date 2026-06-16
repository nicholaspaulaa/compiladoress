import { getAccessToken } from "./supabase";

export async function apiFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const token = await getAccessToken();
  if (!token) {
    throw new Error("Nao autenticado");
  }

  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);
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
  const response = await apiFetch("/api/auth/verify", { method: "POST" });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      (body as { message?: string }).message ?? "Falha ao verificar token",
    );
  }
  return response.json();
}
