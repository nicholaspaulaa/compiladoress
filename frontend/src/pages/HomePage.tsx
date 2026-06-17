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
import { verifyAuth } from "../lib/api";
import type { CompileError } from "../lib/compileTypes";
import { DEFAULT_SIMPLES_CODE } from "../lib/monacoConfig";
import {
  DEFAULT_NASM_PLACEHOLDER,
  formatCompileErrorsForNasm,
} from "../lib/nasm/nasmConfig";
import type { RunState } from "../lib/runState";
import { getAccessToken } from "../lib/supabase";
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
    setRunState("idle");
    wsRef.current = null;
  }, []);

  const handleTerminalInput = useCallback((data: string) => {
    wsRef.current?.sendStdin(data);
  }, []);

  const handleRun = useCallback(async () => {
    if (runState !== "idle") {
      return;
    }

    setRunState("compiling");
    setToolbarStatus(null);
    setCompileErrors([]);
    compileErrorsRef.current = [];

    const token = await getAccessToken();
    if (!token) {
      setToolbarStatus("> Sessao expirada — faca login novamente");
      setRunState("idle");
      return;
    }

    try {
      await verifyAuth();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Falha ao verificar sessao";
      const hint = message.includes("fetch")
        ? "Backend indisponivel — suba: cd backend && python app.py"
        : message;
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
      },
      onExecStarted: () => {
        setRunState("executing");
        terminalRef.current?.focus();
      },
      onStdout: (data) => {
        terminalRef.current?.write(data);
      },
      onExit: (code, durationMs) => {
        terminalRef.current?.writeln(
          `\r\n> fim (code=${code}, ${durationMs}ms)`,
        );
        finishRun();
      },
      onTimeout: (limitS) => {
        terminalRef.current?.writeln(`\r\n> timeout (${limitS}s)`);
        finishRun();
      },
      onInternalError: (message) => {
        setToolbarStatus(`> ${message}`);
        terminalRef.current?.writeln(`> ${message}`);
        finishRun();
      },
      onDisconnected: () => {
        finishRun();
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
