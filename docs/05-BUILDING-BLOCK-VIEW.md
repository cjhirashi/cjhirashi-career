# Vista de bloques de construcción - cjhirashi-career

**VISTA DE BLOQUES** (arc42, sección 5)

**Última actualización**: 2026-11-10
**Resumen**: nivel 1 (los contenedores) y nivel 2 (Admin Panel, Portal, API y base de datos). Para no duplicar, el detalle de cada servicio vive en su propio README y en `cjhirashi-career-api/docs/` (referenciados abajo).

---

## Nivel 1 — Sistema completo

```mermaid
graph TB
    Visitante((Visitante)) --> Portal
    Carlos((Carlos)) --> Admin
    Agente((Agente externo<br/>token rol agent)) --> API

    subgraph Compose["docker-compose.yml — red net-cjhirashi-career"]
        Portal["cjhirashi-career-portfolio<br/>SPA React · 8003"]
        Admin["cjhirashi-career-admin<br/>SPA React · 8002"]
        API["cjhirashi-career-api<br/>FastAPI · 8000 interno"]
        PG[("postgres_db<br/>PostgreSQL 15")]
        S3[("minio_storage<br/>MinIO")]
    end

    Portal -->|/api/| API
    Admin -->|/api/| API
    API --> PG
    API --> S3
```

| Bloque | Responsabilidad | Documentación |
|---|---|---|
| **Portal público** | Lectura del portafolio, formulario de contacto, rastreador de analítica | [`cjhirashi-career-portfolio/README.md`](../cjhirashi-career-portfolio/README.md) |
| **Admin Panel** | Gestión de carrera, vacantes, archivos, PDF, métricas, mensajes, agentes | [`cjhirashi-career-admin/README.md`](../cjhirashi-career-admin/README.md) |
| **API REST** | Autenticación, CRUD, PDF, archivos, analítica; dueña del esquema | [`cjhirashi-career-api/README.md`](../cjhirashi-career-api/README.md), [`docs/API.md`](../cjhirashi-career-api/docs/API.md), [`docs/ARCHITECTURE.md`](../cjhirashi-career-api/docs/ARCHITECTURE.md) |
| **PostgreSQL** | Persistencia de todo el negocio | [`docs/DATABASE.md`](../cjhirashi-career-api/docs/DATABASE.md) |
| **MinIO** | Archivos (bucket único; los públicos se sirven como archivos públicos) | [ENVIRONMENT-SECURITY.md](./ENVIRONMENT-SECURITY.md) |

## Nivel 2 — Admin Panel

SPA React 18 + Vite + TypeScript (Tailwind, React Query, Zustand, React Router, Recharts). Capas: `pages/` y `components/` → `hooks/` → `api/` (cliente Axios tipado con interceptores JWT) → `stores/`.

| Área | Rutas | Contenido |
|---|---|---|
| Panel y métricas | `/dashboard`, `/metrics`, `/metrics/settings`, `/search-metrics` | KPIs de búsqueda; analítica del portafolio con comparación, filtros, metas, embudos y anotaciones |
| Carrera | `/career/:resourceKey/:recordSlug?`, `/files` | Vista genérica de cada recurso de carrera (`config/careerResources.ts`) y archivos |
| Tareas | `/tasks` | Lista, kanban, calendario y Gantt |
| Agentes | `/agent/chat`, `/agent/catalog`, `/agent/instructions`, `/agent/tools`, `/agent/memory`, `/agent/tasks`, `/agent/audit-log`, `/agent/metrics`, `/agent/pdf-templates`, `/agent/pdf-template-styles` | Chat, catálogo y configuración de agentes, memoria, tareas programadas, auditoría y plantillas de PDF |
| Configuración | `/settings/agents`, `/settings/sections`, `/settings/agent-prompts`, `/settings/error-reports` | Perfiles de agentes, secciones del Admin, prompts globales y registro de errores |
| Cuenta | `/login`, `/profile`, `/change-password` | Autenticación |

Componentes compartidos: `section/` (plantilla de tabla, ADR-020), `career/` (formularios y vistas de recursos), `tasks/` (vistas de tareas), selectores temáticos y la campana de notificaciones (incluye los mensajes de contacto). Detalle: README del Admin.

## Nivel 2 — Portal público

SPA React sin estado de negocio: `/`, `/about`, `/projects`, `/projects/:slug`, `/blog`, `/blog/:slug`, `/contact`, `/privacy` y 404. Lee de `/api/public/*`; envía el formulario de contacto y los eventos de analítica (tiempo activo, scroll, enlaces salientes, Web Vitals, UTM; respeta DNT/GPC). `/privacy` permite al visitante borrar sus datos.

## Nivel 2 — API REST

Capas: `routes/` → `services/` → `repositories/` → `models/` (la lógica de negocio vive en `services/`). 419 operaciones HTTP en 282 rutas.

| Dominio | Módulos de ruta | Servicios principales |
|---|---|---|
| Autenticación y usuarios | `auth_enhanced` | `auth_service` (JWT, bcrypt) |
| Carrera (CRUD genérico `/career/{recurso}`) | `career_identity`, `career_search`, `career_digital`, `career_support`, `career_methodologies`, `career_common` | `career_repository` (base común), `vacancy_stage`, `methodology_scope`, `section_catalog` |
| Métricas | `career_metrics` | Agregaciones de la búsqueda de empleo |
| Tareas y avisos | `bedrock_tasks` (`/agent-tasks`), `notifications` | `github_service` |
| Archivos y PDF | `files`, `pdf_templates`, `pdf_template_styles` | `storage_service`, `pdf_service`, `pdf_template_render` |
| Portal y analítica | `public`, `events`, `portal_metrics`, `portal_analytics`, `admin_contact_messages` | `portal_ingest`, `portal_metrics`, `portal_bots`, `portal_geo`, `portal_channels`, `portal_device`, `portal_ratelimit`, `contact_message_service` |
| Operación | `error_reports` | `error_report_service` |

Autorización: `middleware/auth.py` valida el JWT y restringe el rol `agent` a `/career/*` y `POST /files`. Errores como `{"detail": …}` (los 422 de validación añaden la lista de errores); todo fallo relevante se registra en `error_reports` (ADR-018).

## Nivel 2 — PostgreSQL

Una instancia (`postgres_db`) con la base `career_db`: 58 tablas y 56 migraciones Alembic (head `9e5a3b7d2c04`). Dominios: usuarios y sesiones; carrera (identidad, búsqueda y vacantes, presencia digital, soporte y metodologías); tareas (`bedrock_tasks`); archivos; analítica del portafolio (`portal_*`); observabilidad (`audit_logs`, `error_reports`, `events`, `user_notifications`); y mensajes de contacto. El esquema, los IDs prefijados y las migraciones están en [`DATABASE.md`](../cjhirashi-career-api/docs/DATABASE.md), que es la fuente de verdad.

## Interfaces entre bloques

| Origen → Destino | Interfaz |
|---|---|
| Portal / Admin → API | REST JSON bajo `/api/` (la API recibe la ruta sin el prefijo); Admin con `Authorization: Bearer`, Portal sin autenticación |
| API → PostgreSQL | SQLAlchemy async (asyncpg) |
| API → MinIO | Cliente S3 `minio`, bucket único |

## Dependencias externas

| Dependencia | Uso | Credenciales |
|---|---|---|
| GitHub | Lectura de repositorios por el agente | `GITHUB_TOKEN` |

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [04-SOLUTION-STRATEGY.md](./04-SOLUTION-STRATEGY.md) · [06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md) · [07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md)
**Contacto**: cjhirashi@gmail.com
