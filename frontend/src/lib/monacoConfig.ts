import type { editor } from "monaco-editor";

export const DEFAULT_SIMPLES_CODE = `programa exemplo;
inicio
  escreva("Ola, SIMPLES!");
fim.
`;

export const editorOptions: editor.IStandaloneEditorConstructionOptions = {
  readOnly: false,
  fontSize: 15,
  fontFamily: "'Cascadia Code', 'Consolas', 'Courier New', monospace",
  lineNumbers: "on",
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  automaticLayout: true,
  wordWrap: "on",
  tabSize: 2,
  padding: { top: 12, bottom: 12 },
  renderLineHighlight: "all",
  cursorBlinking: "solid",
  smoothScrolling: true,
};
