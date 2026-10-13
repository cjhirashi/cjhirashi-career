---
titulo: "Tasks — Vacantes: quiénes son, qué buscan, qué ofrecen y cultura laboral"
tipo: tasks
estado: draft
fecha: 2026-10-13
feature_id: "008"
spec: ./spec.md
plan: ./plan.md
---

# Tareas (atómicas, TDD, test antes que código)

Marcar `[x]` sólo con salida de terminal **pegada** (corrección del usuario en
`state.md`, 2026-09-02). Nunca "salida esperada". El revisor re-ejecuta, no confía en el
reporte. Anotación de tests: pytest `@pytest.mark.requisito("RF-0NN")`; Vitest
`describe("RF-0NN: …")`. Sin Bedrock ni Qdrant reales en ningún test (RNF-002).

Rutas API relativas a `cjhirashi-career-api/`; Admin a `cjhirashi-career-admin/`.
Las tareas marcadas **[REQUIERE OK DEL USUARIO]** no se ejecutan sin autorización
explícita en ese momento.

## Bloque A — API: schemas (normalización y tope)

- [x] **T-001** `[test]` (cubre RF-002, RF-003, RF-004, RF-005) —
  `tests/unit/test_vacancy_descriptive_texts.py`, capa schemas: Create/Update aceptan los
  cuatro campos; `""`, `"   "`, `"\n\t"` → `None`; `"  hola  "` → `"hola"`; saltos de línea
  internos, viñetas y emojis intactos; 10 000 caracteres válido, 10 001 →
  `ValidationError` (el tope se mide tras el trim); `VacancyResponse` sin valores expone
  las cuatro claves con `None`; Update que omite un campo no lo incluye en
  `model_dump(exclude_unset=True)`; `null` explícito sí lo incluye. Rojo.
- [x] **T-002** `[code]` (cubre RF-002, RF-003, RF-004, RF-005) —
  `src/schemas/career_search.py`: normalizador `_trim_or_none` + `StringConstraints(max_length=10_000)`,
  campos en `VacancyBase` y `VacancyUpdate` (plan §1). Verde T-001.

## Bloque B — API: modelo

- [x] **T-010** `[test]` (cubre RF-001, RF-002) — mismo archivo, con `db_session`: una
  `Vacancy` guarda y relee los cuatro campos (texto multilínea de ≥ 5 000 caracteres); sin
  valores quedan `None`. Rojo.
- [x] **T-011** `[code]` (cubre RF-001, RF-002) — `src/models/vacancy.py`: cuatro
  `Column(Text, nullable=True)` sin default. Verde T-010.

## Bloque C — API: repositorio y KB

- [x] **T-020** `[test]` (cubre RF-001, RF-003, RF-004, RF-005) — mismo archivo, repositorio
  de `vacancies` con `db_session`: create/update persisten los cuatro; update de otro campo
  no los altera. Documenta D-07: por la vía del repositorio (tools) no hay trim ni tope
  (caracterización, no contrato). Debe quedar verde sin código nuevo.
- [x] **T-021** `[test]` (cubre RF-006) — mismo archivo: `_record_to_text(Vacancy con los
  cuatro campos rellenos)` no contiene sus nombres ni su texto; sí contiene `process_stage`
  y `analysis_notes`; `process_stage_updated_at` sigue excluida (no regresión 007 D-13).
  Sin Bedrock ni Qdrant. Rojo.
- [x] **T-022** `[code]` (cubre RF-006) — `src/repositories/career_repository.py`:
  ampliar `_KB_EXCLUDED_COLUMNS["vacancies"]` con los cuatro campos, con comentario
  `# TRANSITORIO: se retira con la spec 009`. Verde T-021.

## Bloque D — API: ruta HTTP

- [x] **T-030** `[test]` (cubre RF-001..RF-005) — mismo archivo, con `async_client` + JWT
  sobre `/career/vacancies`: POST/PUT con cada campo y con los cuatro a la vez devuelve y
  persiste (GET posterior igual); respuestas sin valores traen `null`; PUT que cambia sólo
  `company` o sólo un campo no toca los otros; `null` explícito borra; vacío/espacios →
  `null`; trim; 10 000 → OK; 10 001 → 422 `{"detail","errors"}` y fila sin cambio;
  vacante sin `target_company_id` funciona igual. Si exige Postgres, usar el fixture PG-only
  existente. Debe quedar verde sin código nuevo (lo cubren T-002, T-011, T-022); si falla,
  se corrige en la capa responsable.

## Bloque E — API: migración `d8f2b5a13c97`

- [x] **T-040** `[test]` (cubre RF-007) —
  `tests/unit/test_vacancy_descriptive_texts_migration.py` con dobles (patrón
  `test_vacancy_process_stage_migration.py`): `down_revision == "c7e1a4d92b60"`; upgrade
  emite `ADD COLUMN` de las cuatro (`TEXT NULL`) y ninguna sentencia `UPDATE`; idempotente
  (no repite si existen); downgrade elimina las cuatro sólo si existen. Rojo.
- [x] **T-041** `[code]` (cubre RF-007) —
  `alembic/versions/d8f2b5a13c97_vacancy_descriptive_texts.py` según plan §3. Antes,
  re-verificar con script que `c7e1a4d92b60` sigue siendo el único head. Verde T-040.
- [x] **T-042** `[verify]` (cubre RF-007) — en un clon **desechable** de Postgres
  (`TEST_DATABASE_URL`): con filas previas, upgrade → columnas `text` nullable, filas
  intactas con `NULL`; downgrade → columnas fuera; upgrade de nuevo. Salida pegada. Nunca en
  prod.
- [x] **T-043** `[test]` regresión API — `pytest` completo de la API (incluye
  `test_vacancy_process_stage.py`, `test_vacancy_duplicate_url.py`,
  `test_vacancy_target_company_fk.py`, `test_job_discovery.py`). Salida pegada, 0 fallos.
  Grep de `vacancies` fuera de la API en `cjhirashi-career-ai` y Portfolio: sin impacto.

## Bloque F — Admin

- [x] **T-050** `[test]` (cubre RF-008, RF-010) — `src/tests/config/vacanciesConfig.test.ts`
  (ampliar): los cuatro `name` existen en `fields`, `type === 'textarea'`,
  `fullWidth === true`, etiquetas literales ("Quiénes son", "Qué buscan", "Qué ofrecen",
  "Cultura laboral"), índices consecutivos y en orden canónico; ninguna columna de
  `columns` con esos keys y el array de keys es exactamente el de 007 RF-015. Rojo.
- [x] **T-051** `[code]` (cubre RF-008, RF-010) — `src/types/career.ts` (cuatro campos
  `string | null` opcionales en `Vacancy`) + `src/config/careerResources.ts` (cuatro campos
  en `vacanciesConfig.fields`, tras `contact_id` y antes de `analysis_notes`; `helpText` y
  posición según `experto-ux-ui`, T-070). Verde T-050.
- [x] **T-052** `[test]` (cubre RF-008, RF-009, RF-010) —
  `src/tests/components/career/VacancyDescriptiveTexts.test.tsx` (nuevo): el formulario
  muestra cuatro textareas con esas etiquetas, contiguas y en orden; la ficha de detalle
  muestra los cuatro en orden canónico con su etiqueta y renderiza Markdown vigente (D-06:
  párrafos separados por línea en blanco); la tabla no tiene columnas de estos campos. Debe
  quedar verde sin cambios en `CareerResourceView.tsx` (D-06); si falla, se corrige en
  config.
- [x] **T-053** `[test]` regresión Admin — suite Vitest completa + `npm run type-check` +
  `npm run lint` sin errores nuevos en los archivos tocados (criterio de 007 T-054: deuda de
  lint preexistente no cuenta). Salida pegada.

## Bloque G — Documentación

- [x] **T-060** `[doc]` — `cjhirashi-career-api/docs/sections/career-search/README.md`:
  añadir los cuatro campos a la tabla de `vacancies` y una nota con las reglas (trim,
  vacío → `NULL`, tope de 10 000, 422), que las tools Bedrock no las aplican (D-07) y el
  carácter transitorio de la exclusión de la KB (RF-006, spec 009). Verificar con grep que
  `docs/05-BUILDING-BLOCK-VIEW.md`, `docs/BEDROCK-SYSTEM.md` y `src/models/README.md` no
  quedan obsoletos (plan §8).

## Bloque H — Fase 4: revisión y verificación real

- [x] **T-070** `[ux]` (cubre RF-008, RF-009, RF-010) — revisión de `experto-ux-ui` según
  plan §7 (`helpText`, alto de áreas, posición, vacíos en la ficha, contador de
  caracteres, contraste). Resultado en `spec.md §8`. Los ajustes vuelven a T-051.
- [x] **T-071** `[verify]` **[REQUIERE OK DEL USUARIO]** (cubre RF-007) — BD real (plan
  §3/§9): pre-chequeo `alembic_version` == `c7e1a4d92b60` y `\d vacancies`; `pg_dump -Fc`
  previo (ruta de backup registrada); `alembic upgrade head`; `\d vacancies` muestra las
  cuatro columnas `text` nullable y las filas existentes intactas. Si el pre-chequeo no
  cuadra: PARAR y reportar (sin `alembic stamp`).
- [x] **T-072** `[verify]` **[REQUIERE OK DEL USUARIO]** (cubre RF-001..RF-005, RNF-003) —
  rebuild de `api` y `admin` (`up -d --force-recreate --no-deps`, verificar `DATABASE_URL`),
  `GET /health` 200; CRUD en vivo con una vacante de prueba: crear con los cuatro campos,
  actualizar uno sin tocar los otros, limpiar uno con vacío/`null`, rechazo 422 con 10 001
  caracteres, consultar por GET. Borrar la vacante de prueba. Evidencia pegada.
- [x] **T-073** `[ops]` (cubre RF-006) — confirmar que **no** se hace reindex de la KB
  (spec §2: no aplica) y registrar la exclusión transitoria como deuda a retirar en la spec
  009. Si el usuario pidiera reindex, requiere su autorización explícita (coste Bedrock,
  Art. 5).

## Evidencia (salida real pegada)

**T-071 (2026-10-13, OK del usuario):** pre-chequeo `alembic_version` = `c7e1a4d92b60`;
`vacancies` sin las cuatro columnas; 3 filas (vac-122, vac-137, vac-138). Backup
`pg_dump -Fc` → `/mnt/disco2/cjhirashi-data/backups/career_db_pre_008_20261013_170216.dump`
(903 650 B, 67 TABLE DATA). `docker compose run --rm --no-deps api` (imagen nueva,
`DATABASE_URL` → `postgresql+asyncpg://***@postgres:5432/career_db`): `alembic current`
`c7e1a4d92b60` → `upgrade head` → `d8f2b5a13c97 (head)`. Después:
```
candidate_profile|text|YES|
company_overview|text|YES|
offer_summary|text|YES|
work_culture|text|YES|
vac-122|applied|t
vac-137|not_applied|t
vac-138|not_applied|t
```
(filas intactas, las cuatro columnas en `NULL`).

**T-072 (2026-10-13, OK del usuario):** `docker compose build api admin` →
`up -d --force-recreate --no-deps api admin`; api `healthy`, `DATABASE_URL` →
`career_db`; `GET /api/health` 200; Admin `/` 200. CRUD en vivo sobre
`https://admin.cjhirashi.com/api/career/vacancies`:
```
== CREATE
{'id': 'vac-142', 'company_overview': 'Empresa de prueba.\n\nSegundo párrafo.', 'candidate_profile': 'Python', 'offer_summary': 'Remoto', 'work_culture': 'Colaborativa'}
== UPDATE solo offer_summary
{'company_overview': 'Empresa de prueba.\n\nSegundo párrafo.', 'candidate_profile': 'Python', 'offer_summary': 'Remoto + bonos', 'work_culture': 'Colaborativa'}
== LIMPIAR (vacío y null)
{'company_overview': 'Empresa de prueba.\n\nSegundo párrafo.', 'candidate_profile': None, 'offer_summary': 'Remoto + bonos', 'work_culture': None}
== 10001 chars
{"detail":"Error de validación","errors":[{"type":"string_too_long","loc":["body","company_overview"],"msg":"String should have at most 10000 characters", …
HTTP 422
== 10000 chars
HTTP 200
== GET
vac-142 'Empresa de prueba.\n\nSegundo párrafo.' None 10000 None
== DELETE
HTTP 204
GET tras borrar HTTP 404
```
(el create con espacios al inicio/fin se guardó recortado; el 422 no alteró `company_overview`).

**T-073:** sin reindex de la KB (spec §2). La exclusión transitoria de los cuatro campos en
`_KB_EXCLUDED_COLUMNS` queda registrada como deuda a retirar por la spec 009 (RF-010 de 009).

**T-070:** revisión UX sin bloqueantes; decisiones en `spec.md §8`; `helpText` breve aplicado en
`careerResources.ts` (aserción en `vacanciesConfig.test.ts`).

**T-042** (Postgres 15 desechable, eliminado; `upgrade`/`downgrade` vía `alembic.Operations`):
```
before cols: {}
after upgrade: {'candidate_profile': ('text', 'YES'), 'company_overview': ('text', 'YES'), 'offer_summary': ('text', 'YES'), 'work_culture': ('text', 'YES')}
[('vac-1', 'ACME', 'n1', None, None, None, None), ('vac-2', 'Beta', None, None, None, None, None)]
upgrade again OK (idempotent)
after downgrade: {}
[('vac-1', 'ACME', 'n1'), ('vac-2', 'Beta', None)]
after re-upgrade: {'candidate_profile': ('text', 'YES'), 'company_overview': ('text', 'YES'), 'offer_summary': ('text', 'YES'), 'work_culture': ('text', 'YES')}
[('vac-1', 'ACME', 'n1', None, None, None, None), ('vac-2', 'Beta', None, None, None, None, None)]
```

**T-043** (`pytest` completo de la API):
```
================= 575 passed, 73 skipped, 5 warnings in 7.74s ==================
```

**T-053** (Vitest completo Admin; `npm run type-check` exit 0):
```
    at startTests (file:///mnt/disco2/cjhirashi-data/proyectos/cjhirashi-career/cjhirashi-career-admin/node_modules/@vitest/runner/dist/index.js:967:3)
 Test Files  46 passed (46)
      Tests  491 passed (491)
```

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)

| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-010, T-011, T-020, T-030, T-072 | test_vacancy_descriptive_texts | Pass |
| RF-002 | T-001, T-002, T-010, T-011, T-030 | test_vacancy_descriptive_texts | Pass |
| RF-003 | T-001, T-002, T-020, T-030 | test_vacancy_descriptive_texts | Pass |
| RF-004 | T-001, T-002, T-030, T-072 | test_vacancy_descriptive_texts | Pass |
| RF-005 | T-001, T-002, T-030, T-072 | test_vacancy_descriptive_texts | Pass |
| RF-006 | T-021, T-022, T-073 | test_vacancy_descriptive_texts | Pass |
| RF-007 | T-040, T-041, T-042, T-071 | test_vacancy_descriptive_texts_migration | Pass |
| RF-008 | T-050, T-051, T-052, T-070 | vacanciesConfig.test · VacancyDescriptiveTexts.test | Pass |
| RF-009 | T-052, T-070 | VacancyDescriptiveTexts.test | Pass |
| RF-010 | T-050, T-051, T-052, T-070 | vacanciesConfig.test · VacancyDescriptiveTexts.test | Pass |
| RNF-001 | T-043, T-053 | cobertura ≥ 80 % por módulo (pytest-cov / Vitest) | Pass |
| RNF-002 | T-001, T-021 | tests sin Bedrock ni Qdrant reales | Pass |
| RNF-003 | T-071, T-072 | verificación en vivo (evidencia pegada) | Pass |
| doc: career-search/README | T-060 | — | hecho |
