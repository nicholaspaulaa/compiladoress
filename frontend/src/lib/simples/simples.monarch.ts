import type { languages } from "monaco-editor";

import { SIMPLES_KEYWORDS } from "./simples.keywords";

export const simplesMonarchLanguage: languages.IMonarchLanguage = {
  ignoreCase: true,
  keywords: [...SIMPLES_KEYWORDS],
  operators: ["<-", "+", "-", "*", "div", ">", "<", "=", "<>", ">=", "<="],
  symbols: /[=<>+\-*]+/,

  tokenizer: {
    root: [
      [
        /[a-zA-Z_]\w*/,
        {
          cases: {
            "@keywords": "keyword",
            "@default": "identifier",
          },
        },
      ],
      [/\d+\.\d+/, "number.float"],
      [/\d+/, "number"],
      [/"/, { token: "string.quote", next: "@string" }],
      [/<-/, "operator"],
      [
        /@symbols/,
        {
          cases: {
            "@operators": "operator",
            "@default": "",
          },
        },
      ],
      [/[()[\],;]/, "delimiter"],
      [/\s+/, "white"],
    ],

    string: [
      [/[^\\"]+/, "string"],
      [/"/, { token: "string.quote", next: "@pop" }],
    ],
  },
};
