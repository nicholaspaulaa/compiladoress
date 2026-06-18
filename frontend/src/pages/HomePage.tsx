import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { CodeEditor } from "../components/CodeEditor";
import { IdeLayout } from "../components/IdeLayout";
import { IdeToolbar } from "../components/IdeToolbar";
import { NasmViewer } from "../components/NasmViewer";
import {
  TerminalPanel,
  type TerminalPanelHandle,
} from "../components/TerminalPanel";
import { ThreePanelLayout } from "../components/ThreePanelLayout";
import { useAuth } from "../contexts/AuthContext";
import type { CompileError } from "../lib/compileTypes";
import { DEFAULT_SIMPLES_CODE } from "../lib/monacoConfig";
import {
  DEFAULT_NASM_PLACEHOLDER,
  formatCompileErrorsForNasm,
} from "../lib/nasm/nasmConfig";
import type { RunState } from "../lib/runState";
import { getFreshAccessToken } from "../lib/supabase";
import { createWsRunConnection } from "../lib/wsRunClient";
import type { WsRunConnection } from "../lib/wsRunTypes";

export function HomePage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState(DEFAULT_SIMPLES_CODE);
  const [nasmCode, setNasmCode] = useState(DEFAULT_NASM_PLACEHOLDER);
  const [compileErrors, setCompileErrors] = useState<CompileError[]>([]);
  const [runState, setRunState] = useState<RunState>("idle");
  const [toolbarStatus, setToolbarStatus] = useState<string | null>(null);

  const terminalRef = useRef<TerminalPanelHandle>(null);
  const wsRef = useRef<WsRunConnection | null>(null);
  const compileErrorsRef = useRef<CompileError[]>([]);
  const stoppingRef = useRef(false);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, []);

  async function handleSignOut() {
    wsRef.current?.close();
    wsRef.current = null;
    await signOut();
    navigate("/login", { replace: true });
  }

  const handleCodeChange = useCallback((nextCode: string) => {
    setCode(nextCode);
    setCompileErrors([]);
    setToolbarStatus(null);
  }, []);

  const finishRun = useCallback(() => {
    stoppingRef.current = false;
    setRunState("idle");
    wsRef.current = null;
  }, []);

  const handleTerminalInput = useCallback((data: string) => {
    wsRef.current?.sendStdin(data);
  }, []);

  const handleStop = useCallback(() => {
    if (runState !== "executing" || !wsRef.current || stoppingRef.current) {
      return;
    }

    stoppingRef.current = true;
    setToolbarStatus("> parando execucao...");
    wsRef.current.sendStop();
  }, [runState]);

  const handleRun = useCallback(async () => {
    if (runState !== "idle") {
      return;
    }

    setRunState("compiling");
    setToolbarStatus(null);
    setCompileErrors([]);
    compileErrorsRef.current = [];

    const token = await getFreshAccessToken();
    if (!token) {
      setToolbarStatus("> Sessao expirada — faca login novamente");
      setRunState("idle");
      return;
    }

    try {
      const health = await fetch("/api/health");
      if (!health.ok) {
        throw new Error("Backend indisponivel");
      }
    } catch {
      const hint = "Backend indisponivel — suba: cd backend && python app.py";
      setToolbarStatus(`> ${hint}`);
      terminalRef.current?.clear();
      terminalRef.current?.writeln(`> ${hint}`);
      setRunState("idle");
      return;
    }

    terminalRef.current?.clear();
    terminalRef.current?.write("> compile_and_run via WebSocket...\r\n");

    wsRef.current?.close();

    const connection = createWsRunConnection(token, {
      onCompileStarted: () => {
        setRunState("compiling");
      },
      onCompileError: (error) => {
        compileErrorsRef.current = [...compileErrorsRef.current, error];
        setCompileErrors(compileErrorsRef.current);
        setNasmCode(formatCompileErrorsForNasm(compileErrorsRef.current));
        terminalRef.current?.writeln(`> erro: ${error.message}`);
        finishRun();
      },
      onAsmGenerated: (asm) => {
        setCompileErrors([]);
        setNasmCode(asm);
        setRunState("executing");
      },
      onExecStarted: () => {
        setRunState("executing");
        terminalRef.current?.focus();
      },
      onStdout: (data) => {
        terminalRef.current?.write(data);
      },
      onExit: (code, durationMs, stopped) => {
        if (stopped) {
          terminalRef.current?.writeln(
            `\r\n> interrompido (code=${code}, ${durationMs}ms)`,
          );
        } else {
          terminalRef.current?.writeln(
            `\r\n> fim (code=${code}, ${durationMs}ms)`,
          );
        }
        setToolbarStatus(null);
        finishRun();
      },
      onTimeout: (limitS) => {
        terminalRef.current?.writeln(`\r\n> timeout (${limitS}s)`);
        finishRun();
      },
      onInternalError: (message) => {
        const lower = message.toLowerCase();
        const isAuthError =
          lower.includes("token invalido") ||
          lower.includes("token expirado") ||
          lower.includes("nao autenticado");
        const hint = isAuthError
          ? "Sessao expirada — clique SAIR e entre de novo"
          : message;
        setToolbarStatus(`> ${hint}`);
        terminalRef.current?.writeln(`> ${hint}`);
        finishRun();
      },
      onDisconnected: () => {
        if (runState !== "idle") {
          finishRun();
        }
      },
    });

    wsRef.current = connection;
    connection.sendCompileAndRun(code);
  }, [code, finishRun, runState]);

  return (
    <IdeLayout
      header={
        <header className="retro-header">
          <div className="flex items-center gap-4">
            <h1 className="retro-title text-[0.65rem] sm:text-[0.75rem]">
              SIMPLES EDITOR
            </h1>
            <span className="retro-subtitle hidden text-sm tracking-widest sm:inline">
              &gt; IDE
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="hidden text-lg text-[var(--retro-text-dim)] sm:inline">
              {user?.email}
            </span>
            <button
              type="button"
              onClick={handleSignOut}
              className="retro-btn retro-btn-sm retro-btn-outline"
            >
              SAIR
            </button>
          </div>
        </header>
      }
      toolbar={
        <IdeToolbar
          runState={runState}
          onRun={handleRun}
          onStop={handleStop}
          statusMessage={toolbarStatus}
        />
      }
    >
      <ThreePanelLayout
        editor={
          <CodeEditor
            value={code}
            onChange={handleCodeChange}
            compileErrors={compileErrors}
          />
        }
        nasm={<NasmViewer value={nasmCode} />}
        terminal={
          <TerminalPanel ref={terminalRef} onInput={handleTerminalInput} />
        }
      />
    </IdeLayout>
  );
}
