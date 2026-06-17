import Editor, { type Monaco } from "@monaco-editor/react";

import { DEFAULT_NASM_PLACEHOLDER } from "../lib/nasm/nasmConfig";
import { registerNasmLanguage, NASM_LANGUAGE_ID } from "../lib/nasm/registerNasmLanguage";
import { nasmEditorOptions } from "../lib/monacoConfig";
import {
  registerSimplesTheme,
  SIMPLES_THEME_ID,
} from "../lib/simples/simples.theme";
import { IdePanel } from "./IdePanel";

interface NasmViewerProps {
  value?: string;
}

function handleEditorWillMount(monaco: Monaco) {
  registerNasmLanguage(monaco);
  registerSimplesTheme(monaco);
}

export function NasmViewer({ value = DEFAULT_NASM_PLACEHOLDER }: NasmViewerProps) {
  return (
    <IdePanel
      label="> NASM x32"
      ariaLabel="Painel NASM"
      className="ide-nasm-panel"
    >
      <div className="ide-editor-host">
        <Editor
          height="100%"
          language={NASM_LANGUAGE_ID}
          theme={SIMPLES_THEME_ID}
          value={value}
          beforeMount={handleEditorWillMount}
          options={nasmEditorOptions}
          loading={
            <div className="ide-editor-loading retro-subtitle">
              &gt; carregando NASM...
            </div>
          }
        />
      </div>
    </IdePanel>
  );
}
