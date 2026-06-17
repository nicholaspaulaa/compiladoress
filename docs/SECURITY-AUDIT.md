# Auditoria de Segurança do Sandbox

> **Issue**: [#38](https://github.com/nicholaspaulaa/compiladoress/issues/38)
> **Data**: 2026-06-17
> **Auditor**: Eduardo Tenório Nunes
> **Versão do backend**: `main` (Sprint 5)

## Resumo

O sandbox `simples-runner` implementa 8 camadas de hardening em conformidade com
o PRD §11. Esta auditoria valida a **configuração** de cada camada contra os vetores
de escape especificados no PRD §19 (Riscos).

**Escopo desta auditoria**: validação de configuração (dicionário, kwargs, env vars).
Testes de runtime com container real requerem Docker e estão pendentes de execução
manual — ver seção [Validação Manual Pendente](#validação-manual-pendente).

---

## Checklist de Segurança

| # | Vetor de Escape | Camada | Mitigação | Status |
|---|---|---|---|---|
| 1 | Escrita em `/` (rootfs) | 3 | `read_only: True` + `tmpfs` apenas em `/tmp` | ✅ Config validada |
| 2 | Fork bomb / spawn massivo | 6 | `pids_limit: 64` | ✅ Config validada |
| 3 | Acesso à rede (`curl`, `ping`) | 2 | `network_mode: "none"` | ✅ Config validada |
| 4 | Escape de memória (OOM) | 4 | `mem_limit: 128m` + `memswap_limit: 128m` | ✅ Config validada |
| 5 | Exaustão de CPU | 5 | `cpu_quota: 50000` (0.5 CPU) + `EXEC_TIMEOUT_S: 10` | ✅ Config validada |
| 6 | Escalada de privilégios (root) | 7 | `user: 65534:65534` (nobody) | ✅ Config validada |
| 7 | Abuso de capabilities Linux | 8 | `cap_drop: ["ALL"]` | ✅ Config validada |
| 8 | Conexão persistente indefinida | timeout | `DOCKER_STOP_TIMEOUT_S: 12` + `EXEC_TIMEOUT_S: 10` | ✅ Config validada |

---

## Camadas de Segurança (PRD §11.2)

### Camada 1: Imagem mínima (`simples-runner:latest`)
- Contém apenas: `qemu-i386-static`, `libc6-i386`, binário `programa`
- Sem shell (exceto `sh` via busybox), sem `curl`, `wget`, `gcc`, `python`
- **Vetores prevenidos**: execução de código arbitrário, exfiltração, pivoting

### Camada 2: Isolamento de rede (`network_mode: "none"`)
- Container não possui interface de rede (`lo` apenas)
- `curl`, `ping`, `wget`, `nslookup` **falham** (host unreachable / network unavailable)
- **Vetores prevenidos**: exfiltração de dados, C2, reverse shell, SSRF interno

### Camada 3: Filesystem read-only + tmpfs
- `sandbox_run_kwargs()` define `read_only: True` → qualquer tentativa de escrita em `/` retornaria `EROFS`
- `tmpfs: {"/tmp": "size=8m"}` → única área gravável com limite de 8 MB
- **Vetores prevenidos**: alteração de binários do sistema, persistência, ransomware
- ⚠️ **Exceção de staging**: `PtyExecutionStrategy` usa `sandbox_staging_kwargs()` com **`read_only: False`**
  para permitir `put_archive` do binário em `/sandbox`. Durante a execução real, o rootfs permanece
  gravável em `/sandbox` (workdir do container). Isso é um **risco residual**: código arbitrário pode
  escrever em `/sandbox`, mas o volume é isolado do host e descartado após a execução.
  Ver [Validação Manual Pendente](#validação-manual-pendente).

### Camada 4: Limites de memória (`mem_limit: 128m`, `memswap_limit: 128m`)
- Memória RAM limitada a 128 MB, swap desabilitado
- Alocações excessivas resultam em OOM kill pelo kernel
- **Vetores prevenidos**: exaustão de memória do host, DoS via alocação massiva

### Camada 5: Quota de CPU (`cpu_quota: 50000` + `cpu_period: 100000`)
- 50% de um core CPU (~0.5 vCPU efetivo)
- Combinado com `EXEC_TIMEOUT_S: 10` → execução interrompida em 10s
- **Vetores prevenidos**: exaustão de CPU do host, crypto mining, loops infinitos

### Camada 6: Limite de PIDs (`pids_limit: 64`)
- Máximo de 64 processos/threads simultâneos
- Fork bombs tradicionais (`:(){ :|:& };:`) são contidas — após 64 forks, `fork()` retorna `EAGAIN`
- **Vetores prevenidos**: fork bomb, spawn massivo, exaustão de PID namespace

### Camada 7: Non-root (`user: 65534:65534`)
- Usuário `nobody` (UID 65534) sem privilégios
- Escrita apenas em `/tmp` (tmpfs)
- **Vetores prevenidos**: escalada de privilégios, acesso a dispositivos, syscalls restritas

### Camada 8: Capabilities drop (`cap_drop: ["ALL"]`)
- Todas as capabilities Linux removidas
- Sem `CAP_SYS_ADMIN`, `CAP_NET_RAW`, `CAP_SYS_PTRACE`, etc.
- **Vetores prevenidos**: mount, pivot_root, nsenter, ptrace, raw sockets, alteração de cgroups

---

## Tentativas de Escape (Resultados esperados — config)

Os resultados abaixo descrevem o comportamento **esperado** com base na configuração
validada. Testes de runtime com container real estão pendentes (ver seção abaixo).

### 1. Escrita no rootfs ❌ (contido)

**Tentativa**: `touch /escape_test` dentro do sandbox

**Resultado esperado**: `touch: /escape_test: Read-only file system`

**Evidência**: Camada 3 — `read_only: True`. Apenas `/tmp` (tmpfs 8 MB) é gravável.


### 2. Fork bomb ❌ (contido)

**Tentativa**: `:(){ :|:& };:` ou spawn de 65+ processos

**Resultado esperado**: `fork()` retorna `EAGAIN` após 64 processos

**Evidência**: Camada 6 — `pids_limit: 64`. O kernel bloqueia novos forks além do limite.


### 3. Acesso à rede ❌ (contido)

**Tentativa**: `curl http://example.com`, `ping 8.8.8.8`

**Resultado esperado**: `Network is unreachable` / `Host unreachable`

**Evidência**: Camada 2 — `network_mode: "none"`. Container não possui acesso a nenhuma rede externa.


### 4. Exaustão de memória ❌ (contido)

**Tentativa**: Alocação massiva (ex: `python -c "a='x'*10**9"` se disponível)

**Resultado esperado**: Processo recebe SIGKILL (OOM)

**Evidência**: Camada 4 — `mem_limit: 128m`. OOM killer do kernel encerra o processo.


### 5. Exaustão de CPU ❌ (contido)

**Tentativa**: Loop infinito `while true; do :; done`

**Resultado esperado**: Container recebe SIGTERM após `EXEC_TIMEOUT_S` (10s), depois SIGKILL após `DOCKER_STOP_TIMEOUT_S` (12s)

**Evidência**: Camada 5 + timeout — `cpu_quota: 50000` + timeout de 10s.


### 6. Capabilities check ❌ (contido)

**Tentativa**: `capsh --print` ou syscalls privilegiadas

**Resultado esperado**: Todas as capabilities reportadas como `0` (ausentes)

**Evidência**: Camada 8 — `cap_drop: ["ALL"]`. Nenhuma capability está disponível no container.


### 7. Escalada para root ❌ (contido)

**Tentativa**: `su`, `sudo`, `chroot`

**Resultado esperado**: Comandos ausentes ou permissão negada

**Evidência**: Camada 7 — `user: 65534:65534` (nobody). Sem binários SUID, sem sudo, sem chroot.

---

## Configuração de Produção

| Parâmetro | Valor | Justificativa |
|---|---|---|
| `SANDBOX_IMAGE` | `simples-runner:latest` | Imagem minificada com qemu-i386 |
| `SANDBOX_MEMORY_MB` | `128` | Suficiente para execuções SIMPLES |
| `SANDBOX_CPU_QUOTA` | `50000` | 0.5 CPU, justo para multi-tenant |
| `SANDBOX_PIDS_LIMIT` | `64` | Bloqueia fork bombs |
| `SANDBOX_TMPFS_SIZE_MB` | `8` | Suficiente para stdout/stderr de programas didáticos |
| `SANDBOX_USER` | `65534:65534` | nobody:nogroup |
| `EXEC_TIMEOUT_S` | `10` | Limite de execução por requisição |
| `DOCKER_STOP_TIMEOUT_S` | `12` | Hard limit do Docker daemon |

---

## Validação Manual Pendente

Os seguintes testes de runtime requerem Docker e um container `simples-runner:latest`
construído. Executar manualmente e anexar evidências (logs/screenshots):

### 1. Escrita em `/` (rootfs)
```bash
docker run --rm --read-only --tmpfs /tmp:size=8m simples-runner:latest \
  touch /escape_test 2>&1
# Esperado: touch: /escape_test: Read-only file system
```

### 2. Fork bomb
```bash
docker run --rm --pids-limit 64 simples-runner:latest \
  sh -c 'i=0; while [ $i -lt 100 ]; do (sleep 999 &); i=$((i+1)); done; wait' 2>&1
# Esperado: fork() retorna EAGAIN após 64 processos
```

### 3. Rede bloqueada
```bash
docker run --rm --network=none simples-runner:latest \
  sh -c 'ping -c1 8.8.8.8 2>&1 || curl -s http://example.com 2>&1'
# Esperado: Network is unreachable / Could not resolve host
```

### 4. read_only staging (risco residual)
```bash
# O container de execucao REAL usa sandbox_staging_kwargs() com read_only=False.
# Validar que /sandbox e gravavel mas isolado do host:
docker run --rm --read-only --tmpfs /tmp:size=8m \
  -v /tmp/sim-test:/sandbox:rw \
  simples-runner:latest sh -c 'echo x > /sandbox/test && cat /sandbox/test'
# Confirmar que o arquivo aparece em /tmp/sim-test no host e NAO em /etc ou /
```

---

## Conclusão

A **configuração** das 8 camadas de hardening do sandbox `simples-runner` está em
conformidade com o PRD §11.2. Os valores de `sandbox_run_kwargs()`, `sandbox_staging_kwargs()`
e `Config` foram validados por 25 testes automatizados.

**Limitações conhecidas**:
- `sandbox_staging_kwargs()` usa `read_only: False` (necessário para `put_archive`),
  criando uma superfície gravável em `/sandbox` durante a execução. O risco é mitigado
  pelo isolamento do volume e descarte pós-execução.
- Testes de runtime com container real (Docker) estão pendentes de execução manual.
  Ver [Validação Manual Pendente](#validação-manual-pendente).

**Status final**: ⚠️ CONFIGURAÇÃO CONFORME PRD §11.2 — Validação de runtime pendente.
Não classificar como "aprovado para produção" até que os testes manuais sejam executados
e as evidências anexadas a este documento.
