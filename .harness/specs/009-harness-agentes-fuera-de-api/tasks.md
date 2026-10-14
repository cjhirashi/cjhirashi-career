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

- [x] **T-001** `[code]` (cubre RF-017) — Retirar `cjhirashi-career-ai` del `.gitignore`;
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
- [x] **T-004** `[code]` (cubre RF-007, RF-022, P3) — **[REQUIERE OK DEL USUARIO]**
  Obtener conteos reales de referencia (solo lectura): `SELECT count(*)` de las 10 tablas
  `bedrock_*` en `career_db` y número de puntos de memoria en Qdrant (scroll con conteo, sin
  escribir). Pegar los conteos en la evidencia; sirven de comparación para T-0xx de copia.
- [x] **T-005** `[code]` (cubre RNF-002) — **[REQUIERE OK DEL USUARIO]** Backup de
  `career_db` (`pg_dump`) y snapshot de Qdrant antes de la etapa 1; guardar rutas y tamaños
  en la evidencia.

## Bloque A — AI: esqueleto, configuración y BD propia

- [x] **T-010** `[test]` (cubre RF-006) — `tests/unit/test_config.py`: `Settings` exige
  `AI_DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `API_BASE_URL`, `AI_SERVICE_TOKEN`,
  `MEMORY_FTS_CONFIG` (por defecto `spanish`, D-24); sin variable obligatoria → error claro.
  Rojo.
- [x] **T-011** `[code]` (cubre RF-006) — `src/config.py`, `.env.example`. Verde T-010.
- [x] **T-012** `[test]` (cubre RF-008, RF-002) — `tests/unit/test_app_boot.py`: la app
  carga **todos** los routers (hazard del `ImportError` silenciado); `GET /health` 200 sin
  auth; ruta inexistente 404; falla si un router no se registra. Rojo.
- [x] **T-013** `[code]` (cubre RF-008) — `src/app.py`, `src/routes/health.py`,
  `src/database.py` (engine/async session). Verde T-012.
- [x] **T-014** `[test]` (cubre RF-006) — `tests/unit/models/test_schema_matches_contract.py`:
  los metadatos SQLAlchemy contienen las 11 tablas + `bedrock_agent_memory` (12) con las columnas
  de `contracts/harness-db-schema.md` §1, sin FK a `users`. Rojo.
- [x] **T-015** `[code]` (cubre RF-006) — `src/models/*` (11 modelos copiados de la API sin
  `ForeignKey("users.id")`). Verde parcial T-014 (sin memoria).
- [x] **T-016** `[test]` (cubre RF-006) — `tests/unit/services/test_id_generator.py`: IDs
  `bco/bcm/bct/btk/bam-N` con `nextval` en BD de test; sin colisión tras `setval`. Rojo.
- [x] **T-017** `[code]` (cubre RF-006) — `src/services/id_generator.py` (5 prefijos).
  Verde T-016.
- [x] **T-018** `[test]` (cubre RF-006, RF-022) — `tests/unit/migrations/test_initial_migration.py`:
  `alembic upgrade head` en BD de test crea las 12 tablas (11 migradas + `bedrock_agent_memory`), las secuencias, la columna
  generada `search_vector` y el índice GIN; `downgrade base` las elimina. Rojo.
- [x] **T-019** `[code]` (cubre RF-006, RF-022) — `alembic.ini`, `alembic/env.py` (async),
  `alembic/versions/0001_initial_harness_schema.py`. Verde T-018 y T-014 completo.

## Bloque B — AI: interfaz de proveedor y Bedrock

- [x] **T-020** `[test]` (cubre RF-005) — `tests/unit/providers/test_provider_contract.py`:
  un `FakeProvider` cumple el `Protocol ModelProvider` (`converse`, `converse_stream`,
  `generate_image`, `list_models`, `estimate_cost`); tipos neutros `ModelRequest`,
  `ToolSpec`, `ToolCall`, `Usage`. Rojo.
- [x] **T-021** `[code]` (cubre RF-005) — `src/providers/base.py`. Verde T-020.
- [x] **T-022** `[test]` (cubre RF-005) — `tests/unit/test_provider_boundary.py` (AST):
  fuera de `providers/bedrock/` nada importa `boto3`/`botocore`; `services/`/`routes/` no
  importan `providers.bedrock` (sólo la fábrica de `config`). Rojo si aún hay imports.
- [x] **T-023** `[test]` (cubre RF-005) — `tests/unit/providers/test_bedrock_converse.py`:
  con cliente boto3 simulado (stub, sin red): mapeo de petición/respuesta Converse,
  `cachePoint`, errores de throttling, cálculo de coste (tabla de precios). Rojo.
- [x] **T-024** `[code]` (cubre RF-005) — `src/providers/bedrock/{client,converse,pricing}.py`
  trasladando de `cjhirashi-career-api/src/services/bedrock/` (agent_loop sólo en su parte
  de proveedor). Verde T-023.
- [x] **T-025** `[test]` (cubre RF-005) — `tests/unit/providers/test_bedrock_images.py`:
  `generate_image` con stub (Stability vía Bedrock, ADR-025), validación de parámetros.
  Rojo.
- [x] **T-026** `[code]` (cubre RF-005) — `src/providers/bedrock/images.py` y fábrica
  `get_provider()` en `src/config.py`. Verde T-025 y T-022.

## Bloque C — AI: clientes REST hacia la API

- [x] **T-030** `[test]` (cubre RF-004, RF-003) — `tests/unit/clients/test_api_client.py`
  (`httpx.MockTransport`): bearer del `Principal`; `AI_SERVICE_TOKEN` con `ServiceContext`;
  sin contexto → `MissingCredentialError`; 401/403/404/409/422 → `ApiError`; reintento sólo
  en idempotentes 5xx/timeout (máx. 2). Rojo.
- [x] **T-031** `[code]` (cubre RF-004) — `src/middleware/principal.py`,
  `src/clients/api_client.py`. Verde T-030.
- [x] **T-032** `[test]` (cubre RF-003) — `tests/unit/clients/test_career.py`: list con
  paginación y tope, get/create/update/delete, `count`, `distinct`, `bulk_update` = N× PUT.
  Rojo.
- [x] **T-033** `[code]` (cubre RF-003) — `src/clients/career.py`. Verde T-032.
- [x] **T-034** `[test]` (cubre RF-003, RF-004) — `tests/unit/clients/test_files_sections.py`:
  `files` (POST multipart, GET raw, PATCH visibilidad), `sections` (`GET/PUT /admin/sections`),
  metodologías (`/career/operational-methodologies`). Rojo.
- [x] **T-035** `[code]` (cubre RF-003) — `src/clients/{files,sections}.py`. Verde T-034.
- [x] **T-036** `[test]` (cubre RF-003) — `tests/unit/clients/test_linkedin_pdf_jobs_errors.py`:
  `linkedin`, `pdf` (`/pdf-templates`, `/pdf-template-styles`), `job_discovery`, `errors`
  (`POST /system/error-report` sin auth). Rojo.
- [x] **T-037** `[code]` (cubre RF-003) — `src/clients/{linkedin,pdf,job_discovery,errors}.py`.
  Verde T-036.
- [x] **T-038** `[test]` (cubre RF-020, RF-021) — `tests/unit/clients/test_notifications_audit.py`:
  `POST /notifications` con token de servicio; `GET /audit-log`, `POST /audit-log/{id}/restore`
  con el JWT del usuario. Rojo.
- [x] **T-039** `[code]` (cubre RF-020, RF-021) — `src/clients/{notifications,audit}.py`.
  Verde T-038.
- [x] **T-040** `[test]` (cubre RF-003) — `tests/unit/test_isolation.py`: regex sobre
  `src/` sin referencias a `career_db`, `qdrant`, `SOURCE_`, `psycopg` hacia otra BD. Rojo
  si queda alguna. (Se ejecuta de nuevo al final de cada bloque.)

## Bloque D — AI: autenticación

- [x] **T-050** `[test]` (cubre RF-002, RF-019) — `tests/unit/middleware/test_auth.py`
  (matriz `contracts/auth-jwt-service-account.md` §5, fila ai/middleware): sin header,
  firma inválida, expirado, refresh, `role` desconocido → 401; `role` agent/service → 403;
  sin claim = user; token válido → `Principal`; ninguna llamada a la API. Rojo.
- [x] **T-051** `[code]` (cubre RF-002, RF-019) — `src/middleware/auth.py`. Verde T-050.
- [x] **T-052** `[test]` (cubre RF-019, D-27) — `tests/unit/middleware/test_auth.py`: sin
  `exp` → 401; `type` `refresh`, `linkedin_oauth_state` u otro → 401; `type` ausente o
  `access` → `Principal`. Rojo.
- [x] **T-053** `[code]` (cubre RF-019, D-27) — `src/middleware/auth.py` (`require` de
  `exp`/`sub`; lista blanca de `type`). Verde T-052.

## Bloque E — AI: repositorios y servicios (catálogo, ajustes, uso)

- [x] **T-060** `[test]` (cubre RF-006) — `tests/unit/repositories/test_conversation_repo.py`
  con `db_session`: CRUD de `bedrock_conversations` y mensajes (cascade), listado por
  `user_id`, renombrar. Rojo.
- [x] **T-061** `[code]` (cubre RF-006) — `src/repositories/conversation_repo.py`. Verde T-060.
- [x] **T-062** `[test]` (cubre RF-006) — `test_settings_profile_repo.py`: `bedrock_settings`
  (modelo, presupuesto, reglas), prompts, fotos, tools por perfil, delegación, tools
  personalizadas. Rojo.
- [x] **T-063** `[code]` (cubre RF-006) — `src/repositories/{settings_repo,profile_repo,custom_tool_repo}.py`.
  Verde T-062.
- [x] **T-064** `[test]` (cubre RF-006) — `test_usage_repo.py`: `usage_logs` y
  `usage_round_logs`, agregados de métricas y presupuesto diario. Rojo.
- [x] **T-065** `[code]` (cubre RF-006) — `src/repositories/usage_repo.py`,
  `src/services/usage_service.py`. Verde T-064. Nota: el panel de costes necesita
  `cache_read_savings_usd` (solo en `pricing.py`, ver nota de T-085).
- [x] **T-066** `[test]` (cubre RF-006) — `test_task_repo.py`: `bedrock_tasks` con
  `parent_id`, subtareas, filtros `filters`/orden/`count`/`distinct`. Rojo.
- [x] **T-067** `[code]` (cubre RF-006) — `src/repositories/task_repo.py`. Verde T-066.
- [x] **T-068** `[test]` (cubre RF-012, RF-001) — `tests/contract/test_agent_registry_contract.py`:
  `src/services/agent_registry.py` coincide con `contracts/agent-registry.json` (20 perfiles,
  id/label/nivel). Rojo.
- [x] **T-069** `[code]` (cubre RF-012) — `src/services/agent_registry.py` (+ perfiles
  trasladados de `agent_profiles.py`). Verde T-068.
- [x] **T-070** `[test]` (cubre RF-001, RF-003) — `tests/unit/services/test_profile_catalog.py`:
  catálogo de perfiles cruza metodologías y secciones leídas por REST (cliente simulado);
  regla `applies_to_caller`; tools por sección derivadas de `/admin/sections`. Rojo.
- [x] **T-071** `[code]` (cubre RF-001, RF-003) — `src/config.py` (añadir `BEDROCK_DEFAULT_MODEL_ID`,
  `BEDROCK_ORCHESTRATOR_MODEL_ID`, `BEDROCK_MAX_OUTPUT_TOKENS`, `BEDROCK_MAX_ROUND_TRIPS`,
  `BEDROCK_DAILY_BUDGET_USD`, `BEDROCK_HISTORY_WINDOW`, con los mismos defaults que la API:
  `agent_loop.py:310-321` y `settings_loader.py`; con su test en `tests/unit/test_config.py`
  antes del código), `src/services/{profile_catalog,tools_registry,prompt}.py`.
  Verde T-070.

## Bloque F — AI: memoria (FTS) y bucle de agente

- [x] **T-078** `[test]` (cubre RF-022, D-29) — `tests/unit/test_config.py`: el valor por
  defecto de `MEMORY_FTS_CONFIG` pasa a `spanish_unaccent`. `tests/unit/migrations/test_initial_migration.py`
  (Postgres real): tras `upgrade` existen la extensión `unaccent` y la configuración
  `spanish_unaccent`; `to_tsvector('spanish_unaccent','tecnología') @@
  websearch_to_tsquery('spanish_unaccent','tecnologias')` es verdadero; `downgrade` borra la
  configuración (la extensión puede quedar). Rojo.
- [x] **T-079** `[code]` (cubre RF-022, D-29) — `src/config.py` (defecto), `.env.example`,
  `alembic/versions/0001_initial_harness_schema.py` (extensión + configuración antes de la
  tabla; `downgrade` en orden inverso), docstring de `src/models/bedrock_agent_memory.py`,
  README del ai si menciona `spanish`. Verde T-078 y la suite.

- [x] **T-080** `[test]` (cubre RF-022) — `tests/unit/repositories/test_memory_repo.py` con
  BD de test: insertar nota/hecho/manual, listar por usuario/perfil, borrar, búsqueda
  `websearch_to_tsquery(MEMORY_FTS_CONFIG)` con `ts_rank` (acentos, plurales en español),
  aislamiento por `user_id`, unicidad `user_id+source_ref`. Rojo. **Depende de T-079** (D-29:
  la búsqueda sin tilde encuentra con tilde; revisor rechazó la 1.ª entrega por ese assert,
  inalcanzable con `spanish` a secas).
- [x] **T-081** `[code]` (cubre RF-022) — `src/repositories/memory_repo.py` (el modelo
  `src/models/bedrock_agent_memory.py` ya existe desde T-015; la migración 0001 ya incluye la
  tabla, T-018/T-019). Verde T-080.
- [x] **T-082** `[test]` (cubre RF-022, RF-001) — `test_memory_service.py`: sustituye
  `local_memory` (notas del agente, `memory/events` desde mensajes, `memory/records` por FTS,
  `memory/manual`); sin imports de Qdrant. Rojo. **Ampliación D-30** (reentrega): reenviar
  la misma nota/memoria manual no duplica y devuelve la existente (clave `source_ref`
  determinista, función compartida con T-122).
  Delta T-083 (revisor): test de delete_agent_note limitado a kind note.
- [x] **T-083** `[code]` (cubre RF-022, D-30) — `src/services/memory_service.py`. Verde T-082.
  Llamar a `memory_repo.add_memory(...)` por módulo (no `from ... import add_memory`): el test
  de carrera determinista de T-082 lo parchea así. Ante `IntegrityError` de
  `uq_bedrock_agent_memory_user_source_ref`: rollback y devolver la fila existente.
- [ ] **T-084** `[test]` (cubre RF-005, RF-004) — `tests/unit/services/test_agent_loop.py`
  con `FakeProvider`: turno sin tools, con tool, límite `max_round_trips`, ventana de
  historial, presupuesto diario superado, coste registrado, el JWT del usuario llega al
  cliente; dos `toolUse` en un mismo mensaje en streaming no se mezclan (D-26); fallback de
  `converse_stream` ante `AccessDeniedException` (si se decide, ver T-085). Los tests que usan
  el provider Bedrock limpian el dict de módulo de clientes boto3 cacheados. Rojo.
- [ ] **T-085** `[code]` (cubre RF-005) — `src/services/agent_loop.py` (trasladado,
  inyección del provider). Verde T-084. **Notas (bloque B):**
  - `agent_loop` debe adaptarse a `ModelResponse.tool_calls` y a `Usage` en snake_case (hoy
    usa `tool_uses` e `inputTokens`).
  - `ModelProvider.converse_stream` no tiene el fallback a Converse ante
    `AccessDeniedException` que sí tiene `converse()`: decidir y probar (en T-084) si
    `agent_loop` lo necesita.
  - `cache_read_savings_usd` vive solo en `providers/bedrock/pricing.py`, no en el Protocol;
    el panel de costes (`usage_service`, T-065) la necesita: decidir si se añade al Protocol
    o se expone por otra vía.
  - Streaming multi-`toolUse`: D-26 (corrección de `contentBlockIndex`); T-084 incluye un caso
    con dos `toolUse` en un mensaje en streaming.
- [ ] **T-086** `[test]` (cubre RF-003) — `test_tools_career_and_local.py`: tools
  de CRUD de carrera vía cliente simulado; `web_search`, `web_fetch`, GitHub (LOCAL) con
  `httpx.MockTransport`; `search_knowledge_base` **no existe** en el catálogo; `bulk_update`
  secuencial. Rojo. Además (D-28, revisión del bloque E): `list/get_career_record` sobre
  `operational-methodologies` aplica `applies_to_caller` (asignadas al perfil o compartidas;
  el guardián ve todas), como prometen el prompt (`prompt.py:162-164`) y la API
  (`bedrock_service.py:332-352`). Para `agent_pdf_design`, `agent_visual_design`,
  `agent_configuration` y `agent_settings` (que ganaron `list/get_career_record` sólo por
  D-28) el ejecutor admite **únicamente** `resource_key = operational-methodologies`; test
  de denegación explícito para cualquier otro recurso en esos cuatro perfiles. El llamador del prompt base pasa el registro real de recursos
  (`_known_resource_keys`), con test de paridad contra la lista de recursos de la API.
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
  `error`, no 500. `consume_converse_stream` es síncrono y bloquea el event loop (igual que
  en el origen): el test debe fijar cómo se ejecuta (p. ej. `asyncio.to_thread`) para que el
  ping cada 15 s no se retrase. Rojo.
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
  (BD de test origen/destino): copia las 11 tablas conservando ids; idempotente; `setval`
  (insertar tras copiar no colisiona); reporte JSON por tabla (`source`, `dest`,
  `missing_in_dest`, `checksum_ok`); exit ≠ 0 y `ok:false` si un conteo difiere; `--dry-run`;
  `--verify-only` tolera destino mayor; `--direction ai-to-api`. **Verificación de esquema
  previa:** antes de copiar, el script compara las columnas reales de `career_db` (vía
  `information_schema.columns`: tipo, longitud, nulabilidad) con el esquema de `career_ai_db`
  y falla con exit ≠ 0 y un mensaje claro (tabla, columna, tipo/longitud origen vs destino) si
  hay diferencias de tipo o longitud, sin copiar nada. Motivo: los modelos del harness copian
  los defaults de la API solo en Python (`default=`), sin `server_default`, y la BD dev de la
  API tiene `ALTER` directos (Art. 4). Casos: esquemas iguales pasan; `VARCHAR(50)` vs
  `VARCHAR(100)` y `TEXT` vs `VARCHAR` fallan. Rojo.
- [ ] **T-121** `[code]` (cubre RF-007, RF-017) — `scripts/copy_from_career_db.py` (incluye la verificación de esquema). Verde T-120.
- [ ] **T-122** `[test]` (cubre RF-022, RF-007) — `tests/unit/scripts/test_migrate_memory_from_qdrant.py`
  (cliente Qdrant simulado, jamás real): scroll de puntos de memoria, descarta puntos de
  registros indexados, idempotente (`source_ref`; notas y manuales con la clave de D-30 vía la
  función compartida de `memory_service`), `kind` correcto, reporte con
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
- [ ] **T-142** `[test]` (cubre RF-019, D-27) — `tests/unit/test_jwt_hardening.py` (API):
  `create_access_token` emite `"type": "access"`; `decode_access_token` y
  `get_current_user` rechazan (401) un token sin `exp` y el `state` de LinkedIn OAuth como
  bearer; aceptan `type` ausente; `decode_state_token` sigue funcionando. Rojo.
- [ ] **T-143** `[code]` (cubre RF-019, D-27) — `src/services/auth_service.py`
  (`_create_token`, `decode_token` con `require`, `decode_access_token` con lista blanca de
  `type`). Verde T-142 sin romper la suite de auth/LinkedIn existente.
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
  `upgrade` elimina las 11 tablas y secuencias (idempotente); `downgrade` recrea estructura
  (11 tablas, columnas de `harness-db-schema.md` §1). Rojo.
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
  head` de la API con `AI_COPY_REPORT` apuntando al reporte; verificar que las 11 tablas ya
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
| RF-001 | T-068, T-070, T-071, T-100, T-102..T-109, T-082, T-083 | test_ai_route_parity · test_routes_* · e2e · test_memory_service | |
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
| RF-019 | T-003, T-050, T-052, T-053, T-130, T-131, T-142, T-143 | test_jwt_role_claim · test_jwt_hardening · test_auth (ai) | |
| RF-020 | T-038, T-039, T-092, T-134, T-135 | test_notifications_route · test_task_scheduler | |
| RF-021 | T-038, T-039, T-088, T-107, T-136, T-137 | test_audit_log_routes · test_tools_files_pdf_linkedin_audit | |
| RF-022 | T-004, T-018, T-078, T-079, T-080..T-083, T-122, T-123, T-162 | test_memory_repo · test_memory_service · test_migrate_memory_from_qdrant | |
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

**T-004 (2026-10-13, solo lectura, autorizada por el usuario):**
Discrepancia: `\dt bedrock_*` da **11** tablas, no 10 (incluye `bedrock_conversation_messages`);
`harness-db-schema.md` §1 ya lista las 11. El arquitecto corregirá spec/plan/tasks.
```
$ docker exec postgres_db psql -U career_admin -d career_db -Atc "select count(*) from <tabla>"
bedrock_agent_delegation 1
bedrock_agent_profile_photos 12
bedrock_agent_profile_prompts 1
bedrock_agent_profile_tools 1
bedrock_conversation_messages 578
bedrock_conversations 42
bedrock_custom_tools 0
bedrock_settings 1
bedrock_tasks 4
bedrock_usage_logs 432
bedrock_usage_round_logs 824
```
Qdrant (contenedor `qdrant`, 172.20.0.5:6333 en net-cjhirashi-career, sin API key; la API usa
`QDRANT_URL=http://qdrant:6333`). `GET /collections` -> solo `career_knowledge`;
`POST /collections/career_knowledge/points/count {"exact":true}` -> `{"count":271}`.
Memoria del agente: se guarda en `career_knowledge` con `resource_key` = `manual_memory` o
`agent-notes` (`local_memory.py:99`, `:106`/`:138`). Scroll de los 271 puntos agrupado por `resource_key`:
```
$ curl -s -X POST http://172.20.0.5:6333/collections/career_knowledge/points/scroll -H 'Content-Type: application/json' -d '{"limit":300,"with_payload":["resource_key"],"with_vector":false}' | python3 (Counter)
puntos: 271 next_page_offset: None
competencies: 68
operational-methodologies: 22
target-companies: 15
networking-activities: 15
networking-contacts: 14
certifications: 13
market-segments: 12
projects: 11
contact-interactions: 10
role-narratives: 10
role-gap-analysis: 8
fit-scoring-factors: 7
cover-letter-versions: 7
publications: 7
achievements: 6
work-history: 6
career-reviews: 6
identity-reflections: 4
target-roles: 4
star-stories: 4
agent-tasks: 4
differentiators: 3
vacancies: 3
personal-profile: 2
identity: 2
portal-home: 1
applications: 1
linkedin-profile: 1
portal-about: 1
tags: 1
search-plans: 1
github-profile: 1
portal-contact: 1
$ POST /collections/career_knowledge/points/count {"exact":true,"filter":{"must":[{"key":"resource_key","match":{"value":"<k>"}}]}}
manual_memory: {"result":{"count":0},"status":"ok"}
agent_note: {"result":{"count":0},"status":"ok"}
agent-notes: {"result":{"count":0},"status":"ok"}
```
**Conclusión: la memoria a migrar en Qdrant hoy es 0 puntos.** Los 271 son registros de carrera
indexados (derivados del CRUD) y no se migran (contrato `harness-db-schema.md` §6).

**T-005 (2026-10-13, autorizada por el usuario):**
```
pg_dump -Fc: /mnt/disco2/cjhirashi-data/backups/career_db_pre_009_20261013_202038.dump  904162 bytes
pg_restore -l (dentro de postgres_db): Format CUSTOM, Dump Version 1.14-0, TOC Entries 707, 718 líneas
Snapshot Qdrant (POST /collections/career_knowledge/snapshots):
  career_knowledge-8617655084996019-2026-10-13-20-20-39.snapshot  20825600 bytes
  sha256 cf381d823e721929aa01e38f999d50864b352e84154c16d8979bbbc733092e43 (= checksum de la API; tar tf válido)
Copia (descargada por API): /mnt/disco2/cjhirashi-data/backups/qdrant_pre_009_20261013/career_knowledge-8617655084996019-2026-10-13-20-20-39.snapshot  20825600 bytes (sha256 idéntico)
```

**Bloque A + T-001 (2026-10-13, implementador).** Entorno: venv nuevo `cjhirashi-career-ai/venv` (era `.venv`; renombrado, ver corrección posterior)
(Python 3.14.4 del host; dependencias recientes sin pin, ver desviaciones). BD de test: contenedor
desechable `career-ai-testdb` (`postgres:15-alpine`, igual que `postgres_db`), red bridge por defecto,
`127.0.0.1:55433` (el 55432 ya lo usa `hira-server-postgres-1`), URL
`TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@127.0.0.1:55433/postgres`. Parado con
`docker stop` al terminar (`docker ps -a | grep -c career-ai-testdb` -> 0).

**T-001:** `.gitignore` NO contenía ninguna línea sobre `cjhirashi-career-ai`; `git check-ignore -v
cjhirashi-career-ai cjhirashi-career-ai/Dockerfile` -> sin salida, rc=1; `grep -n "career-ai" .gitignore`
-> rc=1. `git status --ignored` lo mostraba `!! cjhirashi-career-ai/` solo porque todo su contenido eran
cachés (`__pycache__/`, `.pytest_cache`) y `venv_test` (ver `.gitignore:9 __pycache__/`). Restos movidos
con `mv` (sin borrar) a `/mnt/disco2/cjhirashi-data/backups/career-ai-andamiaje-pre-009/`
(`.pytest_cache __pycache__ src tests venv_test`). Creados: `Dockerfile` (python:3.11-slim como la API,
puerto 8010), `pyproject.toml`, `pytest.ini` (mismas convenciones que la API: `--strict-markers`, cov
`--cov-fail-under=80`, marcador `requisito`, `asyncio_mode=auto`), `README.md`, `src/__init__.py`.
```
$ git status --short -uall | grep -v "^ M"   (tras T-001, antes del resto del bloque)
?? cjhirashi-career-ai/Dockerfile
?? cjhirashi-career-ai/README.md
?? cjhirashi-career-ai/pyproject.toml
?? cjhirashi-career-ai/pytest.ini
?? cjhirashi-career-ai/src/__init__.py
$ git status --short --ignored cjhirashi-career-ai   -> solo `!! cjhirashi-career-ai/venv/...` (ignorado por `.gitignore:31 venv/`; entonces era `.venv`); ningún caché ni venv aparece como nuevo
```

**T-010 (rojo)** `pytest tests/unit/test_config.py --no-cov -q`:
```
tests/unit/test_config.py:22: in _settings
    from config import Settings
E   ModuleNotFoundError: No module named 'config'
FAILED ...test_settings_loads_with_all_required_vars / test_memory_fts_config_defaults_to_spanish /
       test_memory_fts_config_is_overridable / test_missing_required_var_fails_naming_it[5 variables] /
       test_short_secret_key_is_rejected
============================== 9 failed in 0.10s ===============================
```
**T-011 (verde):** `src/config.py`, `.env.example`, `tests/conftest.py` (variables mínimas antes de importar el singleton).
```
tests/unit/test_config.py .........                                      [100%]
============================== 9 passed in 0.14s ===============================
```

**T-012 (rojo)** `pytest tests/unit/test_app_boot.py --no-cov -q`:
```
E   ModuleNotFoundError: No module named 'app'      (x4)
E   FileNotFoundError: [Errno 2] No such file or directory: '.../cjhirashi-career-ai/src/app.py'
E   ModuleNotFoundError: No module named 'routes'
========================= 5 failed, 1 warning in 0.44s =========================
```
**T-013 (verde):** `src/app.py`, `src/routes/{__init__,health}.py`, `src/database.py`. Un primer intento dio
`AttributeError: '_IncludedRouter' object has no attribute 'path'` (FastAPI 0.143 envuelve los routers
incluidos); se corrigió el helper del test para comparar por identidad de `original_router`. Verde:
```
tests/unit/test_app_boot.py + tests/unit/test_config.py:  14 passed, 1 warning
tests/unit/test_database.py (get_db commit/rollback, lifespan -> close_db; añadido para llevar database.py a >= 80 %):  3 passed
```

**T-014 (rojo)** `pytest tests/unit/models --no-cov -q`: `============================== 27 errors in 0.31s ===============================`
(`ModuleNotFoundError: models`).
**T-015 (verde)** `src/models/*` (10 modelos copiados con `sed`-equivalente sin `ForeignKey("users.id")` +
`bedrock_agent_memory`, ver desviaciones D2/D3):
```
tests/unit/models/test_schema_matches_contract.py ...................... [ 81%]
.....                                                                    [100%]
============================== 27 passed in 0.49s ==============================
grep -n "users\|ForeignKey(" src/models/*.py -> solo las 2 FK del contrato (bedrock_tasks.parent_id, bedrock_conversation_messages.conversation_id), ambas ON DELETE CASCADE
```

**T-016 (rojo)** `pytest tests/unit/services/test_id_generator.py --no-cov -q`, sin BD y con BD:
```
E   ModuleNotFoundError: No module named 'services'
sin TEST_DATABASE_URL: 1 failed, 4 skipped            con TEST_DATABASE_URL: 1 failed, 4 errors
```
(skip con motivo: `necesita Postgres real (secuencias, tsvector, GIN): exporta TEST_DATABASE_URL=...`)
**T-017 (verde)** `src/services/id_generator.py` + `register_id_listener(...)` en los 4 modelos con prefijo (bco/bcm/bct/btk/bam), contra el contenedor:
```
tests/unit/services/test_id_generator.py .....                           [100%]
============================== 5 passed in 1.91s ===============================
```
(incluye `test_no_collision_after_setval`: ids `btk-5`,`btk-9` + `setval('btk_id_seq',9)` -> siguiente `btk-10`.)

**T-018 (rojo)** `TEST_DATABASE_URL=... pytest tests/unit/migrations --no-cov -q`:
```
E   alembic.util.exc.CommandError: Path doesn't exist: .../cjhirashi-career-ai/alembic.  Please use the 'init' command...
============================== 6 errors in 0.55s ===============================
```
**T-019 (verde)** `alembic.ini`, `alembic/env.py` (async), `alembic/script.py.mako`,
`alembic/versions/0001_initial_harness_schema.py` (autogenerada contra el contenedor y revisada: añade
las 5 secuencias `bco/bcm/bct/btk/bam_id_seq` y su `DROP` en downgrade; `search_vector` generada con
`MEMORY_FTS_CONFIG`, validado `[a-z_]+`, por defecto `spanish`; índice GIN):
```
tests/unit/migrations/test_initial_migration.py ......                   [100%]
============================== 6 passed in 3.55s ===============================
```
(12 tablas + secuencias; columnas/nullable/FK de la migración == metadatos de los modelos; generada `ALWAYS`
con `to_tsvector` y `spanish`; GIN; FTS real `maratón` ~ `maratones`; unicidad `user_id+source_ref`;
`downgrade base` deja solo `alembic_version` y sin secuencias.)

**Suite completa del Bloque A**, sin BD (`pytest`): `42 passed, 10 skipped` (cifra de entonces; actual 50 passed, 12 skipped, ver última corrección) (los 10 con el motivo de arriba;
cobertura 90.30 % entonces). Con el contenedor (`TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@127.0.0.1:55433/postgres pytest`):
```
Name                                         Stmts   Miss  Cover   Missing
src/app.py                                      11      0   100%
src/config.py                                   14      0   100%
src/database.py                                 19      1    95%   47
src/models/__init__.py                          12      0   100%
src/models/bedrock_agent_delegation.py          11      1    91%   23
src/models/bedrock_agent_memory.py              21      1    95%   41
src/models/bedrock_agent_profile_photo.py       10      1    90%   25
src/models/bedrock_agent_profile_prompt.py      10      1    90%   33
src/models/bedrock_agent_profile_tool.py        11      1    91%   35
src/models/bedrock_conversation.py              31      2    94%   45, 60
src/models/bedrock_custom_tool.py               15      1    93%   27
src/models/bedrock_settings.py                  16      1    94%   37
src/models/bedrock_task.py                      35      1    97%   64
src/models/bedrock_usage_log.py                 17      1    94%   36
src/models/bedrock_usage_round_log.py           19      0   100%
src/routes/health.py                             5      0   100%
src/services/id_generator.py                    11      0   100%
TOTAL                                          268     12    96%
Required test coverage of 80% reached. Total coverage: 95.52%
======================== 55 passed, 1 warning in 5.09s =========================
```
`bash .harness/gate/check.sh; echo $?` -> `GATE_EXIT=0` (30 ok, 3 warn, 0 error). Nota: el bloque de
`cjhirashi-career-ai` del gate sale `SKIP` ("pytest no instalado en su venv") porque `check.sh:149` solo
busca `venv_test|venv|venv_run`, no `.venv`; no se tocó el gate. (Corregido abajo.)

**Corrección post-Bloque A (2026-10-13): versiones fijadas y verificación real en Python 3.11.**
- `pyproject.toml` fija las mismas versiones que `cjhirashi-career-api/requirements.txt`: fastapi 0.104.1,
  uvicorn[standard] 0.24.0, sqlalchemy 2.0.23, asyncpg 0.29.0, alembic 1.12.1, pydantic 2.5.0,
  pydantic-settings 2.1.0, python-dotenv 1.0.0, pyjwt 2.8.0, httpx 0.25.2; dev: pytest 7.4.3, pytest-cov 4.1.0,
  pytest-asyncio 0.21.1, psycopg2-binary 2.9.9. Todo lo del harness existe en la API, no hubo pins nuevos.
  Añadido `.dockerignore` (venv, cachés) para que `COPY . .` no meta el venv local en la imagen.
- El test `test_app_boot.py` asumía `_IncludedRouter` (FastAPI 0.143); con 0.104 las rutas van aplanadas.
  Helper ahora admite ambas formas (meta-test sigue detectando un router sin registrar).
- `docker build -t career-ai-test:local .` (python:3.11-slim, `pip install .` con los pins): OK. Suite dentro
  de un contenedor 3.11 desechable de esa imagen (root, `pip install ".[dev]"`), red desechable
  `career-ai-testnet` (sin redes de producción) con `career-ai-testdb` (postgres:15-alpine, `--rm`, publicado en
  127.0.0.1:55433), `TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@career-ai-testdb:5432/postgres`:
```
Python 3.11.15
alembic 1.12.1 / asyncpg 0.29.0 / fastapi 0.104.1 / httpx 0.25.2 / pydantic 2.5.0 / PyJWT 2.8.0 /
pytest 7.4.3 / pytest-asyncio 0.21.1 / SQLAlchemy 2.0.23
platform linux -- Python 3.11.15, pytest-7.4.3 ... plugins: asyncio-0.21.1, cov-4.1.0, anyio-3.7.1
src/app.py 100%  src/config.py 100%  src/database.py 95%  src/services/id_generator.py 100%
src/models/* 90-100%
TOTAL                                          268     12    96%
Required test coverage of 80% reached. Total coverage: 95.52%
============================== 55 passed in 7.88s ==============================
```
  Limpieza: `docker stop career-ai-testdb` (`--rm`), `docker network rm career-ai-testnet`, `docker rmi
  career-ai-test:local`; `docker ps -a | grep -c career-ai` -> 0, `docker images | grep -c career-ai-test` -> 0.
  No se usó `docker compose` ni se tocó ningún servicio.
- Venv local: `.venv` eliminado y recreado como `cjhirashi-career-ai/venv` (el gate lo detecta, `check.sh:149`);
  `git check-ignore -v venv/bin/python` -> `.gitignore:31:venv/`. Los pins NO instalan en Python 3.14 del host
  (falla "Getting requirements to build wheel"), así que el venv local lleva las mismas librerías sin pin
  (fastapi 0.143, pydantic 2.14, SQLAlchemy 2.1.4, pytest 9.1.1...): sirve para el gate y el desarrollo local;
  la verificación con las versiones de producción es la de 3.11 de arriba. Sin `TEST_DATABASE_URL`:
  `45 passed, 10 skipped` (los de Postgres se saltan con motivo).
- Gate tras el cambio (`bash .harness/gate/check.sh; echo $?` sin pipe -> `GATE_EXIT=0`):
```
5· Bloques por perfil de arquitectura
  ⏭️  cjhirashi-career-api · sin cambios — SKIP
  → cjhirashi-career-ai · pytest
  ✅ cjhirashi-career-ai · tests
  ⏭️  cjhirashi-career-admin · sin cambios — SKIP
Resumen: 31 ok · 3 warn · 0 error — ✅ Compuerta abierta.
```

**Correcciones del revisor al Bloque A (2026-10-13, test-first).** Postgres desechable
(`postgres:15-alpine --rm`, `127.0.0.1:55433`, red bridge por defecto), parado al terminar; el venv es
`cjhirashi-career-ai/venv` (cubierto por `.gitignore:31 venv/`).
1. `MEMORY_FTS_CONFIG`: la migración leía solo `os.environ` y el modelo `settings` (que también lee `.env`).
   Tests añadidos primero. Rojo (`pytest --no-cov -q`, con BD):
```
FAILED tests/unit/migrations/test_initial_migration.py::test_migration_uses_validated_settings_fts_config[english]
FAILED tests/unit/test_config.py::test_invalid_fts_config_is_rejected[spanish'); drop]   (+ Spanish, es-ES, "", "english simple")
=================== 6 failed, 56 passed, 1 warning in 7.27s ====================
```
   Código: `Settings` valida `MEMORY_FTS_CONFIG` con `field_validator` (`re.fullmatch(r"[a-z_]+")`); la migración
   0001 usa `settings.MEMORY_FTS_CONFIG` (sin `os`/`re`), igual que el modelo. Test
   `test_migration_search_vector_expression_equals_model` compara la `generation_expression` de la BD con
   `Computed.sqltext` del modelo; `...uses_validated_settings_fts_config[english]` fija `settings` a `english` y
   comprueba `'english'::regconfig` en la BD.
2. `test_migrated_columns_match_model_metadata` compara ahora tipo compilado (incluye longitud) y nulabilidad.
3. `test_get_db_rolls_back_and_reraises_on_error` usa una sesión falsa y afirma `calls == ["rollback", "close"]`.
   (Los puntos 2 y 3 ya pasaban con el código existente: eran huecos de aserción, no de código.)
Verde, con BD (`TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@127.0.0.1:55433/postgres pytest`):
```
src/config.py                                   21      0   100%
src/database.py                                 19      1    95%   47
TOTAL                                          275     12    96%
Required test coverage of 80% reached. Total coverage: 95.64%
======================== 62 passed, 1 warning in 6.63s =========================
```
Sin BD (`pytest`): 
```
TOTAL                                          275     16    94%
Required test coverage of 80% reached. Total coverage: 94.18%
================== 50 passed, 12 skipped, 1 warning in 0.65s ===================
```
(los 12 skips son los de Postgres, con motivo). Cifras anteriores (42 passed / 90.30 %, 45 passed) quedan
superadas. Nota: `pytest --cov` a secas mide también `tests/` (`--cov` sin fuente); usar siempre la
configuración de `pytest.ini` (`--cov=src`), que es la que mide la cobertura por módulo del Art. 3.
`bash .harness/gate/check.sh; echo $?` -> `GATE_EXIT=0` (`✅ cjhirashi-career-ai · tests`, 31 ok · 3 warn · 0 error).
No se repitió la suite en la imagen 3.11 tras este cambio (solo `field_validator`, disponible en pydantic 2.5).

### Bloque B (proveedor) — evidencia

**T-020 (rojo)** `pytest tests/unit/providers/test_provider_contract.py --no-cov -q`:
```
tests/unit/providers/test_provider_contract.py:7: in <module>
    from providers.base import (
E   ModuleNotFoundError: No module named 'providers'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.14s ===============================
```
**T-021 (verde)** `src/providers/{__init__,base}.py` (dataclasses neutras + `ProviderError` + `Protocol ModelProvider` `runtime_checkable`):
```
tests/unit/providers/test_provider_contract.py ......                    [100%]
============================== 6 passed in 0.03s ===============================
```
**T-022 (rojo)** `pytest tests/unit/test_provider_boundary.py --no-cov -q`. Hoy ningún archivo importa boto3, así que la
aserción "sin imports fuera" pasa sola; se añadió un guardia anti-verde-vacío (el SDK debe vivir de verdad en
`providers/bedrock/`), que es el que está en rojo hasta T-024:
```
tests/unit/test_provider_boundary.py .F...........                       [100%]
E   AssertionError: providers/bedrock/ no importa boto3: la frontera no tiene implementación
========================= 1 failed, 12 passed in 0.07s =========================
```
Meta-tests (12 de los 13): árboles sintéticos en `tmp_path` con `import boto3`, `from botocore...`, import dentro de función,
`__import__('boto3')`, `importlib.import_module('botocore.stub')`, boto3 en `providers/base.py`, y `services/`/`routes/`
importando `providers.bedrock` (incluida la forma `from providers import bedrock`) deben detectarse; y el caso permitido
(boto3 en `providers/bedrock/`, `providers.bedrock` en `config.py`) no debe marcarse. Además, prueba de fallo real: copia
desechable de `src/` con `services/leak.py` (`import boto3`):
```
E     Left contains one more item: 'services/leak.py: importa boto3 fuera de providers/bedrock/'
FAILED tests/unit/test_provider_boundary.py::test_src_respects_the_provider_boundary
```
(T-022 queda verde tras T-024; ver más abajo.)

**T-023 (rojo)** `pytest tests/unit/providers/test_bedrock_converse.py --no-cov -q`:
```
tests/unit/providers/test_bedrock_converse.py:15: in <module>
    from providers.bedrock.converse import BedrockProvider
E   ModuleNotFoundError: No module named 'providers.bedrock.converse'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.28s ===============================
```
**T-024 (verde)** `src/providers/bedrock/{__init__,client,converse,errors,pricing}.py`, `src/providers/reply_text.py`;
`boto3==1.43.76`/`botocore==1.43.76` en `pyproject.toml` (== `cjhirashi-career-api/requirements.txt`) e instalados en el venv.
Primer intento con 2 fallos que destaparon un defecto del origen: `consume_converse_stream` de la API lee
`event["contentBlockIndex"]` del nivel superior (siempre 0), pero en la API real el índice va DENTRO de
`contentBlockStart/Delta/Stop` (comprobado en el modelo de servicio de botocore:
`contentBlockStart ['start', 'contentBlockIndex']`, `contentBlockDelta ['delta', 'contentBlockIndex']`,
`contentBlockStop ['contentBlockIndex']`), con lo que dos `toolUse` en un mismo mensaje se mezclaban. El traslado lee
el índice interno con el nivel superior como respaldo (`_block_index`); con un solo bloque el comportamiento es idéntico.
```
tests/unit/providers/test_bedrock_converse.py .......................... [ 78%]
.......                                                                  [100%]
============================== 33 passed in 0.30s ==============================
tests/unit/test_provider_boundary.py + tests/unit/providers: 52 passed   (el guardia de T-022 ya está en verde)
```

**T-025 (rojo)** `pytest tests/unit/providers/test_bedrock_images.py --no-cov -q` (con `generate_image` aún como `NotImplementedError`):
```
      1 E   AttributeError: module 'config' has no attribute 'get_provider'
      1 E   AttributeError: 'Settings' object has no attribute 'BEDROCK_REGION'
     21 E   NotImplementedError: T-026
========================= 23 failed, 1 passed in 0.59s =========================
```
**T-026 (verde)** `src/providers/bedrock/images.py` (+ delegación en `BedrockProvider.generate_image`), campos `BEDROCK_*`/`AWS_*`
y `get_provider()` en `src/config.py`:
```
tests/unit/providers/test_bedrock_images.py ........................     [100%]
============================== 24 passed in 0.40s ==============================
```
**Cierre del Bloque B** — suite completa sin BD, `cjhirashi-career-ai/venv/bin/pytest` (config de `pytest.ini`):
```
src/config.py                                   34      0   100%
src/providers/base.py                           42      0   100%
src/providers/bedrock/client.py                 18      0   100%
src/providers/bedrock/converse.py              175      2    99%   226, 248
src/providers/bedrock/errors.py                 20      0   100%
src/providers/bedrock/images.py                 26      0   100%
src/providers/bedrock/pricing.py                19      0   100%
src/providers/reply_text.py                     13      0   100%
TOTAL                                          601     18    97%
Required test coverage of 80% reached. Total coverage: 97.00%
================== 126 passed, 12 skipped, 1 warning in 1.32s ==================
```
(los 12 skips son los de Postgres, con motivo.) `bash .harness/gate/check.sh > out; echo $?` -> `GATE_EXIT=0`
(`✅ cjhirashi-career-ai · tests`, 31 ok · 3 warn · 0 error; los 3 avisos son los anchors `null` de 005/006/009, previos).
Python 3.11 (cambió `pyproject.toml`): `docker build -t career-ai-test:local .` + `pip install ".[dev]"` en el contenedor:
```
Python 3.11.15
boto3               1.43.76
botocore            1.43.76
pytest              7.4.3
TOTAL                                          617     18    97%
======================= 126 passed, 12 skipped in 2.86s ========================
```
Imagen `career-ai-test:local` borrada (`docker rmi`). Ningún test sale a la red: clientes boto3 reales con credenciales falsas
bajo `Stubber` o dobles; no se tocó `cjhirashi-career-api`.
Desviaciones/notas del Bloque B: (1) `BedrockProvider` vive en `converse.py` (el test lo importa de ahí) y `generate_image`
delega en `images.py`; (2) `providers/reply_text.py` (copia de `reply_text.py`, sin SDK) para que servicios y proveedor la
compartan; (3) el catálogo de modelos/precios pasa de `config.BEDROCK_AVAILABLE_MODELS` a `providers/bedrock/pricing.py`;
(4) el origen no tiene validación de parámetros de imagen en el cliente (la hace la tool): se añadió `validate_params`
(prompt vacío, `aspect_ratio` fuera de los 9 valores del modelo) por T-025; (5) `report_error` no se traslada (el reporte
de errores del harness llega con `services/error_reporting`); (6) defecto del origen en el índice de bloque de ConverseStream
(ver T-024) corregido en el traslado; (7) `converse_stream` (eventos neutros) no existe en el origen: el bucle solo consumía
el stream completo; se implementó la superficie del plan sobre la misma lógica; (8) `messages` mantiene la forma de bloques
Converse (`text`/`toolUse`/`toolResult`) porque es lo que persiste `bedrock_conversation_messages`.

**Correcciones del revisor al Bloque B (test-first).**
(1) `converse.py::_wrap` perdía el traceback. Rojo (`test_wrapped_errors_keep_the_traceback_in_the_log`):
```
E   assert ([<LogRecord: providers.bedrock.converse, 40, ...converse.py, 264, "Converse failed model=%s stage=%s: %s">] and None)
FAILED tests/unit/providers/test_bedrock_converse.py::test_wrapped_errors_keep_the_traceback_in_the_log
========================= 1 failed, 51 passed in 0.45s =========================
```
Verde: `logger.error("Converse failed model=%s stage=%s", ..., exc_info=exc)`.
(2) Test de frontera: imports relativos resueltos a absoluto con la ruta del archivo (`from ..providers.bedrock import client`,
`from .bedrock import x`, `from . import bedrock`, `from ...providers.bedrock...` desde `routes/sub/`); casos permitidos
(`from . import y` en services, `from . import client` / `from ..base import Usage` dentro de `providers/bedrock/`).
`import_module` con nombre no literal queda sin cubrir, anotado en el docstring. Rojo (checker con la lógica anterior, que ignoraba
`level != 0`), mismos tests nuevos:
```
FAILED ...test_meta_services_importing_bedrock_provider_is_detected[services/x.py-from ..providers.bedrock import client\n]
FAILED ...[services/x.py-from .. import providers\nfrom ..providers import bedrock\n]
FAILED ...[routes/sub/x.py-from ...providers.bedrock.converse import BedrockProvider\n]
FAILED ...[providers/x.py-from .bedrock import converse\n]
FAILED ...[providers/x.py-from . import bedrock\n]
========================= 5 failed, 13 passed in 0.11s =========================
```
Verde con el checker corregido y suite completa (`venv/bin/pytest`): `TOTAL 601 18 97%` · `132 passed, 12 skipped, 1 warning`.
`bash .harness/gate/check.sh > out; echo $?` -> `GATE_EXIT=0` (31 ok · 3 warn · 0 error).

**Aislamiento de los tests respecto de `.env` y credenciales (corrección del coordinador).** Desde la raíz del repo,
`Settings` leía el `.env` de la raíz (credenciales reales de AWS; no se pegan aquí) y fallaba
`test_settings_expose_bedrock_defaults_equal_to_the_api`. Test primero, `tests/unit/test_env_isolation.py`, con un `.env`
sintético en `tmp_path` (`AWS_ACCESS_KEY_ID=FAKEFROMENV`, cwd allí, y también `_env_file=` explícito). Rojo:
```
E   AssertionError: assert '<fake>' == ''      (x2: lectura desde cwd y desde _env_file explícito)
========================= 2 failed, 3 passed in 0.24s ==========================
```
Arreglo general en `tests/conftest.py`, al importarse (antes de crear el singleton `settings`): `DotEnvSettingsSource._read_env_files`
neutralizado para toda la sesión (ningún `.env`, de ningún cwd ni argumento, se lee); se eliminan las variables `AWS_*`/`BEDROCK_*`
heredadas; las variables mínimas pasan de `setdefault` a asignación (un entorno real no se cuela); y fixture autouse
`_isolated_environment` que quita `AWS_*`/`BEDROCK_*` por test y vacía los clientes boto3 cacheados antes y después.
Los únicos tests que instancian `Settings` son `test_config.py` (ya usa `_env_file=None` y `delenv`) y el nuevo. Verde, con
`AWS_ACCESS_KEY_ID=FAKEINHERITED` exportada para probar el descarte, desde dos cwd:
```
raíz:  pytest -c cjhirashi-career-ai/pytest.ini cjhirashi-career-ai   -> 137 passed, 12 skipped, 1 warning
cjhirashi-career-ai/:  pytest                                         -> TOTAL 601 18 97% · 137 passed, 12 skipped, 1 warning
GATE_EXIT=0   (31 ok · 3 warn · 0 error)
```
`.coverage` de la raíz borrado. No se imprimió ningún valor de credencial real.

### Bloque C (clientes REST) — evidencia

**T-030/T-032 (rojo)** `pytest --no-cov tests/unit/clients` antes de crear `src/clients`:
```
tests/unit/clients/test_career.py:7: in <module>
    from clients.api_client import ApiError
E   ModuleNotFoundError: No module named 'clients'
ERROR tests/unit/clients/test_api_client.py
ERROR tests/unit/clients/test_career.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.23s ===============================
```
**T-031/T-033 (verde)** `src/middleware/{__init__,principal}.py`, `src/clients/{__init__,api_client,career}.py`; `Settings`
gana `API_TIMEOUT_SECONDS` (15.0) y `API_LIST_MAX_ITEMS` (500) (`API_BASE_URL`/`AI_SERVICE_TOKEN` ya existían desde T-011);
`.env.example` actualizado (sin valores reales); 2 tests nuevos en `test_config.py`:
```
tests/unit/clients/test_api_client.py .........................          [ 43%]
tests/unit/clients/test_career.py ...............                        [ 70%]
tests/unit/test_config.py .................                              [100%]
============================== 57 passed in 0.40s ==============================
```
**T-034 (rojo)** `ModuleNotFoundError: No module named 'clients.files'` · `1 error during collection`.
**T-035 (verde)** `src/clients/{files,sections}.py`: `tests/unit/clients/test_files_sections.py .......  7 passed`.
**T-036 (rojo)** `ERROR tests/unit/clients/test_linkedin_pdf_jobs_errors.py` · `1 error during collection`.
**T-037 (verde)** `src/clients/{linkedin,pdf,job_discovery,errors}.py`: `test_linkedin_pdf_jobs_errors.py ........  8 passed`.
**T-038 (rojo)** `ERROR tests/unit/clients/test_notifications_audit.py` · `1 error during collection`.
**T-039 (verde)** `src/clients/{notifications,audit}.py`: `test_notifications_audit.py .......  7 passed`.
**T-040 (rojo, con una violación temporal `import psycopg2` en `src/_violacion_temporal.py`, luego borrada)**:
```
E   assert ["_violacion_...: 'psycopg2'"] == []
FAILED tests/unit/test_isolation.py::test_src_has_no_reference_to_career_db_qdrant_or_foreign_db_drivers
========================= 1 failed, 1 passed in 0.21s ==========================
```
**T-040 (verde)** sin la violación: `tests/unit/test_isolation.py ..  2 passed`.

**Suite completa y cobertura** (desde `cjhirashi-career-ai/` con `pytest`, y desde la raíz con `-c cjhirashi-career-ai/pytest.ini`):
```
src/clients/api_client.py       94  0 100%     src/clients/audit.py          11 0 100%
src/clients/career.py           78  0 100%     src/clients/errors.py         14 0 100%
src/clients/files.py            21  0 100%     src/clients/job_discovery.py  14 0 100%
src/clients/linkedin.py         14  0 100%     src/clients/notifications.py   9 0 100%
src/clients/pdf.py              35  0 100%     src/clients/sections.py       22 0 100%
src/middleware/principal.py     30  0 100%     TOTAL 945 18 98%
AI (cwd=cjhirashi-career-ai):  204 passed, 12 skipped, 1 warning
raíz (-c ...pytest.ini):       204 passed, 12 skipped, 1 warning
GATE_EXIT=0   (30 ok · 4 warn · 0 error; el warn nuevo: superficie observable (.env.example) sin doc del mapa -> cubierto por T-233)
```
Notas: los 2 tests de `Settings` nuevos se escribieron junto al código (sin rojo previo separado). El paginado usa los
query params reales de la API (`skip`/`limit`), `audit-log` usa `limit`/`offset`. `.coverage` de la raíz borrado.

**Menores del revisor (bloque C), test-first** — `tests/unit/clients/test_hardening.py`.
Rojo (`pytest --no-cov tests/unit/clients/test_hardening.py`):
```
FAILED test_repr_never_contains_the_token
FAILED test_blank_principal_token_is_missing_credential[] / [   ] / [\t\n]
FAILED test_blank_service_token_is_missing_credential[] / [  ]
FAILED test_timeout_zero_is_not_replaced_by_default   (luego renombrado a test_explicit_timeout_zero_is_respected)
FAILED test_cookies_are_not_kept_between_requests
FAILED test_error_report_never_raises_on_unserializable_payload
============================== 9 failed in 0.34s ===============================
```
Verde: `token` con `field(repr=False)`; `_bearer()` rechaza token vacío/blanco con `MissingCredentialError` (modos context y service);
`timeout if timeout is not None`; `cookies.clear()` tras cada respuesta; `ErrorsClient.report` captura `Exception`.
```
test_hardening.py .........   ·   errors.py 100%  api_client.py 100%  principal.py 100%  TOTAL 957 18 98%
AI (cwd=cjhirashi-career-ai): 213 passed, 12 skipped · raíz (-c ...): 213 passed, 12 skipped · GATE_EXIT=0
```
Nota: el test del timeout se reescribió tras el rojo (la primera versión esperaba `ValueError`, no válido); el rojo real es el caso `timeout=0`.

### Bloque D (auth) — evidencia

**T-050 (rojo)** `venv/bin/pytest --no-cov -q tests/unit/middleware` antes de crear `src/middleware/auth.py`:
```
tests/unit/middleware/test_auth.py:16: in <module>
    from middleware.auth import require_principal
E   ModuleNotFoundError: No module named 'middleware.auth'
ERROR tests/unit/middleware/test_auth.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 1 error in 0.35s ==========================
```
**T-051 (verde)** `src/middleware/auth.py` (`authenticate_token`, dependencia `require_principal` que mantiene `principal_scope`):
```
collected 19 items
tests/unit/middleware/test_auth.py ...................                   [100%]
======================== 19 passed, 1 warning in 0.36s =========================
```
Suite completa desde `cjhirashi-career-ai/`:
```
tests/unit/middleware/test_auth.py ...................                   [ 36%]
src/middleware/auth.py                          40      0   100%
src/middleware/principal.py                     32      0   100%
TOTAL                                          997     18    98%
Required test coverage of 80% reached. Total coverage: 98.19%
================== 232 passed, 12 skipped, 1 warning in 1.59s ==================
```
Desde la raíz (`-c cjhirashi-career-ai/pytest.ini`): `232 passed, 12 skipped` (exit 1 por cobertura 0.00 %, conocido). `.harness/gate/check.sh` sin pipe: `GATE=0`
(`31 ok · 3 warn · 0 error`; los 3 avisos son anclas `null` de 005/006/009, previos).
Decisiones: formato de error = el de la API (`{"detail": str}` + `WWW-Authenticate: Bearer` en 401), porque el AI no define otro;
`sub` ausente/no-str y `type == "refresh"` -> 401; `role` no-str o desconocido -> 401. Ningún mensaje ni log contiene el token (test).
Red bloqueada en los tests (transportes reales de httpx y `socket.connect` fallan). `pyjwt==2.8.0` ya fijado en el `pyproject.toml` del AI (igual que la API);
el venv local tiene 2.15.1 (desviación de entorno, no de código).

**Menores del revisor (post-APPROVED)** — tests nuevos en `test_auth.py` (HS384/HS512 -> 401, `sub` entero -> 401, scope `None` si el handler
lanza, 20 requests concurrentes vía ASGI sin mezcla) y en `test_config.py` (allowlist de `ALGORITHM`). Rojo (`pytest --no-cov` antes de tocar `config.py`):
```
FAILED tests/unit/test_config.py::test_algorithm_outside_allowlist_is_rejected[none]
FAILED tests/unit/test_config.py::test_algorithm_outside_allowlist_is_rejected[None]
FAILED tests/unit/test_config.py::test_algorithm_outside_allowlist_is_rejected[RS256]
FAILED tests/unit/test_config.py::test_algorithm_outside_allowlist_is_rejected[ES256]
FAILED tests/unit/test_config.py::test_algorithm_outside_allowlist_is_rejected[hs256]
FAILED tests/unit/test_config.py::test_algorithm_outside_allowlist_is_rejected[]
=================== 6 failed, 44 passed, 3 warnings in 0.56s ===================
```
(los casos de `test_auth.py` ya pasaban: el middleware con `algorithms=[settings.ALGORITHM]` ya los cubría; ahora quedan fijados.)
Verde (`src/config.py`: `_ALLOWED_JWT_ALGORITHMS` + validador de `ALGORITHM`), suite desde `cjhirashi-career-ai/`:
```
src/config.py                                   43      0   100%
src/middleware/auth.py                          40      0   100%
Required test coverage of 80% reached. Total coverage: 98.21%
================= 246 passed, 12 skipped, 3 warnings in 1.64s =================
```
Raíz (`-c ...`): `246 passed, 12 skipped` · `GATE=0` (31 ok · 3 warn · 0 error). Sin cambios en tokens sin `exp` ni `type` desconocido (paridad con la API).

### T-052/T-053 (D-27) — evidencia

Rojo (T-052: 4 tests nuevos en `tests/unit/middleware/test_auth.py`, ejecutados contra el `auth.py` previo de `HEAD`):
```
$ pytest --no-cov -q tests/unit/middleware/test_auth.py      # con src/middleware/auth.py de HEAD
E   assert 200 == 401   (x7: token sin exp; type = linkedin_oauth_state / otro / "" / ACCESS / 7 / lista)
FAILED tests/unit/middleware/test_auth.py::test_sin_exp_401 - assert 200 == 401
FAILED tests/unit/middleware/test_auth.py::test_type_distinto_de_access_401[linkedin_oauth_state]
FAILED tests/unit/middleware/test_auth.py::test_type_distinto_de_access_401[otro]
FAILED tests/unit/middleware/test_auth.py::test_type_distinto_de_access_401[]
FAILED tests/unit/middleware/test_auth.py::test_type_distinto_de_access_401[ACCESS]
FAILED tests/unit/middleware/test_auth.py::test_type_distinto_de_access_401[7]
FAILED tests/unit/middleware/test_auth.py::test_type_distinto_de_access_401[token_type6]
=================== 7 failed, 27 passed, 3 warnings in 0.56s ===================
```
Verde (T-053: `options={"require": ["exp", "sub"]}` + `payload.get("type", "access") != "access"` -> 401):
```
$ pytest --no-cov -q tests/unit/middleware/test_auth.py
======================== 34 passed, 3 warnings in 0.46s ========================
```
`type` ausente o `access` sigue dando `Principal` (casos ya existentes en el mismo archivo).

### Bloque E — evidencia

Entorno: Postgres de pruebas con `docker run --rm -d` (contenedor `career-ai-test-pg-009e`, `127.0.0.1:55477`, sin red de producción ni volúmenes), pasado por `TEST_DATABASE_URL`. Todos los tests llevan `@pytest.mark.requisito`.

Rojo -> verde por pareja (salida real; el rojo es siempre antes de escribir el código):

T-060/T-061 `conversation_repo` (RF-006). Rojo:
```
============================== 10 failed in 4.14s ==============================
     10 E   ModuleNotFoundError: No module named 'repositories'
```
Verde: `$ pytest --no-cov -q tests/unit/repositories/test_conversation_repo.py` -> `11 passed in 4.85s` (10 de T-060 + `conversation_counts_by_profile`, T-070).

T-062/T-063 `settings_repo`, `profile_repo`, `custom_tool_repo` (RF-006). Rojo:
```
============================== 11 failed in 4.76s ==============================
      2 E   ImportError: cannot import name 'custom_tool_repo' from 'repositories'
      4 E   ImportError: cannot import name 'profile_repo' from 'repositories'
      5 E   ImportError: cannot import name 'settings_repo' from 'repositories'
```
Verde: `test_settings_profile_repo.py` -> `11 passed in 5.13s`.

T-064/T-065 `usage_repo` + `usage_service` (RF-006). Rojo:
```
============================== 12 failed in 4.49s ==============================
      8 E   ImportError: cannot import name 'usage_repo' from 'repositories'
      4 E   ImportError: cannot import name 'usage_service' from 'services'
```
Verde: `test_usage_repo.py` + `test_usage_service.py` -> `14 passed in 4.70s` (12 + 2 de la frontera del proveedor, ver "Desviaciones").

T-066/T-067 `task_repo` (RF-006). Rojo:
```
============================== 12 failed in 5.50s ==============================
     12 E   ImportError: cannot import name 'task_repo' from 'repositories'
```
Verde: `test_task_repo.py` -> `12 passed in 5.79s`.

T-068/T-069 `agent_registry` + `agent_profiles` (RF-012, RF-001). Rojo:
```
========================= 13 failed, 1 passed in 0.24s =========================
     11 E   ImportError: cannot import name 'agent_profiles' from 'services'
      2 E   ModuleNotFoundError: No module named 'services.agent_registry'
```
Verde: `$ pytest --no-cov -q tests/contract tests/unit/services/test_agent_profiles.py` -> `14 passed in 0.15s` (el registro coincide con `contracts/agent-registry.json`: 20 perfiles, id/label/nivel).

T-070/T-071 `config` + `settings_loader` + `tools_registry` + `prompt` + `profile_catalog` (RF-001, RF-003). Rojo (tests en `test_config.py`, `test_settings_loader.py`, `test_tools_registry.py`, `test_prompt.py`, `test_profile_catalog.py`, `test_conversation_repo.py`):
```
======================== 40 failed, 10 passed in 8.02s =========================
     12 E   ImportError: cannot import name 'tools_registry' from 'services'
     12 E   ImportError: cannot import name 'prompt' from 'services'
     11 E   ModuleNotFoundError: No module named 'services.profile_catalog'
      3 E   ImportError: cannot import name 'settings_loader' from 'services'
      1 E   ModuleNotFoundError: No module named 'services.settings_loader'
      1 E   AttributeError: module 'repositories.conversation_repo' has no attribute 'conversation_counts_by_profile'
```
y, en `test_config.py` (rojo previo al campo de `src/config.py`):
```
E   AttributeError: 'Settings' object has no attribute 'BEDROCK_DEFAULT_MODEL_ID'. Did you mean: 'BEDROCK_IMAGE_MODEL_ID'?
E   Failed: DID NOT RAISE ValidationError   (x3: BEDROCK_MAX_OUTPUT_TOKENS / BEDROCK_HISTORY_WINDOW / BEDROCK_MAX_ROUND_TRIPS = 0)
========================= 4 failed, 26 passed in 0.27s =========================
```
Verde: `$ pytest --no-cov -q tests/unit/services/test_prompt.py tests/unit/services/test_profile_catalog.py tests/unit/services/test_tools_registry.py tests/unit/services/test_settings_loader.py tests/unit/test_config.py` -> `69 passed in 3.66s`.

Defaults de `src/config.py` (T-071) frente a la API (`cjhirashi-career-api/src/config.py`):

| Campo | AI `src/config.py` | API `src/config.py` |
|---|---|---|
| `BEDROCK_DEFAULT_MODEL_ID` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` (l.65) | l.95 igual |
| `BEDROCK_ORCHESTRATOR_MODEL_ID` | igual (l.66) | l.96 igual |
| `BEDROCK_MAX_OUTPUT_TOKENS` | `8192` (l.67) | l.121 `8192` |
| `BEDROCK_HISTORY_WINDOW` | `20` (l.68) | l.125 `20` |
| `BEDROCK_MAX_ROUND_TRIPS` | `6` (l.69) | l.126 `6` |
| `BEDROCK_DAILY_BUDGET_USD` | `5.0` (l.70) | l.128 `5.0` |

Uso como respaldo cuando no hay fila: `cjhirashi-career-api/src/services/bedrock/settings_loader.py:35-41`, replicado en `src/services/settings_loader.py`. Nota: `agent_loop.py:310-321` (citado en T-071) es la lógica de resolución del modelo, no los defaults; los defaults están en `config.py`. Test: `test_agent_runtime_defaults_match_api`.

Suite completa (tras todo el bloque):
```
$ cd cjhirashi-career-ai && TEST_DATABASE_URL=... pytest -q
Required test coverage of 80% reached. Total coverage: 98.69%
======================= 373 passed, 3 warnings in 31.97s =======================
$ cd cjhirashi-career-ai && pytest -q            # sin TEST_DATABASE_URL
================= 309 passed, 64 skipped, 3 warnings in 2.21s ==================
FAIL Required test coverage of 80% not reached. Total coverage: 75.37%   # los tests de BD se saltan
$ pytest -q -c cjhirashi-career-ai/pytest.ini cjhirashi-career-ai/tests   # raíz, con BD
======================= 373 passed, 3 warnings in 31.30s =======================   (exit 1 por cobertura: "No data was collected", conocido)
$ pytest -q -c cjhirashi-career-ai/pytest.ini cjhirashi-career-ai/tests   # raíz, sin BD
================= 309 passed, 64 skipped, 3 warnings in 1.73s ==================   (exit 1 por cobertura, conocido)
```
Cobertura por módulo nuevo (run con BD, desde `cjhirashi-career-ai/`; todos >= 80 %):
```
src/config.py                                   49      0   100%
src/middleware/auth.py                          40      1    98%   67
src/repositories/conversation_repo.py           72      0   100%
src/repositories/custom_tool_repo.py            32      0   100%
src/repositories/profile_repo.py                76      1    99%   97
src/repositories/settings_repo.py               35      0   100%
src/repositories/task_repo.py                  149      3    98%   34, 41, 59
src/repositories/usage_repo.py                  31      0   100%
src/services/agent_profiles.py                 149      1    99%   907
src/services/agent_registry.py                   9      0   100%
src/services/profile_catalog.py                140      3    98%   149, 164-165
src/services/prompt.py                         105      0   100%
src/services/settings_loader.py                 11      0   100%
src/services/tools_registry.py                  46      0   100%
src/services/usage_service.py                   47      2    96%   42-44
TOTAL                                         1912     25    99%
```
Compuerta: `bash .harness/gate/check.sh` (sin pipe) -> exit 0 (`31 ok · 3 warn · 0 error`; los 3 avisos son el anclaje `null` de 005/006/009, conocidos). `.coverage` de la raíz borrado.

Desviaciones y puntos abiertos (para el revisor / orquestador):
1. **Frontera del proveedor (T-065, corregido en esta entrega).** `usage_service` importaba `providers.bedrock.pricing` y `tests/unit/test_provider_boundary.py` lo detectó. Raíz: el servicio ahora usa `config.get_provider()` (`_provider()`), y el ahorro de caché se deriva solo de `estimate_cost` (coste como entrada normal menos coste como lectura de caché), sin ampliar el `ModelProvider` (su superficie está fijada en 5 métodos por `test_provider_contract.py`). Resuelve la nota de T-065 sobre `cache_read_savings_usd`; el resultado coincide con `pricing.cache_read_savings_usd` (test de paridad).
2. **D-15 y metodologías.** Sin `search_knowledge_base`, los perfiles que la tenían y no tienen `get_career_record` (L2 `agent_configuration`/`agent_settings`; L3 visual y de redacción de documentos) pierden la lectura de metodologías. `profile_can_read_methodologies` devuelve False para ellos y el prompt lo dice. Pendiente de decisión (¿dotar de `get_career_record` a esos perfiles?).
3. **Recursos del prompt base.** En la API la lista `Recursos disponibles` sale de `RESOURCE_REGISTRY`; el harness no lo tiene, así que `default_system_prompt(resource_keys=None)` usa la unión de `resource_keys` de los perfiles (o la lista que pase quien llama; Bloque F puede pasar el registro real).
4. **Paridad del catálogo con la API.** `_methodology_entries` considera "compartida" por `agent_profile_ids` vacío aunque tenga `section_ids` (igual que la API); `list_assigned_methodologies` (prompt) sí usa `applies_to_caller`. Se conserva y se fija en test; es una inconsistencia heredada.
5. `compose_system_prompt` recibe `assigned` (metodologías vía `profile_catalog.list_assigned_methodologies`) y `notes` (memoria, Bloque F) por parámetro, sin acceso a datos de carrera. `tools_registry` solo tiene esquemas (los ejecutores son del Bloque F). Ninguna ruta REST fuera del inventario fue necesaria (`/admin/sections`, `/career/operational-methodologies`).

### Bloque E — ajustes de paridad (D-13) tras la revisión — evidencia

Pedidos por el coordinador tras el APPROVED del revisor; el acceso a metodologías (desviación 3) NO se toca. Postgres de pruebas: `docker run --rm -d --name career-ai-test-pg-009e -p 127.0.0.1:55477:5432 ... postgres:15-alpine` (misma mayor que `docker-compose.yml:189`), eliminado al terminar.

1. `task_repo._sync_subtasks` valida con `SubtaskInput` (nuevo `src/schemas/bedrock_task.py`, traslado del de la API) y aplica `model_dump()`: los campos omitidos vuelven a su default y una subtarea sin `title` da `ValidationError`, no `IntegrityError`.
2. `profile_repo.set_delegation_override` guarda `filter_level_allowed(...)` (movido a `services/agent_profiles.py`; `profile_catalog` lo importa) y lanza `KeyError` si el perfil no existe.

Rojo (tests nuevos en `test_task_repo.py` y `test_settings_profile_repo.py`, antes del código):
```
$ pytest --no-cov -q tests/unit/repositories/test_task_repo.py tests/unit/repositories/test_settings_profile_repo.py
E   AssertionError: assert ('uno-bis', '..., 'high', 'n') == ('uno-bis', '...medium', None)        # defaults no restablecidos
E   sqlalchemy.exc.IntegrityError: (sqlalchemy.dialects.postgresql.asyncpg.NotNullViolationError) null value in column "title" of relation "bedrock_tasks" violates not-null constraint
E   Failed: DID NOT RAISE ValidationError                                                           (x5: status, priority, assignee_type x2, agente desconocido)
E   sqlalchemy.exc.DBAPIError: ... invalid input for query argument $9: '2026-02-01T00:00:00Z' (expected a datetime.date ...)   # due_at < scheduled_at sin validar
E   AssertionError: assert ('agent_support', True) == (None, False)                                 # assignee_type=user sin normalizar
E   AssertionError: assert ['agent_suppo...nt_changelog'] == ['agent_suppo...nt_changelog']          # delegación sin filtrar
FAILED test_task_repo.py::test_subtarea_omitida_vuelve_a_sus_defaults_como_en_la_api
FAILED test_task_repo.py::test_subtarea_sin_titulo_es_error_de_validacion_no_integrity_error
FAILED test_task_repo.py::test_subtarea_invalida_se_rechaza_con_validacion[bad0..bad5]
FAILED test_task_repo.py::test_subtarea_de_usuario_normaliza_agente_y_ejecucion
FAILED test_settings_profile_repo.py::test_delegacion_guarda_filter_level_allowed_como_la_api
======================== 10 failed, 23 passed in 16.63s ========================
```
Verde:
```
$ pytest --no-cov -q tests/unit/repositories tests/unit/services
============================= 111 passed in 29.28s =============================
```
Suite completa tras los ajustes:
```
$ cd cjhirashi-career-ai && TEST_DATABASE_URL=... pytest -q
Required test coverage of 80% reached. Total coverage: 98.73%
======================= 383 passed, 3 warnings in 36.50s =======================
$ cd cjhirashi-career-ai && pytest -q            # sin BD
================= 309 passed, 74 skipped, 3 warnings in 2.14s ==================
FAIL Required test coverage of 80% not reached. Total coverage: 73.01%   # los tests de BD se saltan
$ pytest -q -c cjhirashi-career-ai/pytest.ini cjhirashi-career-ai/tests   # raíz con BD: 383 passed; sin BD: 309 passed, 74 skipped (exit 1 por cobertura, conocido)
```
Cobertura de lo tocado: `schemas/bedrock_task.py` 98 %, `repositories/task_repo.py` 98 %, `repositories/profile_repo.py` 99 %, `services/agent_profiles.py` 99 %, `services/profile_catalog.py` 98 %.
Compuerta: `bash .harness/gate/check.sh` (sin pipe) -> exit 0 (`31 ok · 3 warn · 0 error`, avisos conocidos de 005/006/009). `.coverage` de la raíz borrado. Contenedor `career-ai-test-pg-009e` detenido: `docker ps -a --filter name=career-ai-test-pg-009e` sin filas.

### D-28 — evidencia

Referencia de la API (solo lectura, no se importa): `cjhirashi-career-api/src/services/bedrock/agent_profiles.py:919-923` (`profile_can_search_knowledge`: con `allowed_tool_names` mira `search_knowledge_base`; sin él, `level == 2`). `search_knowledge_base` está en `_PDF_DESIGN_TOOL_NAMES` (l.123), `_VISUAL_TOOL_NAMES` (l.140), `_DOCUMENT_WRITING_TOOL_NAMES` (l.167), `_CONFIGURATION_TOOL_NAMES` (l.194), `_SETTINGS_TOOL_NAMES` (l.201); `_TASK_MANAGER_TOOL_NAMES` (l.145-154) no la tiene. Resultado: 12 de 20 perfiles leen (6 L2 sin conjunto propio + pdf_design, visual_design, cv_writing, cover_letter_writing, settings, configuration). La lista está copiada en `tests/unit/services/test_agent_profiles.py` (`_API_PUEDEN_BUSCAR_KB`) con la cita de líneas.

Causa raíz: sin `search_knowledge_base` ya no hay tool marcadora (`get_career_record` también la tiene `agent_task_manager`), así que el criterio "tiene get_career_record" no reproduce la API. Solución: `_METHODOLOGY_READER_IDS` explícito (cv/cover/settings/configuration/pdf_design/visual_design) + exigir `list_career_record` y `get_career_record` en su conjunto; L2 sin conjunto propio, por nivel (igual que la API). Se añadieron `list_career_record`/`get_career_record` a `_PDF_DESIGN_TOOL_NAMES`, `_VISUAL_TOOL_NAMES`, `_CONFIGURATION_TOOL_NAMES` y `_SETTINGS_TOOL_NAMES`; `agent_task_manager` queda igual (sin lectura de metodologías). El texto del prompt (`methodology_assignment_block`) ya instruía `list_career_record`/`get_career_record` sobre `operational-methodologies`; ahora llega a esos cuatro perfiles. No se tocó `applies_to_caller` ni su ejecutor (T-086, bloque F). Nota: hasta T-086 la restricción a `operational-methodologies` de esas tools en los cuatro perfiles nuevos la impondrá el ejecutor; antes de F no hay ejecutor, así que no hay exposición.

Rojo (antes de implementar), `pytest --no-cov -q tests/unit/services/test_agent_profiles.py tests/unit/services/test_prompt.py`:
```
FAILED test_agent_profiles.py::test_d28_lectura_de_metodologias_identica_a_la_api_en_los_20_perfiles
FAILED test_agent_profiles.py::test_d28_cuatro_perfiles_ganan_lectura_con_tools_de_carrera[agent_pdf_design|agent_settings|agent_configuration|agent_visual_design]
FAILED test_agent_profiles.py::test_d28_task_manager_no_gana_lectura_de_metodologias   (assert True is False)
FAILED test_prompt.py::test_bloque_instruye_leer_metodologias_por_rest_sin_search_knowledge_base
FAILED test_prompt.py::test_d28_perfiles_con_lectura_reciben_la_instruccion_rest_acotada
=================== 8 failed, 18 passed, 3 skipped in 0.36s ====================
```
(El test de prompt existente usaba `agent_configuration` como perfil sin lectura; ahora usa `agent_task_manager`.)

Verde:
```
$ pytest -q   (cjhirashi-career-ai/, con TEST_DATABASE_URL, postgres:15-alpine)
TOTAL 1976 25 99% · Required test coverage of 80% reached. Total coverage: 98.73%
391 passed, 3 warnings
$ pytest -q -c cjhirashi-career-ai/pytest.ini cjhirashi-career-ai   (raíz, con BD): 391 passed (exit 1 por cobertura, conocido)
$ pytest -q   (sin BD): 317 passed, 74 skipped · Total coverage: 73.03% (< 80 % porque los tests de BD se saltan)
$ pytest -q -c cjhirashi-career-ai/pytest.ini cjhirashi-career-ai   (raíz, sin BD): 317 passed, 74 skipped (exit 1 por cobertura, conocido)
```
Compuerta: `bash .harness/gate/check.sh` (sin pipe) -> exit 0 (`31 ok · 3 warn · 0 error`, avisos conocidos de 005/006/009). `.coverage` de la raíz borrado. Contenedor `career-ai-test-pg-009e` detenido y eliminado: `docker ps -a --filter name=career-ai-test-pg-009e` sin filas (solo cabecera).

### T-078 / T-079 / T-080 (reentrega) — evidencia D-29

Rojo T-078 (Postgres desechable 55433), `pytest --no-cov -q tests/unit/test_config.py tests/unit/migrations`:
```
FAILED tests/unit/test_config.py::test_memory_fts_config_defaults_to_spanish_unaccent   (assert 'spanish' == 'spanish_unaccent')
FAILED tests/unit/migrations/test_initial_migration.py::test_upgrade_creates_unaccent_extension_and_config   (pg_extension unaccent: 0 == 1)
FAILED tests/unit/migrations/test_initial_migration.py::test_unaccent_config_is_created_regardless_of_chosen_fts_config[english]
FAILED tests/unit/migrations/test_initial_migration.py::test_downgrade_drops_unaccent_config   (precondición: la config no existía)
4 failed, 37 passed
```
Verde T-079: mismos archivos -> `41 passed`. Suite completa (con BD): `Total coverage: 98.73%`, `8 failed, 394 passed` (los 8 son test_memory_repo.py, solo `ImportError: cannot import name 'memory_repo'`, T-081).

Archivos: `src/config.py`, `.env.example`, `alembic/versions/0001_initial_harness_schema.py` (extensión + config antes de las tablas; `DROP ... IF EXISTS` tras `drop_table('bedrock_agent_memory')`; CREATE TEXT SEARCH CONFIGURATION no admite IF NOT EXISTS, por eso DROP IF EXISTS previo), `src/models/bedrock_agent_memory.py` (docstring), `tests/conftest.py` (fixture `pg_db` usa `create_all`: replica el DDL de la config), README del ai no menciona `spanish`.

T-080: comentario falso corregido; asserts intactos. Verificación directa en PG15 con config equivalente:
```
 a | b | c | d      (a: 'empresa' ~ 'empresas'; b: 'tecnologias' ~ 'tecnología'; c: 'base de dato' ~ 'bases de datos'; d: 'astronauta' sin coincidencia)
 t | t | t | f
```
Rojo legítimo: `8 failed` en test_memory_repo.py, todos `ImportError ... 'memory_repo' from 'repositories'`.

### T-081 — `src/repositories/memory_repo.py` (RF-022)

Postgres desechable `career-ai-testdb` (127.0.0.1:55433, postgres:15-alpine). `venv/bin/python -m pytest tests/unit/repositories/test_memory_repo.py -q --no-cov`:
```
tests/unit/repositories/test_memory_repo.py ........                     [100%]
============================== 8 passed in 3.86s ===============================
```
Suite completa del ai (`pytest -q`, con TEST_DATABASE_URL):
```
src/repositories/memory_repo.py                 44      0   100%
Required test coverage of 80% reached. Total coverage: 98.76%
======================= 402 passed, 3 warnings in 42.81s =======================
```
Compuerta: `bash .harness/gate/check.sh` -> exit 0 (`31 ok · 3 warn · 0 error`). Contenedor detenido: `docker ps -a --filter name=career-ai-testdb` sin filas (solo cabecera). Test T-080 sin modificar. Sin commit.

### T-082 — test_memory_service.py (rojo)
Postgres desechable `career-ai-testdb` (127.0.0.1:55433). `venv/bin/python -m pytest tests/unit/services/test_memory_service.py -q --no-cov`:
```
12 x E   ImportError: cannot import name 'memory_service' from 'services' (.../cjhirashi-career-ai/src/services/__init__.py)
 1 x E   AssertionError: falta src/services/memory_service.py   (test de frontera)
13 failed
```
Resto de la suite (`--deselect` el archivo nuevo): `402 passed, 13 deselected`. Suite completa: `13 failed, 402 passed`.
Decisiones: fixture `pg_db` (FTS exige PG real); `MAX_LIMIT = 50` (el `le=50` de `top_k` de la ruta hoy; la API no acota `max_results` de events ni `limit` de notas, ahora sí); NUL saneado en texto y consulta; `MemoryServiceError(ValueError)`. Contenedor detenido: `docker ps -a` sin `career-ai-testdb`. Sin commit.

### T-082 (reentrega D-30) — idempotencia de notas/manual y `memory_source_ref`
Postgres desechable `career-ai-testdb` (127.0.0.1:55433). `pytest tests/unit/services/test_memory_service.py -q --no-cov`:
```
18 x E   ImportError: cannot import name 'memory_service' from 'services' (.../cjhirashi-career-ai/src/services/__init__.py)
 1 x E   AssertionError: falta src/services/memory_service.py   (test de frontera)
19 failed
```
Resto de la suite (`--deselect` el archivo): `402 passed, 19 deselected`. Contenedor detenido: `docker ps -a` sin `career-ai-testdb`.
Longitud de la clave: `note:` + perfil (<=50) + `:` + 64 puede llegar a 120 > 100. Propuesta (testeada): si la forma literal excede 100, se sustituye el perfil por `sha256(profile_id).hexdigest()[:16]` (<= 86). Perfiles <= 30 caracteres conservan la forma literal de D-30. Sin commit.

### T-082 (ajuste D-30: formato único de clave)
Clave `note:<profile_id>:<h>` / `manual:<h>`, `h` = 40 hex de sha256; máx. 96. Quitada la sustitución condicional del perfil. Postgres desechable 127.0.0.1:55433. `pytest tests/unit/services/test_memory_service.py -q --no-cov`:
```
19 x E   ImportError: cannot import name 'memory_service' from 'services' (.../cjhirashi-career-ai/src/services/__init__.py)
 1 x E   AssertionError: falta src/services/memory_service.py   (test de frontera)
20 failed
```
Resto de la suite (`--deselect` el archivo): `402 passed, 20 deselected`. Contenedor detenido: `docker ps -a` sin `career-ai-testdb`. Sin commit.

### T-082 (reentrega tras rechazo del revisor: D-1, D-2, R-1..R-3)
Añadido: retorno de `create_manual_memory` ({id,text}, reenvío con espacios/NUL igual); dedup por `source_ref` contra fila `qdrant_import` (nota y manual); fila creada (source_ref/kind/perfil NULL en manual/source="harness"); nota y manual con mismo texto = 2 filas; frontera por subproceso (`sys.modules`) además del AST; events = 50 más antiguos en orden; orden exacto de records; `memory_source_ref("note", t)` sin perfil -> ValueError; carrera: (a) 6 `create_agent_note` en `asyncio.gather` con sesión propia cada una (la fixture `pg_db` es una factory, lo permite) y (b) determinista por monkeypatch de `memory_repo.add_memory`, que inserta la fila rival con otra sesión justo antes del INSERT del servicio -> debe capturar `IntegrityError` y devolver la existente.
Postgres desechable 127.0.0.1:55433. `pytest tests/unit/services/test_memory_service.py -q --no-cov`:
```
24 x E   ImportError: cannot import name 'memory_service' from 'services' (.../cjhirashi-career-ai/src/services/__init__.py)
 1 x E   AssertionError: falta src/services/memory_service.py   (frontera AST)
 1 x E   ModuleNotFoundError: No module named 'services.memory_service'   (frontera subproceso)
26 failed
```
Resto de la suite (`--deselect` el archivo): `402 passed, 26 deselected`. Contenedor detenido: `docker ps -a` sin `career-ai-testdb`. Sin commit.

### T-083 — memory_service.py (verde)
Postgres desechable `career-ai-testdb` (127.0.0.1:55433, `postgres:15-alpine`). `pytest tests/unit/services/test_memory_service.py -q --no-cov`:
```
tests/unit/services/test_memory_service.py ..........................    [100%]
============================= 26 passed in 12.16s ==============================
```
Suite completa con `--cov=services.memory_service --cov-report=term-missing`:
```
src/services/memory_service.py                  63      1    98%   71
TOTAL                                         2083     26    99%
Required test coverage of 80% reached. Total coverage: 98.75%
======================= 428 passed, 3 warnings in 53.92s =======================
```
(402 previos + 26 nuevos, sin regresiones. Línea 71 sin cubrir: `raise` defensivo si tras el `IntegrityError` la fila existente no aparece.)
Gate: `env -u TEST_DATABASE_URL bash .harness/gate/check.sh` -> `31 ok · 3 warn · 0 error`, compuerta abierta. Contenedor borrado: `docker ps -a --filter name=career-ai-testdb` sin filas. Test T-082 sin modificar. Sin commit.

### T-083 (reentrega tras rechazo del revisor: delete_agent_note borraba cualquier kind)
Test nuevo `test_delete_agent_note_solo_borra_kind_note` (RF-022). Postgres desechable 127.0.0.1:55433.
ROJO (`pytest tests/unit/services/test_memory_service.py -q --no-cov`):
```
E   assert True is False
FAILED tests/unit/services/test_memory_service.py::test_delete_agent_note_solo_borra_kind_note
1 failed, 26 passed in 12.26s
```
Fix: `delete_agent_note` hace su propio DELETE con `id + user_id + kind='note'` (memory_repo intacto).
VERDE: `27 passed in 12.83s`. Suite completa: `memory_service.py 65 1 98% 71`, `TOTAL 2085 26 99%`, `429 passed, 3 warnings in 54.29s`.
Gate `env -u TEST_DATABASE_URL`: `31 ok · 3 warn · 0 error`, compuerta abierta. Contenedor borrado (`docker ps -a` sin filas). Sin commit.
