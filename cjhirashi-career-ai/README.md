# cjhirashi-career-ai

Harness de agentes de cjhirashi-career (chat, herramientas, memoria, tareas programadas),
separado de la API de datos (spec 009, `.harness/specs/009-harness-agentes-fuera-de-api/`).

- Patron en capas: `routes -> services -> repositories -> models`, mas `providers/` (salida al
  modelo) y `clients/` (salida a la API de datos).
- BD propia (`career_ai_db`); no accede a `career_db` ni a Qdrant.
- Externamente servido bajo `/ai/` (Caddy quita el prefijo); puerto interno 8010.

## Desarrollo

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/pytest            # cobertura >= 80 %
```

Los tests que necesitan Postgres real (secuencias, tsvector, GIN) usan `TEST_DATABASE_URL`
(base DESECHABLE, nunca la de desarrollo) y se saltan si no esta definida:

```bash
docker run -d --rm --name career-ai-testdb -e POSTGRES_PASSWORD=test \
  -p 127.0.0.1:55432:5432 postgres:15-alpine
export TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@127.0.0.1:55432/postgres
```
