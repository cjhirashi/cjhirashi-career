---
titulo: "Tasks — Harness de agentes fuera de la API (cjhirashi-career-ai) y sin indexación"
tipo: tasks
estado: draft
fecha: 2026-10-13
feature_id: "009"
spec: ./spec.md
plan: ./plan.md
---

# Tareas (atómicas ≤ 30 min, TDD: test antes que código)

Marcar `[x]` sólo con salida de terminal **pegada** (corrección del usuario en
`state.md`, 2026-09-02). Nunca "salida esperada". El revisor re-ejecuta.
Pytest `@pytest.mark.requisito("RF-0NN")`; Vitest `describe("RF-0NN: …")`.
Sin Bedrock ni Qdrant reales en ningún test (RNF-001). Rutas relativas a
`cjhirashi-career-api/` (API), `cjhirashi-career-ai/` (AI) o `cjhirashi-career-admin/` (Admin)
salvo que se indique otra cosa. `contracts/` = carpeta de esta feature.

Marcas: **[REQUIERE OK DEL USUARIO]** = toca BD, Qdrant, contenedores, Caddy o Bedrock
vivos; no se ejecuta sin autorización explícita en ese momento. **PARAR** = si se cumple la
condición, detener la feature y consultar al usuario.

Cada bloque deja la suite verde. Los bloques A–I son la **etapa 1**; J–K la **etapa 2**;
L la **etapa 3a**; M la **etapa 3b** (plan §7).

## Bloque 0 — Preparación y verificaciones tempranas

- [ ] **T-001** `[code]` (cubre RF-017) — Retirar `cjhirashi-career-ai` del `.gitignore`;
  mover el andamiaje actual a un directorio fuera del repo (no se reaprovecha, plan §0) y
  dejar sólo `Dockerfile`, `pyproject.toml`, `README.md` mínimos y `src/__init__.py`. Verificar
  `git status` sin sorpresas.
- [x] **T-002** `[code]` (cubre RF-018, P2) — **Inventario de rutas de las tools
  programadas.** Script de solo lectura (AST/grep) sobre `src/services/bedrock/tools.py`
  y `profile_tools.py` que lista, por tool, la ruta REST de la API que usará el harness
  (`contracts/harness-api-dependencies.md`) y las compara con `SERVICE_ALLOWED_PREFIXES`
  del contrato de auth. Salida: tabla pegada en la evidencia. **PARAR** si alguna tool
  usable por tareas programadas exige una ruta fuera de la lista (p. ej. render PDF de
  otros recursos, `generate_pdf`): hay que consultar al usuario y enmendar la spec; no
  ampliar la lista en silencio.
- [x] **T-003** `[code]` (cubre RF-019) — Verificar `access_role` (modelo de usuario y
  `schemas`): confirmar `String(32)` sin CHECK y los lugares que validan los valores
  permitidos. Anotar archivos a ampliar con `service`. Sin cambios de código.
- [ ] **T-004** `[code]` (cubre RF-007, RF-022, P3) — **[REQUIERE OK DEL USUARIO]**
  Obtener conteos reales de referencia (solo lectura): `SELECT count(*)` de las 10 tablas
  `bedrock_*` en `career_db` y número de puntos de memoria en Qdrant (scroll con conteo, sin
  escribir). Pegar los conteos en la evidencia; sirven de comparación para T-0xx de copia.
- [ ] **T-005** `[code]` (cubre RNF-002) — **[REQUIERE OK DEL USUARIO]** Backup de
  `career_db` (`pg_dump`) y snapshot de Qdrant antes de la etapa 1; guardar rutas y tamaños
  en la evidencia.

## Bloque A — AI: esqueleto, configuración y BD propia

- [ ] **T-010** `[test]` (cubre RF-006) — `tests/unit/test_config.py`: `Settings` exige
  `AI_DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `API_BASE_URL`, `AI_SERVICE_TOKEN`,
  `MEMORY_FTS_CONFIG` (por defecto `spanish`, D-24); sin variable obligatoria → error claro.
  Rojo.
- [ ] **T-011** `[code]` (cubre RF-006) — `src/config.py`, `.env.example`. Verde T-010.
- [ ] **T-012** `[test]` (cubre RF-008, RF-002) — `tests/unit/test_app_boot.py`: la app
  carga **todos** los routers (hazard del `ImportError` silenciado); `GET /health` 200 sin
  auth; ruta inexistente 404; falla si un router no se registra. Rojo.
- [ ] **T-013** `[code]` (cubre RF-008) — `src/app.py`, `src/routes/health.py`,
  `src/database.py` (engine/async session). Verde T-012.
- [ ] **T-014** `[test]` (cubre RF-006) — `tests/unit/models/test_schema_matches_contract.py`:
  los metadatos SQLAlchemy contienen las 10 tablas + `bedrock_agent_memory` con las columnas
  de `contracts/harness-db-schema.md` §1, sin FK a `users`. Rojo.
- [ ] **T-015** `[code]` (cubre RF-006) — `src/models/*` (10 modelos copiados de la API sin
  `ForeignKey("users.id")`). Verde parcial T-014 (sin memoria).
- [ ] **T-016** `[test]` (cubre RF-006) — `tests/unit/services/test_id_generator.py`: IDs
  `bco/bcm/bct/btk/bam-N` con `nextval` en BD de test; sin colisión tras `setval`. Rojo.
- [ ] **T-017** `[code]` (cubre RF-006) — `src/services/id_generator.py` (5 prefijos).
  Verde T-016.
- [ ] **T-018** `[test]` (cubre RF-006, RF-022) — `tests/unit/migrations/test_initial_migration.py`:
  `alembic upgrade head` en BD de test crea las 11 tablas, las secuencias, la columna
  generada `search_vector` y el índice GIN; `downgrade base` las elimina. Rojo.
- [ ] **T-019** `[code]` (cubre RF-006, RF-022) — `alembic.ini`, `alembic/env.py` (async),
  `alembic/versions/0001_initial_harness_schema.py`. Verde T-018 y T-014 completo.

## Bloque B — AI: interfaz de proveedor y Bedrock

- [ ] **T-020** `[test]` (cubre RF-005) — `tests/unit/providers/test_provider_contract.py`:
  un `FakeProvider` cumple el `Protocol ModelProvider` (`converse`, `converse_stream`,
  `generate_image`, `list_models`, `estimate_cost`); tipos neutros `ModelRequest`,
  `ToolSpec`, `ToolCall`, `Usage`. Rojo.
- [ ] **T-021** `[code]` (cubre RF-005) — `src/providers/base.py`. Verde T-020.
- [ ] **T-022** `[test]` (cubre RF-005) — `tests/unit/test_provider_boundary.py` (AST):
  fuera de `providers/bedrock/` nada importa `boto3`/`botocore`; `services/`/`routes/` no
  importan `providers.bedrock` (sólo la fábrica de `config`). Rojo si aún hay imports.
- [ ] **T-023** `[test]` (cubre RF-005) — `tests/unit/providers/test_bedrock_converse.py`:
  con cliente boto3 simulado (stub, sin red): mapeo de petición/respuesta Converse,
  `cachePoint`, errores de throttling, cálculo de coste (tabla de precios). Rojo.
- [ ] **T-024** `[code]` (cubre RF-005) — `src/providers/bedrock/{client,converse,pricing}.py`
  trasladando de `cjhirashi-career-api/src/services/bedrock/` (agent_loop sólo en su parte
  de proveedor). Verde T-023.
- [ ] **T-025** `[test]` (cubre RF-005) — `tests/unit/providers/test_bedrock_images.py`:
  `generate_image` con stub (Stability vía Bedrock, ADR-025), validación de parámetros.
  Rojo.
- [ ] **T-026** `[code]` (cubre RF-005) — `src/providers/bedrock/images.py` y fábrica
  `get_provider()` en `src/config.py`. Verde T-025 y T-022.

## Bloque C — AI: clientes REST hacia la API

- [ ] **T-030** `[test]` (cubre RF-004, RF-003) — `tests/unit/clients/test_api_client.py`
  (`httpx.MockTransport`): bearer del `Principal`; `AI_SERVICE_TOKEN` con `ServiceContext`;
  sin contexto → `MissingCredentialError`; 401/403/404/409/422 → `ApiError`; reintento sólo
  en idempotentes 5xx/timeout (máx. 2). Rojo.
- [ ] **T-031** `[code]` (cubre RF-004) — `src/middleware/principal.py`,
  `src/clients/api_client.py`. Verde T-030.
- [ ] **T-032** `[test]` (cubre RF-003) — `tests/unit/clients/test_career.py`: list con
  paginación y tope, get/create/update/delete, `count`, `distinct`, `bulk_update` = N× PUT.
  Rojo.
- [ ] **T-033** `[code]` (cubre RF-003) — `src/clients/career.py`. Verde T-032.
- [ ] **T-034** `[test]` (cubre RF-003, RF-004) — `tests/unit/clients/test_files_sections.py`:
  `files` (POST multipart, GET raw, PATCH visibilidad), `sections` (`GET/PUT /admin/sections`),
  metodologías (`/career/operational-methodologies`). Rojo.
- [ ] **T-035** `[code]` (cubre RF-003) — `src/clients/{files,sections}.py`. Verde T-034.
- [ ] **T-036** `[test]` (cubre RF-003) — `tests/unit/clients/test_linkedin_pdf_jobs_errors.py`:
  `linkedin`, `pdf` (`/pdf-templates`, `/pdf-template-styles`), `job_discovery`, `errors`
  (`POST /system/error-report` sin auth). Rojo.
- [ ] **T-037** `[code]` (cubre RF-003) — `src/clients/{linkedin,pdf,job_discovery,errors}.py`.
  Verde T-036.
- [ ] **T-038** `[test]` (cubre RF-020, RF-021) — `tests/unit/clients/test_notifications_audit.py`:
  `POST /notifications` con token de servicio; `GET /audit-log`, `POST /audit-log/{id}/restore`
  con el JWT del usuario. Rojo.
- [ ] **T-039** `[code]` (cubre RF-020, RF-021) — `src/clients/{notifications,audit}.py`.
  Verde T-038.
- [ ] **T-040** `[test]` (cubre RF-003) — `tests/unit/test_isolation.py`: regex sobre
  `src/` sin referencias a `career_db`, `qdrant`, `SOURCE_`, `psycopg` hacia otra BD. Rojo
  si queda alguna. (Se ejecuta de nuevo al final de cada bloque.)

## Bloque D — AI: autenticación

- [ ] **T-050** `[test]` (cubre RF-002, RF-019) — `tests/unit/middleware/test_auth.py`
  (matriz `contracts/auth-jwt-service-account.md` §5, fila ai/middleware): sin header,
  firma inválida, expirado, refresh, `role` desconocido → 401; `role` agent/service → 403;
  sin claim = user; token válido → `Principal`; ninguna llamada a la API. Rojo.
- [ ] **T-051** `[code]` (cubre RF-002, RF-019) — `src/middleware/auth.py`. Verde T-050.

## Bloque E — AI: repositorios y servicios (catálogo, ajustes, uso)

- [ ] **T-060** `[test]` (cubre RF-006) — `tests/unit/repositories/test_conversation_repo.py`
  con `db_session`: CRUD de `bedrock_conversations` y mensajes (cascade), listado por
  `user_id`, renombrar. Rojo.
- [ ] **T-061** `[code]` (cubre RF-006) — `src/repositories/conversation_repo.py`. Verde T-060.
- [ ] **T-062** `[test]` (cubre RF-006) — `test_settings_profile_repo.py`: `bedrock_settings`
  (modelo, presupuesto, reglas), prompts, fotos, tools por perfil, delegación, tools
  personalizadas. Rojo.
- [ ] **T-063** `[code]` (cubre RF-006) — `src/repositories/{settings_repo,profile_repo,custom_tool_repo}.py`.
  Verde T-062.
- [ ] **T-064** `[test]` (cubre RF-006) — `test_usage_repo.py`: `usage_logs` y
  `usage_round_logs`, agregados de métricas y presupuesto diario. Rojo.
- [ ] **T-065** `[code]` (cubre RF-006) — `src/repositories/usage_repo.py`,
  `src/services/usage_service.py`. Verde T-064.
- [ ] **T-066** `[test]` (cubre RF-006) — `test_task_repo.py`: `bedrock_tasks` con
  `parent_id`, subtareas, filtros `filters`/orden/`count`/`distinct`. Rojo.
- [ ] **T-067** `[code]` (cubre RF-006) — `src/repositories/task_repo.py`. Verde T-066.
- [ ] **T-068** `[test]` (cubre RF-012, RF-001) — `tests/contract/test_agent_registry_contract.py`:
  `src/services/agent_registry.py` coincide con `contracts/agent-registry.json` (20 perfiles,
  id/label/nivel). Rojo.
- [ ] **T-069** `[code]` (cubre RF-012) — `src/services/agent_registry.py` (+ perfiles
  trasladados de `agent_profiles.py`). Verde T-068.
- [ ] **T-070** `[test]` (cubre RF-001, RF-003) — `tests/unit/services/test_profile_catalog.py`:
  catálogo de perfiles cruza metodologías y secciones leídas por REST (cliente simulado);
  regla `applies_to_caller`; tools por sección derivadas de `/admin/sections`. Rojo.
- [ ] **T-071** `[code]` (cubre RF-001, RF-003) — `src/services/{profile_catalog,tools_registry,prompt}.py`.
  Verde T-070.

## Bloque F — AI: memoria (FTS) y bucle de agente

- [ ] **T-080** `[test]` (cubre RF-022) — `tests/unit/repositories/test_memory_repo.py` con
  BD de test: insertar nota/hecho/manual, listar por usuario/perfil, borrar, búsqueda
  `websearch_to_tsquery(MEMORY_FTS_CONFIG)` con `ts_rank` (acentos, plurales en español),
  aislamiento por `user_id`, unicidad `user_id+source_ref`. Rojo.
- [ ] **T-081** `[code]` (cubre RF-022) — `src/models/bedrock_agent_memory.py`,
  `src/repositories/memory_repo.py`. Verde T-080 y T-014.
- [ ] **T-082** `[test]` (cubre RF-022, RF-001) — `test_memory_service.py`: sustituye
  `local_memory` (notas del agente, `memory/events` desde mensajes, `memory/records` por FTS,
  `memory/manual`); sin imports de Qdrant. Rojo.
- [ ] **T-083** `[code]` (cubre RF-022) — `src/services/memory_service.py`. Verde T-082.
- [ ] **T-084** `[test]` (cubre RF-005, RF-004) — `tests/unit/services/test_agent_loop.py`
  con `FakeProvider`: turno sin tools, con tool, límite `max_round_trips`, ventana de
  historial, presupuesto diario superado, coste registrado, el JWT del usuario llega al
  cliente. Rojo.
- [ ] **T-085** `[code]` (cubre RF-005) — `src/services/agent_loop.py` (trasladado,
  inyección del provider). Verde T-084.
- [ ] **T-086** `[test]` (cubre RF-003) — `test_tools_career_and_local.py`: tools
  de CRUD de carrera vía cliente simulado; `web_search`, `web_fetch`, GitHub (LOCAL) con
  `httpx.MockTransport`; `search_knowledge_base` **no existe** en el catálogo; `bulk_update`
  secuencial. Rojo.
- [ ] **T-087** `[code]` (cubre RF-003) — `src/services/{tools_career.py,web_search.py,github_tools.py}`.
  Verde T-086.
- [ ] **T-088** `[test]` (cubre RF-003, RF-021) — `test_tools_files_pdf_linkedin_audit.py`:
  tools de archivos/PDF/LinkedIn/ajustes/errores vía cliente; `list_recent_changes` y
  `restore_deleted_record` vía `/audit-log`; 403 de la API → error de tool legible (no
  excepción). Rojo.
- [ ] **T-089** `[code]` (cubre RF-003, RF-021) — `src/services/tools_*.py` restantes.
  Verde T-088.
- [ ] **T-090** `[test]` (cubre RF-005) — `test_delegation_and_images.py`: delegación
  L1→L2/L3 hereda credencial; `generate_image` usa el provider y sube con `POST /files`.
  Rojo.
- [ ] **T-091** `[code]` (cubre RF-005) — `src/services/{delegation,image_service}.py`.
  Verde T-090.
- [ ] **T-092** `[test]` (cubre RF-004, RF-020) — `test_task_scheduler.py` (reloj
  inyectable): ejecuta tareas con `ServiceContext`; tarea de otro dueño → `failed`;
  `execute_on_turn` → notificación vía `POST /notifications`; avance de subtareas
  (`enqueue_advance`). Rojo.
- [ ] **T-093** `[code]` (cubre RF-004, RF-020) — `src/services/task_scheduler.py`,
  `src/services/error_reporting.py` (envía a `POST /system/error-report`). Verde T-092.

## Bloque G — AI: rutas

- [ ] **T-100** `[test]` (cubre RF-001, RF-002) — `tests/contract/test_ai_route_parity.py`:
  lee `contracts/ai-routes.md` y exige que `app.openapi()` contenga exactamente las
  filas P/P*/S y no las X (D-16). Todas las rutas sin JWT → 401 (salvo `/health`). Rojo.
- [ ] **T-101** `[test]` (cubre RF-008) — `tests/unit/routes/test_chat_sse.py`: `POST
  /bedrock/chat` devuelve `text/event-stream` con eventos `status`/`done`/`error`, ping
  `: ping` cada 15 s (reloj inyectado), `X-Accel-Buffering: no`; error del provider → evento
  `error`, no 500. Rojo.
- [ ] **T-102** `[code]` (cubre RF-001, RF-008) — `src/routes/bedrock.py`,
  `src/services/chat_service.py`, `src/schemas/*` (copiados de la API). Verde T-101.
- [ ] **T-103** `[test]` (cubre RF-001) — `test_routes_agent_profiles.py` (rutas 9–20 de
  `ai-routes.md`) con dobles de servicios. Rojo.
- [ ] **T-104** `[code]` (cubre RF-001) — `src/routes/agent_profiles.py`. Verde T-103.
- [ ] **T-105** `[test]` (cubre RF-001, RF-022) — `test_routes_memory_tools_conversations.py`
  (rutas 21-28, 31-37). Rojo.
- [ ] **T-106** `[code]` (cubre RF-001, RF-022) — `src/routes/{memory,tools,conversations}.py`.
  Verde T-105.
- [ ] **T-107** `[test]` (cubre RF-001, RF-021) — `test_routes_audit_log_agent_tasks.py`
  (rutas 38-39, 40-47): `audit-log` delega en el cliente; `agent-tasks` mismos query params y
  `subtasks` anidadas; `PUT` dispara `enqueue_advance`; `POST .../run` usa el JWT del
  usuario. Rojo.
- [ ] **T-108** `[code]` (cubre RF-001, RF-021) — `src/routes/{audit_log,agent_tasks}.py`.
  Verde T-107, T-100 y T-012.
- [ ] **T-109** `[test]` (cubre RF-001) — `tests/e2e/test_chat_flow.py`: JWT real firmado
  con secreto de prueba → chat → herramienta de carrera contra API simulada → respuesta
  persistida en `career_ai_db` de test. Rojo, luego verde con lo anterior.
- [ ] **T-110** `[code]` (cubre RNF-003) — Métricas Prometheus (`/metrics`), logging;
  cobertura por módulo ≥ 80 % (`pytest --cov`); pegar el informe.

## Bloque H — Scripts de copia de datos (offline)

- [ ] **T-120** `[test]` (cubre RF-007, RF-017) — `tests/unit/scripts/test_copy_from_career_db.py`
  (BD de test origen/destino): copia las 10 tablas conservando ids; idempotente; `setval`
  (insertar tras copiar no colisiona); reporte JSON por tabla (`source`, `dest`,
  `missing_in_dest`, `checksum_ok`); exit ≠ 0 y `ok:false` si un conteo difiere; `--dry-run`;
  `--verify-only` tolera destino mayor; `--direction ai-to-api`. Rojo.
- [ ] **T-121** `[code]` (cubre RF-007, RF-017) — `scripts/copy_from_career_db.py`. Verde T-120.
- [ ] **T-122** `[test]` (cubre RF-022, RF-007) — `tests/unit/scripts/test_migrate_memory_from_qdrant.py`
  (cliente Qdrant simulado, jamás real): scroll de puntos de memoria, descarta puntos de
  registros indexados, idempotente (`source_ref`), `kind` correcto, reporte con
  `source = dest + skipped_invalid`, exit ≠ 0 si no cuadra, inválidos listados. Rojo.
- [ ] **T-123** `[code]` (cubre RF-022) — `scripts/migrate_memory_from_qdrant.py`. Verde T-122.

## Bloque I — API: cambios aditivos (etapa 1)

- [ ] **T-130** `[test]` (cubre RF-019) — `tests/unit/test_jwt_role_claim.py`: access,
  refresh, agente y servicio llevan `role` correcto; sin claim = `user`; claim desconocido →
  401; discrepancia claim/BD manda la BD. Rojo.
- [ ] **T-131** `[code]` (cubre RF-019) — `src/services/auth_service.py` (`_create_token`),
  `src/middleware/auth.py` (lectura). Verde T-130.
- [ ] **T-132** `[test]` (cubre RF-018) — `tests/unit/test_agent_service_scope.py`: `agent`
  200 en `/career/*` y 403 en `/bedrock/chat`, `/agent-tasks`, cualquier otra; `service` 200 en
  cada prefijo de `SERVICE_ALLOWED_PREFIXES` y 403 fuera (p. ej. `/users`, `/auth/*` de
  gestión). Rojo.
- [ ] **T-133** `[code]` (cubre RF-018) — `src/middleware/auth.py`
  (`SERVICE_ALLOWED_PREFIXES`), validación de `access_role` con `service` en
  `schemas`/`models/user.py`. Verde T-132. (Sin migración, T-003.)
- [ ] **T-134** `[test]` (cubre RF-020) — `tests/unit/test_notifications_route.py`: `POST
  /notifications` crea `UserNotification`; usuario/agent → 403; validación del cuerpo. Rojo.
- [ ] **T-135** `[code]` (cubre RF-020) — `src/routes/notifications.py`, registro en
  `src/app.py`. Verde T-134.
- [ ] **T-136** `[test]` (cubre RF-021) — `tests/unit/test_audit_log_routes.py`: `GET
  /audit-log` (paginación, filtros, solo los del usuario), `POST /audit-log/{id}/restore`
  (restaura, 404/409); `service` permitido; `audit_logs` se sigue escribiendo en
  `career_repository`. Rojo.
- [ ] **T-137** `[code]` (cubre RF-021) — `src/routes/audit_log.py`,
  `src/services/audit_service.py` (lógica copiada de `routes/bedrock.py`). Verde T-136.
- [ ] **T-138** `[test]` (cubre RF-012) — `tests/unit/test_agent_registry_contract.py` (API):
  `src/services/agent_registry.py` == `contracts/agent-registry.json`. Rojo.
- [ ] **T-139** `[code]` (cubre RF-012) — `src/services/agent_registry.py` (estático). Verde
  T-138. (Aún no se cambian los imports: eso es 3a.)
- [ ] **T-141** `[test]` (cubre RF-003, RF-018) — `tests/unit/test_file_metadata_route.py`:
  `GET /files/{id}` devuelve `id`, `mime_type`, `original_filename`, tamaño y categoría en
  el mismo formato que los elementos de `GET /files`; 404 si no existe o no es del usuario;
  token `service` 200 (dentro de `/files`); `agent` 403 (D-25). Rojo. Luego `[code]`:
  `src/routes/files.py` (ruta nueva, aditiva; sin romper `/raw` ni `/visibility`). Verde.
  Desbloquea `store_uploaded_image` (T-088/T-089).
- [ ] **T-140** `[code]` (cubre RNF-001) — `pytest` completo de la API y del AI; pegar la
  salida y la cobertura. Cierra la parte de código de la etapa 1.

## Bloque J — Infra de la etapa 1 (archivos; sin aplicar)

- [ ] **T-150** `[test]` (cubre RF-015, RF-016) — `tests/infra/test_deploy_files.py` (en
  AI o en un `tests/` raíz): `docker-compose.yml` define `cjhirashi-career-ai` (puerto 8010,
  `depends_on`, healthcheck); (en etapa 1 **aún** conserva `qdrant`); `caddy.json` es JSON
  válido, el servicio `admin` tiene `/ai/` → `cjhirashi-career-ai:8010` con `quitar_prefijo`
  y `sse`, y el bloque `cjhirashi_srv` es idéntico al de HEAD. Rojo.
- [ ] **T-151** `[code]` (cubre RF-015, RF-016) — `docker-compose.yml` (servicio ai),
  script de init idempotente de `career_ai_db` y usuario propio en `postgres_db` (D-21),
  `caddy.json` (solo `servicios`), `prometheus.yml`, `.env.example`, `Dockerfile` del ai.
  Verde T-150. Validar con `bin/caddy-sync` en modo comprobación (sin aplicar).

## Bloque K — Etapa 1: operación en vivo

- [ ] **T-160** `[code]` (cubre RF-015) — **[REQUIERE OK DEL USUARIO]** Crear `career_ai_db` y
  usuario propio en `postgres_db`; aplicar `alembic upgrade head` del ai contra la BD real
  (verificar antes el estado real, Art. 4). Pegar `\dt` y `\du`.
- [ ] **T-161** `[code]` (cubre RF-007, RF-017) — **[REQUIERE OK DEL USUARIO]** Ejecutar
  `copy_from_career_db.py --dry-run` y luego real (`api-to-ai`); pegar `ai_copy_report.json`
  y comparar con T-004. Aborta si `ok:false`.
- [ ] **T-162** `[code]` (cubre RF-022) — **[REQUIERE OK DEL USUARIO]** Ejecutar
  `migrate_memory_from_qdrant.py` y pegar `memory_migration_report.json` (comparar con
  T-004).
- [ ] **T-163** `[code]` (cubre RF-015, RF-016, RF-017) — **[REQUIERE OK DEL USUARIO]**
  `docker compose up -d cjhirashi-career-ai`, aplicar `caddy.json` (`bin/caddy-sync`), crear
  fuera de banda el usuario `service` y `AI_SERVICE_TOKEN`. Verificar `GET /health` y un
  chat de humo con JWT real en `/ai/` (SSE sin buffering). Pegar salidas. Reversión:
  parar el servicio y quitar la ruta.

## Bloque L — Admin (etapa 2)

- [ ] **T-170** `[test]` (cubre RF-013) — `src/tests/api/aiRoutes.test.ts`: cada llamada de
  `api/bedrock.ts` y `api/agentTasks.ts` usa una ruta de `contracts/ai-routes.md` y la base
  `/ai`; `src/tests/api/noLegacyAgentRoutes.test.ts`: ningún archivo de `src/` contiene
  `/api/bedrock` ni `/api/agent-tasks`. Rojo.
- [ ] **T-171** `[code]` (cubre RF-013) — `src/api/client.ts` (`aiClient`, mismo
  interceptor de JWT/refresh), `src/api/bedrock.ts`, `src/api/agentTasks.ts`,
  `vite.config.ts` (proxy `/ai`), `VITE_AI_BASE_URL`. Verde T-170.
- [ ] **T-172** `[test]` (cubre RF-008, RF-013) — test del cliente SSE del chat con la
  base `/ai`. Rojo.
- [ ] **T-173** `[code]` (cubre RF-008, RF-013) — `src/components/bedrock/*` (URL del
  stream). Verde T-172.
- [ ] **T-174** `[test]` (cubre RF-014) — suite completa de Vitest + `npm run type-check`:
  los tests de los componentes de agentes pasan **sin modificar sus aserciones**. Pegar salida.
- [ ] **T-175** `[code]` (cubre RF-014) — Revisión UX completa (Art. 8, D-22) por
  `experto-ux-ui` de: chat lateral, páginas `Agent*`, métricas de coste, `AdminSectionsPage`,
  `TasksPage`. Hallazgos como tareas nuevas; ninguna regresión visual.
- [ ] **T-176** `[code]` (cubre RF-013, RF-017) — **[REQUIERE OK DEL USUARIO]** Desplegar el
  Admin apuntando a `/ai/` (etapa 2); humo de UI (chat, tareas, métricas, perfiles); pegar
  evidencia. Reversión: Admin anterior (+ `copy --direction ai-to-api` antes si se quieren
  conservar los datos escritos en el harness).

## Bloque M — API: retirada (etapa 3a)

- [ ] **T-180** `[test]` (cubre RF-012) — Pruebas de contrato existentes de
  `admin_sections`/`methodology_scope`/`section_catalog`/`career_methodologies` se mantienen
  sin cambios y deben seguir verdes tras cambiar los imports. Añadir
  `tests/unit/test_no_bedrock_imports.py` (AST): `src/` de la API no contiene `bedrock`,
  `qdrant`, `boto3`. Rojo.
- [ ] **T-181** `[code]` (cubre RF-012) — Editar `src/services/{admin_sections,methodology_scope,section_catalog}.py`,
  `src/schemas/{career_methodologies,admin_sections}.py`, `src/routes/admin_sections.py`:
  imports a `services.agent_registry`; quitar el reindexado al guardar metodologías.
  Contratos verdes.
- [ ] **T-182** `[test]` (cubre RF-010) — `tests/unit/test_career_repository_no_indexing.py`:
  con espía que falla si se llama a indexado/`qdrant`; create/update/delete de un registro
  no indexa; no se crean `BedrockTask` como efecto. Rojo.
- [ ] **T-183** `[code]` (cubre RF-010) — `src/repositories/career_repository.py` (hook de
  indexado, `_KB_EXCLUDED_COLUMNS`, creación de subtareas), `src/routes/career_common.py`.
  Verde T-182.
- [ ] **T-184** `[test]` (cubre RF-009) — `tests/unit/test_bedrock_routes_removed.py`:
  `/bedrock/*` y `/agent-tasks/*` → 404 (con y sin JWT). Rojo.
- [ ] **T-185** `[code]` (cubre RF-009, RF-010) — Quitar `src/routes/{bedrock,bedrock_tasks}.py`,
  sus `include_router`, el scheduler y el cierre de Qdrant en `src/app.py`; quitar
  `src/services/bedrock/**`, `bedrock_service.py`, `qdrant_service.py`, `task_scheduler.py`,
  `src/schemas/bedrock*.py`, `scripts/check_kb_consistency.py`; ajustar
  `middleware/auth.py` (sin `POST /bedrock/chat`), `error_reporting.py`, `id_generator.py`
  (prefijos se quitan en 3b), `pdf_template_styles`, `config.py`. Verde T-184, T-180.
- [ ] **T-186** `[code]` (cubre RF-010) — Quitar de las dependencias `qdrant-client`,
  embeddings y `boto3` (si grep confirma que nadie más lo usa); quitar/mover los tests de
  `tests/**/bedrock/**`, `test_knowledge_base_*`, `test_qdrant_*`. `pytest` completo de la
  API verde; pegar salida y cobertura.
- [ ] **T-187** `[code]` (cubre RF-017) — **[REQUIERE OK DEL USUARIO]** Desplegar la API sin
  Bedrock/KB (etapa 3a); humo de `/career/*`, metodologías, secciones, notificaciones,
  auditoría. Reversión: despliegue anterior (las tablas siguen en `career_db`).

## Bloque N — Etapa 3b: DROP y retirada de Qdrant

- [ ] **T-190** `[test]` (cubre RF-011) — `tests/unit/test_drop_bedrock_tables_migration.py`
  (patrón `test_vacancy_process_stage_migration.py`, dobles): sin `AI_COPY_REPORT` / con
  `ok:false` / con reporte > 24 h / PK actuales ≠ reporte → `RuntimeError` **sin DDL**;
  `upgrade` elimina las 10 tablas y secuencias (idempotente); `downgrade` recrea estructura
  (10 tablas, columnas de `harness-db-schema.md` §1). Rojo.
- [ ] **T-191** `[code]` (cubre RF-011) — `alembic/versions/<nueva>_drop_bedrock_tables.py`
  (`down_revision` re-verificado contra el head real). Verde T-190.
- [ ] **T-192** `[test]` (cubre RF-015) — `test_deploy_files.py`: `docker-compose.yml` no
  contiene `qdrant` ni `QDRANT_*`, ni volumen; `.env.example` sin `QDRANT_*`. Rojo.
- [ ] **T-193** `[code]` (cubre RF-015, RF-010) — Quitar el servicio y volumen `qdrant` de
  `docker-compose.yml` y las variables de `.env.example`/`prometheus.yml`. Verde T-192.
- [ ] **T-194** `[code]` (cubre RF-011, RF-017) — **[REQUIERE OK DEL USUARIO]** Backup
  fresco, `copy_from_career_db.py --verify-only` (reporte `ok:true`) y confirmar reporte de
  memoria `ok:true`; snapshot de Qdrant. Pegar los tres.
- [ ] **T-195** `[code]` (cubre RF-011) — **[REQUIERE OK DEL USUARIO]** `alembic upgrade
  head` de la API con `AI_COPY_REPORT` apuntando al reporte; verificar que las 10 tablas ya
  no existen. Pegar `\dt`.
- [ ] **T-196** `[code]` (cubre RF-015) — **[REQUIERE OK DEL USUARIO]** Detener y eliminar
  el contenedor y volumen `qdrant`; `docker compose up` sin `qdrant`; humo end-to-end
  (chat con memoria FTS). Reversión: `alembic downgrade` + `copy --direction ai-to-api` o
  backup (el snapshot de Qdrant solo restauraría la KB).
- [ ] **T-197** `[code]` (cubre RNF-003) — Cobertura final ≥ 80 % por módulo en AI, API y
  Admin; pegar los informes. Re-ejecutar `test_isolation.py` y `test_provider_boundary.py`.

## Bloque O — Documentación `[doc]` (una tarea = una fila de plan §11)

- [ ] **T-200** `[doc]` — fila 1: `docs/09-DECISIONS/029-harness-agentes-fuera-de-api.md`
  (hecho: Aceptado; verificar enlaces y estado final).
- [ ] **T-201** `[doc]` — fila 2: `docs/09-DECISIONS/README.md` (fila 029 Aceptado).
- [ ] **T-202** `[doc]` — fila 3: `docs/01-INTRODUCTION.md`.
- [ ] **T-203** `[doc]` — fila 4: `docs/02-CONSTRAINTS.md`.
- [ ] **T-204** `[doc]` — fila 5: `docs/03-CONTEXT-SCOPE.md`.
- [ ] **T-205** `[doc]` — fila 6: `docs/04-SOLUTION-STRATEGY.md`.
- [ ] **T-206** `[doc]` — fila 7: `docs/05-BUILDING-BLOCKS.md`.
- [ ] **T-207** `[doc]` — fila 8: `docs/06-RUNTIME-VIEW.md`.
- [ ] **T-208** `[doc]` — fila 9: `docs/07-DEPLOYMENT-VIEW.md`.
- [ ] **T-209** `[doc]` — fila 10: `docs/08-CROSS-CUTTING-CONCEPTS.md`.
- [ ] **T-210** `[doc]` — fila 11: `docs/10-QUALITY-REQUIREMENTS.md`.
- [ ] **T-211** `[doc]` — fila 12: `docs/11-RISKS-TECHNICAL-DEBT.md`.
- [ ] **T-212** `[doc]` — fila 13: `docs/12-GLOSSARY.md`.
- [ ] **T-213** `[doc]` — fila 14: `docs/BEDROCK-SYSTEM.md`.
- [ ] **T-214** `[doc]` — fila 15: `docs/ENVIRONMENT-SECURITY.md` (variables, procedimiento del
  token `service`).
- [ ] **T-215** `[doc]` — fila 16: `docs/IMPLEMENTATION_PLAN.md`.
- [ ] **T-216** `[doc]` — fila 17: `docs/ADMIN_PANEL_SETUP.md`.
- [ ] **T-217** `[doc]` — fila 18: `README.md`.
- [ ] **T-218** `[doc]` — fila 19: `AGENTS.md` (fila ai, puerto 8010, sin Qdrant).
- [ ] **T-219** `[doc]` — fila 20: `.harness/constitution.md` Art. 2 y 4 (**ya aplicada** al
  aprobar el Gate 2; verificar contra ADR-029 y el historial).
- [ ] **T-220** `[doc]` — fila 21: `cjhirashi-career-api/README.md`, `src/README.md`,
  `src/models/README.md`.
- [ ] **T-221** `[doc]` — fila 22: `cjhirashi-career-api/docs/ARCHITECTURE.md`.
- [ ] **T-222** `[doc]` — fila 23: `cjhirashi-career-api/docs/API.md`.
- [ ] **T-223** `[doc]` — fila 24: `cjhirashi-career-api/docs/DATABASE.md`.
- [ ] **T-224** `[doc]` — fila 25: `cjhirashi-career-api/docs/BEDROCK-HARNESS.md` (mover al
  README del harness).
- [ ] **T-225** `[doc]` — fila 26: `cjhirashi-career-api/docs/sections/` (bedrock,
  bedrock-tasks, files, linkedin, pdf-*, career-*).
- [ ] **T-226** `[doc]` — fila 27: `cjhirashi-career-api/src/services/bedrock/README.md`
  (retirar).
- [ ] **T-227** `[doc]` — fila 28: `cjhirashi-career-admin/docs/BEDROCK-CHAT.md`.
- [ ] **T-228** `[doc]` — fila 29: `cjhirashi-career-admin/README.md`.
- [ ] **T-229** `[doc]` — fila 30: `cjhirashi-career-ai/README.md` (nuevo).
- [ ] **T-230** `[doc]` — fila 31: docs de la API de notificaciones y auditoría
  (`cjhirashi-career-api/docs/sections/`).
- [ ] **T-231** `[doc]` — fila 32: sección de autenticación (claim `role`, rol `service`,
  lista de rutas) en `cjhirashi-career-api/docs/ARCHITECTURE.md`/`API.md`.
- [ ] **T-232** `[doc]` — fila 33: `cjhirashi-career-ai/docs/MEMORY.md`.
- [ ] **T-233** `[doc]` — fila 34: comentarios/descripciones en `docker-compose.yml`,
  `caddy.json` (`servicios`), `prometheus.yml`, `.env.example`.

## Cobertura (el gate exige 100 %; `Pass` lo rellena el gate)

| RF / RNF / doc | Tareas | Test(s) | Pass |
|---|---|---|---|
| RF-001 | T-068, T-070, T-071, T-100, T-102..T-109 | test_ai_route_parity · test_routes_* · e2e | |
| RF-002 | T-012, T-050, T-051, T-100 | test_auth (ai) · test_app_boot | |
| RF-003 | T-030..T-040, T-141, T-070, T-086..T-089 | test_api_client · test_career · test_isolation · test_tools_* · test_file_metadata_route | |
| RF-004 | T-030, T-031, T-084, T-092, T-093 | test_api_client · test_agent_loop · test_task_scheduler | |
| RF-005 | T-020..T-026, T-084, T-085, T-090, T-091 | test_provider_contract · test_provider_boundary · test_bedrock_* | |
| RF-006 | T-010..T-019, T-060..T-067 | test_schema_matches_contract · test_initial_migration · test_*_repo | |
| RF-007 | T-004, T-120, T-121, T-122, T-161 | test_copy_from_career_db · evidencia en vivo | |
| RF-008 | T-012, T-013, T-101, T-102, T-172, T-173 | test_chat_sse · test SSE Admin | |
| RF-009 | T-184, T-185 | test_bedrock_routes_removed | |
| RF-010 | T-180, T-182, T-183, T-185, T-186, T-193 | test_career_repository_no_indexing · test_no_bedrock_imports | |
| RF-011 | T-190, T-191, T-194, T-195 | test_drop_bedrock_tables_migration | |
| RF-012 | T-068, T-069, T-138, T-139, T-180, T-181 | test_agent_registry_contract (ambos) · contratos de secciones | |
| RF-013 | T-170..T-173, T-176 | aiRoutes.test · noLegacyAgentRoutes.test | |
| RF-014 | T-174, T-175 | suite Vitest sin cambios de aserciones · revisión UX | |
| RF-015 | T-150, T-151, T-160, T-192, T-193, T-196 | test_deploy_files | |
| RF-016 | T-150, T-151, T-163 | test_deploy_files (caddy) | |
| RF-017 | T-001, T-120, T-121, T-161, T-163, T-176, T-187, T-194 | test_copy_from_career_db · evidencia por etapa | |
| RF-018 | T-002, T-132, T-133, T-141 | test_agent_service_scope · test_file_metadata_route | |
| RF-019 | T-003, T-050, T-130, T-131 | test_jwt_role_claim · test_auth (ai) | |
| RF-020 | T-038, T-039, T-092, T-134, T-135 | test_notifications_route · test_task_scheduler | |
| RF-021 | T-038, T-039, T-088, T-107, T-136, T-137 | test_audit_log_routes · test_tools_files_pdf_linkedin_audit | |
| RF-022 | T-004, T-018, T-080..T-083, T-122, T-123, T-162 | test_memory_repo · test_memory_service · test_migrate_memory_from_qdrant | |
| RNF-001 | T-022, T-140, T-186 | tests sin Bedrock ni Qdrant reales (stubs/dobles) | |
| RNF-002 | T-004, T-005, T-194 | evidencia de backup/snapshot y OK del usuario | |
| RNF-003 | T-110, T-197 | cobertura ≥ 80 % por módulo y marcadores `requisito` | |
| doc (34 filas de plan §11) | T-200..T-233 | — | |

## Evidencia (salida real pegada)

**T-002 (2026-10-13, solo lectura):** script `t002_inventory.py` (AST sobre `_RAW_TOOLS` de
`cjhirashi-career-api/src/services/bedrock/tools.py`; vive en el scratchpad de la sesión, fuera del
repo). El mapa tool -> ruta se verificó leyendo los ejecutores de `tools.py` y los routers reales
(`routes/*.py`). Hecho relevante: `SERVICE_ALLOWED_PREFIXES` **aún no existe** en el código; el script
usa los prefijos del contrato (`auth-jwt-service-account.md` §4) más `/audit-log` (cláusula
"rutas de auditoría"). Las tareas programadas (`services/task_scheduler.py::execute_claimed_task`)
ejecutan **cualquier** perfil (L1/L2/L3 -> `run_single_turn_sync`), así que se inventarían las 41 tools.
```
tools en _RAW_TOOLS: 41 sin mapeo: [] mapeo sobrante: []
tool                           | ruta REST / local                                              | cubierta
list_recent_changes            | GET /audit-log                                                 | SI
restore_deleted_record         | POST /audit-log/{id}/restore                                   | SI
describe_resource_schema       | GET /openapi.json                                              | NO  <<<<
search_knowledge_base          | LOCAL (retirada; GET /career/operational-methodologies)        | n/a (local)
search_knowledge_base          | GET /career/operational-methodologies                          | SI
list_career_record             | GET /career/{r}                                                | SI
count_career_records           | GET /career/{r}/count                                          | SI
get_career_record              | GET /career/{r}/{id}                                           | SI
create_career_record           | POST /career/{r}                                               | SI
update_career_record           | PUT /career/{r}/{id}                                           | SI
bulk_update_career_record      | PUT /career/{r}/{id}                                           | SI
delete_career_record           | DELETE /career/{r}/{id}                                        | SI
get_linkedin_status            | GET /linkedin/status                                           | SI
list_linkedin_posts            | GET /linkedin/posts                                            | SI
create_linkedin_post           | POST /linkedin/posts                                           | SI
delete_scheduled_linkedin_post | DELETE /linkedin/posts/{id}                                    | SI
pdf_template                   | GET /pdf-templates                                             | SI
pdf_template                   | GET /pdf-templates/{id}                                        | SI
pdf_template                   | POST /pdf-templates                                            | SI
pdf_template                   | PUT /pdf-templates/{id}                                        | SI
pdf_style                      | GET /pdf-template-styles                                       | SI
pdf_style                      | GET /pdf-template-styles/{id}                                  | SI
pdf_style                      | POST /pdf-template-styles                                      | SI
pdf_style                      | PUT /pdf-template-styles/{id}                                  | SI
generate_pdf                   | GET /pdf-templates/{id}                                        | SI
generate_pdf                   | POST /pdf-templates/{id}/render                                | SI
generate_pdf                   | POST /files                                                    | SI
list_pdf_capable_resources     | LOCAL (constante PDF_CAPABLE_RESOURCES)                        | n/a (local)
render_record_pdf              | GET /career/{cv-versions|cover-letter-versions}/{id}           | SI
render_record_pdf              | GET /pdf-templates/defaults/by-type                            | SI
render_record_pdf              | GET /pdf-templates/{id}                                        | SI
render_record_pdf              | POST /pdf-templates/{id}/render                                | SI
render_record_pdf              | POST /files                                                    | SI
generate_image                 | LOCAL (provider Bedrock)                                       | n/a (local)
generate_image                 | POST /files                                                    | SI
store_uploaded_image           | GET /files/{id}                                                | SI
store_uploaded_image           | GET /files/{id}/raw                                            | SI
store_uploaded_image           | POST /files                                                    | SI
attach_image_to_record         | PUT /career/{publications|projects}/{id}                       | SI
attach_image_to_record         | LOCAL (agent-profile: foto en BD del harness)                  | n/a (local)
list_generated_images          | GET /files                                                     | SI
delegate_to_specialist         | LOCAL                                                          | n/a (local)
list_job_providers             | GET /career/job-discoveries/providers                          | SI
run_job_discovery              | POST /career/job-discoveries/run                               | SI
import_job_url                 | POST /career/job-discoveries/import-url                        | SI
save_job_listings              | POST /career/job-discoveries/save                              | SI
web_search                     | LOCAL (Brave)                                                  | n/a (local)
web_fetch                      | LOCAL                                                          | n/a (local)
get_github_status              | LOCAL (GitHub)                                                 | n/a (local)
list_github_repos              | LOCAL (GitHub)                                                 | n/a (local)
get_github_repo                | LOCAL (GitHub)                                                 | n/a (local)
list_github_contents           | LOCAL (GitHub)                                                 | n/a (local)
get_github_file                | LOCAL (GitHub)                                                 | n/a (local)
search_github_code             | LOCAL (GitHub)                                                 | n/a (local)
agent_catalog_settings         | LOCAL (catalogo/prompts/delegacion)                            | n/a (local)
agent_catalog_settings         | GET /career/operational-methodologies                          | SI
agent_catalog_settings         | PUT /career/operational-methodologies/{id}                     | SI
admin_section_settings         | GET /admin/sections                                            | SI
admin_section_settings         | GET /admin/sections/{id}                                       | SI
admin_section_settings         | PUT /admin/sections/{id}                                       | SI
bedrock_global_settings        | LOCAL (bedrock_settings)                                       | n/a (local)
error_report_settings          | GET /settings/error-reports                                    | SI
error_report_settings          | GET /settings/error-reports/summary                            | SI
error_report_settings          | GET /settings/error-reports/{id}                               | SI
error_report_settings          | PATCH /settings/error-reports/{id}                             | SI
FUERA DE LISTA: [('describe_resource_schema', 'GET /openapi.json')]
```
Veredicto: **no PARAR**. Ninguna tool exige una ruta de la API fuera de la lista. Única fila `NO`:
`GET /openapi.json` (`describe_resource_schema`): es una ruta integrada de FastAPI sin
`Depends(get_current_user)` (`FastAPI(...)` en `app.py` no fija `openapi_url` ni `dependencies`), por lo
que es pública y la lista de la cuenta de servicio (que se aplica en `get_current_user`) no la afecta.
Observaciones (dentro de prefijos ya permitidos; no se amplía la lista ni se enmienda la spec):
- `store_uploaded_image` necesita metadatos de un archivo por id (`mime_type`, `original_filename`) y
  hoy **no existe `GET /files/{id}`** (sólo `""`, `/count`, `/categories`, `/{id}/download`, `/{id}/raw`,
  PATCH visibilidad, DELETE; `GET /files` no filtra por id). Hueco aditivo bajo `/files`; resolver en los
  bloques C/I (derivar el mime del `Content-Type` de `/raw`, o añadir `GET /files/{id}`).
- Los `resource_key` genéricos del CRUD incluyen `pdf-output-templates`, `pdf-template-styles` y
  `agent-tasks` (`RESOURCE_REGISTRY`), que no cuelgan de `/career/*`: el cliente del harness debe
  enrutarlos a `/pdf-templates`, `/pdf-template-styles` (en lista) y a la BD propia (`agent-tasks`, LOCAL).
- `/audit-log` queda cubierta sólo si `SERVICE_ALLOWED_PREFIXES` lo enumera literalmente; el contrato
  dice "rutas de auditoría" sin el literal. Fijarlo al implementar T-136.
- `generate_pdf`/`render_record_pdf`: cubiertas vía `POST /pdf-templates/{id}/render` + `POST /files`
  (cover-letter no tiene ruta `/pdf` propia; se renderiza con la plantilla).

**T-003 (2026-10-13, solo lectura):** `access_role`:
- Modelo: `cjhirashi-career-api/src/models/user.py:44`
  `Column(String(32), default="user", nullable=False, index=True)`; sin `CheckConstraint`.
- Migración: `alembic/versions/f8a9b0c1d2e3_user_access_roles.py` -> `String(length=32)`,
  `server_default="user"`, índice `ix_users_access_role`; sin CHECK. El valor `service` no requiere migración.
- Schemas: `schemas/user.py` **no** contiene `access_role` (ni `UserCreate/Update/Response`); no se
  expone ni se valida por API.
- Único validador de valores: `src/middleware/auth.py:86` `if user.access_role == "agent":` (limita a
  `/career/*` y `POST /bedrock/chat`; resuelve al dueño con `owner_id` o `PUBLIC_PORTAL_USER_ID`).
  Cualquier otro valor se trata como usuario normal.
- Emisión de tokens: `services/auth_service.py::_create_token` (l.71) sólo añade `exp` (+ `type` en
  refresh); `routes/auth_enhanced.py` l.133 y l.138 (login) y l.194 (refresh) pasan `data={"sub": ...}`
  sin rol. `decode_token` l.174. No hay código que emita tokens `agent` (fuera de banda).
- Admin/portfolio: sin ninguna referencia a `access_role` en `cjhirashi-career-admin/src` ni
  `cjhirashi-career-portfolio/src`; el frontend no valida roles de acceso.
- Tests existentes (`tests/unit/test_auth.py`, `test_middleware*.py`): sin referencias a `access_role`.

Archivos a ampliar con `service` / claim `role`:
1. `cjhirashi-career-api/src/middleware/auth.py` (rama `service` con `SERVICE_ALLOWED_PREFIXES`; quitar
   `POST /bedrock/chat` del `agent`; `role` desconocido -> 401)
2. `cjhirashi-career-api/src/services/auth_service.py` (`_create_token`/`create_*_token` añaden `role`)
3. `cjhirashi-career-api/src/routes/auth_enhanced.py` (l.133, 138, 194: rol derivado de `access_role`)
4. `cjhirashi-career-api/src/models/user.py` (sólo el comentario l.41-43: documentar `service`; sin cambio de columna)
5. `cjhirashi-career-api/src/routes/notifications.py` (`POST /notifications` sólo `service`, RF-020)
6. `cjhirashi-career-ai/src/middleware/auth.py` (nuevo; lee el claim)
7. Tests: nuevos `test_jwt_role_claim`, `test_agent_service_scope`; ampliar `tests/unit/test_middleware*.py`
8. Docs: `docs/ENVIRONMENT-SECURITY.md` (procedimiento fuera de banda). Sin migración ni cambios en schemas ni Admin.
