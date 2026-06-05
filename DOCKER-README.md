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
| http://localhost/ | — | Frontend estatico |
| http://localhost/api/health | publico | Health check |
| http://localhost/api/auth/verify | Bearer JWT | Valida token Supabase (POST) |
| http://localhost:5000/api/health | publico | Backend direto (debug) |

## Observacoes

- O servico `nginx` serve a pasta `frontend` e faz proxy de `/api/*` para o `backend`.
- Credenciais Supabase ficam em `.env` (nao versionado).
- Sem `.env`, o backend sobe mas `/api/auth/verify` retorna 503 ate configurar o JWT secret.
