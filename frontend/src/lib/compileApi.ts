import { apiFetch } from "./api";
import type { CompileError, CompileResult } from "./compileTypes";

function serverError(message: string): CompileResult {
  return {
    success: false,
    errors: [{ phase: "server", line: 0, column: 0, message }],
  };
}

export async function compileSimples(code: string): Promise<CompileResult> {
  const response = await apiFetch("/api/compile", {
    method: "POST",
    body: JSON.stringify({ code }),
  });

  if (response.ok) {
    const body = (await response.json()) as { asm?: string };
    if (!body.asm) {
      return serverError("Resposta de compilacao invalida");
    }
    return { success: true, asm: body.asm };
  }

  if (response.status === 422) {
    const body = (await response.json()) as { errors?: CompileError[] };
    return {
      success: false,
      errors: body.errors?.length
        ? body.errors
        : [{ phase: "unknown", line: 0, column: 0, message: "Erro de compilacao" }],
    };
  }

  const body = (await response.json().catch(() => ({}))) as {
    message?: string;
  };
  return serverError(body.message ?? "Falha ao compilar codigo");
}
