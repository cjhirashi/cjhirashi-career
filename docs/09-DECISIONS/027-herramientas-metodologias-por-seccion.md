# ADR-027: Herramientas y metodologías por sección (agentes L2)

## Estado

Aceptado — 2026-09-08. Revisa parcialmente **ADR-026** (D-1 y el modelo de
metodologías por `agent_profile_ids`) **sólo para los agentes L2**.

## Contexto

Tras ADR-026 (feature 003), las herramientas y metodologías de un agente se vinculan
directamente a su perfil (`bedrock_agent_profile_tools`,
`operational_methodologies.agent_profile_ids`). El operador quiere que, para los agentes
**L2** (los que atienden el chat contextual de una sección del Admin), ese vínculo pase
por la **sección**: la sección tiene sus herramientas y sus metodologías, y ligar un
agente L2 a una sección le da acceso a ambas. Un L2 puede poseer una o varias secciones
relacionadas y trabajar en varias a la vez, tomando sólo lo que la tarea requiere.

## Decisión

- **Sólo L2 cambia.** L1 (orquestador) y L3 (especialistas de tarea) no tienen sección;
  conservan la asignación **directa** de ADR-026 (`bedrock_agent_profile_tools` +
  `agent_profile_ids`), restringida a ids de nivel 1 y 3.
- **Herramientas de sección = derivadas en código** (`admin_sections.tools_for_section`),
  no editables por el operador: una sección tabla expone el CRUD genérico de su
  `resource_key` (`list/get/create/update/delete/bulk_update/count_career_record`,
  `describe_resource_schema`, `search_knowledge_base`); una funcional/métricas/bucket
  expone sus `related_tools`. El `resource_key` lo acota el tool-input en cada llamada
  (no hay tool por recurso).
- **Metodologías de sección = editables.** `operational_methodologies` gana `section_ids`
  (JSONB de `sec-N`). `PUT /bedrock/sections/{id}/methodologies` liga/desliga. Un L2
  ligado a alguna de esas secciones la recibe.
- **Set del L2 = unión de todas sus secciones** (`section_catalog.derived_tools_for_agent`),
  resuelto una vez por turno en `agent_loop`. El agente usa sólo lo que necesita
  (patrón buscar→leer de ADR-026 §Bloque J para metodologías).
- **`scope` en el catálogo de tools** (`section` | `agent` | `both`): las CRUD genéricas
  y `describe_resource_schema` son `section`; `delegate_to_specialist` es `agent`; el
  resto `both`. `set_tool_override` (L1/L3) rechaza tools `scope=section` (400).
- **`PUT /bedrock/agent-profiles/{L2}/tools` y `.../methodologies` → 409** (edítalo en la
  sección). Siguen válidos para L1/L3. `GET .../tools` de un L2 devuelve `by_section`
  (lectura, con procedencia) y `override_tools=null`.
- **Runtime:** `methodology_scope.applies_to_caller(agent_ids, section_ids, caller,
  caller_section_ids)` reemplaza a `applies_to_agent`; el bloque de metodologías del
  system prompt de un L2 se agrupa por sección de procedencia.
- **`admin_section_settings` `action=update`** acepta además `views` (los
  `sidebar_title`/`sidebar_body` por vista) — el servicio ya lo soportaba.

## Migración

`alembic/versions/a1b2c3d4e5f6_methodology_section_ids.py` (down_revision
`f7a8b9c0d1e2`): `ADD COLUMN IF NOT EXISTS section_ids JSONB` + retira los ids de nivel 2
de `agent_profile_ids` (idempotente). El operador re-liga las metodologías a secciones
desde `/settings/sections/:id`.

## Consecuencias

- `search_knowledge_base type=methodology` y el prompt resuelven L2 por sección.
- El payload Qdrant de metodologías lleva ahora `section_ids` además de
  `agent_profile_ids`/`title`/`section`.
- El catálogo de agentes muestra, para un L2, herramientas y metodologías en **lectura**
  con la sección de procedencia; L1/L3 mantienen los editores directos.
- ADR-026 queda vigente para L1/L3; para L2, este ADR manda.
