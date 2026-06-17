import type { Monaco } from "@monaco-editor/react";

import { SIMPLES_THEME_ID, simplesPalette } from "./simples.palette";

let themeRegistered = false;

export function registerSimplesTheme(monaco: Monaco): void {
  if (themeRegistered) {
    return;
  }

  monaco.editor.defineTheme(SIMPLES_THEME_ID, {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "keyword", foreground: simplesPalette.green, fontStyle: "bold" },
      {
        token: "keyword.instruction",
        foreground: simplesPalette.greenGlow,
        fontStyle: "bold",
      },
      { token: "type", foreground: simplesPalette.purpleBright },
      { token: "identifier", foreground: simplesPalette.textDim },
      { token: "number", foreground: simplesPalette.orange },
      { token: "number.float", foreground: simplesPalette.orange },
      { token: "string", foreground: simplesPalette.purpleBright },
      { token: "string.quote", foreground: simplesPalette.purpleBright },
      { token: "operator", foreground: simplesPalette.greenGlow },
      { token: "delimiter", foreground: simplesPalette.textDim },
      { token: "comment", foreground: simplesPalette.green, fontStyle: "italic" },
      { token: "white", foreground: simplesPalette.text },
    ],
    colors: {
      "editor.background": simplesPalette.bgMid,
      "editor.foreground": simplesPalette.text,
      "editorCursor.foreground": simplesPalette.green,
      "editor.lineHighlightBackground": "#2a145066",
      "editorLineNumber.foreground": simplesPalette.purple,
      "editorLineNumber.activeForeground": simplesPalette.green,
      "editor.selectionBackground": "#5c2d9180",
      "editor.inactiveSelectionBackground": "#5c2d9140",
      "editorIndentGuide.background": "#5c2d9140",
      "editorIndentGuide.activeBackground": simplesPalette.purple,
      "editorWidget.background": simplesPalette.bg,
      "editorWidget.border": simplesPalette.green,
      "input.background": simplesPalette.bg,
      "input.border": simplesPalette.purple,
      "scrollbarSlider.background": "#5c2d9166",
      "scrollbarSlider.hoverBackground": "#9b4dff66",
      "editorError.foreground": simplesPalette.error,
      "editorError.border": simplesPalette.error,
      "editorOverviewRuler.errorForeground": simplesPalette.error,
    },
  });

  themeRegistered = true;
}

export { SIMPLES_THEME_ID };
