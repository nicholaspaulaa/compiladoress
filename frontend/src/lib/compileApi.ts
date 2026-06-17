import { apiFetch } from "./api";
import type { CompileError, CompileResult } from "./compileTypes";

function serverError(
  message: string,
  source: "http" | "network",
): CompileResult {
  return {
    success: false,
    source,
    errors: [{ phase: "server", line: 0, column: 0, message }],
  };
}

function readErrorMessage(
  body: Record<string, unknown>,
  status: number,
): string {
  if (typeof body.message === "string" && body.message.trim()) {
    return body.message;
  }
  if (typeof body.error === "string" && body.error.trim()) {
    return body.error;
  }
  if (status === 502 || status === 504) {
    return "Backend indisponivel — verifique se o servidor esta rodando (docker compose up ou flask na porta 5000)";
  }
  if (status === 401) {
    return "Sessao expirada — faca login novamente";
  }
  if (status === 503) {
    return "Servidor indisponivel — verifique a configuracao do Supabase no backend";
  }
  return `Falha ao compilar codigo (HTTP ${status})`;
}

export async function compileSimples(code: string): Promise<CompileResult> {
  let response: Response;

  try {
    response = await apiFetch("/api/compile", {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  } catch {
    return serverError(
      "Nao foi possivel conectar ao backend — suba o servidor (porta 5000) ou use docker compose up",
      "network",
    );
  }

  if (response.ok) {
    const body = (await response.json()) as { asm?: string };
    if (!body.asm) {
      return serverError("Resposta de compilacao invalida", "http");
    }
    return { success: true, asm: body.asm };
  }

  const body = (await response.json().catch(() => ({}))) as Record<
    string,
    unknown
  >;

  if (response.status === 422) {
    const errors = body.errors as CompileError[] | undefined;
    return {
      success: false,
      source: "compiler",
      errors: errors?.length
        ? errors
        : [{ phase: "unknown", line: 0, column: 0, message: "Erro de compilacao" }],
    };
  }

  return serverError(readErrorMessage(body, response.status), "http");
}
