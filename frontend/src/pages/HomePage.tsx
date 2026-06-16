import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { CodeEditor } from "../components/CodeEditor";
import { IdeLayout } from "../components/IdeLayout";
import { IdeToolbar } from "../components/IdeToolbar";
import { ThreePanelLayout } from "../components/ThreePanelLayout";
import { useAuth } from "../contexts/AuthContext";
import { DEFAULT_SIMPLES_CODE } from "../lib/monacoConfig";
import { MOCK_COMPILE_MS, type RunState } from "../lib/runState";

export function HomePage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState(DEFAULT_SIMPLES_CODE);
  const [runState, setRunState] = useState<RunState>("idle");
  const compileTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (compileTimerRef.current !== null) {
        window.clearTimeout(compileTimerRef.current);
      }
    };
  }, []);

  async function handleSignOut() {
    await signOut();
    navigate("/login", { replace: true });
  }

  const handleRun = useCallback(() => {
    if (runState === "compiling") {
      return;
    }

    setRunState("compiling");
    compileTimerRef.current = window.setTimeout(() => {
      setRunState("idle");
      compileTimerRef.current = null;
    }, MOCK_COMPILE_MS);
  }, [runState]);

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
      toolbar={<IdeToolbar runState={runState} onRun={handleRun} />}
    >
      <ThreePanelLayout
        editor={<CodeEditor value={code} onChange={setCode} />}
      />
    </IdeLayout>
  );
}
