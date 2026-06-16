# Instruções rápidas — Docker Compose

## 1. Configurar Supabase

```bash
cp .env.example .env
```

Edite `.env` com `SUPABASE_URL`, `SUPABASE_ANON_KEY` e `SUPABASE_JWT_SECRET`.  
Passo a passo: [docs/SUPABASE.md](./docs/SUPABASE.md).

## 2. Subir containers

```bash
docker compose up --build
```

## 3. Endpoints

| URL | Auth | Descricao |
|-----|------|-----------|
| http://localhost/ | JWT (apos login) | IDE (placeholder) |
| http://localhost/login | — | Tela de login (email/senha) |
| http://localhost/api/health | publico | Health check |
| http://localhost/api/auth/verify | Bearer JWT | Valida token Supabase (POST) |
| ws://localhost/ws/run | JWT (`?token=` ou `Sec-WebSocket-Protocol: bearer.<jwt>`) | Canal compile+run (PRD §9.2) |
| http://localhost:5000/api/health | publico | Backend direto (debug) |

## Observacoes

- O servico `nginx` faz proxy do frontend React (`/`, `/login`), de `/api/*` e de `/ws/*` para o `backend`.
- O container `frontend` e construido com `SUPABASE_URL` e `SUPABASE_ANON_KEY` do `.env` (build Vite).
- Credenciais Supabase ficam em `.env` (nao versionado).
- Sem `.env`, o backend sobe mas `/api/auth/verify` retorna 503 ate configurar o JWT secret.

## 4. Imagem `simples-runner` (sandbox de execução)

A imagem `simples-runner:latest` é construída automaticamente pelo serviço
`runner_image_build` do `docker compose`. Ela contém:

- **`qemu-user-static`** — emula binários ELF i386 em hosts x86_64 e ARM64
- **Usuário `nobody` (65534)** — execução não-root obrigatória
- **`WORKDIR /sandbox`** — ponto de montagem do volume com o binário

O backend invoca:

    docker run --rm --network=none --read-only \
      --memory=128m --cpus=0.5 --pids-limit=64 \
      --cap-drop=ALL --user=65534:65534 \
      -v /tmp/sim-<uuid>:/sandbox:ro \
      simples-runner:latest /usr/bin/qemu-i386-static /sandbox/programa

### Smoke test

Para validar a imagem:

```bash
# Construir a imagem
docker compose build runner_image_build

# Rodar smoke test (requer nasm + linker elf_i386 no host)
chmod +x runner/smoke-test.sh
./runner/smoke-test.sh
```
