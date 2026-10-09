---
titulo: "Plan — Metodologías Operativas: esquema mínimo y vínculo con Secciones editable desde la metodología"
tipo: plan
estado: draft
fecha: 2026-09-09
feature_id: "005"
spec: ./spec.md
---

# Plan de implementación (patrón por capas — Constitución Art. 1/2)

## 0 · Enfoque

Un solo dueño de backend (`cjhirashi-career-api`: modelo, esquema, CRUD genérico,
Alembic, Qdrant, loop Bedrock) + `cjhirashi-career-admin` (config del recurso, celda,
campo de formulario). El portal público y el render de PDF **no se tocan** (RF-020).

El cambio es **reductivo** en el modelo (`DROP` de `section`/`subsection`/`notes`) y
**aditivo** en la superficie de edición (`section_ids` pasa a ser editable desde el
formulario de la metodología). Todo consumidor del `section` de texto libre se adapta
según la resolución cerrada en `spec.md §3.9` (una fila = un `RF-`).

Piezas ya existentes que se reutilizan:

- `schemas.career_methodologies._normalize_section_ids()` — valida `sec-N ⊆
  known_section_ids()`, deduplica, descarta vacíos. **Es** la validación compartida de
  `section_ids` (RF-006/007/027/028); ya la usan `Create` y `Update`.
- `services.admin_sections.known_section_ids()` / `get_section_spec(sec_id).label` —
  catálogo de Secciones en código (feature 004); resolución `sec-N → label`.
- `services.methodology_scope.set_agent_methodologies()` — precedente de "persistir un
  campo JSONB de metodología + `reindex_for_user` completo"; la función de dominio de
  `section_ids` (RF-018) vive **al lado**, mismo patrón.
- `repositories.career_repository.CareerRepository.reindex_for_user()` — reindex
  completo del usuario; `_index_for_search()` best-effort (003 RF-014) → RF-031.
- `routes.career_common.build_crud_router(..., after_write=...)` + `register_resource()`
  + `RESOURCE_VECTORIZE` — punto de enganche del hook post-update (RF-011).
- `services.bedrock_service._invalid_fields_error()` — rechaza nombres de columna
  inexistentes en el path de tools L2; tras el `DROP` rechaza `section`/`subsection`/
  `notes` sin código nuevo (RF-003, path tool).
- Admin: `ResourceForm` ya soporta `fk-multi-select` con `fkApi`; `useFkOptions` ya
  cachea catálogos FK con React Query; `formatCellValue` ya tiene el patrón
  `format:'agents'` (a imitar con `format:'sections'`).
- `SectionMethodologiesEditor` / `PUT /bedrock/sections/{id}/methodologies` (004) —
  se mantienen; sólo se refactoriza su capa de servicio (RF-010/018).

---

## 1 · Los dos puntos que Gate 1 delegó a Fase 2

### 1.1 · Coordinación de `covers` / anchor con specs 003 y 004 (`verified` + `strict`)

**Regla de la compuerta (`gate/check.sh` bloque 3):** para una spec `strict`, si un
archivo de su `covers` cambió desde su `anchor_commit` **y su `spec.md` no cambió** →
la compuerta **cierra**. Si cambiaron **ambos** (covers y spec) → **OK** con aviso
"mover `anchor_commit` al cerrar". Overlap de `covers` entre specs **no** está
prohibido.

**Decisión: co-propiedad + re-anchor coordinado en el Session-End de 005.** No se
"cede" (quitar de 003/004) ningún archivo: las tablas de cobertura de `003/tasks.md`
y `004/tasks.md` referencian tests que viven en esos archivos; quitarlos abriría un
hueco de trazabilidad en specs ya `verified`. En su lugar, 005 **co-lista** cada
archivo compartido y, al cerrar, se mueve el ancla de 003 y 004 con una nota fechada
en su `spec.md`.

**Clasificación archivo por archivo** (S = compartido con esa spec; acción = trato en 005):

| Archivo | En `covers` de | Qué toca 005 | Trato |
|---|---|---|---|
| `src/models/operational_methodology.py` | 004 | `DROP` de 3 columnas (conserva `section_ids`) | **re-anchor 004**; 005 co-lista |
| `src/schemas/career_methodologies.py` | 004 | quita 3 campos de `Base/Create/Update/Response`; `extra="forbid"` | **re-anchor 004**; 005 co-lista |
| `src/schemas/bedrock.py` | 003, 004 | `BedrockSectionDetail.methodologies` → `{id,title}` (quita `section`) | **re-anchor 003+004**; 005 co-lista |
| `src/routes/bedrock.py` | 003, 004 | `_section_detail`: quita `.section` del `select` y del dict | **re-anchor 003+004**; 005 co-lista |
| `src/routes/career_common.py` | 003 | hook post-update por `resource_key` (RF-011) | **re-anchor 003**; 005 co-lista |
| `src/services/methodology_scope.py` | 003, 004 | quita `.section` de `select`/dict; nueva fn de dominio `section_ids` | **re-anchor 003+004**; 005 co-lista |
| `src/services/section_catalog.py` | 004 | `set_section_methodologies` delega persist+reindex en la fn de dominio | **re-anchor 004**; 005 co-lista |
| `src/services/bedrock_service.py` | 003, 004 | `_methodology_snippet`: prefijos + `section`→`sections` (labels) | **re-anchor 003+004**; 005 co-lista |
| `src/services/bedrock/prompt.py` | 003, 004 | `_METHODOLOGY_ASSIGNMENT_RULE` + labels por fila desde `section_ids` | **re-anchor 003+004**; 005 co-lista |
| `src/services/bedrock/profile_catalog.py` | 003 | `_methodology_entries`: quita `"section"` del dict | **re-anchor 003**; 005 co-lista |
| `src/services/bedrock/agent_profiles.py` | 003 | reescribe `_METHODOLOGIES_SUFFIX` | **re-anchor 003**; 005 co-lista |
| `src/services/bedrock/tools.py` | 003, 004 | path tool L2: enruta `fields.section_ids` por la fn de dominio | **re-anchor 003+004**; 005 co-lista |
| `src/repositories/career_repository.py` | 003 | `_index_for_search`: payload Qdrant `section`→`section_ids` crudo | **re-anchor 003**; 005 co-lista |
| `tests/unit/test_methodology_scope.py` | 003, 004 | ajusta aserciones (sin `section`) + casos nuevos | **re-anchor 003+004**; 005 co-lista |
| `tests/unit/test_section_methodologies.py` | 004 | ajusta a la fn de dominio | **re-anchor 004**; 005 co-lista |
| `tests/unit/bedrock/test_prompt_methodology.py` | 003, 004 | labels desde `section_ids` | **re-anchor 003+004**; 005 co-lista |
| `tests/unit/bedrock/test_methodology_snippets.py` | 003, 004 | `sections` (labels) en el extracto | **re-anchor 003+004**; 005 co-lista |
| `src/services/README.md`, `docs/BEDROCK-SYSTEM.md`, `docs/09-DECISIONS/027-*.md`, `cjhirashi-career-api/docs/sections/bedrock/README.md` | 003 y/o 004 | actualización de doc (Art. 11, §8) | **re-anchor** de la(s) spec(s) que lo listen; 005 co-lista |
| `src/services/qdrant_service.py`, `scripts/check_kb_consistency.py`, `src/services/bedrock/agent_loop.py`, `src/services/bedrock/profile_tools.py`, `src/services/admin_sections.py` | 003 y/o 004 | **005 no los edita** (sólo ejecuta `check_kb_consistency.py`) | sin acción; **no** entran en `covers` de 005 |

**Instrucciones concretas para el Session-End de 005** (las ejecuta el Coordinador):

1. Cerrar 005: commit `C` con todos los `RF-`; `gate/check.sh` verde para 005.
2. Para `spec 003` y `spec 004`, en su `spec.md`:
   - añadir una línea fechada en su sección de historial/decisiones:
     `> [2026-…] Feature 005 (esquema mínimo de metodologías) modificó <archivos>;
     sin cambio del contrato de esta spec salvo: metodologías ya no llevan `section`
     de texto libre — el catálogo/extractos usan labels de `section_ids`. Ancla
     movida a <C>.`
   - poner `anchor_commit: C`.
   - dejar `anchor_mode: strict` (no cambia).
3. Volver a correr `gate/check.sh`: el bloque 3 debe mostrar 003 y 004 como
   "covers y spec cambiaron — ok" (no como error de drift).
4. Registrar en el Session-End de `history.md` (`Drift / re-anchor: sí (003, 004)` ·
   `Anclas movidas: 003 → C, 004 → C, 005 → C`).

### 1.2 · Camino único de dominio para `section_ids` (RF-011 / RF-018)

**Recomendación: hook post-update en el CRUD genérico**, acotado a
`resource_key == "operational-methodologies"` y disparado por la presencia del campo
`section_ids` en el payload. **No** endpoint dedicado.

**Por qué el hook y no `PUT .../{id}/sections`:**

- RF-005/RF-006 exigen que **el guardado del formulario** (un solo `PUT
  /career/operational-methodologies/{id}` que emite `ResourceForm` con todos los
  campos) persista `section_ids`. Un endpoint aparte obliga a partir el submit del
  formulario en dos llamadas y a un camino especial en `ResourceForm`/`CareerResourceView`
  — rompe "una sola ruta de escritura humana" y añade estados de fallo parcial en UI.
- El hook mantiene **una** ruta de escritura por lado: `PUT` humano gana el efecto
  reindex; el lado sección sigue por `PUT /bedrock/sections/{id}/methodologies`.

**Contrapartida del hook y su mitigación:** toca `career_common.py` (cubierto por 003).
Se mitiga siendo **data-driven**, no `if` hardcodeado: un mapa
`RESOURCE_REINDEX_ON_FIELDS: dict[str, set[str]]` poblado junto a `RESOURCE_VECTORIZE`
(vía `register_resource(..., reindex_on_fields={"section_ids"})` o registro explícito en
`career_methodologies.py`). En `create_item`/`update_item`, tras el write:
`if set(data) & RESOURCE_REINDEX_ON_FIELDS.get(resource_key, set()): await
methodology_scope.reindex_user_methodologies(db, current_user.id)`.

**La función de dominio única — dónde vive:** `services/methodology_scope.py` (junto a
`set_agent_methodologies`, mismo patrón persist+reindex; `section_catalog.py` es
"catálogo de secciones del Admin", peor encaje). Expone:

```
# services/methodology_scope.py
async def reindex_user_methodologies(db, user_id) -> int
    # primitiva única de reindex: CareerRepository(OperationalMethodology,
    # resource_key="operational-methodologies", vectorize=True).reindex_for_user(db, user_id)
    # best-effort respecto a Qdrant (RF-031): el reindex ya no propaga fallo de indexado.

async def set_methodology_section_ids(db, user_id, methodology_id, raw_section_ids) -> list[str] | None
    # 1. cleaned = _normalize_section_ids(raw_section_ids)   # ⊆ known_section_ids(), dedup, sin tope  (RF-006/7/27/28)
    # 2. obj = await repo.update_for_user(db, user_id, methodology_id, {"section_ids": cleaned})
    #    -> None  => devuelve None (upstream: 404)
    # 3. await reindex_user_methodologies(db, user_id)        # reindex COMPLETO (RF-011/18)
    # 4. return cleaned
```

**Los tres caminos convergen en las dos primitivas compartidas** (`_normalize_section_ids`
para validar + `reindex_user_methodologies` para reindexar), sin duplicar lógica:

| Camino | Entrada | Cómo usa el camino único |
|---|---|---|
| Lado metodología — `PUT /career/operational-methodologies/{id}` (humano) | body con `section_ids` | `OperationalMethodologyUpdate` valida vía `_normalize_section_ids`; el repo persiste; el **hook post-update** llama `reindex_user_methodologies` |
| Lado sección — `PUT /bedrock/sections/{id}/methodologies` | `{methodology_ids}` | `section_catalog.set_section_methodologies` calcula el delta por fila, persiste cada `section_ids` (valores ya ⊆ known: `current ∪ {section_id}` con `section_id` validado contra `known_section_ids()`), y al final delega el reindex en `reindex_user_methodologies` (hoy hace su propio `repo.reindex_for_user`) |
| Lado tool L2 — `create/update_career_record` sobre `operational-methodologies` | `fields.section_ids` | `bedrock_service` enruta: si `fields` trae `section_ids`, tras el write llama `reindex_user_methodologies` (la validación de nombres de campo la hace `_invalid_fields_error`; la de `sec-N` ⊆ known se añade explícita reusando `_normalize_section_ids`, devolviendo `{"error": ...}` al agente si falla — RF-003/007 en el path tool) |

`section_catalog.set_section_methodologies` **se refactoriza** para (a) importar y usar
`reindex_user_methodologies` en vez del `repo.reindex_for_user` inline, y (b) mantener
el guard `section_id not in known_section_ids()` (ya presente). Concurrencia:
**last-write-wins**, sin bloqueo optimista (RF-021) — no se añade `version`/`If-Match`.

---

## 2 · Fronteras y archivos por capa

| Capa | Archivo | Cambio |
|---|---|---|
| Modelo | `src/models/operational_methodology.py` | quita `section` (L29), `subsection` (L30), `notes` (L42) y su docstring; conserva `title`, `description`, `content`, `agent_profile_ids`, `section_ids`, meta |
| Migración | `alembic/versions/<rev>_methodology_drop_section_freeform.py` (**nuevo**) | `down_revision = "b3d4e5f6a7c8"` (head actual); id de revisión **nuevo garantizado único** (verificar contra `alembic/versions/` antes de crear — aviso `state.md` 2026-09-08). `upgrade`: (1) `CREATE TABLE IF NOT EXISTS operational_methodologies_freeform_backup (id text, user_id text, section text, subsection text, notes text, backed_up_at timestamptz default now())`; (2) `INSERT ... SELECT id,user_id,section,subsection,notes FROM operational_methodologies` (volcado, RF-017); (3) `DROP INDEX IF EXISTS` del índice de `section`; (4) `ALTER TABLE ... DROP COLUMN IF EXISTS section / subsection / notes`. **Sin backfill** de `section_ids` (RF-019). `downgrade`: `ADD COLUMN` + `INSERT ... SELECT` de la tabla de respaldo (documenta que sólo restaura filas respaldadas) |
| Esquema dominio | `src/schemas/career_methodologies.py` | `OperationalMethodologyBase` pierde `section`/`subsection`/`notes`; `OperationalMethodologyUpdate` idem; **`model_config = ConfigDict(extra="forbid")`** en `Base` y `Update` (→ `Create`/`Response` heredan) — `Response` mantiene el comentario de por qué no valida ids. `_normalize_section_ids` intacta (validación compartida) |
| CRUD genérico | `src/routes/career_common.py` | `RESOURCE_REINDEX_ON_FIELDS` (mapa) + parámetro `reindex_on_fields` en `build_crud_router`/`register_resource`; en `create_item`/`update_item`, tras write exitoso, si `set(data) & RESOURCE_REINDEX_ON_FIELDS.get(resource_key)` → `await methodology_scope.reindex_user_methodologies(db, current_user.id)` |
| Ruta recurso | `src/routes/career_methodologies.py` | pasa `reindex_on_fields={"section_ids"}` al `build_crud_router` |
| Servicio dominio | `src/services/methodology_scope.py` | **quita** `OperationalMethodology.section` de los `select` de `list_methodologies_for_catalog` (L107) y `list_assigned_methodologies` (L191) y el `"section": row.section` de sus dicts (L122, L209); **añade** `reindex_user_methodologies()` y `set_methodology_section_ids()` (§1.2) |
| Servicio sección | `src/services/section_catalog.py` | `set_section_methodologies` delega el reindex final en `methodology_scope.reindex_user_methodologies`; `section_methodology_ids` sin cambio |
| Servicio prompt | `src/services/bedrock/prompt.py` | `_METHODOLOGY_ASSIGNMENT_RULE` (L85): mantiene "Agentes" (`agent_profile_ids`) + **añade** frase sobre `section_ids` = Secciones del Admin a las que aplica (RF-025). Catálogo por fila L1/L3 (L145, rama `else`): `section = f" [{row['section']}]"` → resolver labels de `row['section_ids']` vía `get_section_spec(sid).label`, coma, `[]`→sin corchete, `sec-N` desconocido omitido (RF-012/030). `_methodologies_grouped_by_section` ya usa `section_ids` (sin cambio salvo el `row.get('section')` legacy) |
| Servicio catálogo perfiles | `src/services/bedrock/profile_catalog.py` | `_methodology_entries` (L40): quita `"section": row.section` del dict; sin sustituto (RF-014). Los `select` de `_methodology_rows` (si nombran `section`) pierden la columna |
| Guardián L2 | `src/services/bedrock/agent_profiles.py` | reescribe `_METHODOLOGIES_SUFFIX` (L273): sin `section, subsection, notes`; el vínculo con secciones se expresa con `section_ids` (lista `sec-N`); el L2 puede fijarlo vía `create/update_career_record`; los 3 campos retirados → error (RF-015/023) |
| Repo / Qdrant | `src/repositories/career_repository.py` | `_index_for_search` (L534): `extra_payload` de methodology quita `"section": getattr(obj,"section",None)`, mantiene `section_ids` (crudo), `title`, `agent_profile_ids` (RF-013). `_record_to_text` (L448) ya emite `section_ids: [...]` automáticamente al iterar `_indexable_columns` (deja de emitir `section:`/`subsection:` al no existir la columna) |
| Servicio tools (extractos + parseo) | `src/services/bedrock_service.py` | `_methodology_snippet` (L243): tupla de prefijos (L252) `("title:", "section:", "subsection:", "description:", "agent_profile_ids:")` → `("title:", "section_ids:", "description:", "agent_profile_ids:")` (RF-026); devuelve `"sections": [labels de row["section_ids"]]` en vez de `"section": row.get("section")` (RF-024, `sec-N` desconocido omitido — RF-030). En `create_career_record`/`update_career_record` (L454/474): si `fields` trae `section_ids`, validar `⊆ known_section_ids()` (reusa `_normalize_section_ids`, `{"error":...}` si falla) y tras el write `await methodology_scope.reindex_user_methodologies` |
| Tool dispatch L2 | `src/services/bedrock/tools.py` | si el enrutado de `create/update_career_record` no pasa por `bedrock_service` directamente, replicar allí el gancho `section_ids` → `reindex_user_methodologies` (verificar en implementación cuál es el único punto; no duplicar) |
| Rutas Bedrock | `src/routes/bedrock.py` | `_section_detail` (L571): quita `OperationalMethodology.section` del `select` (L588) y `"section": r.section` del dict `methodologies` (L605) → `{"id": r.id, "title": r.title}` (RF-016) |
| Esquemas Bedrock | `src/schemas/bedrock.py` | el item de `BedrockSectionDetail.methodologies` pasa a `{id: str, title: str}` (quita `section`) |
| Handler de errores | `src/app.py` | `validation_exception_handler`: respuesta `application/problem+json` con `type` (`"about:blank"`), `title` (`"Unprocessable Entity"`), `status` (422), `detail` (texto), y `errors` (extensión, se conserva). RFC 9457 (Art. 6, hoy infra-implementado) → RF-003/007. **Cambio transversal — confirmar en Gate 2** (ver §7) |
| Admin — config recurso | `src/config/careerResources.ts` | `operationalMethodologiesConfig`: `columns` = `title`, `section_ids` (label "Sección", `format:'sections'`), `agent_profile_ids` (`format:'agents'`) — quita `section`, `subsection`. `fields` = `title`, `description`, `content`, `agent_profile_ids` (sin cambio), `section_ids` (**nuevo**: `type:'fk-multi-select'`, `fkApi:'admin-sections'`, `label:'Secciones del Admin'`, `helpText`) — quita `section`, `subsection`. Tipos `FieldConfig.fkApi` y `ColumnConfig.format` amplían el union |
| Admin — tipos dominio | `src/types/career.ts` | `OperationalMethodology`: quita `section`, `subsection`, `notes`; añade `section_ids?: string[] \| null` |
| Admin — celda | `src/components/career/careerFieldUtils.ts` | `formatCellValue`: `case 'sections'` → `section_ids.map(getSectionLabel).filter(Boolean).join(', ')`, `[]`→`'—'`, `sec-N` desconocido omitido (RF-008/030) |
| Admin — cache de labels de sección | `src/config/sectionCatalog.ts` (**nuevo**) | `primeSectionLabels(list)` / `getSectionLabel(id): string \| ''` (módulo, cache en memoria; `''` si desconocido) — análogo a `@/config/agentProfiles` pero poblado en runtime |
| Admin — hook catálogo | `src/hooks/useFkOptions.ts` | `FkApiMode` += `'admin-sections'`; `fetchFkRecords` rama `admin-sections` → `adminSectionsApi.list()`; label field `label`. **`useAdminSectionsCatalog()`** (nuevo, mismo `queryKey` que `useFkOptions('admin-sections')` → una sola carga, RNF-001) llama `primeSectionLabels` |
| Admin — vista recurso | `src/components/career/CareerResourceView.tsx` | monta `useAdminSectionsCatalog()` cuando alguna columna visible tiene `format:'sections'` (o para el recurso `operational-methodologies`), de modo que la celda `format:'sections'` tenga labels sin llamada por fila |
| Admin — API secciones | `src/api/adminSections.ts` | sin cambio de firma (`list()` ya existe); se reusa |
| Admin — lado sección (verificación no-regresión) | `src/pages/AdminSectionsPage.tsx` | **sin cambio funcional**; test de no-regresión de `SectionMethodologiesEditor` (RF-010) |

---

## 3 · Fronteras de salida — implementación concreta

| Frontera | Implementación | Notas |
|---|---|---|
| **Postgres compartida** | Alembic `<rev>_methodology_drop_section_freeform.py`: `CREATE TABLE ... backup` + `INSERT SELECT` + `DROP COLUMN IF EXISTS` (×3) + `DROP INDEX IF EXISTS`. Sin tablas de dominio nuevas (solo la de respaldo) | Idempotente (RF-001); dev DB no trackea Alembic (Art. 4) → `DROP COLUMN IF EXISTS`. Verificar `alembic_version` real tras aplicar |
| **Qdrant** (`qdrant_service.upsert_point` vía `CareerRepository._index_for_search`) | `extra_payload` de methodology: `{agent_profile_ids, section_ids (crudo), title}` — sin `section`. Reindex completo del usuario vía `reindex_user_methodologies` en cada edición de `section_ids` por los 3 caminos | Best-effort: fallo de Qdrant no rompe el write PG (RF-031, contrato 003 RF-014). Cierre: `POST /bedrock/knowledge-base/reindex` completo + `scripts/check_kb_consistency.py` EXIT 0 (RF-022) |
| **AWS Bedrock** (system prompt L1/L3 vía `prompt.py`; guardián L2 vía `agent_profiles.py`) | Texto del prompt: labels de `section_ids` en el catálogo por fila; frase nueva en la regla; `_METHODOLOGIES_SUFFIX` reescrito. **Sin** cambio del contrato de tools ni llamadas reales | Art. 5: `embed_text`/`converse` mockeados en todos los tests |
| **`GET /admin/sections`** (desde el Admin, `adminSectionsApi.list()`) | Consumido por `useFkOptions('admin-sections')` (campo del form) y `useAdminSectionsCatalog()` (celda de tabla), **misma React Query key** → una carga por render de la vista (RNF-001). Resolución `sec-N → label` en el cliente | admin-only; mismo `axiosInstance` + JWT que el resto del panel |
| **`search_knowledge_base type=methodology`** (superficie 003 RF-016, vía `bedrock_service._execute_tool`) | Extracto: `section` → `sections` (array de labels resueltos de `section_ids` del payload Qdrant) | Contrato en `contracts/search-knowledge-base-methodology.md` |

---

## 4 · Contratos (`contracts/`) y gates de CI

### Archivos en `.harness/specs/005-.../contracts/`

| Archivo | Contenido | Fronteras / RF |
|---|---|---|
| `methodology-schema.md` | Shape de `OperationalMethodology{Base,Create,Update,Response}` tras el retiro; `extra="forbid"`; **shape del 422 RFC 9457** (`application/problem+json`: `type`, `title`, `status`, `detail`, `errors[]`); shape del error del path tool (`{"error", "valid_fields"}`) | RF-002/003/007 |
| `admin-section-field.md` | Config del `fk-multi-select` (`{type, fkApi:'admin-sections', ...}`); wire format (form: string con `sec-N` separados por `\n`; API: `string[]`); contrato de celda `format:'sections'`; campos de `GET /admin/sections` consumidos (`id`, `label`); RNF-001 (una carga) | RF-005/006/008, RNF-001 |
| `search-knowledge-base-methodology.md` | Extracto nuevo: `{record_id, title, sections[], score, shared, excerpt, read_full}` — **sin** `section`. Enmienda el shape de 003 RF-016 | RF-024/030 |
| `bedrock-section-detail.md` | `GET /bedrock/sections/{id}` y `PUT /bedrock/sections/{id}/methodologies`: `methodologies:[{id,title}]` (sin `section`). Payload Qdrant de methodology: `section_ids` crudo, sin `section`. Enmienda `004/contracts/sections.md` | RF-013/016 |

`openapi.yaml` **no** está committeado (`gate/check.sh` bloque 5: "contrato REST aún no
anclado") → sin Spectral/oasdiff. Los contratos son referencia humana.

### Gates de CI (`gate/check.sh` bloque 5, por perfil)

- **`cjhirashi-career-api`** (`rest-http`): `venv_test/bin/python -m pytest -q`.
- **`cjhirashi-career-admin`** (frontend): `npx vitest run` + `npm run type-check`.
- `cjhirashi-career-ai`, `portfolio`: SKIP (sin cambios).
- Sin bloque `mcp`.
- **Art. 5 / RNF-003:** cero llamadas reales a Bedrock — `embed_text` y `converse`
  mockeados; el verificador rechaza cualquier test que las invoque.

---

## 5 · Estrategia de pruebas por capa + secuenciación test-first

TDD (Art. 3, `method.md §3 Fase 4`): **el test se escribe y falla antes del código**.
Cobertura ≥ 80 % por módulo tocado, objetivo 90 % para código nuevo.

### 5.1 · Pruebas por capa

| Capa | Archivo de test | Cubre |
|---|---|---|
| Migración (unit, DB doble) | `tests/unit/test_methodology_drop_section_migration.py` (**nuevo**) | RF-001 (idempotencia `DROP ... IF EXISTS`, re-run), RF-017 (tabla de respaldo poblada antes del `DROP`), RF-019 (`section_ids` intacto, sin backfill), revisión ID único |
| Esquema (unit puro Pydantic) | `tests/unit/test_methodology_schema_forbid.py` (**nuevo**) | RF-002 (`section`/`subsection`/`notes` no son campos), RF-003 (`extra="forbid"` → `ValidationError`), RF-007 (`section_ids` con `sec-N` inexistente → `ValidationError`), RF-027 (dedup), RF-028 (sin tope) |
| Fn de dominio (unit, DB doble) | `tests/unit/test_methodology_section_link_domain.py` (**nuevo**) | RF-018 (`set_methodology_section_ids`: valida ⊆ known + persiste + dispara reindex), RF-011 (reindex **completo**, no per-record), RF-021 (last-write-wins), RF-031 (Qdrant caído → write PG ok), RF-027/028 |
| `section_catalog` (unit, DB doble) | `tests/unit/test_section_methodologies.py` (**ampliar**, 004) | RF-010 (lado sección sin regresión), RF-018 (usa `reindex_user_methodologies` compartida) |
| `methodology_scope` (unit) | `tests/unit/test_methodology_scope.py` (**ampliar**, 003/004) | RF-014 (sin `section` en `select`/dict; `applies_to_caller`, `list_assigned_methodologies` sin regresión — RNF-002), RF-030 (`sec-N` desconocido ignorado en scope) |
| Ruta CRUD genérica (integración, TestClient + JWT) | `tests/unit/bedrock/test_section_routes.py` o `tests/unit/test_methodology_crud_routes.py` (**nuevo**) | RF-003 (`PUT`/`POST` con `section` → 422 `application/problem+json`), RF-005/006 (`PUT` con `section_ids` persiste), RF-011 (hook → reindex del usuario), RF-029 (mismo `get_current_user`, sin permiso nuevo) |
| Ruta `GET /bedrock/sections/{id}` (integración) | `tests/unit/bedrock/test_section_routes.py` (**ampliar**, 004) | RF-016 (`methodologies:[{id,title}]` sin `section`) |
| Repo / payload Qdrant (unit, `qdrant_service` mock) | `tests/unit/test_methodology_indexing.py` o `test_methodology_section_ids_migration.py` (**ampliar**/nuevo) | RF-013 (`extra_payload` con `section_ids` crudo, sin `section`) |
| Extractos (unit) | `tests/unit/bedrock/test_methodology_snippets.py` (**ampliar**, 003/004) | RF-024 (`sections` labels, sin `section`), RF-026 (prefijos: sin `section:`/`subsection:`, con `section_ids:`), RF-030 (`sec-N` desconocido omitido del extracto) |
| Prompt (unit, catálogo mock) | `tests/unit/bedrock/test_prompt_methodology.py` (**ampliar**, 003/004) | RF-012 (labels de `section_ids` por fila; `[]`→sin corchete), RF-025 (`_METHODOLOGY_ASSIGNMENT_RULE` menciona `section_ids` y conserva "Agentes"), RF-030 (label de `sec-N` desconocido omitido) |
| Guardián L2 (unit) | `tests/unit/bedrock/test_agent_profiles_suffix.py` (**nuevo**) o ampliar existente | RF-015 (`_METHODOLOGIES_SUFFIX` sin `section`/`subsection`/`notes`), RF-023 (menciona `section_ids` + `create/update_career_record`) |
| Tool L2 `create/update_career_record` (unit, repo + qdrant mock) | `tests/unit/bedrock/test_career_record_tool_methodology.py` (**nuevo**) | RF-003 (path tool: `section`/`subsection`/`notes` → `{"error"}` vía `_invalid_fields_error`), RF-007 (path tool: `sec-N` inexistente → error), RF-018/011 (`fields.section_ids` → fn de dominio + reindex completo) |
| Handler RFC 9457 (unit, TestClient) | `tests/unit/test_problem_details_handler.py` (**nuevo**) | RF-003/007 (respuesta de validación = `application/problem+json` con `type/title/status/detail/errors`); no-regresión de clientes que leen `detail`/`errors` |
| Admin — celda (Vitest) | `src/tests/components/careerFieldUtils.test.ts` (**ampliar**) | RF-008 (`format:'sections'` → labels join), RF-030 (`sec-N` desconocido omitido) |
| Admin — campo/config (Vitest) | `src/tests/config/careerResources.test.ts` + `src/tests/components/ResourceForm.test.tsx` (**ampliar**/nuevo) | RF-004 (form sin `section`/`subsection`), RF-005 (`fk-multi-select` con `fkApi:'admin-sections'` renderiza opciones del catálogo), RF-009 (`agent_profile_ids` intacto) |
| Admin — catálogo compartido (Vitest) | `src/tests/hooks/useFkOptions.test.ts` (**ampliar**) | RNF-001 (una sola query `admin-sections` para form + celda) |
| Admin — no-regresión lado sección (Vitest) | `src/tests/pages/AdminSectionsPage.test.tsx` (**ampliar**) | RF-010 (`SectionMethodologiesEditor` sigue operando) |
| Assertion-only (revisión, sin código) | — | RF-020 (grep: ningún cambio en `cjhirashi-career-portfolio/` ni en el render de PDF), RF-022 (paso de cierre documentado y ejecutado con evidencia pegada) |

### 5.2 · Secuenciación (orden de `tasks.md`, test antes que código)

1. **Contratos** — redactar los 4 `contracts/*.md` (no requieren código).
2. **Migración** — test rojo → migración → verde. Verificación **"DB doble"** (mock de
   `op`, coherente con §5.1 y con el patrón de todos los tests de migración del repo:
   `test_file_upload_migration.py`, `test_admin_section_migration.py`,
   `test_methodology_section_ids_migration.py`). Deja el modelo aún con columnas:
   primero el `DROP` a nivel DB.
   **Directiva de Pausa aplicada (2026-09-09):** el plan pedía `alembic upgrade head` en
   una DB Postgres de test — inviable: no hay `TEST_DATABASE_URL`/Postgres desechable y el
   DDL es Postgres-only (`DO $$`, `DROP COLUMN IF EXISTS`, `timestamptz`). Solución de raíz,
   no parche:
   - El test de migración **asserta positivamente** el guard de idempotencia
     (`DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns …) THEN … END IF; END $$`
     alrededor del `INSERT … SELECT`), no solo la presencia de `DROP … IF EXISTS` (cierra el
     hallazgo del revisor sobre RF-001: un `second == first` sobre `op` mockeado es
     tautológico).
   - RF-019 se cubre con aserción **positiva** de que `upgrade()` no emite ningún
     `ALTER … section_ids` ni `UPDATE … section_ids` **y** de que `section_ids` no aparece
     en la lista de columnas dropeadas (no solo ausencia de strings sueltos).
   - El `alembic upgrade head` **real** contra Postgres se ejecuta en el paso 12 (Cierre),
     sobre `career_db`, con evidencia de terminal pegada — es el mismo despliegue que ya
     exige `state.md`. RF-001/017/019 quedan verificados por aserción estructural sobre el
     SQL emitido (unit) + esa ejecución real en el Cierre.
3. **Modelo + esquema** — test de esquema rojo → quitar columnas del modelo + esquema + `extra="forbid"` → verde. (API arranca: `uvicorn` / `GET /health` — Art. 3.)
4. **Handler RFC 9457** — test rojo → `app.py` → verde (antes de las rutas que lo asumen).
5. **Fn de dominio** (`methodology_scope.reindex_user_methodologies` + `set_methodology_section_ids`) — test rojo → código → verde.
6. **Hook CRUD genérico** (`career_common` + `career_methodologies`) — test de ruta rojo → código → verde.
7. **Refactor lado sección** (`section_catalog.set_section_methodologies` → primitiva compartida) — test de no-regresión 004 verde.
8. **Path tool L2** (`bedrock_service` create/update + `_invalid_fields_error`) — test rojo → código → verde.
9. **Consumidores de `section`**: `methodology_scope` selects/dicts → `profile_catalog` → `repositories/career_repository` payload → `bedrock_service._methodology_snippet` → `routes/bedrock._section_detail` + `schemas/bedrock` → `prompt.py` → `agent_profiles._METHODOLOGIES_SUFFIX`. Cada uno: test rojo → código → verde.
10. **Admin**: tipos → `sectionCatalog.ts` + `useAdminSectionsCatalog` + `FkApiMode` → `careerResources.ts` config → `careerFieldUtils` celda → `CareerResourceView` montaje del hook → tests Vitest + `type-check`.
11. **Docs** (`[doc]`, §8).
12. **Cierre**: `gate/check.sh` verde → `POST /bedrock/knowledge-base/reindex` + `scripts/check_kb_consistency.py` (EXIT 0, evidencia pegada) → re-anchor 003/004 (§1.1) → `anchor_commit` de 005 → Session-End.

---

## 6 · Implementación por RF

### Implementación de RF-001 + RF-017 + RF-019 — migración `DROP` con respaldo, sin backfill
`alembic/versions/<rev-nuevo-único>_methodology_drop_section_freeform.py`,
`down_revision = "b3d4e5f6a7c8"`. `upgrade()`:
```
op.execute("CREATE TABLE IF NOT EXISTS operational_methodologies_freeform_backup ("
           "id text, user_id text, section text, subsection text, notes text, "
           "backed_up_at timestamptz NOT NULL DEFAULT now())")
op.execute("INSERT INTO operational_methodologies_freeform_backup (id,user_id,section,subsection,notes) "
           "SELECT id,user_id,section,subsection,notes FROM operational_methodologies")   # RF-017, antes del DROP
op.execute("DROP INDEX IF EXISTS ix_operational_methodologies_section")
for col in ("section", "subsection", "notes"):
    op.execute(f"ALTER TABLE operational_methodologies DROP COLUMN IF EXISTS {col}")      # RF-001 idempotente
```
No se escribe `section_ids` (RF-019). `downgrade()`: `ADD COLUMN` ×3 + `UPDATE ... FROM
operational_methodologies_freeform_backup` (documenta: sólo restaura lo respaldado).
Verificar el id de revisión libre en `alembic/versions/` antes de crear (aviso `state.md`).
**Test:** `tests/unit/test_methodology_drop_section_migration.py`.

### Implementación de RF-002 — esquemas sin `section`/`subsection`/`notes`
`src/schemas/career_methodologies.py`: se eliminan los tres campos de
`OperationalMethodologyBase` y `OperationalMethodologyUpdate`. `Create` y `Response`
heredan de `Base`. **Test:** `test_methodology_schema_forbid.py` (los campos no existen).

### Implementación de RF-003 — campos retirados → 422 RFC 9457 (humano) / error (tool)
- HTTP: `model_config = ConfigDict(extra="forbid")` en `Base` y `Update` →
  `RequestValidationError` → `app.validation_exception_handler` responde
  `application/problem+json` (`type="about:blank"`, `title`, `status=422`, `detail`,
  `errors`). Contrato: `contracts/methodology-schema.md`.
- Tool L2 (`create/update_career_record`): `_invalid_fields_error(repo, fields)` ya
  compara contra `repo._indexable_columns` (derivadas del modelo) → tras el `DROP`,
  `section`/`subsection`/`notes` son "unknown field(s)" y la tool devuelve
  `{"error": ..., "valid_fields": [...]}` sin escribir.
**Tests:** `test_methodology_crud_routes.py`, `test_problem_details_handler.py`,
`test_career_record_tool_methodology.py`.

### Implementación de RF-004 — el formulario del Admin oculta `section`/`subsection`
`src/config/careerResources.ts` `operationalMethodologiesConfig.fields`: se eliminan
las entradas `section` y `subsection` (`creatable-select`). **Test:**
`src/tests/config/careerResources.test.ts` + render de `ResourceForm`.

### Implementación de RF-005 + RF-006 + RF-029 — `section_ids` editable desde el formulario
- `careerResources.ts`: `fields += { name:'section_ids', label:'Secciones del Admin',
  type:'fk-multi-select', fkApi:'admin-sections', fullWidth:true, helpText:'…' }`.
- `src/hooks/useFkOptions.ts`: `FkApiMode` += `'admin-sections'`; `fetchFkRecords`
  rama `admin-sections` → `adminSectionsApi.list()` (label `label`).
- Persistencia: `ResourceForm` emite `PUT /career/operational-methodologies/{id}` con
  `section_ids: string[]`; `OperationalMethodologyUpdate._normalize_section_ids` valida
  `⊆ known_section_ids()` (RF-006). Mismo `get_current_user` que el resto del CRUD —
  **sin permiso nuevo** (RF-029).
**Tests:** `ResourceForm.test.tsx`, `test_methodology_crud_routes.py`.

### Implementación de RF-007 — `sec-N` inexistente → error de validación
Ya cubierto por `_normalize_section_ids` (lanza `ValueError` →
`RequestValidationError` → 422 RFC 9457 en el path HTTP; `{"error"}` en el path tool,
donde se invoca explícitamente antes del write). **Test:**
`test_methodology_schema_forbid.py`, `test_career_record_tool_methodology.py`.

### Implementación de RF-008 + RF-030 (celda) — columna "Sección" resuelta a labels
- `careerResources.ts` `columns`: `{ key:'section_ids', label:'Sección', format:'sections' }`.
- `src/config/sectionCatalog.ts` (nuevo): `primeSectionLabels`, `getSectionLabel`.
- `src/components/career/careerFieldUtils.ts` `formatCellValue`: `case 'sections':
  return Array.isArray(value) ? value.map(id=>getSectionLabel(String(id)))
  .filter(Boolean).join(', ') || '—' : '—'` (`sec-N` desconocido → `''` → omitido, RF-030).
- `src/components/career/CareerResourceView.tsx`: monta `useAdminSectionsCatalog()`.
**Tests:** `careerFieldUtils.test.ts`.

### Implementación de RF-009 — `agent_profile_ids` sin cambios
No se toca la entrada `agent_profile_ids` de `fields` ni la columna `format:'agents'`
ni `_normalize_agent_profile_ids`. **Test:** aserción de no-regresión en
`careerResources.test.ts` + `test_methodology_scope.py` (rama L1/L3 de `applies_to_caller`).

### Implementación de RF-010 — el editor del lado sección no regresiona
`PUT /bedrock/sections/{id}/methodologies` y `SectionMethodologiesEditor` intactos en
comportamiento; sólo `section_catalog.set_section_methodologies` cambia su capa interna
(delega el reindex en `reindex_user_methodologies`). **Tests:**
`test_section_methodologies.py` (backend), `AdminSectionsPage.test.tsx` (frontend).

### Implementación de RF-011 + RF-018 + RF-021 + RF-027 + RF-028 + RF-031 — camino único de dominio
Ver §1.2. `services/methodology_scope.py`:
`reindex_user_methodologies(db, user_id)` (primitiva de reindex completo, best-effort
respecto a Qdrant — RF-031) y `set_methodology_section_ids(db, user_id, id, raw)`
(valida vía `_normalize_section_ids` → dedup (RF-027) + `⊆ known` + sin tope (RF-028);
persiste; `reindex_user_methodologies`). Enganche:
- humano → hook `RESOURCE_REINDEX_ON_FIELDS` en `career_common`;
- sección → `section_catalog.set_section_methodologies` (delega reindex);
- tool → `bedrock_service` create/update.
Concurrencia last-write-wins, sin `version`/locking (RF-021).
**Tests:** `test_methodology_section_link_domain.py`, `test_methodology_crud_routes.py`,
`test_section_methodologies.py`.

### Implementación de RF-012 + RF-030 (prompt) — labels de `section_ids` en el catálogo L1/L3
`src/services/bedrock/prompt.py` rama `else` de `methodology_assignment_block` (L145):
```
sids = row.get("section_ids") or []
labels = []
for sid in sids:
    try: labels.append(get_section_spec(sid).label)
    except KeyError: pass          # sec-N desconocido omitido (RF-030)
section = f" [{', '.join(labels)}]" if labels else ""     # [] o sólo-desconocidos → sin corchete (RF-012)
```
`list_assigned_methodologies` debe seguir entregando `section_ids` en cada fila (ya lo
hace, L210). **Test:** `test_prompt_methodology.py`.

### Implementación de RF-013 — payload Qdrant: `section_ids` crudo, sin `section`
`src/repositories/career_repository.py` `_index_for_search`, `extra_payload` de
`resource_type == "methodology"`: quita `"section": getattr(obj,"section",None)`;
mantiene `"section_ids": getattr(obj,"section_ids",None) or []` (crudo), `"title"`,
`"agent_profile_ids"`. **Test:** `test_methodology_indexing.py` (qdrant_service mock).

### Implementación de RF-014 — `methodology_scope` y `profile_catalog` sin `section`
- `methodology_scope.py`: quita `OperationalMethodology.section` de los `select` (L107,
  L191) y `"section": row.section` de los dicts (L122, L209). Sin sustituto.
- `profile_catalog.py` `_methodology_entries` (L40): quita `"section": row.section`;
  `_methodology_rows` deja de seleccionar `section` si la nombra.
RNF-002: `applies_to_caller`, `resolve_*`, `list_assigned_methodologies` sin regresión.
**Tests:** `test_methodology_scope.py` (ampliar), test de `profile_catalog` si existe.

### Implementación de RF-015 + RF-023 — `_METHODOLOGIES_SUFFIX` del guardián L2
`src/services/bedrock/agent_profiles.py` (L273): texto nuevo — cuerpo `content`
(Markdown) + `title`, `description`, `agent_profile_ids`, **`section_ids` (lista de
`sec-N`: Secciones del Admin a las que aplica; fijable vía `create_career_record` /
`update_career_record`)**. **No** menciona `section`, `subsection`, `notes` (retirados).
**Test:** `test_agent_profiles_suffix.py`.

### Implementación de RF-016 — `GET /bedrock/sections/{id}` → `methodologies:[{id,title}]`
`src/routes/bedrock.py` `_section_detail` (L571): quita `OperationalMethodology.section`
del `select` (L588) y `"section": r.section` del dict (L605). `src/schemas/bedrock.py`:
el item de `BedrockSectionDetail.methodologies` pasa a `{id: str, title: str}`.
Verificado en spec: `SectionMethodologiesEditor` sólo usa `id`/`title`. **Test:**
`test_section_routes.py` (ampliar).

### Implementación de RF-020 — sin cambios en portfolio ni render de PDF
Aserción de revisión: `git diff --stat` no toca `cjhirashi-career-portfolio/` ni los
módulos de PDF (`services/bedrock/tools.py::render_record_pdf`, `pdf_*`). Sin código.
**Verificación:** grep + revisión del diff en el gate.

### Implementación de RF-022 — paso de cierre: reindex completo + consistencia
Documentado en §5.2 paso 12 y en el Session-End: tras `alembic upgrade head`,
`POST /bedrock/knowledge-base/reindex` (síncrono, operador) y
`python scripts/check_kb_consistency.py` → **EXIT 0**, evidencia de terminal pegada
(Art. 3). Sin código nuevo (endpoints y script existen, feature 003).

### Implementación de RF-024 + RF-030 (extracto) — `search_knowledge_base` devuelve `sections`
`src/services/bedrock_service.py` `_methodology_snippet` (L243): en vez de
`"section": row.get("section")`, resolver labels desde `row.get("section_ids")` (payload
Qdrant, RF-013) vía `get_section_spec(sid).label`, `try/except KeyError` (RF-030), y
devolver `"sections": [labels]`. **Test:** `test_methodology_snippets.py` (ampliar).

### Implementación de RF-025 — `_METHODOLOGY_ASSIGNMENT_RULE` menciona `section_ids`
`src/services/bedrock/prompt.py` (L85): se conserva la mención a "Agentes"
(`agent_profile_ids`) y se **añade** una frase: las metodologías también se ligan a
`section_ids` (Secciones del Admin a las que aplican; un agente ligado a esa Sección la
recibe). **Test:** `test_prompt_methodology.py` (aserción sobre el texto de la regla).

### Implementación de RF-026 — parseo de prefijos sin `section:`/`subsection:`, con `section_ids:`
`src/services/bedrock_service.py` `_methodology_snippet` (L252): tupla de prefijos
`("title:", "section:", "subsection:", "description:", "agent_profile_ids:")` →
`("title:", "section_ids:", "description:", "agent_profile_ids:")`. Alineado con lo que
`_record_to_text` emite tras el `DROP` (ya no hay líneas `section:`/`subsection:`; sí
`section_ids:`). **Test:** `test_methodology_snippets.py`.

### Implementación de RF-028 — sin tope de secciones por metodología
`_normalize_section_ids` no impone longitud máxima; única regla = `⊆
known_section_ids()`. Aserción explícita en `test_methodology_schema_forbid.py` (lista
larga válida → aceptada).

### Implementación de RF-029 — mismo permiso que el resto del CRUD
El `PUT`/`POST` de `operational-methodologies` sigue con `Depends(get_current_user)` en
`career_common`; el hook post-update no añade dependencia. Aserción en
`test_methodology_crud_routes.py` (sin token → 401; con token → 200; ningún scope nuevo).

### Implementación de RF-030 — `sec-N` desconocido ignorado en runtime (transversal)
Tres puntos, todos con `try/except KeyError` sobre `get_section_spec`: celda del Admin
(`getSectionLabel` → `''`), label del system prompt (RF-012), extracto de
`search_knowledge_base` (RF-024). En scope (`applies_to_caller`) el `sec-N` desconocido
simplemente no intersecta → sin match, sin error (RF-014 test lo cubre). Nunca se
renderiza "sección desconocida".

### Implementación de RF-031 — Qdrant caído al persistir `section_ids`
`reindex_user_methodologies` envuelve `reindex_for_user`; `_index_for_search` ya es
best-effort (captura excepción, `report_error`, continúa — 003 RF-014). El write PG
(`repo.update_for_user`) hace commit antes; un fallo de Qdrant no se propaga al cliente.
**Test:** `test_methodology_section_link_domain.py` (qdrant_service que lanza →
`set_methodology_section_ids` retorna la lista, PG escrito).

---

## 7 · Aserciones de seguridad (Constitución Art. 5)

| Aserción | Cómo se cubre | RF / test |
|---|---|---|
| Campos retirados no se cuelan (contrato) | `extra="forbid"` (HTTP) + `_invalid_fields_error` (tool) → nada se persiste | RF-003 · `test_methodology_crud_routes.py`, `test_career_record_tool_methodology.py` |
| Errores en formato RFC 9457 | `app.validation_exception_handler` → `application/problem+json` con `type/title/status/detail` | RF-003/007 · `test_problem_details_handler.py` |
| `section_ids` validado (no inyección de `sec-N` arbitrario en el índice/scope) | `_normalize_section_ids` ⊆ `known_section_ids()` en los 3 caminos; `sec-N` desconocido en datos viejos → ignorado en runtime (RF-030) | RF-006/007/030 |
| Sin ampliación de superficie de autorización | mismo `get_current_user`; sin permiso ni endpoint nuevo (hook, no ruta nueva) | RF-029 · `test_methodology_crud_routes.py` |
| Aislamiento por `user_id` | `reindex_user_methodologies` / `set_methodology_section_ids` operan `CareerRepository(...).*_for_user(db, user_id, ...)`; el respaldo de migración guarda `user_id` por fila | RF-011/017 |
| Sin llamadas reales a Bedrock en tests | `embed_text`/`converse` mockeados; verificador adversarial | RNF-003 |
| Secretos | sin variables de entorno nuevas; sin secretos en el repo | — |

---

## 8 · Impacto en documentación (Constitución Art. 11)

| Documento | Motivo (superficie que cambia) | Tarea |
|---|---|---|
| `docs/09-DECISIONS/027-herramientas-metodologias-por-seccion.md` | **Enmienda** (D-13, no ADR nuevo): 004 fijó "el vínculo sección↔metodología se edita desde la sección"; 005 amplía a "también desde la metodología, vía una función de dominio única (`methodology_scope.set_methodology_section_ids` + `reindex_user_methodologies`) compartida por los dos editores"; nota de que `section`/`subsection`/`notes` de texto libre se retiraron y el catálogo/extractos/prompt usan labels de `section_ids` | `[doc]` T-D1 |
| `docs/BEDROCK-SYSTEM.md` | §Metodologías / §Perfiles: el catálogo del system prompt y los extractos de `search_knowledge_base type=methodology` ya no llevan `section` de texto libre → labels de `section_ids`; `_METHODOLOGIES_SUFFIX` del guardián L2 sin `section`/`subsection`/`notes`; `GET /bedrock/sections/{id}` → `methodologies:[{id,title}]` | `[doc]` T-D2 |
| `cjhirashi-career-api/docs/sections/bedrock/README.md` | shape de `GET /bedrock/sections/{id}` (sin `section` en `methodologies`); payload Qdrant de methodology (`section_ids` crudo, sin `section`); nota del hook de reindex en `PUT /career/operational-methodologies/{id}` | `[doc]` T-D2 |
| `cjhirashi-career-api/src/services/README.md` | `methodology_scope`: nuevas `reindex_user_methodologies` / `set_methodology_section_ids` (camino único, D-10); `section_catalog.set_section_methodologies` delega el reindex | `[doc]` T-D2 |
| `cjhirashi-career-api/src/models/README.md` | `operational_methodologies`: se retiran `section`, `subsection`, `notes`; queda `section_ids` (JSONB) como único vínculo con Secciones | `[doc]` T-D3 |
| `.harness/specs/005-.../contracts/*.md` (4 archivos, §4) | contratos de fronteras nuevos/modificados | `[doc]` T-D4 |
| `docs/09-DECISIONS/026-configuracion-agentes-app.md` | **Sin cambio** — la nota "parcialmente superado por ADR-027 para L2" (puesta por 004) sigue vigente; 005 no la altera. Declarado explícito, sin tarea |
| `docs/01`–`docs/12` (arc42), `docs/ADMIN_PANEL_SETUP.md`, `docs/ENVIRONMENT-SECURITY.md`, `docs/IMPLEMENTATION_PLAN.md`, `caddy.json`, `docker-compose.yml`, READMEs de otros servicios | **Sin cambio** — 005 no toca estructura de despliegue, puertos, env, red, ni el portal. Declarado explícito, sin tarea |

`cjhirashi-career-admin`: no hay README de superficie de recurso que liste los campos
del formulario de metodologías (la config vive en `careerResources.ts`, ya en `covers`).
Sin tarea `[doc]` de admin.

---

## 9 · `covers` para el front-matter de `spec.md` (ya conciliado con §1.1)

```yaml
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
```

> Nombres de archivos de test propuestos: si un test ya existe con otro nombre para la
> misma superficie (p. ej. `test_methodology_indexing.py` de 003), se **amplía** ese y
> se ajusta el glob — no se crea un duplicado. La tabla de cobertura de `tasks.md` fija
> el nombre real.

## 10 · Estado del artefacto

`estado: draft` — `method.md §3` no define un estado intermedio entre `draft` e
`implemented`; el flujo sube `spec.md`/`plan.md` a `implemented`/`verified` sólo en el
Cierre. Gate 1 aprobado se registra por la existencia de este `plan.md` y la nota del
Coordinador, no por un cambio de `estado:`. `anchor_mode` de 005 sigue `advisory` hasta
`implemented`.
