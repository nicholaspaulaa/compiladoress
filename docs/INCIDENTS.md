# Plano de Resposta a Incidentes (Incident Response)

> **Issue**: [#39](https://github.com/nicholaspaulaa/compiladoress/issues/39)
> **Versão**: Sprint 5 — Hardening & Observability
> **Última atualização**: 2026-06-17

## Contatos de Emergência

| Papel | Nome | Severidades |
|---|---|---|
| **Coordenador de Segurança** | Nicholas Emanuell Lima de Paula | P1, P2 |
| **Desenvolvedor Backend** | Eduardo Tenório Nunes | P1, P2 |
| **Desenvolvedora Frontend** | Érica de Souza Guerzoni Ribeiro | P1, P2 |
| **Professor Responsável** | A informar pelo coordenador | P1 |

## Níveis de Severidade

| Severidade | Descrição | Exemplos | SLA de resposta |
|---|---|---|---|
| **P1 — Crítico** | Serviço indisponível, escape de sandbox confirmado, vazamento de dados | Backend fora do ar por >5 min, aluno executou código no host, secrets expostos | Imediato (acionar todos) |
| **P2 — Alto** | Funcionalidade degradada, suspeita de violação, anomalia de segurança | Rate limit não funciona, logs suspeitos, falha intermitente | Até 2 horas |

## Playbooks de Resposta

---

### P1 — Escape de Sandbox Confirmado

**Indicadores**:
- Logs mostram processos não esperados no host
- Consumo anormal de CPU/memória/IO no servidor
- Arquivos desconhecidos aparecem fora de `/tmp/simples-*`
- Alerta do Docker (container com `network_mode` diferente de `none`)

**Resposta imediata**:

1. **Isolar o host** (5 min)
   ```bash
   # Bloquear acesso externo ao backend
   docker compose stop backend

   # Verificar containers em execução
   docker ps -a --filter "name=simples-"

   # Matar qualquer container suspeito
   docker rm -f $(docker ps -aq --filter "name=simples-")
   ```

2. **Revogar tokens** (10 min)
   - Acessar [Supabase Dashboard](https://supabase.com/dashboard) → Authentication → Users
   - Identificar o usuário suspeito pelo `user_id` dos logs
   - Revogar todas as sessões do usuário: **Ban User**
   - Se necessário, revogar todos os tokens ativos: **Settings → Auth → Revoke all tokens**

3. **Rotacionar secrets** (15 min)
   ```bash
   # Gerar nova JWT secret no Supabase
   # Settings → API → JWT Settings → Generate New Secret

   # Atualizar .env do repositório
   # SUPABASE_JWT_SECRET=<nova_secret>

   # Rotacionar SUPABASE_ANON_KEY se comprometida
   ```

4. **Comunicar professor** (5 min)
   - Enviar email/WhatsApp com:
     - Data/hora do incidente
     - Natureza: escape de sandbox
     - Ações tomadas (isolamento, revogação, rotação)
     - Impacto: quais usuários/dados foram afetados
     - Próximos passos e ETA de restauração

5. **Investigar e corrigir** (pós-contenção)
   - Analisar logs: `docker logs <container_id>`
   - Verificar métricas Prometheus: `GET /metrics`
   - Identificar vetor de escape e corrigir (ver [SECURITY-AUDIT.md](./SECURITY-AUDIT.md))
   - Restaurar serviço após correção: `docker compose up -d backend`
   - Testar com suite de segurança: `pytest tests/test_sandbox_security.py -v`

---

### P1 — Serviço Indisponível (Backend Down)

**Indicadores**:
- `GET /api/health` retorna erro ou timeout
- Métricas Prometheus zeradas ou ausentes
- Frontend mostra erros de conexão

**Resposta imediata**:

1. **Diagnosticar** (2 min)
   ```bash
   docker compose ps          # Verificar status dos serviços
   docker compose logs backend --tail=100  # Últimas 100 linhas de log
   curl http://localhost:5000/api/health   # Health check direto
   ```

2. **Restaurar** (5 min)
   ```bash
   docker compose restart backend
   # Se não resolver:
   docker compose down && docker compose up -d
   ```

3. **Comunicar** se >5 min offline (professor e equipe)

---

### P2 — Suspeita de Abuso (Rate Limit / Token)

**Indicadores**:
- Múltiplos 429 em curto período do mesmo `user_id`
- Tentativas de acesso com tokens inválidos em massa
- Volume anormal de requisições `/api/compile`

**Resposta**:

1. **Investigar** (15 min)
   ```bash
   # Verificar métricas
   curl http://localhost:5000/metrics | grep -E "compile_requests|websocket_connections"

   # Verificar logs do backend
   docker compose logs backend | grep -E "429|rate_limit|invalid token"
   ```

2. **Mitigar** (se necessário)
   - Identificar `user_id` abusivo nos logs
   - Banir usuário no Supabase Dashboard
   - Ajustar temporariamente o rate limit se sob ataque DDoS:
     ```
     # No .env:
     # (não aplicável sem reload — requer novo deploy)
     ```

---

### P2 — Segredos Expostos Acidentalmente

**Indicadores**:
- Commit com `.env` ou secrets no histórico do Git
- Logs contendo tokens JWT ou secrets

**Resposta**:

1. **Rotacionar imediatamente** (10 min)
   - Supabase: gerar nova JWT Secret e Anon Key
   - Atualizar `.env` local e no servidor
   - Fazer deploy com os novos valores

2. **Limpar histórico** (se commitado)
   ```bash
   # NUNCA commitar .env — verificar .gitignore
   git rm --cached .env   # se já trackeado
   git commit -m "chore: remove .env do tracking"
   ```

3. **Comunicar equipe** sobre novos valores de secrets

---

## Procedimentos Periódicos

| Procedimento | Frequência | Responsável |
|---|---|---|
| Rotacionar secrets Supabase | A cada sprint | Coordenador |
| Revisar logs de segurança | Semanal | Backend Dev |
| Testar playbooks de resposta | Mensal | Toda equipe |
| Atualizar este documento | A cada incidente ou sprint | Coordenador |

## Referências

- [PRD §19 — Riscos e Mitigações](../prd-simples-online.md#19-riscos-e-mitigações)
- [SECURITY-AUDIT.md](./SECURITY-AUDIT.md) — Auditoria das camadas de segurança do sandbox
- [SPRINTS.md](../SPRINTS.md) — Plano de sprints e Definition of Done
- [Supabase Docs — Auth](https://supabase.com/docs/guides/auth)
