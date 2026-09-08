---
titulo: Herramientas y metodologías por sección (L2 vía sección; L1/L3 directo)
tipo: spec
estado: verified
fecha: 2026-09-08
feature_id: "004"
covers:
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
  - cjhirashi-career-api/tests/unit/bedrock/test_methodology_snippets.py
  - cjhirashi-career-admin/src/pages/AgentCatalogPage.tsx
  - cjhirashi-career-admin/src/pages/AdminSectionsPage.tsx
  - cjhirashi-career-admin/src/api/bedrock.ts
  - cjhirashi-career-admin/src/types/bedrock.ts
  - cjhirashi-career-admin/src/hooks/useBedrockChat.ts
  - cjhirashi-career-admin/src/tests/pages/AgentCatalogPage.test.tsx
  - cjhirashi-career-api/docs/sections/bedrock/README.md
  - docs/BEDROCK-SYSTEM.md
  - docs/09-DECISIONS/027-herramientas-metodologias-por-seccion.md
  - docs/09-DECISIONS/026-configuracion-agentes-app.md
  - cjhirashi-career-api/src/services/README.md
  - .harness/specs/004-herramientas-metodologias-por-seccion/contracts/sections.md
anchor_commit: 02110918
anchor_mode: strict
---

# Herramientas y metodologías por sección

## 1 · Contexto del dominio

**Problema (una frase):** hoy las herramientas y las metodologías de un agente se
vinculan **directamente al perfil del agente** (`bedrock_agent_profile_tools`,
`operational_methodologies.agent_profile_ids`, feature 003); el operador quiere que para
los agentes **L2** ese vínculo pase por la **sección** — la sección tiene sus
herramientas y sus metodologías, y ligar un agente L2 a una sección le da acceso a
ambas.

**Estado actual (verificado en código):**
- **Secciones del Admin** (`services/admin_sections.py`, ADR-021): ~54 secciones `sec-N`,
  cada una es una pantalla (tabla CRUD con `resource_key`, o funcional / métricas /
  bucket). Override editable en `admin_section_overrides` — hoy solo
  `agent_profile_id` (la L2 del chat contextual del sidebar) y `views` (textos de
  sidebar por vista). El vínculo **agente L2 ↔ sección** ya existe:
  `section_catalog.set_agent_sections(db, profile_id, section_ids)` +
  `PUT /bedrock/agent-profiles/{id}/sections`; es L2-only (`is_l2` gate); un agente puede
  poseer varias secciones, una sección tiene un agente.
- **Herramientas (003):** `tools_for_profile(profile)` calcula el set desde código;
  override por agente en `bedrock_agent_profile_tools` (0 filas en prod).
  `effective_tool_names(profile, override)` resuelve el set efectivo una vez por turno en
  `agent_loop.py`; `delegate_to_specialist` se gestiona por nivel (D-2 de ADR-026), no es
  editable.
- **Metodologías (003):** `operational_methodologies.agent_profile_ids` (JSONB); vacío =
  compartida. `methodology_scope.applies_to_agent` filtra `search_knowledge_base
  type=methodology` y el catálogo del system prompt (`methodology_assignment_block`). El
  guardián `agent_methodologies` ve todas.
- **Herramienta `admin_section_settings`:** existe (`services/bedrock/tools.py`), pero
  `action=update` sólo escribe `agent_profile_id`. **No** deja escribir `views`
  (`sidebar_title` / `sidebar_body` por vista) aunque el modelo y
  `section_catalog.update_section` lo soportan — el agente `agent_configuration`,
  responsable de "Secciones del Admin", no puede redactar las instrucciones de las
  vistas.

**Límites / dependencias:**
- Servicio dueño: `cjhirashi-career-api` (secciones, perfiles, tools, loop Bedrock,
  Alembic, Qdrant).
- Frontend: `cjhirashi-career-admin` (catálogo de agentes + ajustes de sección).
- Frontera externa: AWS Bedrock (tool-calling), Qdrant (búsqueda de metodologías).
- ADR-026 (feature 003) queda **parcialmente superado**: D-1 (override de tools por
  agente) y el modelo de metodologías por `agent_profile_ids` cambian para L2. Nuevo
  ADR-027.

## 2 · Alcance

### En alcance
- **Herramientas de sección (derivadas, no editables):** cada sección expone un conjunto
  de tools calculado **en código** desde su tipo + `resource_key`. Un agente L2 ligado a
  la sección las recibe.
- **Metodologías de sección (editables):** `operational_methodologies` gana `section_ids`
  (JSONB de `sec-N`). El operador liga/desliga metodologías a una sección desde
  `/settings/sections/:id`. Un agente L2 ligado a la sección las recibe.
- **Set DISPONIBLE del L2 = unión sobre TODAS sus secciones** (tools derivadas ∪,
  metodologías ligadas ∪, más las compartidas). Un L2 puede poseer **una o varias**
  secciones; con una sola, su set es exactamente el de esa sección. El agente **usa sólo
  lo que la tarea requiere** — una o varias secciones a la vez según la relación entre
  ellas — no "carga todo" cada turno (patrón buscar→leer de 003 Bloque J para
  metodologías; el tool-calling ya es "usa la que necesites").
- **L1 / L3 sin cambio de modelo:** siguen con asignación **directa** —
  `bedrock_agent_profile_tools` (restringido a perfiles L1/L3) y
  `operational_methodologies.agent_profile_ids` (restringido a ids L1/L3). Editores
  directos en el catálogo de agentes se mantienen para L1/L3.
- **Clasificación `scope`:** el catálogo de tools gana `scope ∈ {section, agent, both}`.
  Las secciones sólo exponen `section`/`both`; a L1/L3 sólo se asignan `agent`/`both`.
  Las metodologías se clasifican por su vínculo (`section_ids` ⇒ de sección;
  `agent_profile_ids` ⇒ de agente; ambos vacíos ⇒ compartida).
- **Herramienta `admin_section_settings`:** `action=update` acepta además
  `views={view_key:{sidebar_title?, sidebar_body?}}`.
- **Runtime:** `search_knowledge_base type=methodology`, `methodology_assignment_block` y
  `effective_tool_names` resuelven L2 vía secciones; L1/L3 como hoy.
- **Migración** de las 23 metodologías actuales + UI + trazabilidad `RF-`.

### Fuera de alcance
- Crear/eliminar secciones o agentes (siguen en código; ADR-021 / ADR-012).
- Editar la **definición** de una tool (nombre/schema/descripción) — es código.
- Cambiar qué tools existen o el routing de agentes.
- Permitir ligar L1/L3 a secciones (queda prohibido, `is_l2` gate se mantiene).
- Que el operador **elija** las tools de una sección — son derivadas.

## 3 · Modelo de datos y contratos de E/S

### 3.1 Herramientas de sección — derivadas en código
- `admin_sections.tools_for_section(spec) -> set[str]`:
  - `SECTION_TABLE` con `resource_key = R` → `{list_career_record, get_career_record,
    create_career_record, update_career_record, delete_career_record,
    bulk_update_career_record, count_career_records, describe_resource_schema,
    search_knowledge_base}` (acotadas a `R` por el propio tool-input; ver D-3).
  - `SECTION_FUNCTIONAL` / `SECTION_METRICS` / `SECTION_BUCKET` → conjunto declarado por
    ese `AdminSectionSpec` en código (p.ej. LinkedIn API → tools LinkedIn).
  - Toda sección incluye `admin_section_settings` para su agente responsable si aplica
    (`_ROUTE_TO_PROFILE`).
- No hay tabla ni endpoint de escritura para esto.

### 3.2 Metodologías — `section_ids` + `agent_profile_ids`
- Nueva columna `operational_methodologies.section_ids` `JSONB` nullable (lista de
  `sec-N`). Migración Alembic idempotente (`ADD COLUMN IF NOT EXISTS`).
- Semántica de visibilidad de una metodología para un caller:
  - **compartida** si `section_ids` y `agent_profile_ids` están ambos vacíos/null.
  - visible a un **L2** si algún `sec-N` de `section_ids` está en
    `sections_for_agent(caller)`.
  - visible a un **L1/L3** si `caller` está en `agent_profile_ids`.
  - el guardián `agent_methodologies` ve todas.
- **Migración de las 23 actuales:** se **limpian** de `agent_profile_ids` los ids que
  sean L2 (quedan sólo ids L1/L3). `section_ids` nace vacío. El operador re-liga desde
  `/settings/sections/:id`. (Se registra la lista de metodologías tocadas en el
  Session-End.)

### 3.3 Contrato de API
- `GET /bedrock/sections/{section_id}` →
  `{ section_id, system_name, label, section_type, resource_key, agent_profile_id,
     derived_tools: [...], methodology_ids: [...] , methodologies: [{id,title,section}] }`.
- `PUT /bedrock/sections/{section_id}/methodologies` con `{ methodology_ids: [...] }` →
  liga exactamente esas metodologías a la sección (reemplazo total del `section_ids` de
  cada una para este `sec-N`). Metodología inexistente → 400.
- `PUT /bedrock/agent-profiles/{id}/tools` y `PUT .../methodologies` (de 003):
  - si `{id}` es **L2** → `409 Conflict` RFC 9457 ("un agente L2 recibe herramientas y
    metodologías de sus secciones; edítalas en /settings/sections/:id").
  - si `{id}` es **L1/L3** → comportamiento actual.
- `GET /bedrock/agent-profiles/{id}/tools` (de 003) para un **L2** →
  `{ default_tools, effective_tools, override_tools: null, by_section: [{section_id,
  tools:[...]}] }` (read-only, con procedencia).
- Errores en formato Problem Details (RFC 9457).

### 3.4 Resolución en runtime
- `effective_tool_names(profile, ...)`:
  - **L2:** `∪ tools_for_section(s)` para `s ∈ sections_for_agent(profile)`, `& all_tool_names()`,
    luego la regla `delegate_to_specialist` por nivel (D-2 de ADR-026, sin cambios).
  - **L1/L3:** como en 003 (`bedrock_agent_profile_tools` override o default de código).
- `methodology_scope`:
  - `applies_to_caller(methodology, caller_profile_id, section_ids_of_caller)` sustituye a
    `applies_to_agent`; implementa 3.2.
  - `list_assigned_methodologies` y el filtro de `search_knowledge_base type=methodology`
    pasan a resolver por secciones para L2.
- **Sin N queries por turno:** `sections_for_agent(profile)` se resuelve **una vez por
  turno** en `agent_loop.py` y se pasa a la composición de prompt y a `execute_tool`.

### 3.5 `scope` en el catálogo de tools
- `services/bedrock/tools.py`: cada entrada de `_RAW_TOOLS` gana `scope ∈ {"section",
  "agent", "both"}` (por defecto `"both"` en la migración inicial; se ajusta por tool).
- `GET /bedrock/tools/catalog` (de 003) devuelve `scope` por tool.
- `set_tool_override` (L1/L3) rechaza (400) una tool cuyo `scope == "section"`.

### 3.6 `admin_section_settings` — edición de `views`
- `action=update` acepta `views: { <view_key>: { sidebar_title?: str, sidebar_body?: str } }`
  además de `agent_profile_id`. `null`/"" en un subcampo = restaura el texto de código;
  ausente = no lo toca. `view_key` desconocido para esa sección → error de tool (no 5xx).
- Plomería: `section_catalog.update_section(..., views=...)` ya existe; la tool sólo lo
  expone.

## 4 · Criterios de aceptación (EARS)

- **RF-001** — El sistema DEBE derivar en código, para cada sección, su conjunto de
  herramientas a partir de su tipo y `resource_key`, sin tabla ni endpoint de escritura.
- **RF-002** — CUANDO un agente **L2** resuelva su set de herramientas para un turno, el
  sistema DEBE usar la unión de las herramientas derivadas de **todas** las secciones que
  ese agente posee (`sections_for_agent`), aplicando después la regla de
  `delegate_to_specialist` por nivel.
- **RF-003** — SI se hace `PUT /bedrock/agent-profiles/{id}/tools` o `.../methodologies`
  para un agente **L2**, el sistema DEBE responder `409` y no persistir nada.
- **RF-004** — SI el agente es **L1 o L3**, el sistema DEBE conservar la asignación
  directa de herramientas (`bedrock_agent_profile_tools`) y de metodologías
  (`agent_profile_ids`) tal como en la feature 003.
- **RF-005** — El sistema DEBE persistir el vínculo metodología↔sección en
  `operational_methodologies.section_ids` y exponer
  `PUT /bedrock/sections/{section_id}/methodologies` para editarlo.
- **RF-006** — SI un `PUT /bedrock/sections/{section_id}/methodologies` incluye un
  `methodology_id` inexistente, el sistema DEBE responder `400` y no persistir nada.
- **RF-007** — CUANDO un agente **L2** consulte `search_knowledge_base type=methodology`,
  el sistema DEBE devolver las metodologías ligadas a alguna de sus secciones más las
  compartidas, y ninguna otra; el guardián `agent_methodologies` DEBE seguir viendo todas.
- **RF-008** — CUANDO se componga el system prompt de un agente **L2**, el bloque de
  metodologías DEBE listar las metodologías resueltas **agrupadas por su sección de
  procedencia** (más las compartidas), actualizadas cada turno, para que el agente elija
  la de la sección en la que va a trabajar.
- **RF-009** — CUANDO un agente **L1/L3** consulte metodologías, el sistema DEBE resolver
  por `agent_profile_ids` (más compartidas), sin considerar secciones.
- **RF-010** — El catálogo de herramientas DEBE exponer el `scope` (`section` | `agent` |
  `both`) de cada tool integrada.
- **RF-011** — SI un override directo de herramientas (L1/L3) incluye una tool con
  `scope == "section"`, el sistema DEBE rechazar con `400` y no persistir nada.
- **RF-012** — CUANDO el agente use `admin_section_settings action=update` con `views`,
  el sistema DEBE persistir los `sidebar_title` / `sidebar_body` por `view_key` en
  `admin_section_overrides.views` (o restaurarlos al código con `null`/"").
- **RF-013** — La migración DEBE añadir `operational_methodologies.section_ids` de forma
  idempotente y DEBE eliminar de `agent_profile_ids` los ids de nivel 2, dejando intactos
  los de nivel 1 y 3.
- **RF-014** — El catálogo de agentes DEBE mostrar, para un **L2**, sus herramientas y
  metodologías efectivas en **modo lectura**, con la sección de procedencia de cada una;
  para **L1/L3** DEBE mantener los editores directos.

## 5 · Casos límite y manejo de errores

- Agente L2 **con una sola sección** → su set disponible es exactamente el de esa
  sección (sin penalización ni caso especial).
- Agente L2 sin ninguna sección → set de herramientas = sólo lo que la regla de nivel
  añade (`delegate_to_specialist` si `can_delegate`); metodologías = sólo las compartidas.
- Sección sin agente (`agent_profile_id = null`) → nadie hereda sus tools/metodologías;
  siguen ligadas a la sección para cuando se le asigne un agente.
- Metodología ligada a una sección **y** a un agente L1/L3 a la vez → visible por ambas
  vías (unión), nunca excluyente.
- Metodología cuyo `section_ids` referencia un `sec-N` inexistente → se ignora ese id en
  la resolución (no rompe); `PUT` valida y rechaza ids desconocidos.
- Turno contextual cuya sección no tiene metodologías ligadas → el bloque del prompt lo
  dice ("no hay metodologías para esta configuración"), no falla.
- `PUT /bedrock/sections/{id}/methodologies` con Qdrant caído → el write a PG no falla;
  la re-indexación de las metodologías afectadas es best-effort (contrato de
  `CareerRepository`; ver 003 RF-014, que se reutiliza).
- L1 orquestador: nunca recibe tools de sección (no tiene secciones); su set sigue
  siendo el de código / su override directo.

## 6 · Registro de decisiones y descartes

| # | Decisión | Porqué | Descartado |
|---|---|---|---|
| D-1 | Sólo los **L2** cambian a modelo por sección; L1/L3 siguen con asignación directa | Una sección = una pantalla con chat L2 (`is_l2` gate ya existente); L1/L3 no tienen pantalla | Migrar todos los niveles a secciones (L1/L3 no tienen a qué ligarse) |
| D-2 | Las herramientas de una sección son **derivadas en código** (tipo + `resource_key`), no editables | "Son las herramientas que controlan la sección" — vienen de qué ES la sección, no de una elección; cero mantenimiento de listas | Lista curada por sección en código (54 listas a mano); override editable por sección |
| D-3 | Las tools CRUD de una sección tabla se acotan al `resource_key` por el propio tool-input, no por una variante de tool | No multiplicar el catálogo por recurso; el loop ya pasa `resource_key` en cada llamada | Una tool `list_projects`, `list_vacancies`… por recurso |
| D-4 | Metodologías: nueva columna `section_ids` (JSONB) en `operational_methodologies`, conservando `agent_profile_ids` para L1/L3 | Mínimo cambio de esquema; una metodología puede ser de sección, de agente L1/L3 o compartida sin tabla nueva | Tabla join `admin_section_methodologies` (endpoint/servicio nuevo, más piezas) |
| D-5 | Set **disponible** del L2 = unión de todas sus secciones, siempre. El agente usa sólo lo que la tarea requiere (una o varias secciones); con una sola sección, su set es el de esa sección | El operador pide que el L2 pueda trabajar en una **o varias** secciones relacionadas a la vez y tome "sólo lo que necesite"; acotar al `page_context` impediría el caso multi-sección | Acotar al `page_context` del turno con unión sólo en chat general |
| D-6 | Migración: **limpiar** los ids L2 de `agent_profile_ids`; el operador re-liga a mano | Un L2 posee muchas secciones — auto-mapear metería la metodología en todas; el texto libre `section` no siempre casa con una sección del Admin | Auto-mapear por el campo `section`; dejar los vínculos L2 muertos |
| D-7 | `scope ∈ {section, agent, both}` como atributo del catálogo de tools | Clasificación explícita pedida; permite validar qué puede ir a L1/L3 y qué expone una sección | Dos catálogos separados sin solape (duplicación conceptual) |
| D-8 | Extender `admin_section_settings` (no tool nueva) para escribir `views` | La tool ya existe y su owner es `agent_configuration`; sólo le falta el campo | Tool nueva `admin_section_views` (más entradas en el catálogo) |
| D-9 | `PUT .../agent-profiles/{L2}/tools|methodologies` → `409`, no se elimina el endpoint | El endpoint sigue siendo válido para L1/L3; 409 comunica "editálo en la sección" sin romper clientes | Borrar los endpoints; devolver 404 |
| D-10 | ADR-027 nuevo que revisa D-1/D-5 de ADR-026; feature 003 no se reabre | Es un rediseño deliberado del modelo, no un fix de 003 | 3ª reapertura de 003 |

## 7 · Requisitos no funcionales

- **RNF-001** — `sections_for_agent(profile)` y la derivación de tools se resuelven **una
  vez por turno** (en `agent_loop.py`); no deben introducir N queries por ronda.
- **RNF-002** — No se cambia el contrato de ninguna tool existente (`tools.py`); sólo se
  añade `scope` y se filtra qué set recibe cada perfil.
- **RNF-003** — Ninguna llamada real a Bedrock en tests (Art. 5); todo mockeado.
