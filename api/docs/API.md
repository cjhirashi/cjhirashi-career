# API REST — Referencia de endpoints

Referencia rápida de todos los endpoints. Para detalle por dominio, ver los README de [sections/](sections/README.md).

**Base URL local:** `http://localhost:8001`  
**Base URL Docker:** `http://api_rest:8001`  
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

→ [sections/bedrock/README.md](sections/bedrock/README.md)

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

CRUD estándar (6 endpoints).

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

## LinkedIn — `/linkedin`

→ [sections/linkedin/README.md](sections/linkedin/README.md)

| Método | Path | Auth |
|--------|------|------|
| GET | `/linkedin/status` | Sí |
| GET | `/linkedin/connect` | Sí |
| GET | `/linkedin/callback` | No |
| DELETE | `/linkedin/disconnect` | Sí |
| GET | `/linkedin/posts` | Sí |
| POST | `/linkedin/posts` | Sí |
| DELETE | `/linkedin/posts/{id}` | Sí |

---

## Portal público — `/public`

→ [sections/public/README.md](sections/public/README.md)

| Método | Path | Auth |
|--------|------|------|
| GET | `/public/home` | No |
| GET | `/public/about` | No |
| GET | `/public/contact` | No |
| GET | `/public/projects` | No |
| GET | `/public/projects/{id}` | No |
| GET | `/public/blog` | No |
| GET | `/public/blog/{slug}` | No |

---

## Códigos HTTP comunes

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 201 | Creado |
| 204 | Sin contenido (delete exitoso) |
| 400 | Request inválido |
| 401 | Token ausente/inválido |
| 404 | Recurso no encontrado |
| 422 | Error de validación Pydantic |
| 502 | Error servicio externo (Bedrock, LinkedIn) |
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

**Última actualización:** 2026-08-24
