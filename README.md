# Simples Editor

IDE web para escrever, compilar e executar programas na linguagem **SIMPLES** (disciplina de Compiladores — IFSULDEMINAS, Poços de Caldas).

O ambiente oferece três painéis: editor com syntax highlighting, visualização do NASM gerado pelo compilador `simplesc` e terminal interativo (`leia` / `escreva`) via WebSocket.

**Repositório:** [github.com/nicholaspaulaa/compiladoress](https://github.com/nicholaspaulaa/compiladoress)

## Documentação

| Arquivo | Conteúdo |
|---------|----------|
| [prd-simples-online.md](./prd-simples-online.md) | PRD completo — requisitos, arquitetura, API, segurança |
| [SPRINTS.md](./SPRINTS.md) | Plano de 6 sprints e entregáveis |
| [PROGRESS.md](./PROGRESS.md) | Checklist das issues do GitHub |
| [docs/SUPABASE.md](./docs/SUPABASE.md) | Criar projeto Supabase e variáveis `.env` |
| [compiler/](./compiler/) | Compilador `simplesc` (C) — fork em [simples-compiler](https://github.com/nicholaspaulaa/simples-compiler) |
| [compiler/UPSTREAM.md](./compiler/UPSTREAM.md) | Como sincronizar o fork com esta pasta |

## Stack (resumo)

| Camada | Tecnologias |
|--------|-------------|
| Frontend | React, TypeScript, TanStack Start, Monaco Editor, xterm.js, Tailwind, Supabase Auth |
| Backend | Python 3.11+, Flask, flask-sock, Docker SDK |
| Compilador | `simplesc` (C99) → NASM x86-32 → `nasm` + `ld` (i386) |
| Infra | Docker Compose, Nginx, Supabase |

> O frontend e backend evoluem por sprint; o compilador vive em [`compiler/`](./compiler/) (cópia do fork [`simples-compiler`](https://github.com/nicholaspaulaa/simples-compiler)).

## Pré-requisitos

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) e Docker Compose v2
- Conta no repositório GitHub

## Como clonar

```bash
git clone https://github.com/nicholaspaulaa/compiladoress.git
cd compiladoress
```

Copie `.env.example` → `.env` e configure o Supabase ([docs/SUPABASE.md](./docs/SUPABASE.md)).

## Desenvolvimento local

```bash
# Subir todos os serviços
docker compose up -d --build
```

### Smoke test (health check)

Após `docker compose up`, valide que o backend está saudável:

```bash
curl http://localhost:5000/api/health
```

Resposta esperada (HTTP 200):

```json
{"status":"ok","service":"backend","components":{"supabase":{"status":"ok"}}}
```

Caso o Supabase não esteja configurado, `supabase.status` será `"unconfigured"` — o endpoint ainda retorna 200.

Acompanhe o [SPRINTS.md](./SPRINTS.md) — **Sprint 1** cobre infraestrutura mínima e autenticação.

## Convenção de branches e revisão

| Regra | Descrição |
|-------|-----------|
| Branch naming | `feat/<descricao>`, `fix/<descricao>`, `docs/<descricao>` |
| Pull Requests | Todo PR deve referenciar a issue relacionada (`Closes #N` ou `Refs #N`) |
| Revisão | Pelo menos 1 aprovação de outro membro da equipe antes do merge |
| Template | Usar o template em [.github/pull_request_template.md](./.github/pull_request_template.md) |

## Equipe

Eduardo Tenório Nunes
Érica de Souza Guerzoni Ribeiro
Nicholas Emanuell Lima de Paula

## Licença

Uso acadêmico — disciplina de Compiladores.
