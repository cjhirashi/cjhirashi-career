---
titulo: Tasks — Herramientas y metodologías por sección
tipo: tasks
estado: verified
fecha: 2026-09-08
feature_id: "004"
spec: ./spec.md
plan: ./plan.md
---

# Tareas (atómicas, TDD, test antes que código)

Marcar `[x]` sólo con salida de terminal **pegada** (corrección del usuario en
`state.md`, 2026-09-02). El verificador re-ejecuta, no confía en el reporte.

## Bloque A — Herramientas derivadas de la sección

- [x] **T-001** `[test]` (cubre RF-001) — `tests/unit/test_section_tools_derivation.py`:
  `tools_for_section` de una sección `SECTION_TABLE` con `resource_key="projects"` →
  incluye `list_career_record`, `get_career_record`, `create/update/delete_career_record`,
  `bulk_update_career_record`, `count_career_records`, `describe_resource_schema`,
  `search_knowledge_base`; de una funcional → exactamente `spec.related_tools`. Rojo.
- [x] **T-002** `[code]` (cubre RF-001) — `admin_sections.tools_for_section(spec)`; poblar
  `related_tools` de las secciones funcionales/métricas/bucket que hoy los tienen vacíos.
  Verde T-001.

## Bloque B — Sección ↔ agente: unión de herramientas

- [x] **T-010** `[test]` (cubre RF-002) — `tests/unit/test_section_methodologies.py`:
  `derived_tools_for_agent` con un L2 doble que posee `[sec-A, sec-B]` (mockeando
  `sections_for_agent`) → unión de `tools_for_section(A)` y `(B)`; L2 con una sola sección
  → set de esa sección. Rojo.
- [x] **T-011** `[code]` (cubre RF-002) — `section_catalog.derived_tools_for_agent(db,
  profile_id)`. Verde T-010.
- [x] **T-012** `[test]` (cubre RF-002/RNF-001) — `tests/unit/bedrock/test_agent_loop_tools.py`
  (ampliar): para un `profile.level == 2`, el loop llama `sections_for_agent` **una vez**
  y el set efectivo (unión de secciones) llega a `converse_tool_specs`. Rojo.
- [x] **T-013** `[code]` (cubre RF-002/RNF-001) — `agent_loop.py`: rama L2 resuelve
  `sections`/`section_tools`/`caller_section_ids` una vez y los propaga. Verde T-012.

## Bloque C — `profile_tools`: rama L2 + `scope`

- [x] **T-020** `[test]` (cubre RF-002) — `tests/unit/bedrock/test_profile_tools.py`
  (ampliar): `effective_tool_names(l2_profile, None, section_tools={...})` → `{...} ∩
  all_tool_names()` + regla `delegate_to_specialist` por nivel. Rojo.
- [x] **T-021** `[code]` (cubre RF-002) — parámetro `section_tools` en
  `effective_tool_names`; `get_tool_state` para L2 emite `by_section` y
  `override_tools=None`. Verde T-020.
- [x] **T-022** `[test]` (cubre RF-010) — `tests/unit/bedrock/test_tools_catalog_routes.py`
  (ampliar): `GET /bedrock/tools/catalog` → cada builtin trae `scope ∈
  {section,agent,both}`. Rojo.
- [x] **T-023** `[code]` (cubre RF-010) — `scope` en `_RAW_TOOLS` + `list_builtin_tool_catalog`
  + schema. Verde T-022.
- [x] **T-024** `[test]` (cubre RF-011) — `test_profile_tools.py`: `validate_tool_names`
  con una tool `scope=="section"` → `ValueError`. Rojo.
- [x] **T-025** `[code]` (cubre RF-011) — `validate_tool_names` rechaza `scope=="section"`.
  Verde T-024.

## Bloque D — Metodologías: modelo + `section_ids` + migración

- [x] **T-030** `[test]` (cubre RF-013) — `tests/unit/test_methodology_section_ids_migration.py`:
  aplicar upgrade dos veces (idempotente); una fila con `agent_profile_ids` mezcla L2+L3
  → queda sólo el L3; el schema del modelo tiene `section_ids`. Rojo.
- [x] **T-031** `[code]` (cubre RF-013) — columna en `models/operational_methodology.py` +
  `section_ids` en `schemas/career_methodologies.py` (valida `sec-N`) + migración
  `<rev>_methodology_section_ids.py` (`ADD COLUMN IF NOT EXISTS` + paso de datos
  `strip_l2_from_agent_ids`, `down_revision = f7a8b9c0d1e2`). Verde T-030.
- [x] **T-032** `[test]` (cubre RF-007/009) — `tests/unit/test_methodology_scope.py`
  (ampliar): `applies_to_caller` — compartida (ambos vacíos) → True; L2 con
  `section_ids ∩ caller_section_ids` → True y sin intersección → False; L1/L3 por
  `agent_profile_ids`; guardián `agent_methodologies` → True siempre;
  `strip_l2_from_agent_ids`. Rojo.
- [x] **T-033** `[code]` (cubre RF-007/009) — `applies_to_caller` + `strip_l2_from_agent_ids`;
  `applies_to_agent` pasa a delegar en el nuevo (compat) o se retira con sus usos. Verde T-032.

## Bloque E — Metodologías de sección: servicio + rutas

- [x] **T-040** `[test]` (cubre RF-005/006) — `test_section_methodologies.py`:
  `set_section_methodologies(db, uid, "sec-A", ["opm-1"])` → `opm-1.section_ids` contiene
  `sec-A`; quitar → lo elimina; `methodology_id` inexistente → `ValueError`; `section_id`
  desconocido → `ValueError`. Rojo.
- [x] **T-041** `[code]` (cubre RF-005/006) — `section_catalog.set_section_methodologies`
  (+ re-index best-effort, patrón 003 RF-014) y `section_methodology_ids`. Verde T-040.
- [x] **T-042** `[test]` (cubre RF-005/006/014) — `tests/unit/bedrock/test_section_routes.py`
  (nuevo): `GET /bedrock/sections/{id}` → `{derived_tools, methodology_ids, methodologies}`;
  `PUT /bedrock/sections/{id}/methodologies` liga; id de metodología inexistente → 400.
  Rojo.
- [x] **T-043** `[code]` (cubre RF-005/006/014) — schemas `BedrockSectionDetail`,
  `BedrockSectionMethodologiesUpdateRequest` + rutas en `routes/bedrock.py`. Verde T-042.
- [x] **T-044** `[test]` (cubre RF-003) — mismo archivo: `PUT /bedrock/agent-profiles/{L2}/tools`
  → `409`; `PUT .../methodologies` para L2 → `409`; para un L1/L3 → sigue funcionando.
  Rojo.
- [x] **T-045** `[code]` (cubre RF-003) — guardia de nivel en ambos endpoints (409 antes
  de tocar nada). Verde T-044.
- [x] **T-046** `[test]` (cubre RF-014) — `test_section_routes.py`: `GET
  /bedrock/agent-profiles/{L2}/tools` → `by_section` presente, `override_tools=null`.
  Rojo.
- [x] **T-047** `[code]` (cubre RF-014) — `get_tool_state`/ruta emite `by_section` para L2.
  Verde T-046.

## Bloque F — Runtime: prompt + filtro de búsqueda

- [x] **T-050** `[test]` (cubre RF-008) — `tests/unit/bedrock/test_prompt_methodology.py`
  (ampliar): `methodology_assignment_block` de un L2 con metodologías de 2 secciones →
  aparecen **agrupadas por sección de procedencia**; compartidas en su propio grupo. Rojo.
- [x] **T-051** `[code]` (cubre RF-008) — `compose_system_prompt(..., caller_section_ids)`
  + agrupación en `methodology_assignment_block`; `list_assigned_methodologies` acepta
  `caller_section_ids`. Verde T-050.
- [x] **T-052** `[test]` (cubre RF-007) — `tests/unit/bedrock/test_methodology_snippets.py`
  (ampliar) o `test_section_routes.py`: `search_knowledge_base type=methodology` para un
  L2 (con `caller_section_ids` propagado) → devuelve sólo metodologías de sus secciones +
  compartidas; para L1/L3 → por `agent_profile_ids`. Rojo.
- [x] **T-053** `[code]` (cubre RF-007) — `execute_tool`/`_execute_tool` propagan
  `caller_section_ids`; el filtro usa `applies_to_caller`. Verde T-052.

## Bloque G — `admin_section_settings` escribe `views`

- [x] **T-060** `[test]` (cubre RF-012) — `tests/unit/bedrock/test_admin_section_settings_views.py`
  (nuevo): `action=update` con `views={"main":{"sidebar_body":"texto"}}` → persiste en
  `admin_section_overrides.views`; `sidebar_body:""` restaura override vacío; `null` /
  ausente → hereda código; `view_key` desconocido → se ignora, sin 5xx. Rojo.
- [x] **T-061** `[code]` (cubre RF-012) — schema + `_run_admin_section_settings` pasan
  `views` a `section_catalog.update_section`. Verde T-060.

## Bloque H — Frontend admin

- [x] **T-070** `[test]` (cubre RF-014) — `AgentCatalogPage.test.tsx` (ampliar): para un
  **L2** el editor de herramientas y el de metodologías se muestran en **lectura** con la
  sección de procedencia; para **L1/L3** siguen editables. Rojo.
- [x] **T-071** `[code]` (cubre RF-014) — `types/bedrock.ts` + `api/bedrock.ts`
  (`getSection`, `setSectionMethodologies`, `by_section`) + render condicional por nivel
  en `AgentCatalogPage.tsx` + multiselect de metodologías en ajustes de sección. Verde
  T-070.

## Bloque I — Documentación

- [x] **T-D1** `[doc]` — `docs/09-DECISIONS/027-herramientas-metodologias-por-seccion.md`
  (nuevo ADR) + nota "parcialmente superado" en `026-configuracion-agentes-app.md` +
  índice de decisiones.
- [x] **T-D2** `[doc]` — `cjhirashi-career-api/docs/sections/bedrock/README.md` +
  `docs/BEDROCK-SYSTEM.md` §Perfiles + `cjhirashi-career-api/src/services/README.md`.
- [x] **T-D3** `[doc]` — `contracts/sections.md` (request/response + el `409`).

## Bloque J — Cierre en vivo

- [x] **T-080** `[ops]` (cierre RF-002/RF-007/RF-013 en vivo, Art. 3) — tras desplegar:
  `alembic upgrade head` en `career_db` (pegar `alembic current`); ligar una metodología
  a una sección vía `PUT /bedrock/sections/{id}/methodologies` con JWT real (pegar 200);
  turno de chat de ese L2 llamando `search_knowledge_base type=methodology` → pegar que
  recibe la de la sección y no las ajenas; `PUT /bedrock/agent-profiles/{L2}/tools` →
  pegar `409`. Evidencia de terminal **pegada**.

---

## Cobertura (el gate exige 100 %)

| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-001, T-002 | test_section_tools_derivation | Pass |
| RF-002 | T-010, T-011, T-012, T-013, T-020, T-021, T-080 | test_section_methodologies::derived_tools · test_agent_loop_tools · test_profile_tools · T-080 (vivo) | Pass |
| RF-003 | T-044, T-045 | test_section_routes::put_l2_tools_returns_409 | Pass |
| RF-004 | (revisión) | 003 sin cambios para L1/L3 — tests de 003 siguen verdes | Pass |
| RF-005 | T-040, T-041, T-042, T-043 | test_section_methodologies · test_section_routes | Pass |
| RF-006 | T-040, T-041, T-042, T-043 | test_section_methodologies::rejects_unknown · test_section_routes | Pass |
| RF-007 | T-032, T-033, T-052, T-053, T-080 | test_methodology_scope::applies_to_caller · test_methodology_snippets · T-080 (vivo) | Pass |
| RF-008 | T-050, T-051 | test_prompt_methodology::block_grouped_by_section | Pass |
| RF-009 | T-032, T-033 | test_methodology_scope::applies_to_caller_l1_l3 | Pass |
| RF-010 | T-022, T-023 | test_tools_catalog_routes::catalog_emits_scope | Pass |
| RF-011 | T-024, T-025 | test_profile_tools::validate_rejects_section_scope | Pass |
| RF-012 | T-060, T-061 | test_admin_section_settings_views | Pass |
| RF-013 | T-030, T-031, T-080 | test_methodology_section_ids_migration · T-080 (vivo, alembic current) | Pass |
| RF-014 | T-042, T-043, T-046, T-047, T-070, T-071 | test_section_routes::get_l2_tools_by_section · AgentCatalogPage.test | Pass |
| RNF-001 | T-012, T-013 | test_agent_loop_tools::sections_resolved_once | Pass |
| RNF-002 | (revisión) | sólo se añade `scope`; sin cambio de contrato de tools | Pass |
| RNF-003 | (revisión) | ningún test llama a Bedrock real (Art. 5) | Pass |
| doc: ADR-027 + 026 | T-D1 | `docs/09-DECISIONS/027-*.md` · `026-*.md` | Pass |
| doc: READMEs | T-D2 | `docs/sections/bedrock/README.md` · `docs/BEDROCK-SYSTEM.md` · `src/services/README.md` | Pass |
| doc: contracts/sections.md | T-D3 | `contracts/sections.md` | Pass |
