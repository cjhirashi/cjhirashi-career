---
titulo: Plan — Herramientas y metodologías por sección
tipo: plan
estado: verified
fecha: 2026-09-08
feature_id: "004"
spec: ./spec.md
---

# Plan de implementación (patrón por capas)

## 0 · Enfoque

Un solo dueño de backend (`cjhirashi-career-api`) + `cjhirashi-career-admin` para UI.
El cambio es **sólo para L2**: su set de herramientas y metodologías se resuelve vía las
secciones que posee (`sections_for_agent`), una vez por turno. L1/L3 no cambian (siguen
con `bedrock_agent_profile_tools` + `operational_methodologies.agent_profile_ids`, 003).

Piezas ya existentes que se reutilizan:
- `section_catalog.sections_for_agent(db, profile_id)` — secciones de un L2.
- `section_catalog.update_section(..., views=...)` — **ya** persiste los textos de vista;
  sólo falta exponerlo en la tool `admin_section_settings`.
- `AdminSectionSpec.resource_key` / `section_type` / `related_tools` — base de la
  derivación de tools.
- `profile_tools.effective_tool_names` / `agent_loop` (003) — punto de resolución por turno.
- 003 RF-014 (`set_agent_methodologies` fuerza re-index) — se reutiliza el patrón para
  `set_section_methodologies`.

## 1 · Fronteras y archivos por capa

| Capa | Archivo | Cambio |
|---|---|---|
| Secciones (código) | `src/services/admin_sections.py` | `tools_for_section(spec) -> set[str]`: tabla → CRUD de `spec.resource_key` (`list/get/create/update/delete/bulk_update/count_career_record`, `describe_resource_schema`, `search_knowledge_base`) ∪ `spec.related_tools`; funcional/métricas/bucket → `spec.related_tools`. Poblar `related_tools` de las secciones funcionales que hoy lo tienen vacío |
| Sección↔agente | `src/services/section_catalog.py` | `derived_tools_for_agent(db, profile_id) -> set[str]` = ∪ `tools_for_section` sobre `sections_for_agent`; `section_methodology_ids(db, section_id)` y `set_section_methodologies(db, user_id, section_id, ids)` (edita `operational_methodologies.section_ids`, re-index best-effort) |
| Herramientas | `src/services/bedrock/profile_tools.py` | `effective_tool_names(profile, override, *, section_tools=None)`: si `profile.level == 2` y `section_tools is not None` → `section_tools & all_tool_names()` (+ regla de nivel D-2); si no, como 003. `get_tool_state` para L2 añade `by_section: [{section_id, tools}]` y `override_tools=None` |
| Metodologías | `src/services/methodology_scope.py` | `applies_to_caller(agent_profile_ids, section_ids, caller_id, caller_section_ids)` sustituye a `applies_to_agent`; `list_assigned_methodologies(..., caller_section_ids)` agrupa por sección para L2; `set_section_methodologies` (arriba); helper `strip_l2_from_agent_ids(ids) -> list` para la migración |
| Modelo | `src/models/operational_methodology.py` | Columna `section_ids` `JSONB` nullable |
| Schema dominio | `src/schemas/career_methodologies.py` | `section_ids: Optional[list[str]]` (valida `sec-N` conocidos) |
| Migración | `alembic/versions/b3d4e5f6a7c8_methodology_section_ids.py` (nuevo) | `ADD COLUMN IF NOT EXISTS operational_methodologies.section_ids JSONB`; paso de datos: por cada fila, `agent_profile_ids := [id for id in agent_profile_ids if not is_l2(id)]`. `down_revision = "f7a8b9c0d1e2"`. Idempotente |
| Rutas | `src/routes/bedrock.py` | `GET /bedrock/sections/{section_id}` (derived_tools + methodology_ids + methodologies); `PUT /bedrock/sections/{section_id}/methodologies`; en `PUT /bedrock/agent-profiles/{id}/tools` y `.../methodologies` → `409` si `get_profile(id).level == 2`; `GET .../tools` para L2 devuelve `by_section` |
| Schemas Bedrock | `src/schemas/bedrock.py` | `BedrockSectionDetail`, `BedrockSectionMethodologiesUpdateRequest`; `BedrockAgentToolsState.by_section: Optional[list[...]]` |
| Catálogo tools | `src/services/bedrock/tools.py` | cada `_RAW_TOOLS[i]` gana `scope ∈ {"section","agent","both"}` (default `"both"`, ajustado por tool); `list_builtin_tool_catalog` emite `scope`; `set_tool_override` (vía `profile_tools.validate_tool_names`) rechaza `400` una tool `scope=="section"` |
| Tool secciones | `src/services/bedrock/tools.py` | `admin_section_settings`: schema + `_run_admin_section_settings` aceptan `views={view_key:{sidebar_title?,sidebar_body?}}` → `section_catalog.update_section(..., views=...)` |
| Loop | `src/services/bedrock/agent_loop.py` | si `profile.level == 2`: `sections = await sections_for_agent(...)` **una vez**; `section_tools = derived_tools_for_agent(...)`; `caller_section_ids = [s.id]`; pasar `section_tools` a `effective_tool_names` y `caller_section_ids` a `compose_system_prompt` y a `execute_tool` |
| Prompt | `src/services/bedrock/prompt.py` | `compose_system_prompt(..., caller_section_ids=None)`; `methodology_assignment_block` agrupa el catálogo por sección de procedencia para L2 |
| Tool exec | `src/services/bedrock_service.py` + `src/services/bedrock/tools.py` | `execute_tool` / `_execute_tool` propagan `caller_section_ids`; el filtro `search_knowledge_base type=methodology` usa `applies_to_caller` |
| Frontend | `cjhirashi-career-admin/src/pages/*Section*` (ajustes de sección) | multiselect de metodologías (liga/desliga) → `PUT /bedrock/sections/{id}/methodologies`; muestra `derived_tools` read-only |
| Frontend | `cjhirashi-career-admin/src/pages/AgentCatalogPage.tsx` | para **L2**: herramientas y metodologías en **lectura** con procedencia por sección; para **L1/L3**: editores directos como hoy |
| Frontend | `cjhirashi-career-admin/src/api/bedrock.ts`, `types/bedrock.ts` | clientes/tipos de `GET /bedrock/sections/{id}`, `PUT .../methodologies`, `by_section` |

## 2 · Fronteras de salida

- **Postgres compartida** — sólo `ALTER TABLE operational_methodologies ADD COLUMN
  section_ids` + un `UPDATE` de datos, vía Alembic. Sin tablas nuevas.
- **AWS Bedrock** — sin cambio de contrato de tools; sólo `scope` en el catálogo y qué
  set recibe un L2. Sin llamadas reales en tests (Art. 5).
- **Qdrant** — `set_section_methodologies` re-indexa best-effort las metodologías tocadas
  (reutiliza `CareerRepository._index_for_search`, ya con `title`/`section` en payload).
  Sin cambio de esquema.

## 3 · Contratos y gates de CI

- `openapi.yaml` no committeado → sin Spectral/oasdiff; el bloque `rest-http` corre pytest.
- Nuevo `contracts/sections.md` — request/response de `GET /bedrock/sections/{id}` y
  `PUT /bedrock/sections/{id}/methodologies`, y el `409` de los endpoints de agente L2.
- Gate: `venv_test/bin/python -m pytest -q` (api) + `npx vitest run` (admin).
- **Art. 5:** ningún test llama a Bedrock real.

## 4 · Estrategia de pruebas por capa

| Capa | Test | Cubre |
|---|---|---|
| `admin_sections.tools_for_section` (unit puro) | `tests/unit/test_section_tools_derivation.py` (nuevo) | RF-001: sección tabla `projects` → set CRUD de `projects` + `search_knowledge_base`; funcional → `related_tools`; el set no incluye tools ajenas |
| `section_catalog` (unit + db doble) | `tests/unit/test_section_methodologies.py` (nuevo) | RF-005/006: `set_section_methodologies` liga/desliga en `section_ids`; id inexistente → error; `derived_tools_for_agent` = unión de sus secciones (RF-002) |
| `profile_tools` (unit puro) | `tests/unit/bedrock/test_profile_tools.py` (ampliar) | RF-002: L2 con `section_tools` → efectivo = unión ∩ catálogo + regla de nivel; RF-011: override L1/L3 con tool `scope=section` → `ValueError` |
| `methodology_scope` (unit) | `tests/unit/test_methodology_scope.py` (ampliar) | RF-007/009: `applies_to_caller` — L2 por `section_ids ∩ caller_section_ids`, L1/L3 por `agent_profile_ids`, compartida, guardián; `strip_l2_from_agent_ids` |
| Rutas (unit TestClient + db doble) | `tests/unit/bedrock/test_section_routes.py` (nuevo) | RF-003 (`PUT /agent-profiles/{L2}/tools` → 409), RF-005/006 (`PUT /sections/{id}/methodologies`), RF-014 (`GET .../tools` L2 con `by_section`) |
| Catálogo `scope` (unit) | `tests/unit/bedrock/test_tools_catalog_routes.py` (ampliar) | RF-010: `GET /tools/catalog` emite `scope` por tool |
| `admin_section_settings` views (unit) | `tests/unit/bedrock/test_admin_section_settings_views.py` (nuevo) | RF-012: `action=update` con `views` persiste `sidebar_title`/`sidebar_body`; `null`/"" restaura; `view_key` desconocido se ignora |
| Migración (unit) | `tests/unit/test_methodology_section_ids_migration.py` (nuevo) | RF-013: columna idempotente; `agent_profile_ids` pierde los ids L2 y conserva L1/L3 |
| Loop (unit, secciones y search mockeados) | `tests/unit/bedrock/test_agent_loop_tools.py` (ampliar) | RF-002/RNF-001: para L2 se resuelve `sections_for_agent` **una vez**; el set efectivo (unión de secciones) llega a `converse_tool_specs` |
| Prompt (unit) | `tests/unit/bedrock/test_prompt_methodology.py` (ampliar) | RF-008: el bloque de un L2 agrupa metodologías por sección de procedencia |
| Frontend (Vitest) | `cjhirashi-career-admin/src/tests/pages/AgentCatalogPage.test.tsx` (ampliar) + ajustes de sección | RF-014: L2 read-only con procedencia; L1/L3 editores; multiselect de metodologías en la sección |

## 5 · Detalle por RF

### RF-001 — herramientas de sección derivadas
`admin_sections.tools_for_section(spec)`:
```
base = set(spec.related_tools)
if spec.section_type == SECTION_TABLE and spec.resource_key:
    base |= {list_career_record, get_career_record, create_career_record,
             update_career_record, delete_career_record, bulk_update_career_record,
             count_career_records, describe_resource_schema, search_knowledge_base}
return base
```
La acotación al `resource_key` la hace el tool-input en cada llamada (D-3); no hay tool
por recurso. Se completan los `related_tools` de las secciones funcionales/métricas/bucket
que hoy los tienen vacíos.

### RF-002 — set del L2 = unión de sus secciones
`section_catalog.derived_tools_for_agent(db, profile_id)` = `∪ tools_for_section(get_section_spec(s["id"]))`
para `s ∈ sections_for_agent(db, profile_id)`. `agent_loop` lo resuelve una vez por turno
(RNF-001) y lo pasa a `profile_tools.effective_tool_names(profile, None, section_tools=...)`.
La regla `delegate_to_specialist` por nivel se aplica después, sin cambios (D-2 de ADR-026).

### RF-003 / RF-009 / RF-014 — endpoints de agente
- `PUT /bedrock/agent-profiles/{id}/tools` y `.../methodologies`: al entrar, si
  `get_profile(id).level == 2` → `HTTPException(409, "…edítalo en /settings/sections/:id")`
  antes de tocar nada.
- `GET /bedrock/agent-profiles/{id}/tools` para L2 → `get_tool_state` añade
  `by_section` (una entrada por sección con sus `tools`) y `override_tools=None`.
- L1/L3: comportamiento de 003 intacto (RF-009 = "sin cambios para L1/L3").

### RF-005 / RF-006 — metodologías de sección
`section_catalog.set_section_methodologies(db, user_id, section_id, methodology_ids)`:
- valida `section_id` conocido y cada `methodology_id` existente del usuario (400 si no).
- para cada metodología del usuario: si está en `methodology_ids` → añade `section_id` a
  su `section_ids`; si no y lo tenía → lo quita.
- re-index best-effort de las metodologías tocadas (patrón 003 RF-014).
`GET /bedrock/sections/{section_id}` devuelve `derived_tools`, `methodology_ids`,
`methodologies` (id/title/section).

### RF-007 / RF-008 — resolución de metodologías en runtime
`methodology_scope.applies_to_caller(agent_profile_ids, section_ids, caller_id, caller_section_ids)`:
```
if not agent_profile_ids and not section_ids: return True           # compartida
if not caller_id or caller_id == AGENT_METHODOLOGIES: return True   # guardián
if set(section_ids or []) & set(caller_section_ids or []): return True   # L2 por sección
if caller_id in (agent_profile_ids or []): return True             # L1/L3 directo
return False
```
`list_assigned_methodologies(db, user_id, caller_id, caller_section_ids)` agrupa el
resultado por `section` de procedencia para L2 (RF-008). El filtro de
`search_knowledge_base type=methodology` (`bedrock_service._execute_tool`) llama
`applies_to_caller` con `caller_section_ids` propagado desde `agent_loop` →
`execute_tool` → `_execute_tool`.

### RF-010 / RF-011 — `scope` de tools
`_RAW_TOOLS` gana `scope`. `list_builtin_tool_catalog` y `GET /tools/catalog` lo emiten.
`profile_tools.validate_tool_names` (usada por `set_tool_override`, sólo L1/L3 ya) añade:
`bad = {t for t in cleaned if catalog_scope(t) == "section"}` → `ValueError` (→ 400).

### RF-012 — `admin_section_settings` escribe `views`
Schema: `views: {type: object}` con `additionalProperties` `{sidebar_title?, sidebar_body?}`.
`_run_admin_section_settings` en `action=update` pasa `views` a
`section_catalog.update_section(..., views=views)` (que ya limpia sub-campos ausentes,
restaura con `null`/"" e ignora `view_key` desconocido). `is_write_tool` ya lista
`admin_section_settings` para auditoría.

### RF-013 — migración
`alembic/versions/b3d4e5f6a7c8_methodology_section_ids.py`:
- `op.execute("ALTER TABLE operational_methodologies ADD COLUMN IF NOT EXISTS section_ids JSONB")`
- paso de datos en Python: cargar `id, agent_profile_ids`; para cada fila,
  `nuevo = [x for x in (agent_profile_ids or []) if not is_l2(x)]`; si cambió, `UPDATE`.
- `downgrade`: `DROP COLUMN IF EXISTS section_ids` (no restaura los ids L2 quitados — se
  documenta).

## § Impacto en documentación (Art. 11)

| Documento | Motivo | Tarea |
|---|---|---|
| `docs/09-DECISIONS/027-herramientas-metodologias-por-seccion.md` (nuevo) | Decisión: L2 vía sección; tools derivadas; `section_ids`; `scope`; revisa D-1/D-5 de ADR-026 | `[doc]` T-D1 |
| `docs/09-DECISIONS/026-configuracion-agentes-app.md` (ampliar) | Nota "parcialmente superado por ADR-027 para L2" | `[doc]` T-D1 |
| `cjhirashi-career-api/docs/sections/bedrock/README.md` | Endpoints `GET /bedrock/sections/{id}`, `PUT .../methodologies`; `409` de los de agente L2; `scope` en `/tools/catalog` | `[doc]` T-D2 |
| `docs/BEDROCK-SYSTEM.md` §Perfiles | L2 recibe herramientas (derivadas) y metodologías (ligadas) de sus secciones; L1/L3 directo | `[doc]` T-D2 |
| `cjhirashi-career-api/src/services/README.md` | `methodology_scope` (nuevo modelo), `section_catalog` (tools derivadas + metodologías de sección) | `[doc]` T-D2 |
| `.harness/specs/004-herramientas-metodologias-por-seccion/contracts/sections.md` (nuevo) | Contrato de los endpoints de sección | `[doc]` T-D3 |

## `covers` (front-matter de spec.md)

```
- cjhirashi-career-api/src/services/admin_sections.py
- cjhirashi-career-api/src/services/section_catalog.py
- cjhirashi-career-api/src/services/methodology_scope.py
- cjhirashi-career-api/src/services/bedrock/profile_tools.py
- cjhirashi-career-api/src/services/bedrock/agent_loop.py
- cjhirashi-career-api/src/services/bedrock/prompt.py
- cjhirashi-career-api/src/services/bedrock/tools.py
- cjhirashi-career-api/src/services/bedrock_service.py
- cjhirashi-career-api/src/models/operational_methodology.py
- cjhirashi-career-api/src/schemas/career_methodologies.py
- cjhirashi-career-api/src/schemas/bedrock.py
- cjhirashi-career-api/src/routes/bedrock.py
- cjhirashi-career-api/alembic/versions/*_methodology_section_ids.py
- cjhirashi-career-api/tests/unit/test_section_tools_derivation.py
- cjhirashi-career-api/tests/unit/test_section_methodologies.py
- cjhirashi-career-api/tests/unit/test_methodology_scope.py
- cjhirashi-career-api/tests/unit/test_methodology_section_ids_migration.py
- cjhirashi-career-api/tests/unit/bedrock/test_profile_tools.py
- cjhirashi-career-api/tests/unit/bedrock/test_section_routes.py
- cjhirashi-career-api/tests/unit/bedrock/test_tools_catalog_routes.py
- cjhirashi-career-api/tests/unit/bedrock/test_admin_section_settings_views.py
- cjhirashi-career-api/tests/unit/bedrock/test_agent_loop_tools.py
- cjhirashi-career-api/tests/unit/bedrock/test_prompt_methodology.py
- cjhirashi-career-admin/src/pages/AgentCatalogPage.tsx
- cjhirashi-career-admin/src/api/bedrock.ts
- cjhirashi-career-admin/src/types/bedrock.ts
- cjhirashi-career-admin/src/tests/pages/AgentCatalogPage.test.tsx
- cjhirashi-career-api/docs/sections/bedrock/README.md
- docs/BEDROCK-SYSTEM.md
- docs/09-DECISIONS/027-herramientas-metodologias-por-seccion.md
- docs/09-DECISIONS/026-configuracion-agentes-app.md
- cjhirashi-career-api/src/services/README.md
- .harness/specs/004-herramientas-metodologias-por-seccion/contracts/sections.md
```
