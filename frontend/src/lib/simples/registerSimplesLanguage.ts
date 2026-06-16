import type { Monaco } from "@monaco-editor/react";

import { simplesMonarchLanguage } from "./simples.monarch";

const SIMPLES_LANGUAGE_ID = "simples";

let registered = false;

export function registerSimplesLanguage(monaco: Monaco): void {
  if (registered) {
    return;
  }

  monaco.languages.register({ id: SIMPLES_LANGUAGE_ID });
  monaco.languages.setMonarchTokensProvider(
    SIMPLES_LANGUAGE_ID,
    simplesMonarchLanguage,
  );

  registered = true;
}

export { SIMPLES_LANGUAGE_ID };
