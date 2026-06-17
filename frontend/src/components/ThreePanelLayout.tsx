import { useCallback, useRef, type ReactNode } from "react";
import {
  Panel,
  PanelGroup,
  PanelResizeHandle,
  type ImperativePanelHandle,
} from "react-resizable-panels";

import { IdePanel } from "./IdePanel";
import { NasmViewer } from "./NasmViewer";
import { TerminalPanel } from "./TerminalPanel";

interface ThreePanelLayoutProps {
  editor: ReactNode;
}

const NASM_DEFAULT_SIZE = 35;
const PANEL_STORAGE_ID = "simples-editor-nasm-panels";

export function ThreePanelLayout({ editor }: ThreePanelLayoutProps) {
  const nasmPanelRef = useRef<ImperativePanelHandle>(null);
  const nasmSizeBeforeCollapse = useRef(NASM_DEFAULT_SIZE);

  const handleSplitterDoubleClick = useCallback(() => {
    const panel = nasmPanelRef.current;
    if (!panel) {
      return;
    }

    if (panel.isCollapsed()) {
      panel.expand();
      panel.resize(nasmSizeBeforeCollapse.current);
      return;
    }

    nasmSizeBeforeCollapse.current = panel.getSize();
    panel.collapse();
  }, []);

  return (
    <div className="ide-panels">
      <PanelGroup
        direction="horizontal"
        autoSaveId={PANEL_STORAGE_ID}
        className="ide-panels__top"
      >
        <Panel defaultSize={65} minSize={25} className="ide-panel-wrapper">
          <IdePanel
            label="> EDITOR SIMPLES"
            ariaLabel="Editor de codigo SIMPLES"
            className="ide-editor-panel"
          >
            {editor}
          </IdePanel>
        </Panel>

        <PanelResizeHandle
          className="ide-resize-handle"
          onDoubleClick={handleSplitterDoubleClick}
          title="Arraste para redimensionar. Duplo clique colapsa/expande NASM."
        />

        <Panel
          ref={nasmPanelRef}
          defaultSize={NASM_DEFAULT_SIZE}
          minSize={0}
          collapsible
          className="ide-panel-wrapper"
        >
          <NasmViewer />
        </Panel>
      </PanelGroup>

      <TerminalPanel />
    </div>
  );
}
