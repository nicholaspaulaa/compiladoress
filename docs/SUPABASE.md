# Supabase — configuracao (issue #5)

Passos para criar o projeto de auth do **Simples Editor**.

## 1. Criar projeto

1. Acesse [supabase.com/dashboard](https://supabase.com/dashboard)
2. **New project** → escolha organizacao, nome (ex.: `simples-editor`) e senha do banco
3. Aguarde o provisionamento (free tier)

## 2. Habilitar email/senha

1. **Authentication** → **Providers**
2. **Email** → habilitado (padrao)
3. Em **Authentication** → **Users**, use **Add user** para criar contas de teste da equipe  
   (ou desabilite "Confirm email" em **Providers → Email** durante desenvolvimento)

## 3. Copiar credenciais

**Project Settings** → **API**:

| Variavel | Onde pegar |
|----------|------------|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_ANON_KEY` | anon / public key |
| `SUPABASE_JWT_SECRET` | JWT Secret (legado HS256; projetos novos usam ES256 via JWKS) |

## 4. Configurar localmente

### Backend + Docker

```bash
cp .env.example .env
# Edite .env com SUPABASE_URL, SUPABASE_ANON_KEY e SUPABASE_JWT_SECRET
docker compose up --build
```

O `docker-compose.yml` repassa as variaveis para o servico `backend` e para o build do `frontend`.

### Frontend com `npm run dev`

O Vite **nao le** o `.env` da raiz. Crie `frontend/.env.local` com prefixo **`VITE_`**:

```bash
cp frontend/.env.example frontend/.env.local
# Edite com os mesmos URL e anon key do Supabase
```

Reinicie o dev server apos alterar env (`Ctrl+C` e `npm run dev` de novo).

## 5. Testar JWT no backend (issue #7)

1. Faca login no Supabase (frontend futuro) ou obtenha um `access_token` via API:

```bash
curl -s -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"seu@email.com","password":"sua-senha"}' | jq -r .access_token
```

2. Chame o endpoint protegido:

```bash
curl -X POST http://localhost/api/auth/verify \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

Resposta esperada:

```json
{"valid": true, "user_id": "uuid...", "email": "seu@email.com"}
```

Sem token ou token invalido → `401` com corpo JSON.

## Referencias

- [PRD §10 — Modelo de dados (Supabase)](../prd-simples-online.md#10-modelo-de-dados-supabase)
- [PRD §11.1 — Autenticacao](../prd-simples-online.md#111-autenticação-e-autorização)
