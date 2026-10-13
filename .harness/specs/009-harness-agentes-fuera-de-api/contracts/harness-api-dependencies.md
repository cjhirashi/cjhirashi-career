---
titulo: "Dependencias del harness sobre la API REST (tool → endpoint) — spec 009"
tipo: contrato
feature_id: "009"
fecha: 2026-10-13
---

# Qué necesita el harness de la API (RF-003: sólo REST)

Hoy las tools del harness importan modelos, repositorios y servicios de la API
(`services/bedrock/tools.py`, 1.4k líneas; `bedrock_service.py`). Al salir, cada acoplamiento
se sustituye por una llamada REST de `cjhirashi-career-ai/src/clients/`. Inventario de las
41 tools (`grep '"name"' tools.py`, 2026-10-13) y de las rutas que ya existen:

**Estado:** `OK` = la ruta existe hoy · `GAP` = no existe: requiere cambio aditivo en la API
(lo señala el plan; sólo con OK del usuario, §12) · `LOCAL` = pasa a ser lógica propia del
harness (sin API). **Alcance `agent`:** ¿accesible con la cuenta de servicio (sólo
`/career/*`, RF-018)? Con el JWT del usuario TODAS las rutas son accesibles.

| Tool(s) | Hoy toca | Reemplazo REST (cliente) | Estado | Cuenta de servicio |
|---|---|---|---|---|
| `list/get/create/update/delete/bulk_update/count_career_record(s)` | `CareerRepository` directo | `/career/<recurso>` GET/POST/PUT/DELETE, `/count`, `/distinct/{campo}`; `bulk_update` = N× PUT | OK | sí |
| `describe_resource_schema` | `RESOURCE_REGISTRY` (columnas del modelo) | `GET /openapi.json` de la API (schemas Create/Update por recurso) | OK (verificar que `/openapi.json` esté expuesto en el despliegue) | sí si se sirve sin auth (verificar) |
| `search_knowledge_base` | Qdrant + embeddings | **Se retira** (D-15/D-04): la tool desaparece; el agente consulta metodologías vía `GET /career/operational-methodologies` filtrando con `applies_to_caller` (en el harness). La memoria pasa a `bedrock_agent_memory` (FTS, local) | LOCAL + OK | sí |
| `list_recent_changes`, `restore_deleted_record`, ruta `/bedrock/audit-log*` | tabla `audit_logs` (API) | D-19/RF-021: `audit_logs` se queda en la API; endpoints REST **nuevos y aditivos**: `GET /audit-log` (filtros `limit/offset`, `resource`, `user_id` del token) y `POST /audit-log/{audit_id}/restore` (restaura el registro; reutiliza la lógica actual de `routes/bedrock.py`). Acceso: usuario (los suyos) y `service` | GAP→nuevo (RF-021) | sí (en la lista) |
| `get_linkedin_status`, `list_linkedin_posts`, `create_linkedin_post`, `delete_scheduled_linkedin_post` | `linkedin_service`, modelos | `/linkedin/status`, `/linkedin/posts` (GET/POST/DELETE) | OK | sí (`/linkedin`) |
| `pdf_template` | `PdfOutputTemplate` | `/pdf-templates` CRUD | OK | sí (en lista) |
| `pdf_style` | `PdfTemplateStyle` | `/pdf-template-styles` CRUD | OK | sí (en lista) |
| `generate_pdf`, `render_record_pdf`, `list_pdf_capable_resources` | WeasyPrint en proceso (`pdf_service`, `pdf_template_render`) | `POST /pdf-templates/{id}/render` y la ruta de PDF de `career_search` (CV/vacante); `generate_pdf` (markdown→PDF) y el render de otros recursos: **a inventariar en la Fase 3** | OK/GAP por verificar | sí (en lista) |
| `generate_image`, `store_uploaded_image`, `attach_image_to_record`, `list_generated_images` | `file_upload`, MinIO (`storage_service`) | `POST /files` (multipart), `GET /files`, `GET /files/{id}/raw`, `PATCH /files/{id}/visibility`; el modelo de imagen lo llama el harness (Stability vía Bedrock, provider) | OK | sí (`/files`) |
| adjuntos del chat (`attachments.py`) | `FileUpload` + MinIO | `GET /files/{id}/raw` con el JWT del usuario | OK | n/a (siempre usuario) |
| `list_job_providers`, `run_job_discovery`, `import_job_url`, `save_job_listings` | `services.job_discovery` | `GET /career/job-discoveries/providers`, `POST /run`, `POST /import-url`, `POST /save` | OK | sí (`/career/*`) |
| `web_search`, `web_fetch` | `web_search_service` (Brave) | **LOCAL**: el servicio se mueve al harness con `BRAVE_SEARCH_API_KEY` | LOCAL | sí |
| `get_github_status`, `get_github_repo`, `list_github_repos`, `list_github_contents`, `get_github_file`, `search_github_code` | `github_service` | **LOCAL**: módulo propio del harness con `GITHUB_TOKEN` (duplica el cliente que conserva la API para `career_digital`; duplicación consciente, Art. 12) | LOCAL | sí |
| `admin_section_settings` | `section_catalog` (overrides en PG) | `GET /admin/sections`, `PUT /admin/sections/{id}` | OK | sí (en lista) |
| `agent_catalog_settings` | catálogo + metodologías + secciones | harness (config propia) + `/career/operational-methodologies` + `/admin/sections` | OK | sí |
| `bedrock_global_settings` | `bedrock_settings` | **LOCAL** (BD del harness) | LOCAL | sí |
| `error_report_settings` | `error_report_service` | `/settings/error-reports*` | OK | sí (en lista) |
| `delegate_to_specialist` | bucle propio | **LOCAL** | LOCAL | sí |
| errores del harness (`report_error`) | tabla `error_reports` (API) | `POST /system/error-report` (ingesta pública, sin auth, rate-limit 30/min/IP) | OK | n/a (sin auth) |
| notificaciones de turno de usuario (`task_scheduler._notify_user_turns`) | `UserNotification` (API) | no hay `POST /notifications` | GAP→nuevo (RF-020, D-20): `POST /notifications`, sólo rol `service` | sí |
| validación de identidad del JWT | BD de usuarios | claim `role` del JWT (RF-019) | OK (sin llamada a la API) | n/a |
| metodologías/secciones para el prompt (`prompt.py`, `profile_catalog`, `section_profiles`) | `methodology_scope`, `section_catalog` | `GET /career/operational-methodologies`, `GET /admin/sections` | OK | sí |

**Cuenta de servicio (D-17):** rol `service` con lista explícita (`/career/*`, `/files`,
`/pdf-templates`, `/pdf-template-styles`, `/linkedin`, `/admin/sections`,
`/settings/error-reports`, `/notifications`, auditoría). Las filas marcadas **no** arriba en
"Cuenta de servicio" pasan a **sí** para las rutas de esa lista; `/files/{id}/raw` y la
generación de PDF quedan sujetas al inventario de la Fase 3 (si requieren una ruta fuera de
la lista, se añade vía cambio de spec). Las tareas programadas conservan así las tools que
hoy usan.

## Cliente (`clients/`)

- `api_client.py`: `httpx.AsyncClient` único, `base_url = API_BASE_URL`
  (`http://cjhirashi-career-api:8000`), timeouts explícitos, reintento sólo en idempotentes
  5xx/timeout (máx. 2), mapea 401/403/404/409/422 a `ApiError` tipado (`status`, `detail`).
- Un módulo por familia: `career.py`, `files.py`, `sections.py`, `linkedin.py`, `pdf.py`,
  `job_discovery.py`, `errors.py`. Las tools sólo hablan con estos módulos (los servicios
  las inyectan; los tests usan `httpx.MockTransport`).
- Paginación: el cliente de `list` itera páginas con el mismo `limit/offset` que acepta la
  API; tope duro configurable para no leer tablas enteras (hazard de coste/latencia).
