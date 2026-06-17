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
  const isBusy = runState !== "idle";

  const runLabel =
    runState === "compiling"
      ? "COMPILANDO..."
      : runState === "executing"
        ? "EXECUTANDO..."
        : "[ RUN ]";

  const statusHint =
    runState === "compiling"
      ? "> compilando..."
      : runState === "executing"
        ? "> digite no terminal (leia)..."
        : null;

  return (
    <div className="ide-toolbar" role="toolbar" aria-label="Ferramentas da IDE">
      <button
        type="button"
        onClick={onRun}
        disabled={isBusy}
        className="retro-btn retro-btn-sm ide-toolbar__run"
        aria-busy={isBusy}
      >
        {isBusy ? (
          <>
            <span className="ide-toolbar__spinner" aria-hidden="true" />
            {runLabel}
          </>
        ) : (
          "[ RUN ]"
        )}
      </button>
      {statusHint && (
        <span className="ide-toolbar__status retro-subtitle">{statusHint}</span>
      )}
      {!isBusy && statusMessage && (
        <span className="ide-toolbar__status ide-toolbar__status--error retro-subtitle">
          {statusMessage}
        </span>
      )}
    </div>
  );
}
