import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";

import { CodeEditor } from "../components/CodeEditor";
import { IdeLayout } from "../components/IdeLayout";
import { IdeToolbar } from "../components/IdeToolbar";
import { NasmViewer } from "../components/NasmViewer";
import { ThreePanelLayout } from "../components/ThreePanelLayout";
import { useAuth } from "../contexts/AuthContext";
import { compileSimples } from "../lib/compileApi";
import type { CompileError } from "../lib/compileTypes";
import { DEFAULT_SIMPLES_CODE } from "../lib/monacoConfig";
import {
  DEFAULT_NASM_PLACEHOLDER,
  formatCompileErrorsForNasm,
} from "../lib/nasm/nasmConfig";
import type { RunState } from "../lib/runState";

export function HomePage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState(DEFAULT_SIMPLES_CODE);
  const [nasmCode, setNasmCode] = useState(DEFAULT_NASM_PLACEHOLDER);
  const [compileErrors, setCompileErrors] = useState<CompileError[]>([]);
  const [runState, setRunState] = useState<RunState>("idle");
  const [toolbarStatus, setToolbarStatus] = useState<string | null>(null);

  async function handleSignOut() {
    await signOut();
    navigate("/login", { replace: true });
  }

  const handleCodeChange = useCallback((nextCode: string) => {
    setCode(nextCode);
    setCompileErrors([]);
    setToolbarStatus(null);
  }, []);

  const handleRun = useCallback(async () => {
    if (runState === "compiling") {
      return;
    }

    setRunState("compiling");
    setToolbarStatus(null);

    try {
      const result = await compileSimples(code);

      if (result.success) {
        setCompileErrors([]);
        setNasmCode(result.asm);
        return;
      }

      if (result.source === "compiler") {
        setCompileErrors(result.errors);
        setNasmCode(formatCompileErrorsForNasm(result.errors));
        return;
      }

      setCompileErrors([]);
      setToolbarStatus(`> ${result.errors[0]?.message ?? "Erro de servidor"}`);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Falha ao comunicar com o servidor";
      setCompileErrors([]);
      setToolbarStatus(`> ${message}`);
    } finally {
      setRunState("idle");
    }
  }, [code, runState]);

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
      />
    </IdeLayout>
  );
}
