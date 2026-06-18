import type { CompileError } from "./compileTypes";

export type WsServerMessage =
  | { type: "compile_started" }
  | { type: "compile_error"; phase?: string; line?: number; column?: number; message: string }
  | { type: "asm_generated"; asm: string }
  | { type: "exec_started" }
  | { type: "stdout"; data: string }
  | { type: "stderr"; data: string }
  | { type: "exit"; code: number; duration_ms: number; stopped?: boolean }
  | { type: "timeout"; limit_s: number }
  | { type: "internal_error"; message: string }
  | { type: "pong" };

export interface WsRunHandlers {
  onCompileStarted: () => void;
  onCompileError: (error: CompileError) => void;
  onAsmGenerated: (asm: string) => void;
  onExecStarted: () => void;
  onStdout: (data: string) => void;
  onExit: (code: number, durationMs: number, stopped?: boolean) => void;
  onTimeout: (limitS: number) => void;
  onInternalError: (message: string) => void;
  onDisconnected: () => void;
}

export interface WsRunConnection {
  sendCompileAndRun: (code: string) => void;
  sendStdin: (data: string) => void;
  sendStop: () => void;
  close: () => void;
  canSendStdin: boolean;
}
