export interface CompileError {
  phase: string;
  line: number;
  column: number;
  message: string;
  limit_s?: number;
}

export type CompileFailureSource = "compiler" | "http" | "network";

export type CompileResult =
  | { success: true; asm: string }
  | { success: false; errors: CompileError[]; source: CompileFailureSource };
