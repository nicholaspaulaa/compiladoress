import type { editor } from "monaco-editor";

export const DEFAULT_SIMPLES_CODE = `programa demo
inicio
  escreva "Ola, SIMPLES!";
fim
`;

const sharedEditorOptions: editor.IStandaloneEditorConstructionOptions = {
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
  smoothScrolling: true,
};

export const editorOptions: editor.IStandaloneEditorConstructionOptions = {
  ...sharedEditorOptions,
  readOnly: false,
  cursorBlinking: "solid",
};

export const nasmEditorOptions: editor.IStandaloneEditorConstructionOptions = {
  ...sharedEditorOptions,
  readOnly: true,
  domReadOnly: true,
  cursorBlinking: "solid",
  renderLineHighlight: "line",
};
