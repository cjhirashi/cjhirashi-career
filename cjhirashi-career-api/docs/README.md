# API REST — Documentación

Índice central de documentación del módulo API (`cjhirashi-career-api/`).

**Entrada principal:** [../README.md](../README.md)

## Arquitectura

```mermaid
flowchart TB
    Index[docs/README.md] --> Sections[sections/]
    Sections --> Auth[auth]
    Sections --> Infra[infrastructure]
    Sections --> Career[career-*]
    Sections --> Agent[bedrock / bedrock-tasks]
    Sections --> Integ[files / pdf / public]
    Index --> Guides[API / ARCHITECTURE / DATABASE / SECURITY / SETUP]
    Career --> Src[src/routes + models]
    Agent --> Harness[src/services/bedrock]
```

---

## Documentación por sección

Cada dominio tiene un README detallado con endpoints, schemas, flujos y ejemplos:

| Sección | README |
|---------|--------|
| **Índice de secciones** | [sections/README.md](sections/README.md) |
| Autenticación | [sections/auth/README.md](sections/auth/README.md) |
| Infraestructura (CRUD, JWT, repos) | [sections/infrastructure/README.md](sections/infrastructure/README.md) |
| Carrera — Identidad | [sections/career-identity/README.md](sections/career-identity/README.md) |
| Carrera — Búsqueda | [sections/career-search/README.md](sections/career-search/README.md) |
| Carrera — Presencia digital | [sections/career-digital/README.md](sections/career-digital/README.md) |
| Carrera — Tags | [sections/career-support/README.md](sections/career-support/README.md) |
| Carrera — Métricas | [sections/career-metrics/README.md](sections/career-metrics/README.md) |
| Carrera — Metodologías | [sections/career-methodologies/README.md](sections/career-methodologies/README.md) |
| Agent Bedrock | sections/bedrock/README.md (retirado, ADR-033) |
| Tareas del agente | [sections/bedrock-tasks/README.md](sections/bedrock-tasks/README.md) |
| Plantillas PDF | [sections/pdf-templates/README.md](sections/pdf-templates/README.md) |
| Estilos PDF | [sections/pdf-template-styles/README.md](sections/pdf-template-styles/README.md) |
| Archivos (MinIO) | [sections/files/README.md](sections/files/README.md) |
| Portal público | [sections/public/README.md](sections/public/README.md) |

---

## Referencia y guías transversales

| Documento | Contenido |
|-----------|-----------|
| [API.md](API.md) | Referencia rápida de todos los endpoints |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Capas Routes → Services → Repositories → Models |
| [DATABASE.md](DATABASE.md) | Esquema PostgreSQL, tablas, relaciones |
| [SECURITY.md](SECURITY.md) | JWT, aislamiento por usuario, CORS, OWASP |
| [SETUP.md](SETUP.md) | Instalación local, Docker, Alembic |
| [TESTING.md](TESTING.md) | Pytest, cobertura, fixtures |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Problemas comunes |

---

## Routers registrados (`src/app.py`)

| Router | Prefijo | Auth |
|--------|---------|------|
| `auth_enhanced` | `/auth` | Mixto |
| `career_identity` | `/career/*` | JWT |
| `career_search` | `/career/*` | JWT |
| `career_digital` | `/career/*` | JWT |
| `career_support` | `/career/tags` | JWT |
| `career_metrics` | `/career/metrics` | JWT |
| `career_methodologies` | `/career/operational-methodologies` | JWT |
| `bedrock` | `/bedrock` | JWT |
| `bedrock_tasks` | `/agent-tasks` | JWT |
| `pdf_templates` | `/pdf-templates` | JWT |
| `pdf_template_styles` | `/pdf-template-styles` | JWT |
| `files` | `/files` | JWT |
| `public` | `/public` | Ninguna |
| `events` | `/events` | Ninguna (ingesta y borrado de analítica del visitante) |
| `portal_metrics`, `portal_analytics` | `/career/portal-*` | JWT |
| `admin_sections` | `/admin` | JWT |
| `admin_contact_messages` | `/career/contact-messages` | JWT |
| `notifications` | `/notifications` | JWT |
| `error_reports` | `/settings/error-reports`, `/system/error-report` | JWT |

**OpenAPI interactivo:** `http://localhost:8000/docs` (solo si publicas el puerto o corres la API en local)

---

## Código por paquete (`src/`)

READMEs de implementación (función de cada módulo Python), distintos de los de sección HTTP:

| Paquete | README |
|---------|--------|
| `src/` | [../src/README.md](../src/README.md) |
| Routes | [../src/routes/README.md](../src/routes/README.md) |
| Services | [../src/services/README.md](../src/services/README.md) |
| Bedrock harness | ../src/services/bedrock/README.md (retirado, ADR-033) |
| Models | [../src/models/README.md](../src/models/README.md) |
| Schemas | [../src/schemas/README.md](../src/schemas/README.md) |
| Repositories | [../src/repositories/README.md](../src/repositories/README.md) |
| Tests | [../tests/README.md](../tests/README.md) |
| Alembic | [../alembic/README.md](../alembic/README.md) |

---

## Consumidores

| Cliente | Puerto host | Endpoints típicos |
|---------|-------------|-------------------|
| Admin Panel | 8002 (`/api/`) | `/auth`, `/career/*`, `/bedrock`, `/agent-tasks`, `/files`, `/pdf-*`, `/notifications` |
| Portal Público | 8003 (`/api/`) | `/public/*`, `/events/*` |
| Agente externo (token `agent`) | vía `/api/` | `/career/*`, `POST /bedrock/chat`, `POST /files` |

---

**Última actualización:** 2026-11-05
