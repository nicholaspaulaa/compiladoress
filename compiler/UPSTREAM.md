# Compilador SIMPLES (`simplesc`)

Código copiado do fork da equipe (opção 2 — pasta dentro do monorepo).

| | |
|---|---|
| **Fork (desenvolvimento)** | [github.com/nicholaspaulaa/simples-compiler](https://github.com/nicholaspaulaa/simples-compiler) |
| **Pasta no IDE** | `compiler/` |

## Build local

```bash
cd compiler
make
./build/simplesc examples/...   # conforme README do compilador
```

## Sincronizar fork → `compiladoress`

Quando o compilador avançar no fork:

1. Atualize o fork (`git pull` no repo `simples-compiler`).
2. Copie de novo para cá (sem `.git`):

```powershell
# Exemplo no Windows — ajuste o caminho do clone do fork
robocopy C:\caminho\simples-compiler .\compiler /E /XD .git build
```

3. Commit no `compiladoress`: `chore(compiler): sync from simples-compiler`.

## Integração com a IDE

O backend empacotará `simplesc` no Docker (issue #17). Até lá, desenvolvimento do compilador pode ser feito só em `compiler/`.
