# API REST — Referencia de endpoints

> **Estado (2026-11-10, [ADR-032](../../docs/09-DECISIONS/032-agentes-externos-y-bedrock-fuera-de-operacion.md)):** el subsistema de agentes con AWS Bedrock está **fuera de operación**. Los agentes de IA son externos y entran por la API con el rol `agent`. Este documento se conserva como referencia del diseño y no describe el comportamiento operativo actual.

Referencia rápida de todos los endpoints. Para detalle por dominio, ver los README de [sections/](sections/README.md).

**Base URL local:** `http://localhost:8000`  
**Base URL Docker:** `http://cjhirashi-career-api:8000`  
**Auth:** `Authorization: Bearer <access_token>` (salvo donde se indique)

---

## Health y raíz

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/` | No | Info de la API + link a `/docs` |

---

## Autenticación — `/auth`

→ [sections/auth/README.md](sections/auth/README.md)

| Método | Path | Auth |
|--------|------|------|
| POST | `/auth/register` | No |
| POST | `/auth/login` | No |
| POST | `/auth/refresh` | No |
| POST | `/auth/logout` | No |
| PATCH | `/auth/me` | Sí |
| POST | `/auth/change-password` | Sí |

---

## Carrera — CRUD genérico — `/career/{resource}`

→ [sections/infrastructure/README.md](sections/infrastructure/README.md)

Patrón por cada resource key (37 recursos):

| Método | Path |
|--------|------|
| GET | `/career/{resource}` |
| GET | `/career/{resource}/count` |
| GET | `/career/{resource}/{id}` |
| POST | `/career/{resource}` |
| PUT | `/career/{resource}/{id}` |
| DELETE | `/career/{resource}/{id}` |

### Identidad (12 recursos)

→ [sections/career-identity/README.md](sections/career-identity/README.md)

`differentiators`, `identity`, `identity-reflections`, `competencies`, `certifications`, `target-roles`, `work-history`, `achievements`, `star-stories`, `career-reviews`, `role-gap-analysis`, `projects`

### Búsqueda (14 recursos)

→ [sections/career-search/README.md](sections/career-search/README.md)

`fit-scoring-factors`, `market-segments`, `role-narratives`, `search-plans`, `networking-contacts`, `target-companies`, `vacancies`, `cv-versions`, `cover-letter-versions`, `applications`, `application-interactions`, `interviews`, `contact-interactions`, `networking-activities`

| Método | Path extra |
|--------|------------|
| POST | `/career/cv-versions/{id}/pdf` |

### Presencia digital (6 recursos)

→ [sections/career-digital/README.md](sections/career-digital/README.md)

`publications`, `linkedin-profile`, `github-profile`, `portal-home`, `portal-about`, `portal-contact`

| Método | Path extra |
|--------|------------|
| GET | `/career/github-profile/repos` |

### Soporte (1 recurso)

→ [sections/career-support/README.md](sections/career-support/README.md)

`tags`

### Metodologías (1 recurso)

→ [sections/career-methodologies/README.md](sections/career-methodologies/README.md)

`operational-methodologies`

---

## Métricas — `/career/metrics`

→ [sections/career-metrics/README.md](sections/career-metrics/README.md)

| Método | Path |
|--------|------|
| GET | `/career/metrics/weekly` |
| GET | `/career/metrics/search-overview` |

---

## Job Discovery — `/career/job-discoveries`

→ [sections/job-discovery/README.md](sections/job-discovery/README.md)

| Método | Path |
|--------|------|
| GET | `/career/job-discoveries/providers` |
| POST | `/career/job-discoveries/run` |
| POST | `/career/job-discoveries/import-url` |
| POST | `/career/job-discoveries/save` |

---

## Agent Bedrock — `/bedrock`

→ sections/bedrock/README.md (retirado, ADR-033)

| Método | Path |
|--------|------|
| POST | `/bedrock/chat` (SSE) |
| GET | `/bedrock/model` |
| POST | `/bedrock/model` |
| GET | `/bedrock/usage-metrics` |
| GET | `/bedrock/budget` |
| GET | `/bedrock/instructions` |
| PUT | `/bedrock/instructions` |
| GET | `/bedrock/agent-profiles` |
| PUT | `/bedrock/agent-profiles/{profile_id}/prompt` |
| GET | `/bedrock/agent-profiles/catalog` |
| GET | `/bedrock/agent-profiles/{profile_id}/catalog` |
| PUT | `/bedrock/agent-profiles/{profile_id}/methodologies` |
| GET | `/bedrock/agent-profiles/{profile_id}/memory` |
| POST | `/bedrock/agent-profiles/{profile_id}/memory/notes` |
| DELETE | `/bedrock/agent-profiles/{profile_id}/memory/notes/{note_id}` |
| GET | `/bedrock/tools` |
| POST | `/bedrock/tools` |
| PUT | `/bedrock/tools/{tool_id}/enabled` |
| DELETE | `/bedrock/tools/{tool_id}` |
| GET | `/bedrock/knowledge/search` |
| GET | `/bedrock/memory/events` |
| GET | `/bedrock/memory/records` |
| POST | `/bedrock/memory/manual` |
| GET | `/bedrock/conversations` |
| GET | `/bedrock/conversations/{session_id}/messages` |
| PUT | `/bedrock/conversations/{session_id}` |
| DELETE | `/bedrock/conversations/{session_id}` |
| GET | `/bedrock/audit-log` |
| POST | `/bedrock/audit-log/{audit_id}/restore` |

---

## Tareas del agente — `/agent-tasks`

→ [sections/bedrock-tasks/README.md](sections/bedrock-tasks/README.md)

CRUD estándar + `POST /{id}/run` (ejecución inmediata de agente). Scheduler in-process a `scheduled_at`.

---

## Plantillas PDF — `/pdf-templates`

→ [sections/pdf-templates/README.md](sections/pdf-templates/README.md)

| Método | Path |
|--------|------|
| GET | `/pdf-templates` |
| GET | `/pdf-templates/defaults/by-type` |
| GET | `/pdf-templates/{id}` |
| POST | `/pdf-templates` |
| PUT | `/pdf-templates/{id}` |
| DELETE | `/pdf-templates/{id}` |
| POST | `/pdf-templates/{id}/render` |

---

## Estilos PDF — `/pdf-template-styles`

→ [sections/pdf-template-styles/README.md](sections/pdf-template-styles/README.md)

| Método | Path |
|--------|------|
| GET | `/pdf-template-styles` |
| GET | `/pdf-template-styles/{id}` |
| POST | `/pdf-template-styles` |
| PUT | `/pdf-template-styles/{id}` |
| DELETE | `/pdf-template-styles/{id}` |

---

## Archivos — `/files`

→ [sections/files/README.md](sections/files/README.md)

| Método | Path |
|--------|------|
| POST | `/files` |
| GET | `/files` |
| GET | `/files/categories` |
| PATCH | `/files/{id}/visibility` |
| GET | `/files/{id}/download` |
| GET | `/files/{id}/raw` |
| DELETE | `/files/{id}` |

---

## Analítica del portafolio — `/events` y `/career/portal-*`

→ [sections/portal-analytics/README.md](sections/portal-analytics/README.md)

| Método | Path | Auth |
|--------|------|------|
| POST | `/events/track` | No (valida `siteKey` y `Origin`) |
| POST | `/events/forget` | No (autoservicio) |
| GET | `/career/portal-sites` `/portal-visitors` `/portal-visits` `/portal-events` `/portal-daily` (+ `/count`, `/{id}`) | JWT o token de agente (solo lectura) |
| CRUD | `/career/portal-goals` `/portal-funnels` `/portal-annotations` | JWT o token de agente |
| GET | `/career/portal-metrics/overview` `/kpis` `/trend` `/channels` `/sources` `/campaigns` `/geo` `/devices` `/breakdown` `/pages` `/paths` `/retention` `/realtime` `/goals` `/funnel/{id}` `/dictionary` | JWT o token de agente |
| POST | `/career/portal-metrics/rebuild` | JWT o token de agente |

---

## Portal público — `/public`

→ [sections/public/README.md](sections/public/README.md)

| Método | Path | Auth |
|--------|------|------|
| GET | `/public/home` | No |
| GET | `/public/about` | No |
| GET | `/public/contact` | No |
| POST | `/public/contact-message` | No (honeypot `website`, 3/h por IP y por correo → 429) |
| GET | `/public/projects` | No |
| GET | `/public/projects/{id}` | No |
| GET | `/public/blog` | No |
| GET | `/public/blog/{slug}` | No |

Mensajes del formulario de contacto: `/career/contact-messages` (JWT del dueño): `GET` lista/detalle, `PUT` solo `status` (`new`/`read`/`archived`), `DELETE`. No hay `POST`: los mensajes solo entran por `/public/contact-message`.

---

## Operación del Admin — `/admin`, `/notifications`, `/settings`, `/system`

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/admin/sections` | JWT | Catálogo de secciones del Admin |
| GET | `/admin/sections/{id}` | JWT | Detalle de una sección |
| PUT | `/admin/sections/{id}` | JWT | Actualiza dominio e instrucciones de la sección |
| GET | `/notifications` | JWT | Lista los avisos del usuario (turnos de tareas, mensajes de contacto) |
| GET | `/notifications/unread-count` | JWT | Avisos sin leer |
| POST | `/notifications/{id}/read` | JWT | Marca un aviso como leído |
| POST | `/notifications/read-all` | JWT | Marca todos como leídos |
| GET | `/settings/error-reports` | JWT | Lista paginada de reportes de falla |
| GET | `/settings/error-reports/summary` | JWT | Contadores de pendientes y resueltos |
| GET | `/settings/error-reports/{id}` | JWT | Detalle de un reporte |
| PATCH | `/settings/error-reports/{id}` | JWT | Marca como resuelto o reabre |
| DELETE | `/settings/error-reports/{id}` | JWT | Elimina un reporte |
| POST | `/settings/error-reports/purge-resolved` | JWT | Elimina los resueltos antiguos |
| POST | `/system/error-report` | Ninguna | Ingesta pública de una falla del cliente (con límite de tasa; nunca falla por el registro) |
| GET | `/system/readiness` | Ninguna | Comprueba dependencias que `/health` no ve (hoy, MinIO) |
| GET | `/health` | Ninguna | Estado de la API |

Además, bajo `/bedrock`: `PUT /bedrock/global-rules` (reglas globales del agente), `PUT /bedrock/agent-profiles/{id}/delegation`, `.../photo` y `.../sections` (destinos de delegación, foto y secciones que gestiona cada perfil); bajo `/agent-tasks`: `GET /agent-tasks/distinct/{campo}`; bajo `/files`: `GET /files/count`.

---

## Códigos HTTP comunes

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 201 | Creado |
| 204 | Sin contenido (delete exitoso) |
| 400 | Request inválido |
| 401 | Token ausente/inválido |
| 403 | Token de rol `agent` fuera de su lista de rutas, o cuenta inactiva |
| 404 | Recurso no encontrado |
| 429 | Límite de tasa excedido (contacto, analítica, ingesta de errores) |
| 422 | Error de validación Pydantic |
| 502 | Error servicio externo (Bedrock) |
| 503 | Servicio no configurado |

---

## Paginación (CRUD carrera)

Query params en `GET /career/{resource}`:

- `skip` (default 0)
- `limit` (default 20, max 100)
- `sort_by`, `sort_dir` (`asc`|`desc`)
- `search` (texto libre)

---

## IDs prefijados

Formato `{prefijo}-{n}` — ej. `usr-1`, `ach-17`, `vac-5`, `pdt-1`.

Ver [sections/infrastructure/README.md](sections/infrastructure/README.md).

---

**Última actualización:** 2026-11-05
