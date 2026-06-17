import type { CompileError } from "../compileTypes";

export const DEFAULT_NASM_PLACEHOLDER = `; NASM x32 — aguardando compilacao do codigo SIMPLES
; O assembly gerado pelo simplesc aparecera aqui apos Run.

section .bss
    x resd 1
    y resd 1
    z resd 1

section .text
    global _start

_start:
    ; x := 10
    mov dword [x], 10

    ; y := 20
    mov dword [y], 20

    ; z := x + y
    mov eax, [x]
    add eax, [y]
    mov [z], eax

    ; exit(0)
    mov eax, 1
    xor ebx, ebx
    int 0x80
`;

export function formatCompileErrorsForNasm(errors: CompileError[]): string {
  const lines = errors.map((error) => {
    const location =
      error.line > 0
        ? ` linha ${error.line}${error.column > 0 ? `, col ${error.column}` : ""}`
        : "";
    const phase =
      error.phase && error.phase !== "unknown" ? `[${error.phase}]` : "[erro]";
    return `; ${phase}${location}: ${error.message}`;
  });

  return ["; --- erro de compilacao ---", ...lines].join("\n");
}
