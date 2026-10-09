---
titulo: "Metodologías Operativas: esquema mínimo y vínculo con Secciones editable desde la metodología"
tipo: spec
estado: draft
fecha: 2026-09-09
feature_id: "005"
anchor_mode: advisory
# covers fijado por el arquitecto en Fase 2 (plan.md §9), conciliado con specs 003/004 (plan.md §1.1)
covers:
  # --- API · código ---
  - cjhirashi-career-api/src/models/operational_methodology.py
  - cjhirashi-career-api/src/schemas/career_methodologies.py
  - cjhirashi-career-api/src/schemas/bedrock.py
  - cjhirashi-career-api/src/routes/career_methodologies.py
  - cjhirashi-career-api/src/routes/career_common.py
  - cjhirashi-career-api/src/routes/bedrock.py
  - cjhirashi-career-api/src/services/methodology_scope.py
  - cjhirashi-career-api/src/services/section_catalog.py
  - cjhirashi-career-api/src/services/bedrock_service.py
  - cjhirashi-career-api/src/services/bedrock/prompt.py
  - cjhirashi-career-api/src/services/bedrock/profile_catalog.py
  - cjhirashi-career-api/src/services/bedrock/agent_profiles.py
  - cjhirashi-career-api/src/services/bedrock/tools.py
  - cjhirashi-career-api/src/repositories/career_repository.py
  - cjhirashi-career-api/src/app.py
  - cjhirashi-career-api/alembic/versions/*_methodology_drop_section_freeform.py
  # --- API · tests ---
  - cjhirashi-career-api/tests/unit/test_methodology_drop_section_migration.py
  - cjhirashi-career-api/tests/unit/test_methodology_schema_forbid.py
  - cjhirashi-career-api/tests/unit/test_methodology_section_link_domain.py
  - cjhirashi-career-api/tests/unit/test_methodology_crud_routes.py
  - cjhirashi-career-api/tests/unit/test_problem_details_handler.py
  - cjhirashi-career-api/tests/unit/test_methodology_scope.py
  - cjhirashi-career-api/tests/unit/test_section_methodologies.py
  - cjhirashi-career-api/tests/unit/test_methodology_indexing.py
  - cjhirashi-career-api/tests/unit/bedrock/test_prompt_methodology.py
  - cjhirashi-career-api/tests/unit/bedrock/test_methodology_snippets.py
  - cjhirashi-career-api/tests/unit/bedrock/test_section_routes.py
  - cjhirashi-career-api/tests/unit/bedrock/test_agent_profiles_suffix.py
  - cjhirashi-career-api/tests/unit/bedrock/test_career_record_tool_methodology.py
  # --- Admin · código ---
  - cjhirashi-career-admin/src/config/careerResources.ts
  - cjhirashi-career-admin/src/types/career.ts
  - cjhirashi-career-admin/src/config/sectionCatalog.ts
  - cjhirashi-career-admin/src/hooks/useFkOptions.ts
  - cjhirashi-career-admin/src/components/career/careerFieldUtils.ts
  - cjhirashi-career-admin/src/components/career/CareerResourceView.tsx
  # --- Admin · tests ---
  - cjhirashi-career-admin/src/tests/config/careerResources.test.ts
  - cjhirashi-career-admin/src/tests/components/careerFieldUtils.test.ts
  - cjhirashi-career-admin/src/tests/components/ResourceForm.test.tsx
  - cjhirashi-career-admin/src/tests/hooks/useFkOptions.test.ts
  - cjhirashi-career-admin/src/tests/pages/AdminSectionsPage.test.tsx
  # --- Doc ---
  - docs/BEDROCK-SYSTEM.md
  - docs/09-DECISIONS/027-herramientas-metodologias-por-seccion.md
  - cjhirashi-career-api/docs/sections/bedrock/README.md
  - cjhirashi-career-api/src/services/README.md
  - cjhirashi-career-api/src/models/README.md
  - .harness/specs/005-metodologias-esquema-minimo-y-vinculo-seccion/contracts/
revisa_adr:            # confirmado en elicitación (tanda 2 · G) — el arquitecto formaliza el texto en Fase 2
  - ADR-027            # ENMIENDA (no ADR nuevo): 004 fijó "el vínculo sección↔metodología se edita desde la sección"; 005 amplía a "también desde la metodología, vía una función de dominio única compartida por ambos editores" (amplía, no contradice)
anchor_commit: null
---

# Metodologías Operativas: esquema mínimo y vínculo con Secciones editable desde la metodología

> **Estado: lista para Gate 1.** `[NEEDS CLARIFICATION] = 0`. `estado: draft` en el
> front-matter lo sube el flujo tras aprobar Gate 1. Elicitación cerrada en dos tandas
> con el operador (Carlos); la tanda 2 (A–I) se aprobó completa el 2026-09-09.

## 1 · Contexto del dominio

**Problema (una frase):** la tabla/recurso `operational-methodologies` (Metodologías
Operativas) del Admin arrastra campos de texto libre (`section` String(150) indexada,
`subsection` String(150), `notes` Text) que duplican y compiten con el catálogo real de
**Secciones del Admin**; el operador quiere que una metodología tenga sólo lo esencial
(título, descripción breve, instrucciones) y que su vínculo con las Secciones del Admin
(`section_ids`, JSONB de `sec-N`, introducido por la feature 004) se pueda **editar desde
la propia metodología**, no sólo desde `/settings/sections/:id`.

**Estado actual (verificado en código — radio de impacto del Coordinador):**
- **Modelo** `models/operational_methodology.py`: `section` (L29, `nullable=True,
  index=True`), `subsection` (L30), `notes` (L42) — a eliminar. `section_ids` (L40,
  JSONB) y `agent_profile_ids` (L36, JSONB) ya existen (feature 004). Docstring:
  "Not exposed on the public portal, admin-only."
- **Esquema** `schemas/career_methodologies.py`: `OperationalMethodologyBase/Create/
  Update/Response` con `section`/`subsection`/`notes`. Ya existe `_normalize_section_ids()`
  que valida `sec-N` contra `known_section_ids()` (004). `Response` NO valida
  `agent_profile_ids` a propósito.
- **CRUD genérico** `routes/career_methodologies.py` → `build_crud_router(...)` de
  `routes/career_common.py`; `register_resource("operational-methodologies",
  vectorize=True)` → el `PUT` genérico re-vectoriza **sólo** el registro tocado (upsert
  de su punto Qdrant), NO dispara `reindex_for_user` completo.
- **Editor del lado sección (se mantiene):** `PUT /bedrock/sections/{id}/methodologies`
  (`routes/bedrock.py:624`) → `section_catalog.set_section_methodologies` → por cada
  metodología `repo.update_for_user(..., {"section_ids": nxt})` + al final
  `repo.reindex_for_user(db, user_id)` (reindex **completo** del usuario).
- **`section` (texto libre) se consume en:** `routes/bedrock.py:588,605`
  (`GET /bedrock/sections/{id}` devuelve `methodologies:[{id,title,section}]`);
  `services/methodology_scope.py:107,122,191,209` (`select(...section)` → payload
  `"section": row.section` de `list_assigned_methodologies`); `services/bedrock_service.py:252`
  (parseo de prefijos `title:/section:/subsection:/description:/agent_profile_ids:`),
  `:267` (`"section": row.get("section")`); `services/bedrock/prompt.py:145`
  (`methodology_assignment_block` L1/L3 inyecta el label `[section]` en el system prompt);
  `services/bedrock/profile_catalog.py:40`; `repositories/career_repository.py:530-536`
  (payload Qdrant de metodologías: `section_ids`, `title`, `section` en L536);
  `services/bedrock/agent_profiles.py:275,281` (docstring del guardián L2
  `_METHODOLOGIES_SUFFIX` menciona `section, subsection, notes` y "llama
  create_career_record con fields.title, fields.section y fields.content").
- **`subsection`/`notes`:** uso mínimo — `bedrock_service.py:252` (parseo de prefijos),
  `agent_profiles.py:275` (docstring). NO están en el form del Admin hoy.
- **Admin** `config/careerResources.ts` `operationalMethodologiesConfig` (L1734-1770):
  `columns` = `title`, `section`, `subsection`, `agent_profile_ids` (`format:'agents'`);
  `fields` = `title` (text), `section` (`creatable-select`), `subsection`
  (`creatable-select`), `agent_profile_ids` (`multi-select`, `options` ESTÁTICAS vía
  `allAgentSelectOptions()`), `description` (textarea), `content` (textarea). `notes` y
  `section_ids` NO están expuestos hoy. `types/career.ts:600` tipa el recurso.
  `components/career/ResourceForm.tsx` ofrece `multi-select` (options estáticas),
  `fk-multi-select` (`fkResource`/`fkApi`), `creatable-select`.
  `components/career/careerFieldUtils.ts:131` define `format:'agents'` para celda.
- **Lado sección en el Admin (se mantiene):** `pages/AdminSectionsPage.tsx` →
  `SectionMethodologiesEditor` (llama `PUT /bedrock/sections/{id}/methodologies`).

**Límites / dependencias:**
- Servicio dueño: `cjhirashi-career-api` (modelo, esquema, CRUD genérico, Alembic,
  Qdrant, loop Bedrock).
- Frontend: `cjhirashi-career-admin` (config del recurso + celda + editor de sección).
- Fronteras externas: AWS Bedrock (system prompt L1/L3, guardián L2), Qdrant (payload de
  metodologías, `search_knowledge_base type=methodology`).
- **Admin-only.** El portal público (`cjhirashi-career-portfolio`) no consume este
  recurso y ningún flujo de generación/exportación de PDF lee `section`/`subsection`/
  `notes` de metodologías (confirmado con el operador 2026-09-09 → §2 Fuera de alcance).
- **Riesgo de anclaje:** specs **003 y 004** están `verified` + `anchor_mode: strict` y
  su `covers` incluye archivos que esta feature va a tocar (`methodology_scope.py`,
  `models/operational_methodology.py`, `schemas/career_methodologies.py`,
  `routes/bedrock.py`, `services/bedrock/prompt.py`, `services/bedrock_service.py`,
  `services/bedrock/profile_catalog.py`). La coordinación de `covers` / posible
  re-anchor la decide el arquitecto en Fase 2 (ver §6).

## 2 · Alcance

### En alcance
- **Eliminar** `section`, `subsection` y `notes` del modelo `operational_methodology.py`,
  de los esquemas `career_methodologies.py` (`Base/Create/Update/Response`), de la
  migración Alembic (`DROP COLUMN`), y del Admin (`fields` y `columns` de
  `operationalMethodologiesConfig`, tipo en `types/career.ts`).
- **`section_ids` pasa a ser la columna "Sección" del Admin:** multi-valuada, resuelta a
  labels de sección; **EDITABLE desde el formulario de la metodología** contra el
  catálogo de Secciones del Admin (`GET /admin/sections`).
- **Nuevo formato de celda** para la columna "Sección" (`sec-N` → label), análogo a
  `format:'agents'`: `format:'sections'` (tanda 2 · F), que **reusa el mismo
  endpoint/caché** (`GET /admin/sections`) que el campo del formulario — una sola carga
  del catálogo para formulario y tabla.
- **Nuevo tipo de campo del formulario** para `section_ids`: `fk-multi-select` con
  `fkApi: '/admin/sections'` (tanda 2 · F), que resuelve `sec-N` → label contra el
  catálogo de Secciones del Admin.
- **`agent_profile_ids` se conserva SIN cambios** — columna "Agentes"; la asignación de
  agentes L1/L3 se sigue haciendo aquí.
- `description` (breve) se muestra en la vista de detalle; `content` (Instrucciones,
  Markdown) sigue siendo obligatorio (`nullable=False`).
- **El editor del lado sección se mantiene:** `SectionMethodologiesEditor` /
  `PUT /bedrock/sections/{id}/methodologies` siguen operativos. Dos vistas del **mismo**
  dato (`operational_methodologies.section_ids`).
- Adaptar los consumidores de `section` (texto libre) al retirarlo, **cada uno con
  resolución cerrada** (tanda 2 · A–E, ver §3.9):
  - **system prompt L1/L3** — la regla `_METHODOLOGY_ASSIGNMENT_RULE` (`prompt.py:85`)
    mantiene la mención a "Agentes" y **añade** `section_ids` (Secciones del Admin a las
    que aplica); el catálogo por fila de L1/L3 (`prompt.py:145`) **sustituye** el
    `[section]` de texto libre por los **labels resueltos** de `section_ids` (coma;
    `section_ids` vacío → sin corchete).
  - **payload Qdrant** (`career_repository.py:536`) — quita `section`, añade `section_ids`
    (los `sec-N` **crudos**). Los extractos de `search_knowledge_base type=methodology`
    (003 RF-016) dejan de devolver `section` y devuelven `sections` (labels resueltos).
  - **`methodology_scope`** — quita `OperationalMethodology.section` de los `select` y el
    `"section"` del payload de `list_assigned_methodologies`, sin sustituto.
  - **`bedrock_service`** (`:252`) — retira los prefijos `section:` y `subsection:` del
    parseo, añade `section_ids:` (lista de `sec-N` por comas).
  - **guardián L2** (`agent_profiles.py:275-281`) — ya decidido (P2 / D-12).
  - **`GET /bedrock/sections/{id}`** y **`profile_catalog`** — quitan `section` sin
    sustituto (el `SectionMethodologiesEditor` no lo consume, verificado).
- **Nuevo formato de celda y nuevo tipo de campo del Admin** (tanda 2 · F, ver arriba).
- **Migración de datos** de las metodologías existentes (pérdida por `DROP` — decisión y
  descarte explícitos en §6).
- **Enmienda a ADR-027** (tanda 2 · G): no ADR nuevo. El arquitecto formaliza el texto en
  Fase 2 (§6 · D-13).

### Fuera de alcance
- Cambiar `agent_profile_ids` o el modelo de asignación de agentes L1/L3 (feature 003/004).
- Eliminar `PUT /bedrock/sections/{id}/methodologies` ni el `SectionMethodologiesEditor`
  (el lado sección se queda).
- Cualquier cambio en `cjhirashi-career-portfolio` / portal público (recurso admin-only).
- Crear / eliminar Secciones del Admin (código, ADR-021).
- Rediseñar la búsqueda semántica de metodologías (feature 003) más allá de quitar
  `section` de los extractos si se decide así.
- **Sin cambios en `cjhirashi-career-portfolio` / portal público** (recurso admin-only;
  P1, confirmado 2026-09-09).
- **Sin cambios en la generación/exportación de PDF**: ningún export lee
  `section`/`subsection`/`notes` de metodologías (P1).
- **Sin backfill ni mapeo automático** del texto libre de `section` a `sec-N`: arranque
  en frío aceptado — tras el deploy `section_ids` queda como estaba (vacío donde ya lo
  estaba) y el operador re-liga a mano desde la app (P6 / arranque en frío).
- No convertir `subsection`/`notes` en estructura anidada dentro de `section_ids` ni en
  campos nuevos: se eliminan sin sustituto (P6).

## 3 · Modelo de datos y contratos de E/S

### 3.1 Modelo `operational_methodologies` — resultado
| Se queda | Se elimina |
|---|---|
| `id`, `user_id`, `created_at`, `updated_at` (meta) | `section` — `String(150)`, `nullable=True`, `index=True` (L29) |
| `title` | `subsection` — `String(150)` (L30) |
| `description` — breve, se muestra en la vista de detalle | `notes` — `Text` (L42) |
| `content` — Instrucciones, Markdown, `nullable=False` | |
| `agent_profile_ids` — JSONB, sin cambios (columna "Agentes", L1/L3) | |
| `section_ids` — JSONB de `sec-N`, pasa a columna "Sección" editable desde el form | |

### 3.2 Migración Alembic
- `DROP COLUMN` de `section`, `subsection`, `notes` — idempotente (`IF EXISTS`), con
  **id de revisión nuevo garantizado único** (aviso de `memory/state.md`: el
  2026-09-08 la de 004 chocó con `a1b2c3d4e5f6`).
- **DECIDIDO (P6):** *drop simple sin backfill*. La migración **vuelca** el contenido de
  `section`, `subsection` y `notes` de todas las filas a un **respaldo persistente**
  (tabla o archivo) **antes** del `DROP` — sólo para rollback/auditoría, no se re-consume.
  **No hay backfill** de `section_ids` desde el texto de `section`.
- **DECIDIDO (P4 / P7):** tras aplicar la migración, el proceso de cierre ejecuta
  `POST /bedrock/knowledge-base/reindex` **completo** + `scripts/check_kb_consistency.py`
  (debe terminar EXIT 0). Nota operativa en el Session-End. El cambio toca el payload
  Qdrant de metodologías aunque no toque ids/`user_id`.

### 3.3 Esquema `career_methodologies.py`
- `OperationalMethodologyBase/Create/Update/Response` pierden `section`, `subsection`,
  `notes`. `_normalize_section_ids()` (valida `sec-N` contra `known_section_ids()`) se
  mantiene y pasa a ser la validación del campo editable.
- **DECIDIDO (P3):** los esquemas de metodología llevan `extra="forbid"` — un `POST`/
  `PUT` (humano o vía tool `create_career_record`/`update_career_record`) con `section`,
  `subsection` o `notes` responde **422** (cambio de contrato deliberado). Acepta
  `section_ids`. Errores en formato Problem Details (RFC 9457).

### 3.4 Form del Admin (`operationalMethodologiesConfig`)
- `fields` resultantes: `title` (text), `description` (textarea), `content` (textarea),
  `agent_profile_ids` (**sin cambios**, `multi-select` estático), `section_ids`
  (**nuevo**, `fk-multi-select` con `fkApi: '/admin/sections'` — §3.5).
- `columns` resultantes: `title`, `section_ids` (nueva columna "Sección",
  `format:'sections'` — §3.6), `agent_profile_ids` (`format:'agents'`).
- Se retiran los `fields`/`columns` `section` y `subsection`.

### 3.5 Tipo de campo para `section_ids` en el form — DECIDIDO (tanda 2 · F)
- `fk-multi-select` **nuevo** en `operationalMethodologiesConfig.fields`, con
  `fkApi: '/admin/sections'`. `ResourceForm` ya soporta `fk-multi-select` con `fkApi`; el
  catálogo de Secciones es dinámico y ya tiene endpoint → sin hook a medida.
- Contrato de entrada del endpoint: `GET /admin/sections` (existente, admin-only) →
  lista de secciones con `id` (`sec-N`) y label. La resolución `sec-N` → label es
  responsabilidad del campo/celda, no del backend.
- Descartado: `multi-select` alimentado por un hook nuevo (duplica maquinaria que
  `ResourceForm` ya tiene); opciones estáticas como `agent_profile_ids` (el catálogo de
  secciones cambia sin redeploy).

### 3.6 Formato de celda "Sección" en la tabla — DECIDIDO (tanda 2 · F)
- `format:'sections'` **nuevo** en `careerFieldUtils.ts`, análogo a `format:'agents'`:
  resuelve cada `sec-N` de `section_ids` → label de sección, separados por coma.
- **Misma fuente que el formulario:** el diccionario `sec-N` → label sale del **mismo
  endpoint/caché** (`GET /admin/sections`) que alimenta el `fk-multi-select` de §3.5 —
  una sola carga del catálogo para formulario y tabla (ver RNF-001).
- Un `sec-N` que ya no exista en el catálogo se **omite** del render (no se pinta
  "sección desconocida") — ver §5 y RF-030.

### 3.7 Efecto de re-indexación al editar `section_ids` desde el CRUD de la metodología — DECIDIDO (P4)
- Hoy: `PUT /bedrock/sections/{id}/methodologies` fuerza `reindex_for_user` **completo**;
  el `PUT /career/operational-methodologies/{id}` genérico re-vectoriza **sólo** ese
  registro.
- **DECIDIDO:** toda edición de `section_ids` (lado sección o lado metodología) pasa por
  **un único camino de dominio** (§3.8) que **garantiza un `reindex_for_user` completo**.
  A nivel requisito basta con eso; si ese camino se implementa como *hook post-update*
  del CRUD genérico para este `resource_key` o como *endpoint dedicado* lo decide el
  **arquitecto en Fase 2**.
- **Asunción a validar en Plan:** la resolución "qué metodologías ve un L2" (§`methodology_scope`)
  se hace **en runtime** a partir de `section_ids` + secciones del L2, **no** depende de
  precómputo del índice Qdrant; el reindex completo sólo mantiene coherentes los extractos
  de `search_knowledge_base`.

### 3.8 Coexistencia de dos editores del mismo dato — DECIDIDO (P5)
- `SectionMethodologiesEditor` (lado sección) y el nuevo campo (lado metodología)
  escriben ambos `operational_methodologies.section_ids`.
- **DECIDIDO:** se factoriza **una única función de dominio** que ambos caminos invocan:
  valida `sec-N` contra `known_section_ids()` → persiste `section_ids` → dispara el
  `reindex_for_user` completo (§3.7). `section_catalog.set_section_methodologies` se
  **refactoriza** para invocarla en vez de duplicar validación + reindex.
- **DECIDIDO:** concurrencia **last-write-wins**, sin bloqueo optimista. Documentado; la
  última escritura persistida gana.

### 3.9 Consumidores de `section` (texto libre) al retirarlo — DECIDIDO (tanda 2 · A–E)

Un renglón por frontera; el contrato previsto de cada una va en `contracts/`.

| Consumidor | Hoy | Resolución (tanda 2) | RF |
|---|---|---|---|
| `prompt.py:85` — regla `_METHODOLOGY_ASSIGNMENT_RULE` (L1/L3) | menciona "Agentes" (`agent_profile_ids`) | **A** · mantener "Agentes" + **añadir** frase: `section_ids` = Secciones del Admin a las que aplica la metodología | RF-025 |
| `prompt.py:145` — catálogo por fila del system prompt L1/L3 | inyecta ` [section]` (texto libre) | **B** · **sustituir** por los labels resueltos de `section_ids` (`sec-N`→nombre), separados por coma; `section_ids` vacío → **sin corchete** | RF-012 |
| `career_repository.py:530-536` — payload Qdrant de metodologías | `section_ids`, `title`, `section` | **C** · quitar `section`; **añadir `section_ids`** (los `sec-N` **crudos**, NO labels) | RF-013 |
| `search_knowledge_base type=methodology` — extractos (003 RF-016) | `record_id`, `title`, `section`, `excerpt`, `read_full` | **C** · `section` → **`sections`**: lista de **labels** resueltos de `section_ids` (p. ej. `["Búsqueda de empleo", …]`) | RF-024 |
| `methodology_scope.py:107,122,191,209` — `select(...section)` + `"section": row.section` en `list_assigned_methodologies` | expone `section` texto libre | **D** · quitar de los `select` y del dict; **sin sustituto** en ese payload | RF-014 |
| `bedrock_service.py:252` — parseo de prefijos `title:/section:/subsection:/description:/agent_profile_ids:` | acepta `section:` y `subsection:` | **E** · retirar `section:` y `subsection:`; **añadir `section_ids:`** (lista de `sec-N` por comas). El L2 usa esta vía textual **o** el `fields` estructurado de `create/update_career_record`; ambas válidas, ambas sujetas al **422** de campos retirados | RF-026 |
| `agent_profiles.py:275-281` — `_METHODOLOGIES_SUFFIX` (guardián L2) | menciona `section, subsection, notes` | **P2 / D-12** · reescrito: no menciona los 3 campos; el vínculo se expresa con `section_ids` (lista de `sec-N`); el L2 puede setearlo vía `create/update_career_record`; los 3 campos retirados → **422** | RF-015, RF-023 |
| `routes/bedrock.py:588,605` — `GET /bedrock/sections/{id}` → `methodologies:[{id,title,section}]` | array con `section` | **D-style** · a `[{id,title}]` (drop `section`). Verificado: `SectionMethodologiesEditor` sólo usa `id`/`title` → sin regresión | RF-016 |
| `profile_catalog.py:40` — `_methodology_entries` → `"section": row.section` | dict con `section` | **D-style** · quitar `"section"` del dict; sin sustituto | RF-014 |

**Asunción a validar en Plan (no bloquea Gate 1):** si el arquitecto descubre en Fase 2
un consumidor del `"section"` retirado de `methodology_scope` / `profile_catalog` /
`GET /bedrock/sections/{id}` que **muestra ese valor a un usuario**, se adapta a los
**labels resueltos de `section_ids`** (mismo criterio que **B**). Con la evidencia de
código actual (§1) no existe tal consumidor.

## 4 · Criterios de aceptación (EARS)

- **RF-001** — La migración Alembic DEBE eliminar las columnas `section`, `subsection` y
  `notes` de `operational_methodologies` de forma idempotente, con un id de revisión no
  reutilizado.
- **RF-002** — El sistema NO DEBE exponer `section`, `subsection` ni `notes` en los
  esquemas `OperationalMethodologyBase`, `Create`, `Update` ni `Response`.
- **RF-003** — SI un `POST` o `PUT` a `/career/operational-methodologies` (humano o vía
  tool `create_career_record`/`update_career_record`) incluye `section`, `subsection` o
  `notes`, el sistema DEBE responder `422` con Problem Details (RFC 9457) y no persistir
  el registro.
- **RF-004** — El formulario del recurso `operational-methodologies` del Admin NO DEBE
  mostrar los campos `section` ni `subsection`.
- **RF-005** — El formulario del recurso `operational-methodologies` del Admin DEBE
  permitir editar `section_ids` como campo multi-valuado cuyas opciones provienen del
  catálogo de Secciones del Admin (`GET /admin/sections`).
- **RF-006** — CUANDO se guarde el formulario de una metodología con `section_ids`, el
  sistema DEBE persistir exactamente esa lista de `sec-N` en
  `operational_methodologies.section_ids`, validada contra `known_section_ids()`.
- **RF-007** — SI `section_ids` contiene un `sec-N` que no existe en el catálogo, el
  sistema DEBE responder con error de validación (RFC 9457) y no persistir nada.
- **RF-008** — La tabla del recurso `operational-methodologies` del Admin DEBE mostrar una
  columna "Sección" que renderiza los `section_ids` de cada fila como labels de sección.
- **RF-009** — El sistema DEBE conservar `agent_profile_ids` y su columna "Agentes" sin
  cambios de comportamiento respecto a la feature 004.
- **RF-010** — El endpoint `PUT /bedrock/sections/{section_id}/methodologies` y el
  `SectionMethodologiesEditor` DEBEN seguir editando el mismo dato
  (`operational_methodologies.section_ids`) sin regresión respecto a la feature 004.
- **RF-011** — CUANDO se modifique `section_ids` de una metodología por cualquiera de los
  dos caminos de edición (lado sección o lado metodología), el sistema DEBE ejecutar un
  `reindex_for_user` completo del índice de conocimiento del usuario, no sólo la
  re-vectorización del registro tocado.
- **RF-012** — CUANDO el sistema construya el catálogo de metodologías del system prompt
  de un agente L1 o L3, DEBE renderizar, por cada metodología con `section_ids` no vacío,
  los labels de sección resueltos de esos `sec-N` separados por coma entre corchetes, y
  DEBE omitir el corchete cuando `section_ids` esté vacío (ya no se usa el texto libre
  `section`).
- **RF-013** — El payload Qdrant de cada metodología DEBE incluir `section_ids` (la lista
  de `sec-N` cruda, sin resolver a label) y NO DEBE incluir el campo `section`.
- **RF-014** — El sistema NO DEBE seleccionar ni exponer `OperationalMethodology.section`
  en `services/methodology_scope.py` (ni en el payload de `list_assigned_methodologies`)
  ni en `services/bedrock/profile_catalog.py`, sin regresión observable en
  `applies_to_caller`, `resolve_*` ni `list_assigned_methodologies`.
- **RF-015** — El texto del guardián L2 (`_METHODOLOGIES_SUFFIX` en
  `services/bedrock/agent_profiles.py`) NO DEBE mencionar `section`, `subsection` ni
  `notes` como campos de `operational-methodologies`.
- **RF-016** — El endpoint `GET /bedrock/sections/{section_id}` DEBE devolver cada
  elemento del array `methodologies` con la forma `{id, title}`, sin el campo `section`.
- **RF-017** — La migración Alembic DEBE volcar el contenido de `section`, `subsection` y
  `notes` de todas las filas de `operational_methodologies` a un respaldo persistente
  (tabla o archivo) antes de ejecutar el `DROP COLUMN`.
- **RF-018** — El sistema DEBE editar `section_ids` (por el camino lado sección y por el
  camino lado metodología) a través de una única función de dominio que valida los
  `sec-N` contra `known_section_ids()`, persiste la lista y dispara el `reindex_for_user`
  completo.
- **RF-019** — El sistema NO DEBE ejecutar backfill automático de `section_ids` a partir
  del texto de `section`; tras el despliegue de la migración, `section_ids` de cada fila
  conserva exactamente su valor previo.
- **RF-020** — El sistema NO DEBE requerir cambios en `cjhirashi-career-portfolio` ni en
  ningún flujo de generación/exportación de PDF para funcionar tras esta feature.
- **RF-021** — CUANDO dos ediciones de `section_ids` de la misma metodología se apliquen
  en secuencia, el sistema DEBE conservar el resultado de la última escritura persistida
  (last-write-wins), sin bloqueo optimista ni error de conflicto.
- **RF-022** — CUANDO se aplique la migración de esta feature, el proceso de cierre DEBE
  ejecutar `POST /bedrock/knowledge-base/reindex` y `scripts/check_kb_consistency.py`, y
  este último DEBE terminar con EXIT 0.
- **RF-023** — El texto del guardián L2 (`_METHODOLOGIES_SUFFIX`) DEBE indicar que el
  vínculo de una metodología con secciones se expresa con `section_ids` (lista de
  `sec-N`) y que el agente L2 puede establecerlo vía
  `create_career_record`/`update_career_record`.
- **RF-024** — CUANDO `search_knowledge_base` con `type=methodology` devuelva extractos
  de metodología, cada extracto DEBE incluir `sections` (la lista de labels de sección
  resueltos de `section_ids`) y NO DEBE incluir el campo `section`.
- **RF-025** — La regla `_METHODOLOGY_ASSIGNMENT_RULE` del system prompt (L1/L3) DEBE
  mencionar `section_ids` como las Secciones del Admin a las que aplica la metodología,
  conservando la mención existente a `agent_profile_ids` ("Agentes").
- **RF-026** — El parseo de prefijos de `services/bedrock_service.py` para
  `operational-methodologies` NO DEBE reconocer los prefijos `section:` ni `subsection:`,
  y DEBE reconocer el prefijo `section_ids:` con una lista de `sec-N` separada por comas.
- **RF-027** — La función de dominio de RF-018 DEBE deduplicar los `sec-N` repetidos de
  `section_ids` antes de persistir, sin devolver error.
- **RF-028** — El sistema NO DEBE imponer un límite superior al número de `sec-N` por
  metodología; la única validación de `section_ids` es que sea un subconjunto de
  `known_section_ids()`.
- **RF-029** — La edición de `section_ids` desde el CRUD del recurso
  `operational-methodologies` (lado metodología) DEBE exigir el mismo permiso que el
  resto de operaciones de escritura de ese recurso, sin introducir un permiso nuevo.
- **RF-030** — SI `section_ids` contiene un `sec-N` que ya no existe en el catálogo de
  Secciones en código, ENTONCES el sistema DEBE ignorarlo en la resolución de scope, en
  la celda de la tabla del Admin y en el label del system prompt, sin renderizar texto de
  "sección desconocida" y sin error.
- **RF-031** — SI Qdrant no está disponible cuando se persiste `section_ids`, ENTONCES el
  sistema DEBE completar la escritura en PostgreSQL y tratar la re-indexación como
  best-effort, sin propagar el fallo al cliente (reutiliza el contrato de 003 RF-014).

## 5 · Casos límite y manejo de errores

- Metodología cuyo `section_ids` referencia un `sec-N` retirado del catálogo en código →
  **se ignora en runtime** (mismo criterio que 004); la celda de la tabla y el label del
  system prompt **omiten** ese id, sin pintar "sección desconocida" (RF-030).
- `sec-N` presente en el payload Qdrant de una metodología pero inexistente en el catálogo
  → **ignorado en runtime** al resolver labels o scope (RF-030).
- `section_ids` recibido con `sec-N` duplicados → la función de dominio única
  **deduplica** sin error antes de persistir (RF-027).
- Guardar una metodología con `section_ids = []` (ninguna sección) **y** sin
  `agent_profile_ids` → queda **compartida por todos** (semántica de 004, se mantiene);
  con `agent_profile_ids` sigue ligada a esos agentes L1/L3.
- Edición simultánea de la misma metodología desde el lado sección y desde el lado
  metodología → **last-write-wins** (P5, RF-021); sin locking, sin error de conflicto.
- `PUT` de `section_ids` con Qdrant caído → el write a PG **no falla**; la re-indexación
  es best-effort (contrato de `CareerRepository`, reutiliza 003 RF-014) — RF-031.
- Migración corrida dos veces → idempotente (`DROP COLUMN IF EXISTS`).
- Cliente viejo del Admin que aún envía `section`/`subsection` tras el deploy → RF-003
  (422).
- Portal público / export que lea `section` y se rompa → **no aplica** (P1: recurso
  admin-only, ningún export lo consume — RF-020).
- Arranque en frío tras el deploy: `section_ids` queda como estaba (vacío en la mayoría);
  el operador re-liga a mano desde la app. Sin mapeo automático (P6, RF-019).

## 6 · Registro de decisiones y descartes

| # | Decisión | Porqué | Descartado |
|---|---|---|---|
| D-1 | Eliminar `section`, `subsection`, `notes` del modelo de metodología | Texto libre que duplica y compite con el catálogo real de Secciones del Admin; `subsection`/`notes` sin uso real; el operador quiere "sólo lo esencial" | Conservarlos "por si acaso"; convertir `section` en un enum |
| D-2 | El vínculo con Secciones se representa con `section_ids` (ya existente, 004) y se hace **editable desde el form de la metodología** | El operador quiere editar el vínculo desde ambos lados; `section_ids` ya es el dato canónico (004) | Un campo de texto nuevo; una tabla join nueva |
| D-3 | `agent_profile_ids` se conserva **sin cambios** | La asignación de agentes L1/L3 a metodologías (003/004) es ortogonal a este cambio | Refactorizar también la asignación de agentes en esta feature |
| D-4 | El editor del lado sección (`PUT /bedrock/sections/{id}/methodologies`) **se mantiene** | 004 lo definió y está `verified`; esto amplía, no reemplaza | Migrar toda la edición al lado metodología y borrar el endpoint |
| D-5 | Fase 0 (rúbrica §2): **CARRIL SDD** | `DROP COLUMN` ×3; `section` se consume en el AI service y `methodology_scope.py`; traer la edición de `section_ids` al CRUD **revisa** una decisión de 004 (ADR-027); toca `covers` de 003 y 004 (`verified` + `strict`) | Prompt directo "porque es un cambio de esquema pequeño" |
| D-6 (P6) | Migración = *drop simple sin backfill*, pero **vuelca `section`/`subsection`/`notes` a un respaldo persistente antes del `DROP`** (rollback/auditoría). Arranque en frío aceptado: el operador re-liga `section_ids` a mano | El operador quiere "sólo lo esencial" y no confía en un mapeo automático texto→`sec-N` | Pérdida tal cual sin respaldo; **backfill** de `section_ids` desde el texto de `section` (heurística frágil, falsos positivos) |
| D-7 (tanda 2 · A+B) | **A:** la regla `_METHODOLOGY_ASSIGNMENT_RULE` (`prompt.py:85`) mantiene la mención a "Agentes" y **añade** una frase: `section_ids` = Secciones del Admin a las que aplica. **B:** el catálogo por fila de L1/L3 (`prompt.py:145`) **sustituye** el `[section]` de texto libre por los **labels resueltos** de `section_ids` (coma; vacío → sin corchete) | El agente debe seguir viendo la procedencia por sección, ahora desde el dato canónico; texto libre daba pistas obsoletas | Eliminar el corchete sin sustituto (el agente pierde la pista de sección); dejar el texto libre |
| D-8 (tanda 2 · C) | Payload Qdrant: quitar `section`, **añadir `section_ids`** (los `sec-N` **crudos**). Extractos de `search_knowledge_base type=methodology` (003 RF-016): `section` → **`sections`** (lista de **labels** resueltos) | El payload guarda el dato canónico crudo; el extracto que lee el agente muestra labels legibles. El reindex completo tras migración ya está decidido (D-18) | Mantener `section` texto libre en el payload; devolver `sec-N` crudos en el extracto (ilegibles para el agente) |
| D-9 (P4, parcial) | Toda edición de `section_ids` pasa por **un único camino de dominio** que **garantiza `reindex_for_user` completo** | Un solo punto de validación + reindex evita índices stale (lección de 003 Bloque F) | Re-vectorizar sólo el registro tocado (deja el índice incoherente para el resto). *Abierto para el arquitecto (Fase 2): hook post-update del CRUD genérico vs. endpoint dedicado* |
| D-10 (P5) | **Una función de dominio única** compartida por los dos editores (valida `sec-N` + persiste + reindex); `set_section_methodologies` se refactoriza para invocarla. Concurrencia **last-write-wins**, sin locking | No duplicar validación+reindex; la app es de un solo operador, el coste de optimistic locking no se justifica | Lógica duplicada en cada editor; control de versión / optimistic locking |
| D-11 (tanda 2 · F) | Campo del form = `fk-multi-select` **nuevo** con `fkApi: '/admin/sections'`; celda de tabla = `format:'sections'` **nuevo** que **reusa el mismo endpoint/caché**. Una sola carga del catálogo para form y tabla (RNF-001) | El catálogo de Secciones es dinámico y ya tiene endpoint; `ResourceForm` ya soporta `fk-multi-select`/`fkApi` → sin hook a medida; una fuente única evita N llamadas por fila | `multi-select` con hook nuevo (duplica maquinaria de `ResourceForm`); opciones estáticas como `agent_profile_ids` (no refleja altas/bajas de secciones sin redeploy) |
| D-12 (P2) | El CRUD (PUT humano y tool `create/update_career_record`) **rechaza** `section`/`subsection`/`notes`; el docstring del guardián L2 se reescribe para usar `section_ids`; el agente L2 **sí puede** setear `section_ids` | Contrato limpio: un solo modelo de datos, sin campos zombis que el agente rellene por inercia | Aceptar e ignorar silenciosamente los 3 campos (el agente nunca aprende que desaparecieron) |
| D-13 (tanda 2 · G) | **Enmienda a `docs/09-DECISIONS/027-herramientas-metodologias-por-seccion.md`** (no ADR nuevo). Texto: 004 fijó "el vínculo sección↔metodología se edita desde la sección"; 005 amplía a "también desde la metodología, vía una función de dominio única compartida por ambos editores". `spec.md` front-matter: `revisa_adr: [ADR-027]`. El arquitecto formaliza la redacción en Fase 2 | Amplía sin contradecir la decisión de 004 → una enmienda es más fiel a la historia que un ADR que la "supere" | ADR nuevo (fragmenta el rationale sección↔metodología en dos documentos) |
| D-14 (→ Fase 2, no bloquea Gate 1) | Coordinación de `covers` con specs 003 y 004 (`verified` + `strict`) | Esta feature toca archivos que esas specs poseen; fijar `covers` es competencia del arquitecto en Fase 2 (`method.md §3`) | Opciones para Fase 2: ceder `covers`, re-anchor de 003/004, o co-propiedad — decisión del arquitecto, no de la spec |
| D-15 (P1) | **Fuera de alcance:** `cjhirashi-career-portfolio` y toda generación/exportación de PDF — no consumen `section`/`subsection`/`notes` de metodologías | Recurso admin-only; verificado que ningún export lo lee | — |
| D-16 (P3) | Campos desconocidos en los esquemas de metodología → **422** (`extra="forbid"` en Pydantic) | Cambio de contrato deliberado; un cliente que manda campos retirados debe enterarse, no que se los traguen | Ignorado silencioso (comportamiento por defecto del CRUD genérico hoy) |
| D-17 (P7) | Paso de cierre explícito: `POST /bedrock/knowledge-base/reindex` + `scripts/check_kb_consistency.py` (EXIT 0). Nota operativa en el Session-End | El payload Qdrant de metodologías cambia; sin reindex los extractos de `search_knowledge_base` quedan stale (lección de 003) | Confiar en la re-vectorización incremental por registro |
| D-18 (P4) | Reindex **completo** (`reindex_for_user`) en el cierre de toda edición de `section_ids`, por cualquiera de los dos caminos | Coherencia garantizada del índice; la resolución L2↔metodología es runtime, el reindex sólo mantiene los extractos | Reindex parcial / best-effort por registro |
| D-19 (tanda 2 · D) | `methodology_scope.py` y `profile_catalog.py` quitan `OperationalMethodology.section` de los `select` y `"section"` de sus dicts, **sin sustituto**. `GET /bedrock/sections/{id}` → `methodologies:[{id,title}]`. **Asunción a validar en Plan:** si aparece un consumidor que muestra ese valor a un usuario, se adapta a labels de `section_ids` | Con la evidencia de código actual ningún consumidor renderiza ese `section` a un humano (el `SectionMethodologiesEditor` sólo usa `id`/`title`) → retiro limpio | Sustituir preventivamente por labels en payloads que nadie muestra (trabajo muerto) |
| D-20 (tanda 2 · E) | `bedrock_service.py:252`: retirar prefijos `section:`/`subsection:`, **añadir `section_ids:`** (lista de `sec-N` por comas). El L2 puede usar la vía textual **o** el `fields` estructurado de `create/update_career_record`; ambas sujetas al 422 de los campos retirados | El agente L2 sigue teniendo una vía textual para el dato canónico; el 422 le enseña que los 3 campos ya no existen | Sólo `fields` estructurado (rompe la vía textual que el guardián ya usa); aceptar `section:` e ignorarlo |
| D-21 (tanda 2 · I) | **Sin tope** de secciones por metodología (validación = subconjunto de `known_section_ids()`). Editar `section_ids` desde la metodología usa **el mismo permiso** que el resto del CRUD de `operational-methodologies`; **sin permiso nuevo** | App de un solo operador; un tope sería arbitrario. Reusar el permiso del CRUD evita superficie de autorización nueva | Límite superior fijo; permiso dedicado para el vínculo sección↔metodología |
| D-22 (tanda 2 · H) | La función de dominio única **deduplica** `section_ids` sin error. Un `sec-N` retirado del catálogo se **ignora en runtime** y se **omite** del render (celda, label), nunca "sección desconocida" | Entrada tolerante, salida limpia; mismo criterio de 004 para ids obsoletos | Rechazar la escritura por duplicados; pintar un placeholder "sección desconocida" (ruido para el operador) |

## 7 · Requisitos no funcionales

- **RNF-001** — La resolución de labels de sección en el formulario y en la celda de la
  tabla del recurso `operational-methodologies` del Admin DEBE servirse de una única
  fuente compartida (el endpoint/caché de `GET /admin/sections`), con como máximo una
  carga del catálogo por render de la vista, no una llamada por fila.
- **RNF-002** — El cambio NO DEBE introducir regresión en `applies_to_caller`,
  `resolve_*` ni `list_assigned_methodologies` (`services/methodology_scope.py`),
  verificado con los tests existentes de 003/004 más los nuevos.
- **RNF-003** — Ninguna llamada real a Bedrock en tests (Constitución Art. 5); todo
  mockeado.
