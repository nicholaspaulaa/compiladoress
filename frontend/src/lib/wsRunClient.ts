import type { CompileError } from "./compileTypes";
import type { WsRunConnection, WsRunHandlers, WsServerMessage } from "./wsRunTypes";

function buildWsRunUrl(token: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const query = new URLSearchParams({ token });
  return `${protocol}//${window.location.host}/ws/run?${query}`;
}

function parseCompileError(message: WsServerMessage): CompileError | null {
  if (message.type !== "compile_error") {
    return null;
  }
  return {
    phase: message.phase ?? "unknown",
    line: message.line ?? 0,
    column: message.column ?? 0,
    message: message.message,
  };
}

function dispatchMessage(
  raw: WsServerMessage,
  handlers: WsRunHandlers,
  setExecuting: (value: boolean) => void,
  markRunSettled: () => void,
): void {
  switch (raw.type) {
    case "compile_started":
      handlers.onCompileStarted();
      break;
    case "compile_error": {
      const error = parseCompileError(raw);
      if (error) {
        handlers.onCompileError(error);
      }
      setExecuting(false);
      markRunSettled();
      break;
    }
    case "asm_generated":
      handlers.onAsmGenerated(raw.asm);
      break;
    case "exec_started":
      setExecuting(true);
      handlers.onExecStarted();
      break;
    case "stdout":
    case "stderr":
      handlers.onStdout(raw.data);
      break;
    case "exit":
      setExecuting(false);
      markRunSettled();
      handlers.onExit(raw.code, raw.duration_ms, raw.stopped);
      break;
    case "timeout":
      setExecuting(false);
      markRunSettled();
      handlers.onTimeout(raw.limit_s);
      break;
    case "internal_error":
      setExecuting(false);
      markRunSettled();
      handlers.onInternalError(raw.message);
      break;
    case "pong":
      break;
    default:
      break;
  }
}

export function createWsRunConnection(
  token: string,
  handlers: WsRunHandlers,
): WsRunConnection {
  let ws: WebSocket | null = null;
  let executing = false;
  let closed = false;
  let runSettled = false;
  let pendingCompileCode: string | null = null;

  const setExecuting = (value: boolean) => {
    executing = value;
  };

  const markRunSettled = () => {
    runSettled = true;
  };

  const sendJson = (payload: Record<string, unknown>) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
    }
  };

  const flushPendingCompile = () => {
    if (pendingCompileCode === null) {
      return;
    }
    sendJson({ type: "compile_and_run", code: pendingCompileCode });
    pendingCompileCode = null;
  };

  const url = buildWsRunUrl(token);
  let opened = false;
  ws = new WebSocket(url);

  ws.onopen = () => {
    opened = true;
    flushPendingCompile();
  };

  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(String(event.data)) as WsServerMessage;
      dispatchMessage(message, handlers, setExecuting, markRunSettled);
    } catch {
      handlers.onInternalError("Resposta WebSocket invalida");
    }
  };

  ws.onerror = () => {
    // Mensagem detalhada vem em onclose (code/reason)
  };

  ws.onclose = (event) => {
    if (!closed) {
      setExecuting(false);
      if (!opened) {
        handlers.onInternalError(
          "Backend indisponivel — suba o servidor: cd backend && python app.py (porta 5000)",
        );
      } else if (event.code === 4403) {
        handlers.onInternalError("Token invalido ou expirado");
      } else if (event.code === 1006 && !runSettled) {
        handlers.onInternalError(
          "Conexao caiu — verifique Docker Desktop e clique Run novamente",
        );
      } else if (!runSettled && event.code !== 1000 && event.code !== 1001) {
        handlers.onInternalError(
          `WebSocket fechou inesperadamente (code=${event.code})`,
        );
      }
      handlers.onDisconnected();
    }
  };

  return {
    get canSendStdin() {
      return executing && ws?.readyState === WebSocket.OPEN;
    },
    sendCompileAndRun(code: string) {
      if (ws?.readyState === WebSocket.OPEN) {
        sendJson({ type: "compile_and_run", code });
        return;
      }
      pendingCompileCode = code;
    },
    sendStdin(data: string) {
      if (!this.canSendStdin) {
        return;
      }
      sendJson({ type: "stdin", data });
    },
    sendStop() {
      sendJson({ type: "stop" });
    },
    close() {
      closed = true;
      executing = false;
      ws?.close();
      ws = null;
    },
  };
}
