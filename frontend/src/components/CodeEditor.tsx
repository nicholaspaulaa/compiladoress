import Editor from "@monaco-editor/react";
import { useCallback } from "react";

import {
  DEFAULT_SIMPLES_CODE,
  editorOptions,
} from "../lib/monacoConfig";

interface CodeEditorProps {
  value?: string;
  onChange?: (value: string) => void;
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
        defaultLanguage="plaintext"
        theme="vs-dark"
        value={value}
        onChange={handleChange}
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
