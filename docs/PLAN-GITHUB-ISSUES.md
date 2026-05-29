# Plano — Milestones, Labels e Issues (Simples Editor)

> **Status:** aplicado em 2026-05-29 — ver [PROGRESS.md](../PROGRESS.md) e issues no GitHub.  
> **Fontes:** `SPRINTS.md`, `prd-simples-online.md` (PRD “Simples Editor”)  
> **Total:** 6 milestones · 11 labels · **47 issues** (1 por entregável)

---

## 1. Milestones

| # | Título | Descrição (gh milestone `description`) | Due date |
|---|--------|----------------------------------------|----------|
| 1 | Sprint 1 — Foundation & Auth | Estrutura mínima: Docker Compose, Supabase, login, JWT, health. DoD: clone → `docker compose up` → login → health verde. | _(definir com a turma)_ |
| 2 | Sprint 2 — Editor & NASM Panel | Monaco + tokenizer SIMPLES + layout 3 painéis. Run mockado. | _(definir)_ |
| 3 | Sprint 3 — Compilation Pipeline | `simplesc → nasm → ld` via REST, erros como markers. | _(definir)_ |
| 4 | Sprint 4 — Interactive Execution | WebSocket + PTY + xterm.js + `leia` E2E. | _(definir)_ |
| 5 | Sprint 5 — Hardening & Observability | Stop, timeouts, sandbox, rate limit, métricas, auditoria. | _(definir)_ |
| 6 | Sprint 6 — Polish & (Opcional) Deploy | E2E, cobertura, docs, demo, deploy opcional. | _(definir)_ |

**Comandos (após aprovação):**

```bash
gh api repos/:owner/:repo/milestones -f title="Sprint 1 — Foundation & Auth" -f description="..."
# repetir para sprints 2–6
```

---

## 2. Labels (~11)

| Label | Cor (hex) | Descrição |
|-------|-----------|-----------|
| `sprint-1` | `0E8A16` | Trabalho do Sprint 1 |
| `sprint-2` | `1D76DB` | Trabalho do Sprint 2 |
| `sprint-3` | `5319E7` | Trabalho do Sprint 3 |
| `sprint-4` | `D93F0B` | Trabalho do Sprint 4 |
| `sprint-5` | `B60205` | Trabalho do Sprint 5 |
| `sprint-6` | `FBCA04` | Trabalho do Sprint 6 |
| `frontend` | `7057FF` | React, Monaco, xterm, UI |
| `backend` | `0075CA` | Flask, APIs, WebSocket, compilação |
| `devops` | `006B75` | Docker, Nginx, CI, deploy, GitHub |
| `docs` | `C5DEF5` | Documentação, README, apresentação |
| `security` | `E11D21` | Sandbox, JWT, rate limit, auditoria |

**Comandos (após aprovação):**

```bash
gh label create "sprint-1" --color "0E8A16" --description "Sprint 1"
# ... demais labels
```

---

## 3. Issues por sprint

Convenções aplicadas em todas:
- **Assignee:** vazio
- **Labels:** `sprint-N` + um tipo (`frontend` | `backend` | `devops` | `docs` | `security`)
- **Milestone:** sprint correspondente

---

### Sprint 1 — Foundation & Auth

#### Issue 1.1

- **Título:** `chore(repo): initialize GitHub repository and README`
- **Labels:** `sprint-1`, `docs`
- **Milestone:** Sprint 1 — Foundation & Auth

**Body:**

```markdown
## Contexto
O time precisa de um repositório central com instruções mínimas para clonar e entender o projeto antes de qualquer código de produto.

## Critérios de aceite
- [ ] Repositório GitHub criado e acessível a todos os integrantes
- [ ] `README.md` descreve o Simples Editor, stack resumida e como clonar
- [ ] Links para `prd-simples-online.md` e `SPRINTS.md` no README
- [ ] `.gitignore` adequado (Node, Python, `.env`, Docker)

## Stack afetado
- docs
- devops

## Referências
- [PRD §1 — Visão geral](prd-simples-online.md#1-visão-geral)
- [PRD §18 — Roadmap (semana 1)](prd-simples-online.md#18-roadmap)
- `SPRINTS.md` — Sprint 1
```

---

#### Issue 1.2

- **Título:** `chore(project): configure GitHub Project Kanban with automations`
- **Labels:** `sprint-1`, `devops`

**Body:**

```markdown
## Contexto
O fluxo da disciplina exige visibilidade do trabalho em paralelo; o Kanban no GitHub Projects automatiza o movimento das issues conforme PRs.

## Critérios de aceite
- [ ] GitHub Project (board) criado e vinculado ao repositório
- [ ] Colunas definidas (ex.: Backlog, In Progress, In Review, Done)
- [ ] Automação: issue aberta → Backlog; PR aberto → In Review; PR mergeado → Done
- [ ] Todas as issues dos sprints 1–6 aparecem no board

## Stack afetado
- devops

## Referências
- `SPRINTS.md` — Sprint 1 (entregável Kanban)
- [PRD §18 — Roadmap](prd-simples-online.md#18-roadmap)
```

---

#### Issue 1.3

- **Título:** `feat(infra): add docker-compose with nginx frontend and backend skeletons`
- **Labels:** `sprint-1`, `devops`

**Body:**

```markdown
## Contexto
Toda a stack deve subir com um único comando para que integrantes de frontend, backend e infra trabalhem no mesmo ambiente local.

## Critérios de aceite
- [ ] `docker-compose.yml` define 3 serviços: `nginx`, `frontend`, `backend`
- [ ] Frontend: skeleton React (TanStack Start conforme PRD)
- [ ] Backend: skeleton Flask com estrutura de app factory ou equivalente
- [ ] Nginx faz proxy para frontend e rotas `/api/*` para o backend
- [ ] Volumes e networks documentados no README ou comentários

## Stack afetado
- devops
- frontend (skeleton)
- backend (skeleton)

## Referências
- [PRD §14 — Docker Compose](prd-simples-online.md#14-docker-compose)
- [PRD §7 — Arquitetura](prd-simples-online.md#7-arquitetura)
- [PRD §15 — Nginx](prd-simples-online.md#15-nginx--reverse-proxy)
- `SPRINTS.md` — Sprint 1
```

---

#### Issue 1.4

- **Título:** `feat(infra): verify docker compose up serves localhost homepage`
- **Labels:** `sprint-1`, `devops`

**Body:**

```markdown
## Contexto
Validar que o ambiente local está realmente integrado — não apenas containers “up”, mas página acessível via reverse proxy.

## Critérios de aceite
- [ ] `docker compose up` (ou `docker compose up --build`) sobe sem erro fatal
- [ ] http://localhost responde com página inicial do frontend (200)
- [ ] Proxy `/api` encaminha ao backend (mesmo que 404 em rotas ainda não implementadas)
- [ ] Instruções reproduzíveis no README (host limpo com Docker instalado)

## Stack afetado
- devops

## Referências
- [PRD §20 — Critérios de aceite (`docker compose up`)](prd-simples-online.md#20-critérios-de-aceite)
- [PRD §14 — Docker Compose](prd-simples-online.md#14-docker-compose)
- `SPRINTS.md` — Sprint 1 — Definition of Done
```

---

#### Issue 1.5

- **Título:** `feat(auth): configure Supabase project and Auth`
- **Labels:** `sprint-1`, `backend`

**Body:**

```markdown
## Contexto
A IDE é multiusuário na nuvem; o gate de acesso v1 usa apenas Supabase Auth (sem persistência de código).

## Critérios de aceite
- [ ] Projeto Supabase criado (free tier)
- [ ] Provider email/senha habilitado
- [ ] Variáveis `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET` documentadas em `.env.example`
- [ ] Frontend e backend sabem ler credenciais via env (sem commit de secrets)

## Stack afetado
- backend
- devops

## Referências
- [PRD §10 — Modelo de dados (Supabase)](prd-simples-online.md#10-modelo-de-dados-supabase)
- [PRD §11.1 — Autenticação](prd-simples-online.md#111-autenticação-e-autorização)
- [PRD RF01](prd-simples-online.md#5-requisitos-funcionais)
- `SPRINTS.md` — Sprint 1
```

---

#### Issue 1.6

- **Título:** `feat(frontend): implement login screen with email and password`
- **Labels:** `sprint-1`, `frontend`

**Body:**

```markdown
## Contexto
Alunos precisam autenticar antes de acessar a IDE; a tela de login é o primeiro fluxo real da aplicação React.

## Critérios de aceite
- [ ] Rota/página de login com campos email e senha
- [ ] Integração com Supabase client (`signInWithPassword` ou equivalente)
- [ ] Erros de credencial exibidos de forma clara ao usuário
- [ ] Após login bem-sucedido, redireciona para rota principal (placeholder aceito)
- [ ] Token JWT disponível para chamadas autenticadas subsequentes

## Stack afetado
- frontend

## Referências
- [PRD US-01](prd-simples-online.md#32-user-stories-escopo-v1)
- [PRD RF01](prd-simples-online.md#5-requisitos-funcionais)
- [PRD §12 — UI/UX](prd-simples-online.md#12-uiux)
- `SPRINTS.md` — Sprint 1
```

---

#### Issue 1.7

- **Título:** `feat(backend): add verify_jwt decorator for protected endpoints`
- **Labels:** `sprint-1`, `security`

**Body:**

```markdown
## Contexto
Endpoints REST e futuras conexões WebSocket devem rejeitar requisições sem JWT válido do Supabase.

## Critérios de aceite
- [ ] Decorator `@verify_jwt` (ou middleware equivalente) valida `Authorization: Bearer <token>`
- [ ] Usa segredo/chaves Supabase para validar assinatura e expiração
- [ ] Retorna 401 com corpo JSON claro quando token ausente ou inválido
- [ ] `user_id` (`sub`) disponível no contexto da request após validação
- [ ] Pelo menos um endpoint de exemplo protegido além de `/api/health`

## Stack afetado
- backend
- security

## Referências
- [PRD §11.1 — Autenticação](prd-simples-online.md#111-autenticação-e-autorização)
- [PRD §6.2 — Segurança (JWT)](prd-simples-online.md#62-segurança)
- [PRD §9.1 — REST endpoints](prd-simples-online.md#91-rest-endpoints)
- `SPRINTS.md` — Sprint 1
```

---

#### Issue 1.8

- **Título:** `feat(backend): implement GET /api/health endpoint`
- **Labels:** `sprint-1`, `backend`

**Body:**

```markdown
## Contexto
Health check permite validar deploy e integração Docker sem login; é base para observabilidade futura.

## Critérios de aceite
- [ ] `GET /api/health` retorna JSON com `{ "status": "ok" }` no mínimo (v1 simplificado do sprint)
- [ ] Endpoint público (sem JWT), conforme PRD
- [ ] Responde 200 quando backend está saudável
- [ ] Documentado no README como smoke test pós-`docker compose up`
- [ ] (Opcional neste sprint) esqueleto de `components` para expansão futura

## Stack afetado
- backend

## Referências
- [PRD RF20](prd-simples-online.md#5-requisitos-funcionais)
- [PRD §16.3 — Health check](prd-simples-online.md#163-health-check)
- [PRD §9.1 — REST](prd-simples-online.md#91-rest-endpoints)
- `SPRINTS.md` — Sprint 1
```

---

#### Issue 1.9

- **Título:** `docs(process): validate PR workflow with one merge per team member`
- **Labels:** `sprint-1`, `docs`

**Body:**

```markdown
## Contexto
Antes de escalar o código, cada integrante precisa praticar branch → PR → review → merge no repositório compartilhado.

## Critérios de aceite
- [ ] Template de PR em uso (`.github/pull_request_template.md`)
- [ ] Pelo menos 1 PR mergeado por integrante da equipe
- [ ] PRs referenciam issues (`Closes #N` ou `Refs #N`)
- [ ] Branch protection ou convenção de review acordada em equipe (documentar no README)

## Stack afetado
- docs
- devops

## Referências
- `SPRINTS.md` — Sprint 1 — Definition of Done
- `.github/pull_request_template.md`
```

---

### Sprint 2 — Editor & NASM Panel

#### Issue 2.1

- **Título:** `feat(editor): integrate Monaco Editor on main route`
- **Labels:** `sprint-2`, `frontend`

**Body:**

```markdown
## Contexto
O editor SIMPLES é o componente central da IDE; sem Monaco na rota principal não há trabalho de highlighting nem layout.

## Critérios de aceite
- [ ] `@monaco-editor/react` instalado e configurado
- [ ] Editor visível na rota principal pós-login
- [ ] Editor editável (não read-only)
- [ ] Altura preenche área designada do layout

## Stack afetado
- frontend

## Referências
- [PRD §13 — Editor de código (Monaco)](prd-simples-online.md#13-editor-de-código-monaco)
- [PRD §8.1 — Frontend](prd-simples-online.md#81-frontend)
- [PRD RF02, RF03](prd-simples-online.md#5-requisitos-funcionais)
- `SPRINTS.md` — Sprint 2
```

---

#### Issue 2.2

- **Título:** `feat(editor): register simples language with Monarch tokenizer`
- **Labels:** `sprint-2`, `frontend`

**Body:**

```markdown
## Contexto
Syntax highlighting das 27 palavras reservadas ajuda o aluno a identificar erros de digitação e entender a linguagem.

## Critérios de aceite
- [ ] Linguagem `simples` registrada no Monaco (`monaco.languages.register`)
- [ ] Tokenizer Monarch cobre as 27 keywords do PRD
- [ ] Comentários e literais (se aplicável) tokenizados
- [ ] Arquivo de definição versionado (ex.: `simples.monarch.ts`)

## Stack afetado
- frontend

## Referências
- [PRD §13 — Monaco / linguagem SIMPLES](prd-simples-online.md#13-editor-de-código-monaco)
- [PRD RF02](prd-simples-online.md#5-requisitos-funcionais)
- `SPRINTS.md` — Sprint 2
```

---

#### Issue 2.3

- **Título:** `feat(editor): apply dark theme with keyword highlighting`
- **Labels:** `sprint-2`, `frontend`

**Body:**

```markdown
## Contexto
v1 usa apenas tema dark; keywords devem se destacar visualmente do código comum.

## Critérios de aceite
- [ ] Tema dark aplicado ao editor SIMPLES
- [ ] Keywords SIMPLES com cor/distinção visível no tema
- [ ] Consistência visual com restante da UI (Tailwind)
- [ ] Sem opção de tema claro em v1 (fora de escopo)

## Stack afetado
- frontend

## Referências
- [PRD §4.2 — Fora de escopo (tema customizável)](prd-simples-online.md#42-fora-de-escopo-v1)
- [PRD §12 — UI/UX](prd-simples-online.md#12-uiux)
- [PRD §13](prd-simples-online.md#13-editor-de-código-monaco)
- `SPRINTS.md` — Sprint 2
```

---

#### Issue 2.4

- **Título:** `feat(ui): implement three-panel layout with terminal placeholder`
- **Labels:** `sprint-2`, `frontend`

**Body:**

```markdown
## Contexto
A IDE expõe três painéis simultâneos (editor, NASM, terminal); o terminal pode ser placeholder até o Sprint 4.

## Critérios de aceite
- [ ] Layout com editor à esquerda, NASM à direita, terminal inferior
- [ ] Área do terminal visível com placeholder (“terminal em breve” ou similar)
- [ ] Layout responsivo mínimo em desktop (mobile fora de escopo v1)
- [ ] Estrutura de componentes preparada para integrar xterm.js depois

## Stack afetado
- frontend

## Referências
- [PRD §1 — Visão geral (3 painéis)](prd-simples-online.md#1-visão-geral)
- [PRD §12 — UI/UX](prd-simples-online.md#12-uiux)
- `SPRINTS.md` — Sprint 2
```

---

#### Issue 2.5

- **Título:** `feat(ui): add resizable splitter between editor and NASM panels`
- **Labels:** `sprint-2`, `frontend`

**Body:**

```markdown
## Contexto
Alunos alternam foco entre código fonte e assembly; splitter arrastável e colapso por double-click atendem US-06.

## Critérios de aceite
- [ ] `react-resizable-panels` (ou equivalente) entre editor e NASM
- [ ] Usuário redimensiona arrastando o divisor
- [ ] Double-click no divisor colapsa/expande painel NASM
- [ ] Estado de layout razoável após refresh (persistência opcional)

## Stack afetado
- frontend

## Referências
- [PRD RF07](prd-simples-online.md#5-requisitos-funcionais)
- [PRD US-06](prd-simples-online.md#32-user-stories-escopo-v1)
- [PRD §20 — Painel NASM expande/contrai](prd-simples-online.md#20-critérios-de-aceite)
- `SPRINTS.md` — Sprint 2
```

---

#### Issue 2.6

- **Título:** `feat(ui): add mock Run button with compiling state`
- **Labels:** `sprint-2`, `frontend`

**Body:**

```markdown
## Contexto
O botão Run é affordance central da IDE; no Sprint 2 apenas simula feedback visual até o pipeline real existir.

## Critérios de aceite
- [ ] Botão **Run** visível na toolbar ou header da IDE
- [ ] Ao clicar, exibe estado “compilando…” (loading) por tempo definido
- [ ] Não chama backend real de compilação/execução
- [ ] Botão desabilitado ou spinner durante estado mock

## Stack afetado
- frontend

## Referências
- [PRD US-03](prd-simples-online.md#32-user-stories-escopo-v1)
- `SPRINTS.md` — Sprint 2 — Definition of Done
```

---

#### Issue 2.7

- **Título:** `feat(editor): add read-only NASM panel with Monaco asm mode`
- **Labels:** `sprint-2`, `frontend`

**Body:**

```markdown
## Contexto
O painel direito mostrará o assembly gerado; já no Sprint 2 deve existir viewer read-only com highlight de assembly.

## Critérios de aceite
- [ ] Segundo Monaco no painel NASM, `readOnly: true`
- [ ] Linguagem/modo `asm` (ou `nasm`) configurado
- [ ] Conteúdo inicial pode ser placeholder ou exemplo estático
- [ ] Scroll e fonte alinhados ao editor principal

## Stack afetado
- frontend

## Referências
- [PRD RF06](prd-simples-online.md#5-requisitos-funcionais)
- [PRD §13](prd-simples-online.md#13-editor-de-código-monaco)
- `SPRINTS.md` — Sprint 2
```

---

### Sprint 3 — Compilation Pipeline

#### Issue 3.1

- **Título:** `feat(backend): package simplesc in backend container multi-stage build`
- **Labels:** `sprint-3`, `devops`

**Body:**

```markdown
## Contexto
O compilador `simplesc` já existe em C; o backend precisa invocá-lo dentro do container de forma reproduzível.

## Critérios de aceite
- [ ] Dockerfile multi-stage compila/copia `simplesc` para imagem final do backend
- [ ] Binário `simplesc` invocável no PATH do container
- [ ] `docker compose build` inclui estágio do compilador sem erro
- [ ] Versão do compilador registrável para health check futuro

## Stack afetado
- devops
- backend

## Referências
- [PRD §8.3 — Compilador](prd-simples-online.md#83-compilador-já-existente)
- [PRD §7.3 — Fluxo de execução](prd-simples-online.md#73-fluxo-de-execução-end-to-end)
- `SPRINTS.md` — Sprint 3
```

---

#### Issue 3.2

- **Título:** `feat(backend): install binutils-i686-linux-gnu for ELF i386 linking`
- **Labels:** `sprint-3`, `devops`

**Body:**

```markdown
## Contexto
Após gerar NASM, o pipeline monta e linka binário ELF i386; `ld -m elf_i386` exige toolchain 32-bit no container.

## Critérios de aceite
- [ ] Pacote `binutils-i686-linux-gnu` (e dependências NASM) instalado na imagem backend
- [ ] `nasm -f elf32` e `ld -m elf_i386` funcionam em smoke test manual ou script
- [ ] Documentado no Dockerfile com comentário do porquê i386

## Stack afetado
- devops
- backend

## Referências
- [PRD RF09](prd-simples-online.md#5-requisitos-funcionais)
- [PRD §2.2 — Premissas (ELF i386)](prd-simples-online.md#22-premissas-técnicas)
- `SPRINTS.md` — Sprint 3
```

---

#### Issue 3.3

- **Título:** `feat(backend): implement POST /api/compile endpoint`
- **Labels:** `sprint-3`, `backend`

**Body:**

```markdown
## Contexto
Antes do WebSocket completo, a compilação expõe REST para validar `simplesc` e retorno de NASM ou erros.

## Critérios de aceite
- [ ] `POST /api/compile` aceita JSON `{ "code": "..." }` autenticado (JWT)
- [ ] Sucesso retorna corpo com NASM gerado (texto ou campo `asm`)
- [ ] Falha de compilação retorna HTTP 4xx com lista de erros estruturados
- [ ] Invoca `simplesc` como subprocesso com captura de stderr

## Stack afetado
- backend

## Referências
- [PRD §9.1 — REST](prd-simples-online.md#91-rest-endpoints)
- [PRD RF05, RF15](prd-simples-online.md#5-requisitos-funcionais)
- `SPRINTS.md` — Sprint 3
```

---

#### Issue 3.4

- **Título:** `feat(backend): parse compile errors into line column message per phase`
- **Labels:** `sprint-3`, `backend`

**Body:**

```markdown
## Contexto
Erros didáticos devem apontar linha/coluna por fase (lexer, parser, semantic) para o frontend marcar o editor.

## Critérios de aceite
- [ ] Parser de stderr/stdout do `simplesc` produz objetos `{ line, column, message, phase }`
- [ ] Fases distinguíveis: `lexer` | `parser` | `semantic` (ou equivalente)
- [ ] Múltiplos erros suportados em uma resposta
- [ ] Erros desconhecidos têm fallback com mensagem genérica sem derrubar API

## Stack afetado
- backend

## Referências
- [PRD RF08](prd-simples-online.md#5-requisitos-funcionais)
- [PRD US-08](prd-simples-online.md#32-user-stories-escopo-v1)
- `SPRINTS.md` — Sprint 3
```

---

#### Issue 3.5

- **Título:** `feat(editor): render compile errors as Monaco markers`
- **Labels:** `sprint-3`, `frontend`

**Body:**

```markdown
## Contexto
Highlight de linha com erro reduz tempo de correção; markers são o padrão Monaco para diagnósticos.

## Critérios de aceite
- [ ] Resposta de erro de `/api/compile` convertida em `monaco.editor.setModelMarkers`
- [ ] Linha com sublinhado/ícone vermelho (severity error)
- [ ] Hover ou gutter mostra mensagem do compilador
- [ ] Markers limpos após compilação bem-sucedida

## Stack afetado
- frontend

## Referências
- [PRD RF08](prd-simples-online.md#5-requisitos-funcionais)
- [PRD §20 — Erro destaca linha](prd-simples-online.md#20-critérios-de-aceite)
- `SPRINTS.md` — Sprint 3
```

---

#### Issue 3.6

- **Título:** `feat(ui): auto-populate NASM panel after successful compile`
- **Labels:** `sprint-3`, `frontend`

**Body:**

```markdown
## Contexto
US-03 exige ver NASM lado a lado após Run; no Sprint 3 o fluxo usa REST (ainda sem execução).

## Critérios de aceite
- [ ] Botão Run chama `POST /api/compile` (substitui mock do Sprint 2)
- [ ] NASM retornado preenche modelo do Monaco do painel direito
- [ ] Painel permanece read-only
- [ ] Loading/erro tratados na UI

## Stack afetado
- frontend

## Referências
- [PRD US-03](prd-simples-online.md#32-user-stories-escopo-v1)
- [PRD RF05, RF06](prd-simples-online.md#5-requisitos-funcionais)
- `SPRINTS.md` — Sprint 3 — Definition of Done
```

---

#### Issue 3.7

- **Título:** `feat(backend): enforce 15s compilation timeout`
- **Labels:** `sprint-3`, `backend`

**Body:**

```markdown
## Contexto
Compilações pathológicas não podem bloquear workers; RF15 define teto de 15 segundos.

## Critérios de aceite
- [ ] Subprocesso `simplesc` (e fases nasm/ld se no mesmo request) com timeout 15s
- [ ] Timeout retorna erro estruturado ao cliente (ex.: `compile_timeout`)
- [ ] Processo filho terminado após timeout (sem zombie)
- [ ] Teste manual ou automatizado documentado

## Stack afetado
- backend

## Referências
- [PRD RF15](prd-simples-online.md#5-requisitos-funcionais)
- [PRD §6.1 — Performance](prd-simples-online.md#61-performance)
- `SPRINTS.md` — Sprint 3
```

---

### Sprint 4 — Interactive Execution

#### Issue 4.1

- **Título:** `feat(backend): implement WebSocket /ws/run with flask-sock`
- **Labels:** `sprint-4`, `backend`

**Body:**

```markdown
## Contexto
`leia` exige stdin interativo; REST não basta — WebSocket autenticado é o canal de compile+run.

## Critérios de aceite
- [ ] Rota `/ws/run` com upgrade WebSocket (flask-sock)
- [ ] Worker gevent (ou config documentada) compatível com WS
- [ ] JWT validado no handshake antes de aceitar conexão
- [ ] Conexão rejeitada com código apropriado se token inválido

## Stack afetado
- backend

## Referências
- [PRD §9.2 — WebSocket `/ws/run`](prd-simples-online.md#92-websocket--wsrun)
- [PRD RF04](prd-simples-online.md#5-requisitos-funcionais)
- [PRD §2.2 — leia obriga WS](prd-simples-online.md#22-premissas-técnicas)
- `SPRINTS.md` — Sprint 4
```

---

#### Issue 4.2

- **Título:** `feat(frontend): integrate xterm.js in terminal panel`
- **Labels:** `sprint-4`, `frontend`

**Body:**

```markdown
## Contexto
O terminal inferior substitui o placeholder por emulador real que receberá stdout/stdin via WebSocket.

## Critérios de aceite
- [ ] `xterm.js` (+ fit addon se necessário) renderizado no painel inferior
- [ ] Terminal redimensiona com o painel
- [ ] Fonte e tema consistentes com IDE dark
- [ ] API exposta para escrever saída e capturar input do usuário

## Stack afetado
- frontend

## Referências
- [PRD §1 — Terminal xterm.js](prd-simples-online.md#1-visão-geral)
- [PRD §8.1 — Frontend](prd-simples-online.md#81-frontend)
- [PRD §12 — UI/UX](prd-simples-online.md#12-uiux)
- `SPRINTS.md` — Sprint 4
```

---

#### Issue 4.3

- **Título:** `feat(devops): build simples-runner image with qemu-user-static`
- **Labels:** `sprint-4`, `devops`

**Body:**

```markdown
## Contexto
Binários i386 não rodam nativamente em ARM64 (OCI Ampere); qemu-user-static emula execução no sandbox.

## Critérios de aceite
- [ ] Imagem Docker `simples-runner` definida e buildável
- [ ] `qemu-user-static` / binfmt configurado para ELF i386
- [ ] Smoke test: executar hello-world i386 dentro do container
- [ ] Documentado no README ou PRD interno do repo

## Stack afetado
- devops

## Referências
- [PRD §2.2 — qemu-user em ARM](prd-simples-online.md#22-premissas-técnicas)
- [PRD §11 — Segurança e sandboxing](prd-simples-online.md#11-segurança-e-sandboxing)
- [PRD §19 — Risco emulação ARM](prd-simples-online.md#19-riscos-e-mitigações)
- `SPRINTS.md` — Sprint 4
```

---

#### Issue 4.4

- **Título:** `feat(backend): implement PtyExecutionStrategy with docker-py attach_socket`
- **Labels:** `sprint-4`, `backend`

**Body:**

```markdown
## Contexto
Execução interativa usa PTY no container; Strategy pattern isola detalhes de docker-py do handler WebSocket.

## Critérios de aceite
- [ ] Classe `PtyExecutionStrategy` implementada
- [ ] `docker run` descartável por execução usando imagem `simples-runner`
- [ ] `attach_socket` (ou API equivalente) para stdin/stdout/stderr
- [ ] Container removido ao fim da sessão (`--rm`)

## Stack afetado
- backend

## Referências
- [PRD §7.4 — Padrões (Strategy)](prd-simples-online.md#74-padrões-de-projeto-aplicados)
- [PRD §11 — Sandbox](prd-simples-online.md#11-segurança-e-sandboxing)
- [PRD RF10](prd-simples-online.md#5-requisitos-funcionais)
- `SPRINTS.md` — Sprint 4
```

---

#### Issue 4.5

- **Título:** `feat(backend): implement bidirectional WS bridge between PTY and xterm`
- **Labels:** `sprint-4`, `backend`

**Body:**

```markdown
## Contexto
Saída do programa deve aparecer em tempo real no xterm; teclas digitadas devem chegar ao stdin do processo.

## Critérios de aceite
- [ ] Task/coroutine `pty_to_ws`: stdout/stderr → mensagens WS → frontend
- [ ] Handler `ws_to_pty`: input do cliente → stdin do PTY
- [ ] Encoding UTF-8 tratado de forma consistente
- [ ] Conexão encerrada limpa buffers e container

## Stack afetado
- backend
- frontend (consumo das mensagens)

## Referências
- [PRD §7.3 — Fluxo (pty_to_ws / ws_to_pty)](prd-simples-online.md#73-fluxo-de-execução-end-to-end)
- [PRD RF11, RF12](prd-simples-online.md#5-requisitos-funcionais)
- `SPRINTS.md` — Sprint 4
```

---

#### Issue 4.6

- **Título:** `feat(runtime): enable interactive leia end-to-end`
- **Labels:** `sprint-4`, `backend`

**Body:**

```markdown
## Contexto
Critério didático central: programa com `leia` pede número, usuário digita no terminal, programa continua e escreve resultado.

## Critérios de aceite
- [ ] Programa SIMPLES com `leia` + `escreva` executa via Run (WebSocket)
- [ ] Prompt visível no xterm; input do usuário entregue ao processo
- [ ] Saída de `escreva` aparece após o input
- [ ] Fluxo testado manualmente com exemplo mínimo do `SPRINTS.md`

## Stack afetado
- frontend
- backend

## Referências
- [PRD US-05](prd-simples-online.md#32-user-stories-escopo-v1)
- [PRD §20 — `leia` no terminal](prd-simples-online.md#20-critérios-de-aceite)
- `SPRINTS.md` — Sprint 4 — Definition of Done
```

---

#### Issue 4.7

- **Título:** `feat(backend): implement WebSocket protocol message types`
- **Labels:** `sprint-4`, `backend`

**Body:**

```markdown
## Contexto
Frontend reage a eventos discretos (Observer); protocolo padronizado evita acoplamento ad hoc.

## Critérios de aceite
- [ ] Mensagens servidor→cliente: `compile_started`, `asm_generated`, `exec_started`, `stdout`, `stdin`, `exit`
- [ ] Mensagens cliente→servidor conforme PRD (ex.: `compile_and_run`, `stdin`, `stop` esqueleto)
- [ ] Payloads JSON documentados e validados minimamente
- [ ] Máquina de estados por conexão respeitada (sem execução antes de compile ok)

## Stack afetado
- backend

## Referências
- [PRD §9.2.1 e §9.2.2 — Mensagens WS](prd-simples-online.md#921-mensagens-cliente--servidor)
- [PRD §9.2.3 — Máquina de estados](prd-simples-online.md#923-máquina-de-estados-do-servidor-por-conexão)
- [PRD §7.4 — Observer](prd-simples-online.md#74-padrões-de-projeto-aplicados)
- `SPRINTS.md` — Sprint 4
```

---

### Sprint 5 — Hardening & Observability

#### Issue 5.1

- **Título:** `feat(ui): implement functional Stop button with WS stop message`
- **Labels:** `sprint-5`, `frontend`

**Body:**

```markdown
## Contexto
Loops infinitos são comuns em exercícios; US-07 exige interromper execução sem recarregar a página.

## Critérios de aceite
- [ ] Botão **Stop** envia `{ "type": "stop" }` no WebSocket
- [ ] Backend propaga SIGTERM ao processo/container
- [ ] SIGKILL após ~1s se processo não encerrar (conforme PRD)
- [ ] UI volta a estado idle em ≤2s (Definition of Done do sprint)

## Stack afetado
- frontend
- backend

## Referências
- [PRD RF13](prd-simples-online.md#5-requisitos-funcionais)
- [PRD US-07](prd-simples-online.md#32-user-stories-escopo-v1)
- [PRD §20 — Stop ≤2s](prd-simples-online.md#20-critérios-de-aceite)
- `SPRINTS.md` — Sprint 5
```

---

#### Issue 5.2

- **Título:** `feat(backend): add 10s wall-clock execution timeout with asyncio`
- **Labels:** `sprint-5`, `backend`

**Body:**

```markdown
## Contexto
RF14 limita execução a 10s wall-clock para proteger o serviço e a turma de loops infinitos.

## Critérios de aceite
- [ ] `asyncio.wait_for` (ou equivalente) com 10s na sessão de execução
- [ ] Cliente recebe evento/mensagem `timeout` ao estourar
- [ ] Recursos (PTY, container) liberados após timeout
- [ ] Loop `enquanto 1 = 1` interrompido em ≤11s (DoD sprint)

## Stack afetado
- backend

## Referências
- [PRD RF14](prd-simples-online.md#5-requisitos-funcionais)
- [PRD §20 — Loop infinito ≤11s](prd-simples-online.md#20-critérios-de-aceite)
- `SPRINTS.md` — Sprint 5
```

---

#### Issue 5.3

- **Título:** `feat(security): configure Docker stop-timeout hard limit`
- **Labels:** `sprint-5`, `security`

**Body:**

```markdown
## Contexto
Camada extra além do timeout em Python: Docker garante que container não sobrevive além do limite hard.

## Critérios de aceite
- [ ] `docker run` usa `--stop-timeout=12` (ou valor acordado com PRD)
- [ ] Container não permanece após stop/timeout do orchestrator
- [ ] Comportamento documentado em comentário no código de execução

## Stack afetado
- backend
- security
- devops

## Referências
- [PRD §4.1 — Timeouts em três camadas](prd-simples-online.md#41-em-escopo-v1)
- [PRD §11 — Sandboxing](prd-simples-online.md#11-segurança-e-sandboxing)
- `SPRINTS.md` — Sprint 5
```

---

#### Issue 5.4

- **Título:** `feat(security): harden sandbox with cap-drop read-only and cgroups`
- **Labels:** `sprint-5`, `security`

**Body:**

```markdown
## Contexto
Código do aluno é não confiável; sandbox deve minimizar superfície de ataque (US-10, RF10).

## Critérios de aceite
- [ ] `--cap-drop=ALL` (e capabilities mínimas se alguma necessária)
- [ ] `--read-only` com tmpfs apenas onde indispensável
- [ ] `--network=none`
- [ ] Limites de cgroup (CPU/memória) configurados conforme PRD
- [ ] Processo roda non-root dentro do container

## Stack afetado
- backend
- security
- devops

## Referências
- [PRD §11 — Segurança e sandboxing](prd-simples-online.md#11-segurança-e-sandboxing)
- [PRD §6.2 — Segurança](prd-simples-online.md#62-segurança)
- [PRD US-10](prd-simples-online.md#32-user-stories-escopo-v1)
- `SPRINTS.md` — Sprint 5
```

---

#### Issue 5.5

- **Título:** `feat(backend): add rate limiting 30 executions per minute per user`
- **Labels:** `sprint-5`, `security`

**Body:**

```markdown
## Contexto
RF18 evita abuso e queda do backend sob carga; limite por `user_id` do JWT.

## Critérios de aceite
- [ ] `flask-limiter` (ou equivalente) configurado
- [ ] 30 execuções/minuto por usuário autenticado
- [ ] Resposta 429 com mensagem clara ao exceder
- [ ] WebSocket `/ws/run` conta execução no mesmo bucket

## Stack afetado
- backend
- security

## Referências
- [PRD RF18](prd-simples-online.md#5-requisitos-funcionais)
- [PRD §6.2 — Rate limiting](prd-simples-online.md#62-segurança)
- `SPRINTS.md` — Sprint 5
```

---

#### Issue 5.6

- **Título:** `feat(backend): add structured JSON logging with structlog`
- **Labels:** `sprint-5`, `backend`

**Body:**

```markdown
## Contexto
Logs estruturados facilitam debug em Docker e preparação para observabilidade em produção.

## Critérios de aceite
- [ ] `structlog` configurado com saída JSON no stdout
- [ ] Campos: timestamp, level, event, `user_id` hasheado (sem PII em claro)
- [ ] Eventos chave: compile_start/end, exec_start/end, timeout, stop, errors
- [ ] Logs visíveis via `docker compose logs backend`

## Stack afetado
- backend

## Referências
- [PRD §6.5 — Observabilidade](prd-simples-online.md#65-observabilidade)
- [PRD §16.1 — Logs](prd-simples-online.md#161-logs)
- `SPRINTS.md` — Sprint 5
```

---

#### Issue 5.7

- **Título:** `feat(backend): expose Prometheus metrics on /metrics`
- **Labels:** `sprint-5`, `backend`

**Body:**

```markdown
## Contexto
Métricas permitem monitorar compilações, execuções e sandboxes ativos; endpoint interno apenas em v1.

## Critérios de aceite
- [ ] `GET /metrics` retorna formato Prometheus `text/plain`
- [ ] Métricas mínimas: duração compile/exec, `executions_total`, `active_sandboxes` (nomes conforme PRD)
- [ ] Endpoint não exposto publicamente via Nginx (rede interna / bind local)
- [ ] Smoke test com `curl` a partir do container ou host documentado

## Stack afetado
- backend
- devops

## Referências
- [PRD §16.2 — Métricas Prometheus](prd-simples-online.md#162-métricas-prometheus-metrics)
- [PRD §20 — Métricas em `/metrics`](prd-simples-online.md#20-critérios-de-aceite)
- `SPRINTS.md` — Sprint 5
```

---

#### Issue 5.8

- **Título:** `feat(security): audit sandbox against escape attempts`
- **Labels:** `sprint-5`, `security`

**Body:**

```markdown
## Contexto
Outro grupo deve revisar segurança; testes manuais/automatizados provam que vetores óbvios falham.

## Critérios de aceite
- [ ] Tentativa de escrever em `/` dentro do sandbox falha
- [ ] Fork bomb ou spawn massivo contido por limites
- [ ] Acesso à rede bloqueado (`curl`/`ping` falham)
- [ ] Resultados registrados (checklist em issue/PR ou `docs/SECURITY-AUDIT.md`)

## Stack afetado
- security
- backend

## Referências
- [PRD §11 — Sandboxing](prd-simples-online.md#11-segurança-e-sandboxing)
- [PRD §19 — Riscos (escape sandbox)](prd-simples-online.md#19-riscos-e-mitigações)
- `SPRINTS.md` — Sprint 5 — Definition of Done
```

---

#### Issue 5.9

- **Título:** `docs(security): document incident response in INCIDENTS.md`
- **Labels:** `sprint-5`, `docs`

**Body:**

```markdown
## Contexto
Se um aluno escapar do sandbox ou o serviço cair, a equipe precisa de playbook de resposta.

## Critérios de aceite
- [ ] Arquivo `docs/INCIDENTS.md` criado
- [ ] Passos: isolar host, revogar tokens, rotacionar secrets, comunicar professor
- [ ] Contatos e severidade (P1/P2) definidos
- [ ] Link no README na seção de segurança

## Stack afetado
- docs
- security

## Referências
- [PRD §19 — Riscos](prd-simples-online.md#19-riscos-e-mitigações)
- `SPRINTS.md` — Sprint 5
```

---

### Sprint 6 — Polish & (Opcional) Deploy

#### Issue 6.1

- **Título:** `test(e2e): add Playwright tests for login run stdin stop timeout`
- **Labels:** `sprint-6`, `frontend`

**Body:**

```markdown
## Contexto
Regressões no fluxo principal (login → editar → run → stdin → stop) devem ser capturadas antes da apresentação.

## Critérios de aceite
- [ ] Playwright configurado no CI ou script local documentado
- [ ] Cenário: login com credenciais de teste
- [ ] Cenário: editar código, Run, ver output
- [ ] Cenário: stdin interativo (`leia`)
- [ ] Cenário: Stop interrompe execução
- [ ] Cenário: timeout após ~10s em loop infinito

## Stack afetado
- frontend
- devops (CI)

## Referências
- [PRD §17.3 — E2E Playwright](prd-simples-online.md#173-e2e-playwright--v11)
- `SPRINTS.md` — Sprint 6
```

---

#### Issue 6.2

- **Título:** `test(backend): reach 70 percent pytest coverage`
- **Labels:** `sprint-6`, `backend`

**Body:**

```markdown
## Contexto
Backend concentra lógica crítica de compilação e sandbox; cobertura mínima garante refatoração segura.

## Critérios de aceite
- [ ] `pytest --cov` reporta ≥ 70% de cobertura de linhas (ou branches, definir no `pyproject`/CI)
- [ ] Testes unitários para strategies e parsers de erro
- [ ] Testes de integração do pipeline compile (fixtures SIMPLES)
- [ ] `make test` ou comando equivalente documentado

## Stack afetado
- backend

## Referências
- [PRD §17.1 — Backend pytest](prd-simples-online.md#171-backend-pytest)
- [PRD §20 — `make test` passa](prd-simples-online.md#20-critérios-de-aceite)
- `SPRINTS.md` — Sprint 6
```

---

#### Issue 6.3

- **Título:** `docs(readme): complete README with GIFs and screenshots`
- **Labels:** `sprint-6`, `docs`

**Body:**

```markdown
## Contexto
Repositório público e apresentação exigem documentação visual do fluxo feliz da IDE.

## Critérios de aceite
- [ ] README com: visão, arquitetura resumida, setup, env vars, troubleshooting
- [ ] GIF ou screenshots: login, editor+NASM, terminal com execução
- [ ] Badges opcionais (CI, cobertura)
- [ ] Créditos e licença da disciplina

## Stack afetado
- docs

## Referências
- [PRD §18 — Fase 2 documentação](prd-simples-online.md#fase-2--estabilização-2-semanas)
- `SPRINTS.md` — Sprint 6
```

---

#### Issue 6.4

- **Título:** `docs(demo): record 2-3 minute demonstration video`
- **Labels:** `sprint-6`, `docs`

**Body:**

```markdown
## Contexto
Vídeo curto facilita correção pelo professor e divulgação do projeto.

## Critérios de aceite
- [ ] Arquivo `docs/demo.mp4` (ou link externo documentado no README)
- [ ] Duração 2–3 minutos
- [ ] Mostra: login, highlight SIMPLES, Run, NASM, `leia`/stdout, Stop
- [ ] Áudio ou legendas explicando o fluxo

## Stack afetado
- docs

## Referências
- `SPRINTS.md` — Sprint 6
```

---

#### Issue 6.5

- **Título:** `feat(deploy): optional Oracle Cloud Ampere A1 deploy with TLS`
- **Labels:** `sprint-6`, `devops`

**Body:**

```markdown
## Contexto
Deploy opcional na OCI valida qemu-user e toolchain em ARM real; vale pontuação extra (+1.0).

## Critérios de aceite
- [ ] Instância Ampere A1 provisionada (Always Free)
- [ ] `docker compose` sobe em produção com Nginx + TLS válido (Let's Encrypt)
- [ ] IDE acessível via HTTPS end-to-end
- [ ] Playbook em PRD §14.7 seguido e checklist iptables OK

## Stack afetado
- devops

## Referências
- [PRD §14.7 — Deploy OCI](prd-simples-online.md#147-deploy-em-produção-oracle-cloud-oci)
- [PRD §20 — Deploy OCI](prd-simples-online.md#20-critérios-de-aceite)
- [PRD §19 — Riscos OCI/iptables](prd-simples-online.md#19-riscos-e-mitigações)
- `SPRINTS.md` — Sprint 6 (opcional)
```

---

#### Issue 6.6

- **Título:** `feat(deploy): optional edu.br domain pointing to instance`
- **Labels:** `sprint-6`, `devops`

**Body:**

```markdown
## Contexto
Domínio institucional opcional melhora apresentação e certificado TLS com nome amigável.

## Critérios de aceite
- [ ] Registro DNS `*.edu.br` (ou subdomínio acordado) aponta para IP da instância
- [ ] Certificado TLS cobre o hostname
- [ ] Documentado no README como URL de demo

## Stack afetado
- devops

## Referências
- `SPRINTS.md` — Sprint 6 (opcional)
- [PRD §15 — Nginx TLS](prd-simples-online.md#15-nginx--reverse-proxy)
```

---

#### Issue 6.7

- **Título:** `docs(presentation): prepare final team presentation`
- **Labels:** `sprint-6`, `docs`

**Body:**

```markdown
## Contexto
Apresentação final consolida arquitetura, decisões e demo ao vivo para a banca/turma.

## Critérios de aceite
- [ ] Slides ou Notion com: problema, arquitetura, demo, segurança, lições
- [ ] Todos os integrantes com parte definida
- [ ] Roteiro de demo alinhado ao vídeo/README
- [ ] Tempo de apresentação dentro do limite da disciplina

## Stack afetado
- docs

## Referências
- `SPRINTS.md` — Sprint 6
- [PRD §1 — Visão geral](prd-simples-online.md#1-visão-geral)
```

---

#### Issue 6.8

- **Título:** `docs(retro): conduct team retrospective`
- **Labels:** `sprint-6`, `docs`

**Body:**

```markdown
## Contexto
Retrospectiva fecha o ciclo ágil do projeto e documenta aprendizados para entregas futuras.

## Critérios de aceite
- [ ] Reunião de retro realizada com a equipe
- [ ] Documento curto: o que funcionou, o que melhorar, ações
- [ ] Arquivo em `docs/RETRO.md` ou seção no README
- [ ] Link ou print no repositório (opcional)

## Stack afetado
- docs

## Referências
- `SPRINTS.md` — Sprint 6
```

---

## 4. Resumo quantitativo

| Sprint | Issues | Milestone |
|--------|--------|-----------|
| 1 | 9 | Sprint 1 — Foundation & Auth |
| 2 | 7 | Sprint 2 — Editor & NASM Panel |
| 3 | 7 | Sprint 3 — Compilation Pipeline |
| 4 | 7 | Sprint 4 — Interactive Execution |
| 5 | 9 | Sprint 5 — Hardening & Observability |
| 6 | 8 | Sprint 6 — Polish & (Opcional) Deploy |
| **Total** | **47** | |

---

## 5. PROGRESS.md (preview — criar após issues existirem)

Após `gh issue create`, numerar `#N` reais e substituir placeholders abaixo.

```markdown
# Progress — Simples Editor

> Atualizar conforme issues forem fechadas. Gerado a partir de `SPRINTS.md`.

## Sprint 1 — Foundation & Auth
- [ ] #__ — chore(repo): initialize GitHub repository and README
- [ ] #__ — chore(project): configure GitHub Project Kanban with automations
- [ ] #__ — feat(infra): add docker-compose with nginx frontend and backend skeletons
- [ ] #__ — feat(infra): verify docker compose up serves localhost homepage
- [ ] #__ — feat(auth): configure Supabase project and Auth
- [ ] #__ — feat(frontend): implement login screen with email and password
- [ ] #__ — feat(backend): add verify_jwt decorator for protected endpoints
- [ ] #__ — feat(backend): implement GET /api/health endpoint
- [ ] #__ — docs(process): validate PR workflow with one merge per team member

## Sprint 2 — Editor & NASM Panel
- [ ] #__ — feat(editor): integrate Monaco Editor on main route
- [ ] #__ — feat(editor): register simples language with Monarch tokenizer
- [ ] #__ — feat(editor): apply dark theme with keyword highlighting
- [ ] #__ — feat(ui): implement three-panel layout with terminal placeholder
- [ ] #__ — feat(ui): add resizable splitter between editor and NASM panels
- [ ] #__ — feat(ui): add mock Run button with compiling state
- [ ] #__ — feat(editor): add read-only NASM panel with Monaco asm mode

## Sprint 3 — Compilation Pipeline
- [ ] #__ — feat(backend): package simplesc in backend container multi-stage build
- [ ] #__ — feat(backend): install binutils-i686-linux-gnu for ELF i386 linking
- [ ] #__ — feat(backend): implement POST /api/compile endpoint
- [ ] #__ — feat(backend): parse compile errors into line column message per phase
- [ ] #__ — feat(editor): render compile errors as Monaco markers
- [ ] #__ — feat(ui): auto-populate NASM panel after successful compile
- [ ] #__ — feat(backend): enforce 15s compilation timeout

## Sprint 4 — Interactive Execution
- [ ] #__ — feat(backend): implement WebSocket /ws/run with flask-sock
- [ ] #__ — feat(frontend): integrate xterm.js in terminal panel
- [ ] #__ — feat(devops): build simples-runner image with qemu-user-static
- [ ] #__ — feat(backend): implement PtyExecutionStrategy with docker-py attach_socket
- [ ] #__ — feat(backend): implement bidirectional WS bridge between PTY and xterm
- [ ] #__ — feat(runtime): enable interactive leia end-to-end
- [ ] #__ — feat(backend): implement WebSocket protocol message types

## Sprint 5 — Hardening & Observability
- [ ] #__ — feat(ui): implement functional Stop button with WS stop message
- [ ] #__ — feat(backend): add 10s wall-clock execution timeout with asyncio
- [ ] #__ — feat(security): configure Docker stop-timeout hard limit
- [ ] #__ — feat(security): harden sandbox with cap-drop read-only and cgroups
- [ ] #__ — feat(backend): add rate limiting 30 executions per minute per user
- [ ] #__ — feat(backend): add structured JSON logging with structlog
- [ ] #__ — feat(backend): expose Prometheus metrics on /metrics
- [ ] #__ — feat(security): audit sandbox against escape attempts
- [ ] #__ — docs(security): document incident response in INCIDENTS.md

## Sprint 6 — Polish & (Opcional) Deploy
- [ ] #__ — test(e2e): add Playwright tests for login run stdin stop timeout
- [ ] #__ — test(backend): reach 70 percent pytest coverage
- [ ] #__ — docs(readme): complete README with GIFs and screenshots
- [ ] #__ — docs(demo): record 2-3 minute demonstration video
- [ ] #__ — feat(deploy): optional Oracle Cloud Ampere A1 deploy with TLS
- [ ] #__ — feat(deploy): optional edu.br domain pointing to instance
- [ ] #__ — docs(presentation): prepare final team presentation
- [ ] #__ — docs(retro): conduct team retrospective
```

---

## 6. Próximo passo (após sua aprovação)

1. Confirmar **owner/repo** (`gh repo view --json nameWithOwner`)
2. Criar milestones → labels → issues (script ou loop `gh issue create`)
3. Atualizar `PROGRESS.md` na raiz com números reais das issues
4. Adicionar todas as issues ao GitHub Project

**Ajustes comuns na revisão:** agrupar entregáveis pequenos, renomear scopes (`infra` vs `devops`), datas das milestones, issues opcionais do Sprint 6 com label extra `optional`.
