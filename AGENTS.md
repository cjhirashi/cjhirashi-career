# AGENTS.md — mapa de cjhirashi-career

> **Punto de entrada** para cualquier agente que trabaje en este repo. Es un **mapa**,
> no una biblia: lee sólo lo que necesites, cuando lo necesites.
>
> **Cómo trabajamos:** este repo usa un arnés **SDD Anchored** (spec viva anclada al
> código). Empieza por **`.harness/method.md §0`**. Los principios innegociables están
> en **`.harness/constitution.md`**.
>
> **Separación estricta:** `.harness/` = cómo operamos · `docs/` = el producto (arc42,
> ADRs, diseño). Nada del arnés en `docs/`.

## Antes de empezar (en orden)

1. Ejecuta **`.harness/gate/check.sh`**. Si cierra la compuerta (exit 1 / algún ❌),
   **DETENTE** y reporta. No se programa sobre un entorno roto.
2. Lee **`.harness/memory/state.md`** completo (es corto; las correcciones del usuario
   van arriba y se leen SIEMPRE).
3. Ojea **`.harness/specs/`** — carpetas `NNN-slug` = features; `estado:` en el
   front-matter de cada `spec.md`.
4. Si vas a tocar red/exposición: **`caddy.json`** (bloque `servicios` únicamente).

## Qué es el sistema

Plataforma de gestión de carrera profesional. **Monorepo de microservicios**:

| Servicio | Stack | Rol | Puerto (compose) |
|---|---|---|---|
| `cjhirashi-career-api` | Python 3.14 · FastAPI · SQLAlchemy · Alembic | Sistema de registro (~187 endpoints, dueño del schema) | 8000 (interno, sin publicar) |
| `cjhirashi-career-ai` | Python 3.14 · FastAPI **async** · asyncpg · boto3 | Microservicio IA (AWS Bedrock, perfiles de agente) | `ia-service` :8010 |
| `cjhirashi-career-admin` | React · **Vite** SPA · TS · React Query · Vitest | Panel de administración | 8002 → 8000 |
| `cjhirashi-career-portfolio` | React · **Vite** SPA · TS · Vitest | Portal público read-only | 8003 → 8000 |

Infra: **Postgres compartida** (Alembic en `api`; `ai` la usa async), **Qdrant**
(búsqueda vectorial), **MinIO** (objetos). Routing externo por **Caddy** vía
`caddy.json` (contrato con el repo `cjhirashi-srv`).

> El **MCP Server** (`cjhirashi-career-mcp`, host `mcp.cjhirashi.com`) se retiró el
> 2026-09-04 — ver `docs/09-DECISIONS/023-retirar-mcp-server.md`. El arc42 aún lo
> describe como "Canal 3"; ese texto es diseño previo.

**Arquitectura interna: por capas.** Servicios Python: `routes → services →
repositories → models`. Frontends: `components/pages → hooks → services (API tipada)
→ stores`. La **lógica de negocio vive en `services/`**, no en `routes/` ni en
componentes. Detalle: `.harness/constitution.md` Art. 2 + `docs/05-BUILDING-BLOCK-VIEW.md`.

## Comandos por subproyecto

| Servicio | Tests | Arranque local |
|---|---|---|
| `api` | `cd cjhirashi-career-api && venv_test/bin/python -m pytest -q` | `uvicorn app:app --app-dir src --port 8000` |
| `ai` | `cd cjhirashi-career-ai && ./venv_test/bin/python -m pytest -q` | `python -m uvicorn main:app --app-dir src --port 8010` |
| `admin` | `cd cjhirashi-career-admin && npx vitest run` · `npm run type-check` | `npm run dev` (:3000) |
| `portfolio` | `cd cjhirashi-career-portfolio && npx vitest run` | `npm run dev` |

Vía compose: `docker compose up -d --build <servicio>` → `GET /health`.
Los venv de test de `api`/`ai` pueden no existir en limpio — el gate hace `SKIP` con
guía para recrearlos.

## Convenciones

- Código y comentarios en **inglés**; specs, `.harness/`, ADRs e interacción en **español**.
- Commits: **Conventional Commits** + sufijo `(RF-NNN)`.
- IDs: `RF-`/`RNF-`/`T-` por feature, `ADR-` por proyecto; estables, número reservado al crear el archivo.
- Tests anotados con su `RF-`: pytest `@pytest.mark.requisito("RF-014")`, Vitest `describe("RF-014: …", …)`.
- Errores de API: **RFC 9457** (Problem Details).

## Mapa de documentación (producto)

`docs/01`–`docs/12` (arc42) · `docs/09-DECISIONS/` (ADRs de producto) ·
`docs/BEDROCK-SYSTEM.md` · `docs/ADMIN_PANEL_SETUP.md` · `docs/ENVIRONMENT-SECURITY.md` ·
`docs/IMPLEMENTATION_PLAN.md` · `caddy.json` · `docker-compose.yml` · READMEs de servicio.
Tabla completa (con "se actualiza cuando cambia…"): `.harness/constitution.md` Art. 11.

## Hazards conocidos

`ai` ha arrancado "sano" silenciando `ImportError` de routers; verifica arranque real,
no imports. La dev DB no trackea Alembic del todo. Lista completa: fin de
`.harness/constitution.md`.

## Bindings de herramienta

`.claude/agents/` (si existe) es el binding de Claude Code — opcional. El núcleo del
arnés vive en `.harness/` y no depende de él.
