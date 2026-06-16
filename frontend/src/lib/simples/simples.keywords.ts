/** 27 palavras reservadas SIMPLES — PRD §13.1 */
export const SIMPLES_KEYWORDS = [
  // Estrutura
  "programa",
  "inicio",
  "fim",
  // Tipos
  "inteiro",
  "flutuante",
  "vazio",
  // Controle
  "se",
  "entao",
  "senao",
  "fimse",
  // Lacos
  "enquanto",
  "fimenquanto",
  "para",
  "de",
  "ate",
  "passo",
  "faca",
  "fimpara",
  // E/S
  "leia",
  "escreva",
  "escreval",
  // Logicos
  "e",
  "ou",
  "nao",
  // Operador
  "div",
  // Subprograma
  "procedimento",
  "retorna",
] as const;

export type SimplesKeyword = (typeof SIMPLES_KEYWORDS)[number];
