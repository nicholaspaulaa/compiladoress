import { IdePanel } from "./IdePanel";

/**
 * Container preparado para xterm.js (Sprint 4).
 * O elemento `.terminal-panel__host` sera o mount point do terminal.
 */
export function TerminalPanelPlaceholder() {
  return (
    <IdePanel
      label="> TERMINAL"
      ariaLabel="Painel terminal"
      className="ide-terminal-panel"
    >
      <div className="terminal-panel">
        <div
          className="terminal-panel__host"
          id="terminal-host"
          role="region"
          aria-label="Area do terminal interativo"
        >
          <p className="terminal-panel__placeholder retro-blink">
            &gt; terminal em breve — xterm.js (sprint 4)
          </p>
        </div>
      </div>
    </IdePanel>
  );
}
