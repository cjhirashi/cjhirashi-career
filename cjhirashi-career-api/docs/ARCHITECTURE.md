# API REST — Guía de arquitectura

**Ubicación:** `cjhirashi-career-api/docs/ARCHITECTURE.md`

**Última actualización:** 2026-11-10

Arquitectura en capas de la API REST de cjhirashi-career: FastAPI + SQLAlchemy 2.0 async + PostgreSQL, con integraciones Bedrock, MinIO, y Qdrant.

---

## Tabla de contenidos

- [Visión general](#visión-general)
- [Arquitectura en capas](#arquitectura-en-capas)
- [Consumidores y red](#consumidores-y-red)
- [Componentes principales](#componentes-principales)
- [Dominios funcionales](#dominios-funcionales)
- [Flujos de datos](#flujos-de-datos)
- [Servicios externos](#servicios-externos)
- [Principios de diseño](#principios-de-diseño)
- [Manejo de errores](#manejo-de-errores)
- [Testing](#testing)
- [Escalabilidad](#escalabilidad)
- [Documentación relacionada](#documentación-relacionada)

---

## Visión general

La API es el **único escritor** de PostgreSQL en el ecosistema. Centraliza:

- Autenticación JWT (access + refresh)
- CRUD de ≈48 recursos de carrera profesional bajo `/career`
- Agent Bedrock (Harness local Converse API)
- Job discovery multi-proveedor
- Archivos (MinIO), plantillas PDF
- Endpoints públicos read-only para el Portal

**Stack:** FastAPI 0.104 · SQLAlchemy 2.0 async · asyncpg · Pydantic v2 · Alembic · boto3 (Bedrock) · Qdrant client

**Estado:** en producción — 21 routers registrados en `src/app.py`, 419 operaciones HTTP, 69 modelos ORM y 53 migraciones Alembic. El harness de agentes y Qdrant se trasladarán/retirarán según el ADR-029 (spec 009, en curso; aún sin aplicar).

---

## Arquitectura en capas

```mermaid
graph TD
    subgraph Clients["Clientes (por /api/ en net-cjhirashi-career)"]
        Admin[Admin Panel :8002]
        Portal[Portal Público :8003]
        Agent[Agente externo<br/>token rol agent]
    end

    subgraph API["cjhirashi-career-api :8000"]
        Routes[Routes — HTTP/SSE]
        Services[Services — lógica de negocio]
        Repos[Repositories — acceso a datos]
        Models[Models — SQLAlchemy ORM]
    end

    subgraph External["Servicios externos"]
        PG[(PostgreSQL)]
        MinIO[(MinIO)]
        Qdrant[(Qdrant)]
        AWS[AWS Bedrock]
        GH[GitHub API]
    end

    Admin --> Routes
    Agent --> Routes
    Portal --> Routes
    Routes --> Services
    Services --> Repos
    Repos --> Models
    Models --> PG
    Services --> MinIO
    Services --> Qdrant
    Services --> AWS
    Services --> GH
```

| Capa | Responsabilidad | Ejemplos |
|------|-----------------|----------|
| **Routes** | HTTP, validación Pydantic, auth deps, SSE | `routes/bedrock.py`, `routes/career_identity.py` |
| **Services** | Reglas de negocio, integraciones externas | `bedrock/agent_loop.py`, `job_discovery/` |
| **Repositories** | Queries SQLAlchemy, aislamiento por user | `career_repository.py`, `user_repository.py` |
| **Models** | Esquema ORM, relaciones | `models/vacancy.py`, `models/bedrock_conversation.py` |

---

## Consumidores y red

```
Admin (8002) / Portal (8003)
   └─ /api/ (la API recibe la ruta sin el prefijo) → cjhirashi-career-api:8000 (solo red interna Docker)
```

| Cliente | Auth | Endpoints típicos |
|---------|------|-------------------|
| Admin Panel | JWT | `/auth`, `/career/*`, `/bedrock`, `/agent-tasks`, `/files`, `/pdf-*`, `/notifications`, `/settings`, `/admin` |
| Portal Público | Ninguna | `/public/*`, `/events/*` |
| Agente externo | JWT de rol `agent` | `/career/*`, `POST /bedrock/chat`, `POST /files` (el resto, 403) |

---

## Componentes principales

### `src/app.py`

- Lifespan: `init_db()`, MinIO bucket y scheduler de tareas de agentes
- CORS, exception handlers globales
- Registra 21 routers (ver [API.md](./API.md))
- Health check `/health`

### `src/config.py`

`pydantic_settings.BaseSettings` — JWT, PostgreSQL, Bedrock, MinIO, Qdrant, CORS, descubrimiento de vacantes y portal público.

### `src/database.py`

Engine async, `AsyncSessionLocal`, `get_db()` dependency, `init_db()` / `close_db()`.

### `src/routes/`

| Archivo | Dominio |
|---------|---------|
| `auth_enhanced.py` | Autenticación JWT + refresh |
| `career_common.py` | Factory CRUD + `RESOURCE_REGISTRY` |
| `career_identity.py` | Recursos de identidad |
| `career_search.py` | Recursos de búsqueda (vacantes, aplicaciones, CVs y cartas) |
| `career_digital.py` | Recursos de presencia digital |
| `career_support.py` | Tags |
| `career_metrics.py` | Métricas agregadas de búsqueda |
| `career_methodologies.py` | Metodologías operativas |
| `job_discovery.py` | Búsqueda multi-proveedor |
| `bedrock.py` | Agent Bedrock (streaming) |
| `bedrock_tasks.py` | Tareas del agente |
| `notifications.py` | Notificaciones in-app |
| `admin_sections.py` | Secciones configurables del Admin |
| `admin_contact_messages.py` | Mensajes del formulario de contacto |
| `pdf_templates.py` | Plantillas HTML (`pdf_template`) |
| `pdf_template_styles.py` | Estilos CSS (`pdf_style`) |
| `files.py` | Upload MinIO |
| `public.py` | Portal read-only y contacto |
| `error_reports.py` | Registro de errores |
| `events.py` | Ingesta y borrado de analítica |
| `portal_metrics.py`, `portal_analytics.py` | Consulta y configuración de la analítica |

Documentación por sección: [sections/README.md](./sections/README.md)

### `src/services/`

| Paquete / módulo | Rol |
|------------------|-----|
| `auth_service.py` | Hash bcrypt, JWT access/refresh |
| `bedrock/` | Harness local: loop Converse, tools, memoria, presupuesto |
| `bedrock_service.py` | Fachada + CRUD tools del agente |
| `job_discovery/` | Adaptadores: Adzuna (Indeed), Greenhouse, Lever, LinkedIn, Remotive, RemoteOK, GetOnBoard |
| `task_scheduler.py` | Bucle in-process de tareas programadas de agentes |
| `portal_*.py` | Analítica: ingesta, sesionización, bots, geografía, canales, dispositivo, límites de tasa y métricas |
| `contact_message_service.py` | Mensajes del formulario de contacto |
| `error_report_service.py`, `error_reporting.py` | Registro y deduplicación de errores |
| `storage_service.py` | MinIO upload/presigned URLs |
| `qdrant_service.py` | Indexación y búsqueda vectorial |
| `pdf_service.py` | Generación PDF |
| `id_generator.py` | IDs prefijados (`ach-17`, `usr-1`) |

### `src/repositories/`

- `career_repository.py` — CRUD genérico con aislamiento `user_id`, indexación Qdrant
- `user_repository.py` — queries de usuario

### `src/middleware/auth.py`

`get_current_user` — decodifica JWT, extrae `sub` (ID prefijado `usr-N`), carga `User`.

### `src/schemas/`

Pydantic v2 por dominio: `user`, `career_identity`, `career_search`, `career_digital`, `bedrock`, `job_discovery`, `public`, etc.

### `src/models/`

69 modelos ORM. Import centralizado en `models/__init__.py`. Ver [DATABASE.md](./DATABASE.md).

---

## Dominios funcionales

```mermaid
graph LR
    subgraph Career["Dominio Carrera"]
        ID[Identidad]
        SR[Búsqueda]
        DG[Digital]
        MT[Métricas]
        JD[Job Discovery]
    end

    subgraph Agent["Agent Bedrock"]
        Chat[Chat SSE]
        Tools[Tools CRUD]
        Mem[Memoria PG + Qdrant]
    end

    subgraph Integrations["Integraciones"]
        Files[MinIO]
        PDF[PDF Templates]
    end

    Career --> Agent
    Agent --> Career
    Integrations --> Career
```

---

## Flujos de datos

### Login con refresh token

```mermaid
sequenceDiagram
    participant C as Cliente
    participant R as auth_enhanced
    participant S as AuthService
    participant DB as PostgreSQL

    C->>R: POST /auth/login
    R->>DB: SELECT user
    R->>S: verify_password + create tokens
    S-->>R: access + refresh JWT
    R->>DB: INSERT refresh_token
    R-->>C: LoginResponse
```

### CRUD de carrera (factory)

```mermaid
sequenceDiagram
    participant C as Admin / agente
    participant R as career_common router
    participant M as get_current_user
    participant Repo as CareerRepository
    participant DB as PostgreSQL
    participant Q as Qdrant

    C->>M: Bearer JWT
    M-->>R: User (usr-N)
    R->>Repo: create_for_user(user_id, data)
    Repo->>DB: INSERT + ID prefijado
    Repo->>Q: upsert embedding (si vectorize)
    Repo-->>C: 201 EntityResponse
```

### Chat Bedrock (SSE)

```mermaid
sequenceDiagram
    participant A as Admin Panel
    participant R as /bedrock/chat
    participant L as agent_loop
    participant AWS as bedrock-runtime
    participant T as tools.py
    participant DB as PostgreSQL

    A->>R: POST message + session_id
    R->>L: chat_stream()
    loop hasta stop_reason != tool_use
        L->>AWS: Converse + tools
        AWS-->>L: tool_use requests
        L->>T: execute_tool()
        T->>DB: CRUD / Qdrant
        T-->>L: tool results
    end
    L->>DB: guardar historial + usage
    L-->>A: SSE done {reply, affected_resources}
```

---

## Servicios externos

| Servicio | Uso en API | Config |
|----------|------------|--------|
| PostgreSQL | Persistencia única | `DATABASE_URL` |
| MinIO | Archivos, imágenes IA | `MINIO_*` |
| Qdrant | Knowledge base Bedrock | `QDRANT_*` |
| AWS Bedrock | Converse, embeddings (Titan) e imágenes (Stability) | `AWS_*`, `BEDROCK_*` |
| GitHub API | Repos públicos | Sin key (API pública) |

---

## Principios de diseño

**Single Responsibility:** cada router/service por dominio; `CareerRepository` solo acceso a datos de carrera.

**Open/Closed:** `build_crud_router()` extiende CRUD sin modificar el factory.

**Dependency Inversion:** routes dependen de `Depends(get_db)`, `Depends(get_current_user)`, servicios inyectables.

**DRY:** un repositorio y un registry (`RESOURCE_REGISTRY`) para ≈48 recursos; Bedrock tools reutilizan el mismo CRUD que el Admin.

**Aislamiento multi-tenant:** `user_id` siempre del JWT, nunca del request body.

---

## Manejo de errores

| Nivel | Comportamiento |
|-------|----------------|
| Route | `HTTPException` (401, 404, 422, 502, 503) |
| Service | `BedrockError`, `ValueError` → convertidos en route |
| App global | `RequestValidationError` → 422 `{"detail": "Error de validación", ...}` con la lista de errores |
| App global | `Exception` no capturada → 500 + log y registro en `error_reports` |
| App global | Los 5xx y los 4xx relevantes (salvo 401 y 404) se registran en `error_reports` con huella |

Bedrock chat usa SSE event `type: error` además de códigos HTTP en fallos previos al stream.

---

## Testing

Estructura en `cjhirashi-career-api/tests/`:

| Carpeta | Alcance |
|---------|---------|
| `unit/` | Services, middleware, bedrock, job_discovery |
| `integration/` | Auth routes, flujos HTTP |
| `conftest.py` | Fixtures async, DB test |

Ver [TESTING.md](./TESTING.md).

---

## Escalabilidad

**Implementado:**
- App stateless (JWT, sin sesión en memoria)
- Async end-to-end
- Connection pool (`pool_size=10`, `max_overflow=20`)
- Paginación en listados CRUD
- Presupuesto diario Bedrock por usuario

**Limitación:** el scheduler de tareas corre in-process con un solo worker; con varias réplicas duplicaría ejecuciones (se resuelve al mover el harness, ADR-029).

**No implementado:**
- Cache Redis
- Cola de mensajes (Celery/RQ)
- Réplicas read PostgreSQL
- Versionado API (`/v1`)

---

## Documentación relacionada

| Documento | Ubicación | Contenido |
|-----------|-----------|-----------|
| README API | [../README.md](../README.md) | Overview y mapa de secciones |
| Secciones | [sections/README.md](./sections/README.md) | README detallado por dominio |
| Endpoints | [API.md](./API.md) | Referencia rápida |
| Base de datos | [DATABASE.md](./DATABASE.md) | Esquema PostgreSQL |
| Seguridad | [SECURITY.md](./SECURITY.md) | JWT, CORS, OWASP |
| Bedrock IAM | [BEDROCK-HARNESS.md](./BEDROCK-HARNESS.md) | Permisos AWS |
| Setup | [SETUP.md](./SETUP.md) | Instalación y Docker |

---

**Relacionado:** [DATABASE.md](./DATABASE.md) · [SECURITY.md](./SECURITY.md) · [API.md](./API.md)
