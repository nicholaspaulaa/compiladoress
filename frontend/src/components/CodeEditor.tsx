import Editor, { type Monaco, type OnMount } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { useCallback, useEffect, useRef } from "react";

import type { CompileError } from "../lib/compileTypes";
import { setCompileMarkers } from "../lib/compileMarkers";
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
  compileErrors?: CompileError[];
}

function handleEditorWillMount(monaco: Monaco) {
  registerSimplesLanguage(monaco);
  registerSimplesTheme(monaco);
}

export function CodeEditor({
  value = DEFAULT_SIMPLES_CODE,
  onChange,
  compileErrors = [],
}: CodeEditorProps) {
  const monacoRef = useRef<Monaco | null>(null);
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  const handleMount: OnMount = useCallback((editorInstance, monaco) => {
    editorRef.current = editorInstance;
    monacoRef.current = monaco;
  }, []);

  useEffect(() => {
    const monaco = monacoRef.current;
    const editorInstance = editorRef.current;
    if (!monaco || !editorInstance) {
      return;
    }

    setCompileMarkers(monaco, editorInstance.getModel(), compileErrors);
  }, [compileErrors]);

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
        onMount={handleMount}
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
