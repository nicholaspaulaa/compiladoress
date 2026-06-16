import type { Monaco } from "@monaco-editor/react";

import { nasmMonarchLanguage } from "./nasm.monarch";

const NASM_LANGUAGE_ID = "nasm";

let registered = false;

export function registerNasmLanguage(monaco: Monaco): void {
  if (registered) {
    return;
  }

  monaco.languages.register({ id: NASM_LANGUAGE_ID });
  monaco.languages.setMonarchTokensProvider(
    NASM_LANGUAGE_ID,
    nasmMonarchLanguage,
  );

  registered = true;
}

export { NASM_LANGUAGE_ID };
