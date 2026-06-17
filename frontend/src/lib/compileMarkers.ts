import type { Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";

import type { CompileError } from "./compileTypes";

export const COMPILE_MARKER_OWNER = "simplesc";

function formatMarkerMessage(error: CompileError): string {
  if (error.phase && error.phase !== "unknown") {
    return `[${error.phase}] ${error.message}`;
  }
  return error.message;
}

export function compileErrorsToMarkers(
  errors: CompileError[],
  monaco: Monaco,
  model?: editor.ITextModel | null,
): editor.IMarkerData[] {
  return errors.map((error) => {
    const line = error.line > 0 ? error.line : 1;
    const hasColumn = error.column > 0;

    let endColumn = hasColumn ? error.column + 1 : 2;
    if (!hasColumn && model) {
      endColumn = model.getLineMaxColumn(line);
    }

    return {
      severity: monaco.MarkerSeverity.Error,
      startLineNumber: line,
      endLineNumber: line,
      startColumn: hasColumn ? error.column : 1,
      endColumn,
      message: formatMarkerMessage(error),
    };
  });
}

export function setCompileMarkers(
  monaco: Monaco,
  model: editor.ITextModel | null,
  errors: CompileError[],
): void {
  if (!model) {
    return;
  }

  if (errors.length === 0) {
    monaco.editor.setModelMarkers(model, COMPILE_MARKER_OWNER, []);
    return;
  }

  monaco.editor.setModelMarkers(
    model,
    COMPILE_MARKER_OWNER,
    compileErrorsToMarkers(errors, monaco, model),
  );
}
