# Paquete `routes/`

Capa HTTP de FastAPI. Cada módulo registra un `APIRouter` que `app.py` monta. La lógica de negocio vive en `services/`; aquí solo se validan payloads, se aplica JWT y se serializan respuestas.

**Contrato HTTP detallado:** [docs/sections/](../../docs/sections/README.md)

## Arquitectura

```mermaid
flowchart TB
    App[app.py] --> Auth[auth_enhanced /auth]
    App --> Identity[career_identity]
    App --> Search[career_search]
    App --> Digital[career_digital]
    App --> Support[career_support]
    App --> Metrics[career_metrics]
    App --> Methods[career_methodologies]
    App --> Jobs[job_discovery]
    App --> Bedrock[bedrock /bedrock]
    App --> Tasks[bedrock_tasks]
    App --> PDF[pdf_templates + styles]
    App --> Files[files /files]
    App --> Public[public /public]
    Identity --> Factory[career_common.build_crud_router]
    Search --> Factory
    Digital --> Factory
    Support --> Factory
    Methods --> Factory
    Tasks --> Factory
    Factory --> Repo[CareerRepository]
```

---

## Factory CRUD

### `career_common.py` — `build_crud_router`

Genera list / count / get / create / update / delete para un `(model, schemas)`:

- JWT obligatorio (`get_current_user`).
- Aislamiento por `user_id` del token vía `CareerRepository` (nunca del body).
- Registra el recurso en `RESOURCE_REGISTRY` para que las tools de Bedrock operen el mismo CRUD.

Prefijos de ID (`ach-17`, `vac-5`) los asigna `id_generator` al insertar.

---

## Autenticación

### `auth_enhanced.py` — `/auth`

| Método | Path | Función |
|--------|------|---------|
| POST | `/register` | Alta de usuario + hash bcrypt |
| POST | `/login` | Access + refresh JWT |
| POST | `/refresh` | Renueva access token |
| POST | `/logout` | Invalida sesión (cliente descarta tokens) |
| PATCH | `/me` | Actualiza perfil |
| POST | `/change-password` | Cambia contraseña |

Usa `AuthService` + `UserRepository`. Tag OpenAPI: `Authentication`.

---

## Carrera (JWT)

### `career_identity.py` — Identidad profesional

Monta 12 CRUD bajo `/career`: differentiators, identity, identity-reflections, competencies, certifications, target-roles, work-history, achievements, star-stories, career-reviews, role-gap-analysis, projects.

### `career_search.py` — Operativa de búsqueda

14 CRUD: fit-scoring-factors, market-segments, role-narratives, search-plans, networking-contacts, target-companies, vacancies, cv-versions, cover-letter-versions, applications, application-interactions, interviews, contact-interactions, networking-activities.

Extra no-CRUD: export PDF de `cv-versions` vía `pdf_service.generate_markdown_document`. `cv-versions` no se vectoriza en Qdrant.

### `career_digital.py` — Presencia digital

CRUD: publications, linkedin-profile, github-profile, portal-home, portal-about, portal-contact.

Extra: `GET /career/github-profile/repos` — repos públicos en vivo (`github_service`).

### `career_support.py` — Tags

CRUD `/career/tags` (etiquetas transversales).

### `career_metrics.py` — `/career/metrics`

Solo lectura: métricas semanales de búsqueda y overview agregado (funnel, counts). No escribe tablas.

### `career_methodologies.py` — Metodologías

CRUD `/career/operational-methodologies` (protocolos Markdown de cómo operar el dominio).

### `job_discovery.py` — `/career/job-discoveries`

No es CRUD genérico. Preview-then-save:

| Método | Path | Efecto |
|--------|------|--------|
| GET | `/providers` | Estado de adaptadores |
| POST | `/run` | Búsqueda multi-proveedor (no persiste vacantes) |
| POST | `/import-url` | Importa una URL a preview |
| POST | `/save` | Crea `vacancies` autorizadas desde refs L1, L2… |

---

## Agente y documentos

### `bedrock.py` — `/bedrock`

Chat SSE (`POST /chat`), modelo activo, presupuesto, instrucciones, **catálogo de agentes**, tools MCP, memoria, conversaciones, auditoría. Delega el loop a `services.bedrock.chat_stream`. Ver [services/bedrock/README.md](../services/bedrock/README.md).

### `bedrock_tasks.py` — `/agent-tasks`

CRUD de `BedrockTask` con `build_crud_router` más `POST /{id}/run`. Registrar el módulo mete `agent-tasks` en `RESOURCE_REGISTRY`. El scheduler (`task_scheduler`) ejecuta filas de agente a `scheduled_at` sin JWT.

### `pdf_templates.py` — `/pdf-templates`

CRUD de plantillas HTML + `POST /{id}/render` (WeasyPrint vía `pdf_service`). Registra `pdf-output-templates` en el registry (sin vectorizar). Tool del agente: `pdf_template`.

### `pdf_template_styles.py` — `/pdf-template-styles`

CRUD de estilos CSS reutilizables (`style_id` en plantillas). Tool del agente: `pdf_style`.

---

## Integraciones y portal

### `files.py` — `/files`

Upload a MinIO con re-encode de imágenes (JPEG 85 / PNG con alpha, lado máximo 1920). Listado, visibilidad pública/privada, download presigned, stream raw, delete. Lectura pública de objetos `public/` no pasa por JWT.

### `events.py` — `/events`

Ingesta pública de analítica: `POST /track` (valida `siteKey` y `Origin`, limita el ritmo, responde 204 ante errores internos) y `POST /forget` (borrado autoservicio de un visitante). Ver [docs/sections/portal-analytics](../../docs/sections/portal-analytics/README.md).

### `portal_metrics.py` — `/career/portal-metrics`

Métricas agregadas del portafolio (kpis, tendencia, desgloses, páginas, recorridos, retención, metas, embudo, diccionario, `rebuild`) con filtros y `sample_size` comunes.

### `portal_analytics.py` — `/career/portal-*`

Recursos de solo lectura (`portal-sites`, `-visitors`, `-visits`, `-events`, `-daily`) y CRUD de `portal-goals`, `portal-funnels`, `portal-annotations`.

### `admin_contact_messages.py` — `/career/contact-messages`

CRUD sin `POST` (`build_crud_router(create_schema=None)`) de los mensajes del formulario de contacto; solo `status` es editable (SPEC-0011).

### `public.py` — `/public`

Sin auth para el Portal: lectura de home, about, contact, projects, blog, y `POST /contact-message` (formulario de contacto: honeypot, límite 3/h por IP y correo, guarda en `contact_messages` y avisa al dueño; `services/contact_message_service.py`). Transforma Markdown de una línea por ítem a `List[str]` para que el SPA no conozca esa convención.

### `__init__.py`

Marcador de paquete. Los routers se importan por módulo desde `app.py`.
