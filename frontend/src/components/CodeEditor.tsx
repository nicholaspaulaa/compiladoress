import Editor, { type Monaco } from "@monaco-editor/react";
import { useCallback } from "react";

import {
  DEFAULT_SIMPLES_CODE,
  editorOptions,
} from "../lib/monacoConfig";
import {
  registerSimplesLanguage,
  SIMPLES_LANGUAGE_ID,
} from "../lib/simples/registerSimplesLanguage";
import {
  registerSimplesTheme,
  SIMPLES_THEME_ID,
} from "../lib/simples/simples.theme";

interface CodeEditorProps {
  value?: string;
  onChange?: (value: string) => void;
}

function handleEditorWillMount(monaco: Monaco) {
  registerSimplesLanguage(monaco);
  registerSimplesTheme(monaco);
}

export function CodeEditor({
  value = DEFAULT_SIMPLES_CODE,
  onChange,
}: CodeEditorProps) {
  const handleChange = useCallback(
    (nextValue: string | undefined) => {
      onChange?.(nextValue ?? "");
    },
    [onChange],
  );

  return (
    <div className="ide-editor-host">
      <Editor
        height="100%"
        language={SIMPLES_LANGUAGE_ID}
        theme={SIMPLES_THEME_ID}
        value={value}
        onChange={handleChange}
        beforeMount={handleEditorWillMount}
        options={editorOptions}
        loading={
          <div className="ide-editor-loading retro-subtitle">
            &gt; carregando editor...
          </div>
        }
      />
    </div>
  );
}
