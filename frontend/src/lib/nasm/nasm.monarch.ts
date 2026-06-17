import type * as monaco from "monaco-editor";

export const nasmMonarchLanguage: monaco.languages.IMonarchLanguage = {
  defaultToken: "",
  ignoreCase: true,
  tokenizer: {
    root: [
      [/;.*$/, "comment"],
      [/".*?"/, "string"],
      [
        /\b(section|global|extern|equ|db|dw|dd|dq|resb|resw|resd|resq|times|align|org|bits|use16|use32|use64)\b/,
        "keyword",
      ],
      [
        /\b(mov|add|sub|mul|div|and|or|xor|not|inc|dec|push|pop|call|ret|jmp|je|jne|jl|jg|jle|jge|ja|jb|int|nop|lea|cmp|test|shl|shr|xor)\b/,
        "keyword.instruction",
      ],
      [
        /\b(eax|ebx|ecx|edx|esi|edi|esp|ebp|ax|bx|cx|dx|al|ah|bl|bh|cl|ch|dl|dh)\b/,
        "type",
      ],
      [/\b(dword|byte|word|qword|near|far)\b/, "keyword"],
      [/0[xX][0-9a-fA-F]+|\d+/, "number"],
      [/[_a-zA-Z][\w$]*/, "identifier"],
      [/[\[\]]/, "delimiter.bracket"],
      [/[,.:]/, "delimiter"],
    ],
  },
};
