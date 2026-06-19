# Simples Editor

[![License: Academic](https://img.shields.io/badge/License-Academic-blue.svg)](#licença)
[![Sprint](https://img.shields.io/badge/Sprint-6%20%E2%80%94%20Polish%20%26%20Deploy-green)](./SPRINTS.md)
[![Stack](https://img.shields.io/badge/Stack-React%20%7C%20Flask%20%7C%20Docker-2496ED?logo=docker)](./docker-compose.yml)

IDE web para escrever, compilar e executar programas na linguagem **SIMPLES** (disciplina de Compiladores — IFSULDEMINAS, Poços de Caldas).

O ambiente oferece três painéis: editor com syntax highlighting, visualização do NASM gerado pelo compilador `simplesc` e terminal interativo (`leia` / `escreva`) via WebSocket.

**Repositório:** [github.com/nicholaspaulaa/compiladoress](https://github.com/nicholaspaulaa/compiladoress)

---

## Visão

O **Simples Editor** é uma IDE online para o ensino de compiladores. Alunos escrevem código na linguagem SIMPLES,
veem o assembly NASM x86-32 gerado em tempo real e executam o programa em um terminal interativo — tudo no navegador,
sem instalar nada.

**Por que existe**: a disciplina de Compiladores do IFSULDEMINAS precisava de um ambiente onde os alunos pudessem
compilar e executar programas SIMPLES sem configurar `nasm`, `ld`, `gcc` ou emuladores localmente. O sandbox Docker
garante isolamento e segurança para execução multi-tenant.

## Arquitetura (resumo)

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────────────┐
│   Navegador   │────▶│   Nginx :80   │────▶│  Frontend (React/TS)    │
│  (xterm.js +  │     │  (proxy)      │     │  Monaco Editor          │
│   Monaco)     │◀────│               │◀────│  Tailwind CSS           │
└──────┬───────┘     └──────┬────────┘     └─────────────────────────┘
       │                    │
       │ WebSocket          │ HTTP
       │ /ws/run            │ /api/*
       ▼                    ▼
┌──────────────────────────────────────────────────┐
│              Backend (Flask + flask-sock)          │
│  ┌──────────┐  ┌───────────┐  ┌────────────────┐ │
│  │ Auth JWT │  │ Compile   │  │ WS Run Session │ │
│  │ Supabase │  │ simplesc  │  │ Protocol §9.2   │ │
│  └──────────┘  └───────────┘  └───────┬────────┘ │
│                                        │          │
│                              ┌─────────▼────────┐ │
│                              │  Docker SDK       │ │
│                              │  PtyExecution     │ │
│                              └─────────┬────────┘ │
└───────────────────────────────────────┼──────────┘
                                        │ docker.sock
                                        ▼
┌──────────────────────────────────────────────────┐
│        Sandbox Container (simples-runner)         │
│  network=none | read-only | 128MB | nobody:65534 │
│  ┌────────────────────────────────────────────┐  │
│  │  qemu-i386-static /sandbox/programa        │  │
│  │  stdin/stdout via PTY attach               │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Stack tecnológico

| Camada | Tecnologias |
|--------|-------------|
| Frontend | React 18, TypeScript, Vite, Monaco Editor, xterm.js, Tailwind CSS, Supabase Auth |
| Backend | Python 3.11+, Flask 2.3, flask-sock, Docker SDK, Prometheus metrics |
| Compilador | `simplesc` (C99) → NASM x86-32 → `nasm` + `ld` (elf_i386) |
| Sandbox | Docker + `qemu-i386-static` (emulação ARM64/x86_64), 8 camadas de hardening |
| Infra | Docker Compose, Nginx, Supabase (Auth + JWT) |

### Fluxo de execução

1. **Login** — Supabase Auth (email/senha) → JWT
2. **Editor** — Usuário escreve código SIMPLES no Monaco Editor
3. **Compilar** — `POST /api/compile` → backend chama `simplesc` → retorna NASM
4. **Executar** — `WS /ws/run` → backend compila, monta container sandbox Docker,
   executa binário via `qemu-i386-static` com PTY → stdout/stderr stream via WebSocket

---

## Documentação

| Arquivo | Conteúdo |
|---------|----------|
| [prd-simples-online.md](./prd-simples-online.md) | PRD completo — requisitos, arquitetura, API, segurança |
| [SPRINTS.md](./SPRINTS.md) | Plano de 6 sprints e entregáveis |
| [PROGRESS.md](./PROGRESS.md) | Checklist das issues do GitHub |
| [docs/SUPABASE.md](./docs/SUPABASE.md) | Criar projeto Supabase e variáveis `.env` |
| [docs/SECURITY-AUDIT.md](./docs/SECURITY-AUDIT.md) | Auditoria de segurança do sandbox (camadas de hardening) |
| [docs/INCIDENTS.md](./docs/INCIDENTS.md) | Plano de resposta a incidentes (escape, vazamento, P1/P2) |
| [compiler/](./compiler/) | Compilador `simplesc` (C) — fork em [simples-compiler](https://github.com/nicholaspaulaa/simples-compiler) |
| [compiler/UPSTREAM.md](./compiler/UPSTREAM.md) | Como sincronizar o fork com esta pasta |
| [DOCKER-README.md](./DOCKER-README.md) | Comandos Docker e smoke test do sandbox |

---

## Pré-requisitos

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) e Docker Compose v2
- Conta no [Supabase](https://supabase.com/) (gratuita)
- Conta no repositório GitHub

## Configuração (env vars)

```bash
git clone https://github.com/nicholaspaulaa/compiladoress.git
cd compiladoress
cp .env.example .env
```

Edite `.env` com os valores do Supabase Dashboard ([guia passo a passo](./docs/SUPABASE.md)):

| Variável | Onde encontrar | Exemplo |
|----------|---------------|---------|
| `SUPABASE_URL` | Project Settings → API | `https://abc123.supabase.co` |
| `SUPABASE_ANON_KEY` | Project Settings → API → anon/public | `eyJhbGci...` |
| `SUPABASE_JWT_SECRET` | Project Settings → API → JWT Settings | `sua-jwt-secret` |
| `VITE_SUPABASE_URL` | Mesmo valor de `SUPABASE_URL` | `https://abc123.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Mesmo valor de `SUPABASE_ANON_KEY` | `eyJhbGci...` |

> **Importante**: o `.env` NÃO é versionado (está no `.gitignore`).
> **Nunca** commite secrets no repositório.

### Variáveis opcionais (comportamento)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `COMPILE_TIMEOUT_S` | `15` | Tempo máximo de compilação |
| `EXEC_TIMEOUT_S` | `10` | Tempo máximo de execução no sandbox |
| `DOCKER_STOP_TIMEOUT_S` | `12` | Hard limit do Docker daemon |
| `SANDBOX_IMAGE` | `simples-runner:latest` | Imagem Docker do sandbox |

---

## Desenvolvimento local

```bash
# Subir todos os serviços (frontend + backend + nginx + sandbox)
docker compose up -d --build
```

### Smoke test

```bash
# Health check do backend
curl http://localhost:5000/api/health
```

Resposta esperada (HTTP 200):

```json
{"status":"ok","service":"backend","components":{"supabase":{"status":"ok"}}}
```

Se o Supabase não estiver configurado, `supabase.status` será `"unconfigured"` — o endpoint ainda retorna 200.

### Testes

```bash
# Suite completa + cobertura minima 70% (validacao da issue #41)
cd backend && make test-cov

# Suite completa, sem relatorio de cobertura
cd backend && make test

# Apenas os testes novos da issue #41 (sem gate de cobertura global)
cd backend && make test-new

# Testes de segurança do sandbox (24 testes)
python -m pytest tests/test_sandbox_security.py -v
```

### Testes E2E (Playwright — issue #40)

Requer stack completa e usuario de teste no Supabase Auth.

```bash
# 1. Subir stack (rebuild se mudou o frontend)
docker compose up --build

# 2. Credenciais em e2e/.env (copie e2e/.env.example)
#    E2E_TEST_EMAIL=...
#    E2E_TEST_PASSWORD=...

# 3. Rodar (suite leva ~1 min quando tudo OK)
cd e2e
npm test
```

Cenarios cobertos: login, Run + NASM, stdin (`leia`), Stop e timeout (**10s**, conforme `EXEC_TIMEOUT_S` padrao).

No CI (GitHub Actions), configure os secrets: `SUPABASE_*`, `E2E_TEST_EMAIL`, `E2E_TEST_PASSWORD`.

---

## Screenshots

> **Para a equipe**: capture screenshots/GIFs e salve em `docs/screenshots/`.
> Instruções detalhadas em [docs/screenshots/README.md](./docs/screenshots/README.md).

| Funcionalidade | Screenshot |
|----------------|------------|
| **Tela de login** com Supabase Auth | ![Login](./docs/screenshots/01-login.png) |
| **Editor + NASM** após compilar código SIMPLES | ![Editor + NASM](./docs/screenshots/02-editor-nasm.png) |
| **Terminal interativo** com execução (`leia`/`escreva`) | ![Terminal](./docs/screenshots/03-terminal-execution.png) |

### Fluxo completo (GIF)

![Fluxo completo](./docs/screenshots/00-full-flow.gif)

*Login → escrever código → compilar → ver NASM → executar no terminal*

---

## Troubleshooting

| Problema | Causa provável | Solução |
|----------|---------------|---------|
| `docker compose up` falha | Docker não está rodando | Inicie Docker Desktop |
| Frontend não carrega | `.env` ausente ou `VITE_*` errados | Verifique `.env` e rode `docker compose build --no-cache frontend` |
| `/api/auth/verify` retorna 503 | Supabase não configurado | Configure `.env` conforme [docs/SUPABASE.md](./docs/SUPABASE.md) |
| `curl http://localhost:5000/api/health` falha | Backend não iniciou | `docker compose logs backend --tail=50` |
| WebSocket `/ws/run` fecha com 4403 | Token JWT inválido/expirado | Faça login novamente; verifique `SUPABASE_JWT_SECRET` |
| `simples-runner` não constrói | Falta `qemu-user-static` | `docker compose build runner_image_build` |
| Erro `docker.errors.NotFound: simples-runner:latest` | Imagem não foi construída | `docker compose up --build` (constrói todas as imagens) |
| Erro 429 ao compilar | Rate limit excedido (30/min) | Aguarde 1 minuto; ver [PRD §6.2](./prd-simples-online.md#62-segurança) |
| Testes falham com `ImportError` | Dependências não instaladas | `cd backend && uv pip install -r requirements.txt` (ou `pip install`) |

---

## Segurança

O sandbox implementa 8 camadas de hardening (PRD §11.2):

| Camada | Mecanismo |
|--------|-----------|
| Rede | `network_mode: none` — sem acesso à internet |
| Filesystem | `read_only: True` + `tmpfs` 8 MB — rootfs imutável |
| Memória | `mem_limit: 128m` + `memswap_limit: 128m` — sem swap |
| CPU | `cpu_quota: 50000` (0.5 CPU) — throttling |
| Processos | `pids_limit: 64` — bloqueia fork bombs |
| Usuário | `user: 65534:65534` (nobody) — non-root |
| Capabilities | `cap_drop: ["ALL"]` — sem syscalls privilegiadas |
| Timeout | `EXEC_TIMEOUT_S: 10` + `DOCKER_STOP_TIMEOUT_S: 12` |

Documentação completa: [SECURITY-AUDIT.md](./docs/SECURITY-AUDIT.md) |
Plano de incidentes: [INCIDENTS.md](./docs/INCIDENTS.md)

---

## Convenção de branches e revisão

| Regra | Descrição |
|-------|-----------|
| Branch naming | `feat/<descricao>`, `fix/<descricao>`, `docs/<descricao>` |
| Pull Requests | Todo PR deve referenciar a issue relacionada (`Closes #N` ou `Refs #N`) |
| Revisão | Pelo menos 1 aprovação de outro membro da equipe antes do merge |
| Template | Usar o template em [.github/pull_request_template.md](./.github/pull_request_template.md) |
| Commits | Convencionais: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:` |

---

## Equipe

| Nome | Papel |
|------|-------|
| **Eduardo Tenório Nunes** | Desenvolvedor Backend & DevOps |
| **Érica de Souza Guerzoni Ribeiro** | Desenvolvedora Frontend |
| **Nicholas Emanuell Lima de Paula** | Coordenador & Compilador `simplesc` |

---

## Licença

Uso acadêmico — disciplina de Compiladores, IFSULDEMINAS, Poços de Caldas.

Projeto desenvolvido como trabalho da disciplina de Compiladores sob orientação do professor da disciplina.

---

<p align="center">
  <sub>Última atualização: Sprint 6 — Junho 2026</sub>
</p>
