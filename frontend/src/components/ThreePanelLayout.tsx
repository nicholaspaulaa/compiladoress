import type { ReactNode } from "react";

import { IdePanel } from "./IdePanel";
import { NasmPanelPlaceholder } from "./NasmPanelPlaceholder";
import { TerminalPanelPlaceholder } from "./TerminalPanelPlaceholder";

interface ThreePanelLayoutProps {
  editor: ReactNode;
}

export function ThreePanelLayout({ editor }: ThreePanelLayoutProps) {
  return (
    <div className="ide-panels">
      <div className="ide-panels__top">
        <IdePanel
          label="> EDITOR SIMPLES"
          ariaLabel="Editor de codigo SIMPLES"
          className="ide-editor-panel"
        >
          {editor}
        </IdePanel>
        <NasmPanelPlaceholder />
      </div>
      <TerminalPanelPlaceholder />
    </div>
  );
}
