import type { RunState } from "../lib/runState";

interface IdeToolbarProps {
  runState: RunState;
  onRun: () => void;
  statusMessage?: string | null;
}

export function IdeToolbar({
  runState,
  onRun,
  statusMessage = null,
}: IdeToolbarProps) {
  const isCompiling = runState === "compiling";

  return (
    <div className="ide-toolbar" role="toolbar" aria-label="Ferramentas da IDE">
      <button
        type="button"
        onClick={onRun}
        disabled={isCompiling}
        className="retro-btn retro-btn-sm ide-toolbar__run"
        aria-busy={isCompiling}
      >
        {isCompiling ? (
          <>
            <span className="ide-toolbar__spinner" aria-hidden="true" />
            COMPILANDO...
          </>
        ) : (
          "[ RUN ]"
        )}
      </button>
      {isCompiling && (
        <span className="ide-toolbar__status retro-subtitle">
          &gt; compilando...
        </span>
      )}
      {!isCompiling && statusMessage && (
        <span className="ide-toolbar__status ide-toolbar__status--error retro-subtitle">
          {statusMessage}
        </span>
      )}
    </div>
  );
}
