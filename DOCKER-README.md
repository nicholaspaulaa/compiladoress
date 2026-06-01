# Instruções rápidas — Docker Compose

1. Construir e subir containers:

```bash
docker compose up --build
```

2. Acesse o frontend em: http://localhost/
3. Endpoint de teste do backend: http://localhost:5000/api/health

Observações:
- O serviço `nginx` usa a pasta `frontend` como conteúdo estático (montada como volume).
- O `backend` é um exemplo mínimo em Flask para servir um endpoint de saúde.
