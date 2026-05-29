# Progress — Simples Editor

> Atualizar conforme issues forem fechadas. Gerado por `scripts/create_github_issues.py`.

## Sprint 1 — Foundation & Auth
- [ ] #1 — chore(repo): initialize GitHub repository and README
- [ ] #2 — chore(project): configure GitHub Project Kanban with automations
- [ ] #3 — feat(infra): add docker-compose with nginx frontend and backend skeletons
- [ ] #4 — feat(infra): verify docker compose up serves localhost homepage
- [ ] #5 — feat(auth): configure Supabase project and Auth
- [ ] #6 — feat(frontend): implement login screen with email and password
- [ ] #7 — feat(backend): add verify_jwt decorator for protected endpoints
- [ ] #8 — feat(backend): implement GET /api/health endpoint
- [ ] #9 — docs(process): validate PR workflow with one merge per team member

## Sprint 2 — Editor & NASM Panel
- [ ] #10 — feat(editor): integrate Monaco Editor on main route
- [ ] #11 — feat(editor): register simples language with Monarch tokenizer
- [ ] #12 — feat(editor): apply dark theme with keyword highlighting
- [ ] #13 — feat(ui): implement three-panel layout with terminal placeholder
- [ ] #14 — feat(ui): add resizable splitter between editor and NASM panels
- [ ] #15 — feat(ui): add mock Run button with compiling state
- [ ] #16 — feat(editor): add read-only NASM panel with Monaco asm mode

## Sprint 3 — Compilation Pipeline
- [ ] #17 — feat(backend): package simplesc in backend container multi-stage build
- [ ] #18 — feat(backend): install binutils-i686-linux-gnu for ELF i386 linking
- [ ] #19 — feat(backend): implement POST /api/compile endpoint
- [ ] #20 — feat(backend): parse compile errors into line column message per phase
- [ ] #21 — feat(editor): render compile errors as Monaco markers
- [ ] #22 — feat(ui): auto-populate NASM panel after successful compile
- [ ] #23 — feat(backend): enforce 15s compilation timeout

## Sprint 4 — Interactive Execution
- [ ] #24 — feat(backend): implement WebSocket /ws/run with flask-sock
- [ ] #25 — feat(frontend): integrate xterm.js in terminal panel
- [ ] #26 — feat(devops): build simples-runner image with qemu-user-static
- [ ] #27 — feat(backend): implement PtyExecutionStrategy with docker-py attach_socket
- [ ] #28 — feat(backend): implement bidirectional WS bridge between PTY and xterm
- [ ] #29 — feat(runtime): enable interactive leia end-to-end
- [ ] #30 — feat(backend): implement WebSocket protocol message types

## Sprint 5 — Hardening & Observability
- [ ] #31 — feat(ui): implement functional Stop button with WS stop message
- [ ] #32 — feat(backend): add 10s wall-clock execution timeout with asyncio
- [ ] #33 — feat(security): configure Docker stop-timeout hard limit
- [ ] #34 — feat(security): harden sandbox with cap-drop read-only and cgroups
- [ ] #35 — feat(backend): add rate limiting 30 executions per minute per user
- [ ] #36 — feat(backend): add structured JSON logging with structlog
- [ ] #37 — feat(backend): expose Prometheus metrics on /metrics
- [ ] #38 — feat(security): audit sandbox against escape attempts
- [ ] #39 — docs(security): document incident response in INCIDENTS.md

## Sprint 6 — Polish & (Opcional) Deploy
- [ ] #40 — test(e2e): add Playwright tests for login run stdin stop timeout
- [ ] #41 — test(backend): reach 70 percent pytest coverage
- [ ] #42 — docs(readme): complete README with GIFs and screenshots
- [ ] #43 — docs(demo): record 2-3 minute demonstration video
- [ ] #44 — feat(deploy): optional Oracle Cloud Ampere A1 deploy with TLS
- [ ] #45 — feat(deploy): optional edu.br domain pointing to instance
- [ ] #46 — docs(presentation): prepare final team presentation
- [ ] #47 — docs(retro): conduct team retrospective
