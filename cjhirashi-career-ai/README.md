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

## Estado (2026-11-05)

En construcción, **no desplegado** (spec 009, etapa 1; 62 de 163 tareas): no hay servicio en `docker-compose.yml` ni ruta `/ai/` en `caddy.json`, y el Admin sigue hablando con el harness que vive en la API (`cjhirashi-career-api/src/services/bedrock/`).

- **Hecho**: configuración, base propia (`career_ai_db`, Alembic propio), modelos y repositorios, cliente de la API de datos, proveedor Bedrock y el port de los servicios del harness (`agent_loop`, perfiles y catálogo, memoria con búsqueda de texto completo, herramientas, adjuntos, uso y costos).
- **Expuesto hoy**: solo `GET /health`. Las rutas con paridad `/bedrock/*` y `/agent-tasks/*` llegan en la etapa 1 y el Admin se conecta a `/ai/` en la etapa 2.
- **Retiro de la API** (Bedrock, KB y Qdrant): etapa 3. Plan y contrato: `.harness/specs/009-harness-agentes-fuera-de-api/` y [ADR-029](../docs/09-DECISIONS/029-harness-agentes-fuera-de-api.md).
