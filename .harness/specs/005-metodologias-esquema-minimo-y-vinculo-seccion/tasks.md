---
titulo: "Tasks — Metodologías Operativas: esquema mínimo y vínculo con Secciones editable desde la metodología"
tipo: tasks
estado: draft
fecha: 2026-09-09
feature_id: "005"
spec: ./spec.md
plan: ./plan.md
---

# Tareas (atómicas ≤ 30 min, TDD, test antes que código)

Marcar `[x]` **sólo** con salida de terminal pegada (corrección de `state.md`
2026-09-02). El revisor re-ejecuta, no confía en el reporte. `RNF-003` / Art. 5:
ningún test nuevo llama a Bedrock real — `embed_text` / `converse` mockeados.

Orden = `plan.md §5.2`. Bloques A→K en secuencia; dentro de cada bloque, el `[test]`
rojo antes de su código.

---

## Bloque A — Migración `DROP` con respaldo, sin backfill  (`plan.md §5.2·2`, §6 RF-001/017/019)

- [x] **T-001** `[test]` (cubre RF-001, RF-017, RF-019) —
  `tests/unit/test_methodology_drop_section_migration.py` (**nuevo**): sobre DB de test,
  (a) tras `upgrade`, `operational_methodologies` no tiene `section`/`subsection`/`notes`
  y **sí** `section_ids` con su valor previo intacto (RF-019); (b) la tabla
  `operational_methodologies_freeform_backup` existe y contiene una fila por metodología
  con el `section`/`subsection`/`notes` originales y su `user_id` (RF-017); (c) segundo
  `upgrade` no falla (idempotente, RF-001); (d) el id de revisión no existe ya en
  `alembic/versions/`. Rojo.
  > **Desviación de forma (raíz, no parche):** `plan.md §5.1` define esta fila como
  > "Migración — unit, **DB doble**". No hay `TEST_DATABASE_URL` (backend de test =
  > SQLite in-memory, que no ejecuta DDL Postgres: `timestamptz`, `now()`, `DO $$`,
  > `DROP COLUMN IF EXISTS`). El patrón establecido del repo para tests de migración
  > (`test_methodology_section_ids_migration.py` de 004, `test_admin_section_migration.py`,
  > `test_file_upload_migration.py`) es `op`/`bind` mockeados con aserción sobre el SQL
  > emitido y su **orden**. Se sigue ese patrón: (a) `DROP COLUMN IF EXISTS` x3 +
  > `DROP INDEX IF EXISTS ix_operational_methodologies_section`, y ninguna sentencia
  > escribe/elimina `section_ids`; (b) `CREATE TABLE IF NOT EXISTS ..._freeform_backup`
  > + `INSERT ... SELECT id,user_id,section,subsection,notes` **antes** de todo
  > `DROP COLUMN`; (c) segundo `upgrade` idéntico y toda la DDL guardada con
  > `IF [NOT] EXISTS`; (d) `revision == "c5d6e7f8a9b0"`, `down_revision == "b3d4e5f6a7c8"`,
  > id no colisiona con ningún `^revision =` de `alembic/versions/`.
  >
  > Rojo (4 tests, migración ausente):
  > ```
  > E   FileNotFoundError: [Errno 2] No such file or directory: '.../alembic/versions/c5d6e7f8a9b0_methodology_drop_section_freeform.py'
  > FAILED tests/unit/test_methodology_drop_section_migration.py::test_a_drops_freeform_columns_and_index_keeps_section_ids
  > FAILED tests/unit/test_methodology_drop_section_migration.py::test_b_freeform_backup_table_populated_before_drop
  > FAILED tests/unit/test_methodology_drop_section_migration.py::test_c_second_upgrade_is_idempotent
  > FAILED tests/unit/test_methodology_drop_section_migration.py::test_d_revision_id_is_unique_and_chains_from_004
  > 4 failed in 0.10s
  > ```
  > Verde (tras T-002):
  > ```
  > ....                                                                     [100%]
  > 4 passed in 0.08s
  > ```
- [x] **T-002** `[migration]` (cubre RF-001, RF-017, RF-019) —
  `alembic/versions/c5d6e7f8a9b0_methodology_drop_section_freeform.py`,
  `down_revision = "b3d4e5f6a7c8"`. `upgrade()`: `CREATE TABLE IF NOT EXISTS
  operational_methodologies_freeform_backup` -> `INSERT ... SELECT` (volcado antes del
  `DROP`, RF-017, envuelto en `DO $$ IF EXISTS(column) $$` para que el 2º upgrade no
  falle) -> `DROP INDEX IF EXISTS ix_operational_methodologies_section` ->
  `ALTER TABLE ... DROP COLUMN IF EXISTS` x3 (RF-001). **Sin** escritura de `section_ids`
  (RF-019). `downgrade()`: `ADD COLUMN IF NOT EXISTS` x3 + `CREATE INDEX IF NOT EXISTS` +
  `UPDATE ... FROM ...backup` (documenta: sólo restaura filas respaldadas; filas nuevas
  quedan NULL). Id `c5d6e7f8a9b0` verificado libre contra `alembic/versions/` (aviso
  `state.md` 2026-09-08). Verde T-001.
  > `venv_test/bin/python -m pytest -q tests/unit/test_methodology_drop_section_migration.py`
  > -> `4 passed in 0.08s`. No-regresión (48 tests unit de metodologías/migraciones/
  > secciones): `48 passed in 0.14s`. Gate: `27 ok · 1 warn · 0 error` — warn = `005:
  > anchor_commit 'null'` (conocido, no es fallo); `cjhirashi-career-api · tests` ✅.

## Bloque B — Modelo + esquema mínimo + `extra="forbid"`  (`plan.md §5.2·3`, §6 RF-002)

- [ ] **T-010** `[test]` (cubre RF-002, RF-003, RF-007, RF-027, RF-028) —
  `tests/unit/test_methodology_schema_forbid.py` (**nuevo**), Pydantic puro:
  `OperationalMethodologyBase`/`Create`/`Update` **no** tienen `section`/`subsection`/
  `notes` (RF-002); un dict con cualquiera de esos 3 -> `ValidationError`
  (`extra_forbidden`, RF-003); `section_ids` con un `sec-N` fuera de `known_section_ids()`
  -> `ValidationError` con `"section_ids desconocidos"` (RF-007); `section_ids` con `sec-N`
  duplicados -> válido y deduplicado (RF-027); `section_ids` con lista larga de ids
  conocidos -> aceptada sin tope (RF-028). Rojo.
- [ ] **T-011** `[model]` (cubre RF-002) — `src/models/operational_methodology.py`: quita
  `section` (L29), `subsection` (L30), `notes` (L42) y su docstring; conserva `title`,
  `description`, `content` (`nullable=False`), `agent_profile_ids`, `section_ids`, meta.
- [ ] **T-012** `[schema]` (cubre RF-002, RF-003, RF-007, RF-027, RF-028) —
  `src/schemas/career_methodologies.py`: `OperationalMethodologyBase` y
  `OperationalMethodologyUpdate` pierden los 3 campos; `model_config =
  ConfigDict(extra="forbid")` en `Base` y `Update`; `_normalize_section_ids` intacta como
  validación compartida; `Response` conserva su comentario de por qué no valida ids.
  API arranca (`GET /health`, Art. 3). Verde T-010.

## Bloque C — Handler RFC 9457  (`plan.md §5.2·4`, §6 RF-003)

- [ ] **T-020** `[test]` (cubre RF-003, RF-007) —
  `tests/unit/test_problem_details_handler.py` (**nuevo**), TestClient: una petición con
  error de validación devuelve `422` con `Content-Type: application/problem+json` y cuerpo
  `{type:"about:blank", title:"Unprocessable Entity", status:422, detail, errors:[...]}`;
  `errors` conserva el array de `RequestValidationError.errors()` (no-regresión de
  clientes que lo leen). Rojo.
- [ ] **T-021** `[route]` (cubre RF-003, RF-007) — `src/app.py`
  `validation_exception_handler`: respuesta `application/problem+json` con
  `type/title/status/detail/errors` (RFC 9457, Art. 6). Cambio transversal — sin regresión
  en el resto de rutas. Verde T-020.

## Bloque D — Función de dominio única para `section_ids`  (`plan.md §5.2·5`, §1.2, §6 RF-011/018)

- [ ] **T-030** `[test]` (cubre RF-011, RF-018, RF-021, RF-027, RF-028, RF-031) —
  `tests/unit/test_methodology_section_link_domain.py` (**nuevo**), DB de test +
  `qdrant_service` mock: `set_methodology_section_ids(db, uid, id, raw)` (a) normaliza vía
  `_normalize_section_ids` (subconjunto de `known_section_ids()`, dedup RF-027, sin tope
  RF-028), (b) persiste la lista limpia, (c) invoca `reindex_user_methodologies`
  **completo** (no re-vectorización per-record) — RF-011/018; id inexistente -> `None`;
  dos llamadas en secuencia -> gana la última (RF-021); `qdrant_service` que lanza -> la
  función retorna la lista y PG queda escrito (RF-031). Rojo.
- [ ] **T-031** `[service]` (cubre RF-011, RF-018, RF-021, RF-027, RF-028, RF-031) —
  `src/services/methodology_scope.py`: `reindex_user_methodologies(db, user_id)`
  (primitiva única de reindex completo vía `CareerRepository(...).reindex_for_user`,
  best-effort respecto a Qdrant) y `set_methodology_section_ids(db, user_id,
  methodology_id, raw_section_ids)` (§1.2). Sin `version`/locking (last-write-wins). Verde
  T-030.

## Bloque E — Hook CRUD genérico (lado metodología)  (`plan.md §5.2·6`, §6 RF-005/006/011/029)

- [ ] **T-040** `[test]` (cubre RF-003, RF-005, RF-006, RF-011, RF-029) —
  `tests/unit/test_methodology_crud_routes.py` (**nuevo**), TestClient + JWT: `POST`/`PUT`
  `/career/operational-methodologies[/{id}]` con `section` -> `422 application/problem+json`
  y nada persistido (RF-003); `PUT` con `section_ids` de `sec-N` conocidos -> `200`, lista
  persistida exacta y validada (RF-005/006); tras ese `PUT` se dispara
  `reindex_user_methodologies` del usuario, no sólo del registro (RF-011, mock/espía);
  sin token -> `401`, con token -> `200`, sin scope nuevo (RF-029). Rojo.
- [ ] **T-041** `[route]` (cubre RF-003, RF-005, RF-006, RF-011, RF-029) —
  `src/routes/career_common.py`: mapa `RESOURCE_REINDEX_ON_FIELDS: dict[str, set[str]]` +
  parámetro `reindex_on_fields` en `build_crud_router`/`register_resource`; en
  `create_item`/`update_item`, tras write exitoso, `if set(data) &
  RESOURCE_REINDEX_ON_FIELDS.get(resource_key, set()): await
  methodology_scope.reindex_user_methodologies(db, current_user.id)`. Data-driven, sin
  `if` hardcodeado. Verde T-040 (parcial).
- [ ] **T-042** `[route]` (cubre RF-005, RF-006, RF-011) —
  `src/routes/career_methodologies.py`: pasa `reindex_on_fields={"section_ids"}` al
  `build_crud_router`. Verde T-040.

## Bloque F — Refactor del lado sección hacia la primitiva compartida  (`plan.md §5.2·7`, §6 RF-010/018)

- [ ] **T-050** `[test]` (cubre RF-010, RF-018) —
  `tests/unit/test_section_methodologies.py` (**ampliar**, 004): `set_section_methodologies`
  sigue ligando/desligando `section_ids` sin regresión (RF-010) y al final invoca
  `methodology_scope.reindex_user_methodologies` (espía) en vez de un `repo.reindex_for_user`
  inline (RF-018); mantiene el guard `section_id not in known_section_ids()` -> `ValueError`.
  Rojo.
- [ ] **T-051** `[service]` (cubre RF-010, RF-018) —
  `src/services/section_catalog.py`: `set_section_methodologies` importa y delega el
  reindex final en `methodology_scope.reindex_user_methodologies`; `section_methodology_ids`
  sin cambio. Verde T-050.

## Bloque G — Path tool L2 (`create/update_career_record`)  (`plan.md §5.2·8`, §6 RF-003/007/011/018)

- [ ] **T-060** `[test]` (cubre RF-003, RF-007, RF-011, RF-018) —
  `tests/unit/bedrock/test_career_record_tool_methodology.py` (**nuevo**), repo + qdrant
  mock: `create/update_career_record` sobre `operational-methodologies` con
  `fields.section`/`subsection`/`notes` -> `{"error": "...", "valid_fields": [...]}` sin
  persistir (RF-003); `fields.section_ids` con `sec-N` inexistente ->
  `{"error": "section_ids desconocidos: [...]"}` sin persistir (RF-007);
  `fields.section_ids` válido -> tras el write se llama `reindex_user_methodologies`
  **una** vez (RF-011/018). Rojo.
- [ ] **T-061** `[service]` (cubre RF-003, RF-007, RF-011, RF-018) —
  `src/services/bedrock_service.py` `create_career_record`/`update_career_record`
  (L454/474): si `fields` trae `section_ids`, validar contra `known_section_ids()`
  reusando `_normalize_section_ids` (`{"error": ...}` al agente si falla) y tras el write
  `await methodology_scope.reindex_user_methodologies`. `_invalid_fields_error` ya rechaza
  `section`/`subsection`/`notes` tras el `DROP` (columnas inexistentes). Verde T-060
  (parcial).
- [ ] **T-062** `[service]` (cubre RF-011, RF-018) — `src/services/bedrock/tools.py`:
  verificar el punto único de dispatch de `create/update_career_record`; si NO pasa por
  `bedrock_service` directamente, enrutar allí `fields.section_ids` ->
  `reindex_user_methodologies` (no duplicar el gancho). Verde T-060.

## Bloque H — Consumidores de `section` (texto libre) al retirarlo  (`plan.md §5.2·9`, §3.9)

- [ ] **T-070** `[test]` (cubre RF-014, RF-030, RNF-002) —
  `tests/unit/test_methodology_scope.py` (**ampliar**, 003/004): `list_methodologies_for_catalog`
  y `list_assigned_methodologies` no seleccionan ni devuelven `section`; `applies_to_caller`,
  `resolve_*` y `list_assigned_methodologies` sin regresión observable (RNF-002); un
  `sec-N` desconocido en `section_ids` no intersecta y no rompe el scope (RF-030). Rojo.
- [ ] **T-071** `[service]` (cubre RF-014, RF-030, RNF-002) —
  `src/services/methodology_scope.py`: quita `OperationalMethodology.section` de los
  `select` (L107, L191) y `"section": row.section` de los dicts (L122, L209), sin
  sustituto. Verde T-070 (parcial).
- [ ] **T-072** `[service]` (cubre RF-014) —
  `src/services/bedrock/profile_catalog.py` `_methodology_entries` (L40): quita
  `"section": row.section` del dict; `_methodology_rows` deja de seleccionar `section` si
  la nombra. Verde T-070.
- [ ] **T-073** `[test]` (cubre RF-013) —
  `tests/unit/test_methodology_indexing.py` (**ampliar**/nuevo, `qdrant_service` mock): el
  `extra_payload` de una metodología en `_index_for_search` incluye `section_ids` (los
  `sec-N` **crudos**), `title`, `agent_profile_ids` y **no** incluye `section`. Rojo.
- [ ] **T-074** `[repo]` (cubre RF-013) —
  `src/repositories/career_repository.py` `_index_for_search` (L534): quita
  `"section": getattr(obj,"section",None)` del `extra_payload` de `resource_type ==
  "methodology"`; mantiene `section_ids` crudo. Verde T-073.
- [ ] **T-075** `[test]` (cubre RF-024, RF-026, RF-030) —
  `tests/unit/bedrock/test_methodology_snippets.py` (**ampliar**, 003/004): el extracto de
  `search_knowledge_base type=methodology` devuelve `sections` (lista de labels resueltos
  de `section_ids`) y **no** `section` (RF-024); un `sec-N` del payload no presente en el
  catálogo se omite de `sections` sin error (RF-030); la tupla de prefijos de
  `_methodology_snippet` es `("title:", "section_ids:", "description:",
  "agent_profile_ids:")` — sin `section:`/`subsection:` (RF-026). Rojo.
- [ ] **T-076** `[service]` (cubre RF-024, RF-026, RF-030) —
  `src/services/bedrock_service.py` `_methodology_snippet` (L243/252): tupla de prefijos
  nueva (RF-026); en vez de `"section": row.get("section")`, resolver labels de
  `row.get("section_ids")` vía `get_section_spec(sid).label` con `try/except KeyError`
  (RF-030) y devolver `"sections": [labels]` (RF-024). Verde T-075.
- [ ] **T-077** `[test]` (cubre RF-016) —
  `tests/unit/bedrock/test_section_routes.py` (**ampliar**, 004): `GET
  /bedrock/sections/{id}` devuelve cada item de `methodologies` como `{id, title}` sin
  `section`; `PUT /bedrock/sections/{id}/methodologies` responde el mismo shape. Rojo.
- [ ] **T-078** `[route]` `[schema]` (cubre RF-016) —
  `src/routes/bedrock.py` `_section_detail` (L571): quita
  `OperationalMethodology.section` del `select` (L588) y `"section": r.section` del dict
  (L605) -> `{"id": r.id, "title": r.title}`. `src/schemas/bedrock.py`: el item de
  `BedrockSectionDetail.methodologies` pasa a `{id: str, title: str}`. Verde T-077.
- [ ] **T-079** `[test]` (cubre RF-012, RF-025, RF-030) —
  `tests/unit/bedrock/test_prompt_methodology.py` (**ampliar**, 003/004): el catálogo por
  fila de L1/L3 renderiza `[label1, label2]` resueltos de `section_ids`, `[]` o
  sólo-desconocidos -> **sin corchete** (RF-012); un `sec-N` desconocido se omite del
  label (RF-030); `_METHODOLOGY_ASSIGNMENT_RULE` menciona `section_ids` (Secciones del
  Admin a las que aplica) y **conserva** la mención a "Agentes"/`agent_profile_ids`
  (RF-025). Rojo.
- [ ] **T-080** `[service]` (cubre RF-012, RF-025, RF-030) —
  `src/services/bedrock/prompt.py`: `_METHODOLOGY_ASSIGNMENT_RULE` (L85) añade la frase
  sobre `section_ids` conservando "Agentes" (RF-025); rama `else` de
  `methodology_assignment_block` (L145) resuelve labels de `row["section_ids"]` vía
  `get_section_spec(sid).label` con `try/except KeyError`, coma, `[]`->sin corchete
  (RF-012/030). Verde T-079.
- [ ] **T-081** `[test]` (cubre RF-015, RF-023) —
  `tests/unit/bedrock/test_agent_profiles_suffix.py` (**nuevo**): `_METHODOLOGIES_SUFFIX`
  **no** menciona `section`, `subsection` ni `notes` (RF-015); **sí** indica que el
  vínculo con secciones se expresa con `section_ids` (lista de `sec-N`) y que el L2 puede
  fijarlo vía `create_career_record`/`update_career_record` (RF-023). Rojo.
- [ ] **T-082** `[service]` (cubre RF-015, RF-023) —
  `src/services/bedrock/agent_profiles.py` (L273): reescribe `_METHODOLOGIES_SUFFIX`
  según T-081. Verde T-081.

## Bloque I — Admin (`cjhirashi-career-admin`)  (`plan.md §5.2·10`, §6 RF-004/005/008/009)

- [ ] **T-090** `[admin]` (cubre RF-002) — `src/types/career.ts`: `OperationalMethodology`
  quita `section`, `subsection`, `notes`; añade `section_ids?: string[] | null`.
  (`type-check` del gate cubre la no-regresión.)
- [ ] **T-091** `[test]` (cubre RF-005, RNF-001) —
  `src/tests/hooks/useFkOptions.test.ts` (**ampliar**): `useFkOptions('admin-sections')`
  llama `adminSectionsApi.list()` y expone `{value: sec-N, label}`; el campo del form y
  `useAdminSectionsCatalog()` comparten la **misma** React Query key -> **una** petición a
  `/admin/sections` por render, nunca una por fila (RNF-001). Rojo.
- [ ] **T-092** `[admin]` (cubre RF-005, RNF-001) — `src/hooks/useFkOptions.ts`:
  `FkApiMode += 'admin-sections'`; rama `admin-sections` en `fetchFkRecords` ->
  `adminSectionsApi.list()` (label `label`); `useAdminSectionsCatalog()` (nuevo, mismo
  `queryKey`) llama `primeSectionLabels`. `src/config/sectionCatalog.ts` (**nuevo**):
  `primeSectionLabels(list)` / `getSectionLabel(id): string` (cache en memoria, `''` si
  desconocido). Verde T-091.
- [ ] **T-093** `[test]` (cubre RF-008, RF-030) —
  `src/tests/components/careerFieldUtils.test.ts` (**ampliar**): `formatCellValue(value,
  'sections')` -> labels de `section_ids` unidos por `', '` (RF-008); `sec-N` desconocido
  omitido; lista vacía / todos desconocidos -> `'—'` (RF-030). Rojo.
- [ ] **T-094** `[admin]` (cubre RF-008, RF-030) —
  `src/components/career/careerFieldUtils.ts` `formatCellValue`: `case 'sections'` ->
  `value.map(getSectionLabel).filter(Boolean).join(', ') || '—'`; `ColumnConfig.format`
  amplía el union. Verde T-093.
- [ ] **T-095** `[test]` (cubre RF-004, RF-005, RF-008, RF-009) —
  `src/tests/config/careerResources.test.ts` + `src/tests/components/ResourceForm.test.tsx`
  (**ampliar**/nuevo): `operationalMethodologiesConfig.fields` **no** tiene `section` ni
  `subsection` (RF-004); tiene `section_ids` `type:'fk-multi-select'`
  `fkApi:'admin-sections'` que renderiza opciones del catálogo (RF-005); `columns` tiene
  `section_ids` `format:'sections'` y **no** `section`/`subsection` (RF-008);
  `agent_profile_ids` (campo y columna `format:'agents'`) intacto (RF-009). Rojo.
- [ ] **T-096** `[admin]` (cubre RF-004, RF-005, RF-008, RF-009) —
  `src/config/careerResources.ts` `operationalMethodologiesConfig`: `fields` = `title`,
  `description`, `content`, `agent_profile_ids` (sin cambio), `section_ids` (**nuevo**
  `fk-multi-select`, `fkApi:'admin-sections'`, `fullWidth`, `helpText`); `columns` =
  `title`, `section_ids` (`label:'Sección'`, `format:'sections'`), `agent_profile_ids`
  (`format:'agents'`). `FieldConfig.fkApi` amplía el union. Verde T-095.
- [ ] **T-097** `[admin]` (cubre RNF-001) —
  `src/components/career/CareerResourceView.tsx`: monta `useAdminSectionsCatalog()` cuando
  el recurso tiene una columna `format:'sections'` (o es `operational-methodologies`), de
  modo que la celda tenga labels sin llamada por fila. Verde (cubierto por T-091 +
  render de T-093).
- [ ] **T-098** `[test]` (cubre RF-010) —
  `src/tests/pages/AdminSectionsPage.test.tsx` (**ampliar**): `SectionMethodologiesEditor`
  sigue listando y guardando metodologías de una sección sin regresión (consume sólo
  `id`/`title`). Rojo/verde de no-regresión.

## Bloque J — Documentación  (`plan.md §8`)

- [ ] **T-D1** `[doc]` (doc: ADR-027) —
  `docs/09-DECISIONS/027-herramientas-metodologias-por-seccion.md`: **enmienda** (D-13, no
  ADR nuevo) — 004 fijó "el vínculo sección<->metodología se edita desde la sección"; 005
  amplía a "también desde la metodología, vía `methodology_scope.set_methodology_section_ids`
  + `reindex_user_methodologies` compartidas por los dos editores"; nota de que
  `section`/`subsection`/`notes` de texto libre se retiraron y catálogo/extractos/prompt
  usan labels de `section_ids`.
- [ ] **T-D2** `[doc]` (doc: BEDROCK-SYSTEM.md + READMEs API) —
  `docs/BEDROCK-SYSTEM.md` (§Metodologías/§Perfiles: catálogo del system prompt y
  extractos de `search_knowledge_base type=methodology` sin `section` libre -> labels de
  `section_ids`; `_METHODOLOGIES_SUFFIX` sin los 3 campos; `GET /bedrock/sections/{id}` ->
  `methodologies:[{id,title}]`), `cjhirashi-career-api/docs/sections/bedrock/README.md`
  (shape de `GET /bedrock/sections/{id}`; payload Qdrant `section_ids` crudo sin
  `section`; hook de reindex en `PUT /career/operational-methodologies/{id}`),
  `cjhirashi-career-api/src/services/README.md` (`methodology_scope`:
  `reindex_user_methodologies` / `set_methodology_section_ids`; `section_catalog` delega
  el reindex).
- [ ] **T-D3** `[doc]` (doc: models/README.md) —
  `cjhirashi-career-api/src/models/README.md`: `operational_methodologies` retira
  `section`, `subsection`, `notes`; `section_ids` (JSONB) queda como único vínculo con
  Secciones.
- [ ] **T-D4** `[doc]` (doc: contracts/*.md) —
  `.harness/specs/005-.../contracts/` (`methodology-schema.md`, `admin-section-field.md`,
  `search-knowledge-base-methodology.md`, `bedrock-section-detail.md`, ya redactados en
  Fase 2): conciliar con los shapes finales de la implementación (nombres de test, id de
  revisión de la migración, texto exacto del 422).

## Bloque K — Cierre  (`plan.md §5.2·12`, §6 RF-020/022)

- [ ] **T-100** `[test]` (cubre RF-020) — revisión del `git diff --stat` del cierre:
  ningún archivo bajo `cjhirashi-career-portfolio/` ni en los módulos de render de PDF
  (`services/bedrock/tools.py::render_record_pdf`, `pdf_*`) fue tocado. `grep` + diff
  pegados como evidencia. Sin código.
- [ ] **T-101** `[ops]` (cubre RF-022, y cierra RF-001/013/024 en vivo — Art. 3) — tras
  desplegar: `alembic upgrade head` en `career_db` (pegar `alembic current`) ->
  `POST /bedrock/knowledge-base/reindex` con JWT real (pegar `200` + conteos) ->
  `python scripts/check_kb_consistency.py` -> **EXIT 0** (evidencia de terminal pegada).
  Nota operativa en el Session-End. Sin código nuevo.

---

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)

| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-001, T-002 | test_methodology_drop_section_migration | — |
| RF-002 | T-010, T-011, T-012, T-090 | test_methodology_schema_forbid | — |
| RF-003 | T-010, T-012, T-020, T-021, T-040, T-041, T-060, T-061 | test_methodology_schema_forbid · test_problem_details_handler · test_methodology_crud_routes · test_career_record_tool_methodology | — |
| RF-004 | T-095, T-096 | careerResources.test · ResourceForm.test | — |
| RF-005 | T-040, T-041, T-091, T-092, T-095, T-096 | test_methodology_crud_routes · useFkOptions.test · ResourceForm.test | — |
| RF-006 | T-030, T-031, T-040, T-041, T-042 | test_methodology_section_link_domain · test_methodology_crud_routes | — |
| RF-007 | T-010, T-012, T-020, T-021, T-060, T-061 | test_methodology_schema_forbid · test_problem_details_handler · test_career_record_tool_methodology | — |
| RF-008 | T-093, T-094, T-095, T-096 | careerFieldUtils.test · careerResources.test | — |
| RF-009 | T-070, T-071, T-095, T-096 | test_methodology_scope · careerResources.test | — |
| RF-010 | T-050, T-051, T-098 | test_section_methodologies · AdminSectionsPage.test | — |
| RF-011 | T-030, T-031, T-040, T-041, T-042, T-050, T-051, T-060, T-061, T-062 | test_methodology_section_link_domain · test_methodology_crud_routes · test_section_methodologies · test_career_record_tool_methodology | — |
| RF-012 | T-079, T-080 | test_prompt_methodology | — |
| RF-013 | T-073, T-074 | test_methodology_indexing | — |
| RF-014 | T-070, T-071, T-072 | test_methodology_scope | — |
| RF-015 | T-081, T-082 | test_agent_profiles_suffix | — |
| RF-016 | T-077, T-078 | test_section_routes | — |
| RF-017 | T-001, T-002 | test_methodology_drop_section_migration | — |
| RF-018 | T-030, T-031, T-050, T-051, T-060, T-061, T-062 | test_methodology_section_link_domain · test_section_methodologies · test_career_record_tool_methodology | — |
| RF-019 | T-001, T-002 | test_methodology_drop_section_migration | — |
| RF-020 | T-100 | grep + git diff (revisión) — sin cambios en portfolio ni render de PDF | — |
| RF-021 | T-030, T-031 | test_methodology_section_link_domain::last_write_wins | — |
| RF-022 | T-101 | T-101 (en vivo, `check_kb_consistency.py` EXIT 0, evidencia pegada) | — |
| RF-023 | T-081, T-082 | test_agent_profiles_suffix | — |
| RF-024 | T-075, T-076 | test_methodology_snippets | — |
| RF-025 | T-079, T-080 | test_prompt_methodology::assignment_rule | — |
| RF-026 | T-075, T-076 | test_methodology_snippets::prefixes | — |
| RF-027 | T-010, T-012, T-030, T-031 | test_methodology_schema_forbid · test_methodology_section_link_domain | — |
| RF-028 | T-010, T-012, T-030, T-031 | test_methodology_schema_forbid · test_methodology_section_link_domain | — |
| RF-029 | T-040, T-041 | test_methodology_crud_routes::no_new_scope | — |
| RF-030 | T-070, T-071, T-075, T-076, T-079, T-080, T-093, T-094 | test_methodology_scope · test_methodology_snippets · test_prompt_methodology · careerFieldUtils.test | — |
| RF-031 | T-030, T-031 | test_methodology_section_link_domain::qdrant_down | — |
| RNF-001 | T-091, T-092, T-097 | useFkOptions.test::single_query | — |
| RNF-002 | T-070, T-071 | test_methodology_scope (applies_to_caller / resolve_* / list_assigned_methodologies sin regresión) | — |
| RNF-003 | (revisión) | aserción en todos los tests nuevos: `embed_text`/`converse` mockeados (Art. 5) | — |
| doc: ADR-027 (`docs/09-DECISIONS/027-herramientas-metodologias-por-seccion.md`) | T-D1 | — | — |
| doc: `docs/BEDROCK-SYSTEM.md` + `cjhirashi-career-api/docs/sections/bedrock/README.md` + `cjhirashi-career-api/src/services/README.md` | T-D2 | — | — |
| doc: `cjhirashi-career-api/src/models/README.md` | T-D3 | — | — |
| doc: `.harness/specs/005-.../contracts/*.md` | T-D4 | — | — |
| doc: ADR-026 / arc42 (`docs/01`–`12`) / `caddy.json` / `docker-compose.yml` | — (sin cambio — declarado explícito en `plan.md §8`) | — | — |
