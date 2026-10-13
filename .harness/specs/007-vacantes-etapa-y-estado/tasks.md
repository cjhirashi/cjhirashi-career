---
titulo: "Tasks — Vacantes: etapa del proceso y estado calculado"
tipo: tasks
estado: approved
fecha: 2026-10-12
feature_id: "007"
spec: ./spec.md
plan: ./plan.md
---

# Tareas (atómicas, TDD, test antes que código)

Marcar `[x]` sólo con salida de terminal **pegada** (corrección del usuario en
`state.md`, 2026-09-02). Nunca "salida esperada". El revisor re-ejecuta, no confía en el
reporte. Anotación de tests: pytest `@pytest.mark.requisito("RF-0NN")`; Vitest
`describe("RF-0NN: …")`. Canon de tests: `contracts/process-stage-catalog.json`.

Rutas API relativas a `cjhirashi-career-api/`; Admin a `cjhirashi-career-admin/`.

## Bloque A — API: catálogo y reglas puras (`services/vacancy_stage.py`)

- [x] **T-001** `[test]` (cubre RF-004, RF-017) — `tests/unit/test_vacancy_process_stage.py`:
  `PROCESS_STAGES`/`STAGE_TO_STATUS` == contrato JSON (valores y orden);
  `vacancy_status_for` de las 13 etapas, nunca nulo; `stages_for_statuses` de cada
  estado, de dos estados, y de sólo inválidos → vacío. Rojo.
- [x] **T-002** `[test]` (cubre RF-002, RF-005, RF-021, RF-022, RF-023) — mismo archivo:
  `prepare_vacancy_write` con reloj inyectable: etapa fuera de catálogo → `ValueError`;
  `process_stage=None` → `ValueError`; quita `vacancy_status` y
  `process_stage_updated_at`; Create fija el instante UTC; Update con etapa distinta lo
  fija; Update con etapa omitida o igual no lo incluye. Rojo.
- [x] **T-003** `[code]` (cubre RF-002, RF-004, RF-005, RF-017, RF-021..023) — crear
  `src/services/vacancy_stage.py` según plan §1. Verde T-001, T-002.

## Bloque B — API: modelo y schemas

- [x] **T-010** `[test]` (cubre RF-001, RF-003, RF-005, RF-006, RF-023) — mismo archivo:
  `Vacancy(...)` sin etapa → `not_applied` tras flush y `process_stage_updated_at` no
  nulo; INSERT/UPDATE directo con etapa fuera de catálogo → `IntegrityError` (CHECK);
  schemas: Create sin campo → `not_applied`; Create/Update descartan `vacancy_status` y
  `process_stage_updated_at`; Update con `process_stage: null` → error de validación;
  `VacancyResponse` expone `vacancy_status` calculado. Rojo.
- [x] **T-011** `[code]` (cubre RF-001, RF-003, RF-006) — `src/models/vacancy.py`:
  `process_stage` (NOT NULL, default/server_default, index, CHECK con nombre desde
  `PROCESS_STAGES`) + `process_stage_updated_at`; quitar `application_status`.
- [x] **T-012** `[code]` (cubre RF-001, RF-002, RF-004, RF-005, RF-023) —
  `src/schemas/career_search.py`: `ProcessStageLiteral`, Create/Update/Response,
  `model_validator` para `null`, `@computed_field vacancy_status`. Verde T-010.

## Bloque C — API: repositorio (escritura, filtro, KB)

- [x] **T-020** `[test]` (cubre RF-001, RF-002, RF-003, RF-005, RF-021, RF-022, RF-023) —
  mismo archivo, con `db_session`: `CareerRepository` de `vacancies` (vía tools): create
  sin etapa, etapa inválida → `ValueError` sin `IntegrityError` ni sesión rota,
  `vacancy_status`/`process_stage_updated_at` en `data` ignorados, update de otro campo y
  update con la misma etapa no mueven la fecha, update con etapa nueva sí. Rojo.
- [x] **T-021** `[code]` (mismos RF) — rama `resource_key == "vacancies"` en
  `create_for_user`/`update_for_user` de `src/repositories/career_repository.py` que delega
  en `prepare_vacancy_write`. Verde T-020.
- [x] **T-022** `[test]` (cubre RF-017) — mismo archivo: `list`/`count` con filtro
  `vacancy_status` (cada estado; dos estados) devuelven exactamente las etapas del
  contrato; estado inválido → 0 filas; `vacancy_status` + `process_stage` se intersectan;
  `count` == `len(list)`; regresión R-6: el filtro por columna de otro recurso no cambia.
  Rojo.
- [x] **T-023** `[code]` (cubre RF-017) — expansión de `vacancy_status` en
  `_apply_filters`, sólo para `vacancies`. Verde T-022.
- [x] **T-024** `[test]` (cubre RF-023, D-13) — mismo archivo: `_record_to_text` de una
  `Vacancy` contiene `process_stage` y no contiene `process_stage_updated_at` ni
  `vacancy_status`. Rojo.
- [x] **T-025** `[code]` (cubre RF-023, D-13) — `_KB_EXCLUDED_COLUMNS` en
  `_record_to_text`. Verde T-024.

## Bloque D — API: ruta HTTP y job discovery

- [x] **T-030** `[test]` (cubre RF-001..005, RF-017, RF-021..023) — mismo archivo, con
  `async_client` + JWT sobre `/career/vacancies`: POST/PUT con cada etapa del contrato
  devuelve el valor + `vacancy_status`; etapa inválida → 422 (formato vigente, D-14) y GET posterior sin
  cambio; `process_stage: null` → 422; POST/PUT con `vacancy_status`/
  `process_stage_updated_at` no se persisten; GET con `filters={"vacancy_status":[...]}`.
  Si exige Postgres, usar el fixture PG-only existente. Debe quedar verde sin código nuevo
  (lo cubren T-003..T-025); si falla, se corrige en la capa responsable.
- [x] **T-031** `[test]` (cubre RF-003) — mismo archivo: la vacante guardada por
  `services/job_discovery/service.py` queda `not_applied` con fecha de etapa. Verde sin
  cambio de código.

## Bloque E — API: migración `c7e1a4d92b60`

- [x] **T-040** `[test]` (cubre RF-006, RF-007, RF-008, RF-009, RF-024) —
  `tests/unit/test_vacancy_process_stage_migration.py` con dobles (patrón
  `test_methodology_section_ids_migration.py`): `down_revision == "a9b1c2d3e4f5"`; copia
  literal del catálogo == contrato; preflight con `"foo"` lanza antes de cualquier
  `ALTER`/`CREATE CONSTRAINT`; orden de pasos de upgrade (rename, NULL→`not_applied`,
  fecha con `COALESCE(updated_at, created_at, now())`, CHECK); idempotencia; downgrade
  en orden inverso. Rojo.
- [x] **T-041** `[code]` (mismos RF) — `alembic/versions/c7e1a4d92b60_vacancy_process_stage.py`
  según plan §3. Verde T-040.
- [x] **T-042** `[verify]` (cubre RF-006, RF-007, RF-008, RF-009, RF-024) — en un clon
  **desechable** de Postgres (`TEST_DATABASE_URL`): upgrade → CHECK rechaza valor
  inválido, NULL→`not_applied`, fecha rellenada en los 3 casos; downgrade → vuelve
  `application_status` sin la fecha; upgrade de nuevo. Salida pegada. Nunca en prod.
- [x] **T-043** `[test]` regresión API — `pytest` completo de la API (incluye
  `test_vacancy_duplicate_url.py`, `test_vacancy_target_company_fk.py`,
  `test_job_discovery.py`). Salida pegada, 0 fallos.

## Bloque F — Admin

- [ ] **T-050** `[test]` (cubre RF-011, RF-012, RF-013, RF-015, RF-016, RF-017, RF-018,
  RF-019, RF-020, RF-025) — `src/tests/config/vacanciesConfig.test.ts`: opciones de etapa
  == contrato (valor, etiqueta, orden); label y helpText literales de RF-016; colores de
  las 13 etapas y 3 estados; colores sólo de la unión existente de `Badge`; "Sin
  definir"/`slate` ante `null`/`''`/`'zzz'`; orden exacto de columnas (RF-015);
  `filterFields` con `vacancy_status` (3 opciones) y ausente de `fields`; ni
  `vacancy_status` ni `process_stage_updated_at` en `fields`; columna fecha con
  `format: 'date'`. Rojo.
- [ ] **T-051** `[code]` (cubre RF-011..013, RF-015..020, RF-025) — `src/types/career.ts`
  (uniones y `Vacancy`) + `src/config/careerResources.ts` (`ColumnConfig.badgeLabel`,
  `ResourceConfig.filterFields`, catálogo, funciones de color/etiqueta, columnas, campo).
  Verde T-050.
- [ ] **T-052** `[test]` (cubre RF-010, RF-014, RF-017, RF-019, RF-025) —
  `src/tests/components/career/VacancyBadges.test.tsx`: la fila muestra dos badges con
  "Entrevista RH"/"En proceso" y no `hr_interview`/`in_process`; valor fuera de catálogo
  muestra "Sin definir" sin romper; encabezados de Estado y Etapa con botón de filtro; el
  formulario no tiene control `vacancy_status`; la fecha sin hora; no regresión de
  `cv-versions.status`; preferencia guardada con `application_status` no rompe (R-5).
  Rojo.
- [ ] **T-053** `[code]` (cubre RF-010, RF-014, RF-017, RF-019) —
  `src/components/career/CareerResourceView.tsx`: prioridad opt-in de la rama badge con
  `badgeLabel` en `renderListCell`; `listHeaderExtra` busca en `filterFields` y luego en
  `fields`. Verde T-052.
- [ ] **T-054** `[test]` regresión Admin — suite Vitest completa + `npm run type-check` +
  `npm run lint`. Salida pegada, 0 fallos.

## Bloque G — Documentación

- [ ] **T-060** `[doc]` — `cjhirashi-career-api/docs/sections/career-search/README.md`:
  subsección "Etapa y estado de la vacante" (catálogo, mapeo, campos de sólo lectura,
  reglas de la fecha, filtro por estado, 422).
- [ ] **T-061** `[doc]` — `docs/05-BUILDING-BLOCK-VIEW.md` líneas ~250, ~287, ~323 al
  vocabulario `process_stage`/`vacancy_status` e índice `ix_vacancies_process_stage`.

## Bloque H — Fase 4: revisión y verificación real

- [ ] **T-070** `[ux]` (cubre RF-010..RF-020, RF-025) — revisión de `experto-ux-ui` según
  plan §7, con contraste **medido** de cada color de badge (RF-018). Resultado en
  `spec.md §8`.
- [ ] **T-071** `[verify]` (cubre RF-006, RF-007, RF-024) — BD real (plan §3/§8):
  pre-chequeo `alembic_version` == `a9b1c2d3e4f5`, `\d vacancies`, valores actuales;
  `pg_dump`; `alembic upgrade head`; `\d vacancies` muestra CHECK, NOT NULL, fecha. Si el
  pre-chequeo no cuadra: PARAR y reportar (sin `alembic stamp`). **Requiere OK del
  usuario antes de ejecutar.**
- [ ] **T-072** `[verify]` (cubre RF-001, RF-004, RF-010, RF-017, RF-021) — rebuild de
  `api` y `admin` (`up -d --force-recreate --no-deps`, verificar `DATABASE_URL`),
  `GET /health` 200, crear/actualizar una vacante en vivo y filtrar por estado. Evidencia
  pegada.
- [ ] **T-073** `[ops]` — reindex de la KB + `scripts/check_kb_consistency.py`. **Sólo con
  autorización explícita del usuario en ese momento** (coste Bedrock, D-13). Si no se
  autoriza, se registra como pendiente.

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)

| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-010, T-011, T-012, T-020, T-021, T-030, T-072 | test_vacancy_process_stage | — |
| RF-002 | T-002, T-003, T-012, T-020, T-021, T-030 | test_vacancy_process_stage | — |
| RF-003 | T-010, T-011, T-020, T-021, T-030, T-031 | test_vacancy_process_stage | — |
| RF-004 | T-001, T-003, T-012, T-030, T-072 | test_vacancy_process_stage | — |
| RF-005 | T-002, T-003, T-010, T-012, T-020, T-021, T-030 | test_vacancy_process_stage | — |
| RF-006 | T-010, T-011, T-040, T-041, T-042, T-071 | test_vacancy_process_stage · test_vacancy_process_stage_migration | — |
| RF-007 | T-040, T-041, T-042, T-071 | test_vacancy_process_stage_migration | — |
| RF-008 | T-040, T-041, T-042 | test_vacancy_process_stage_migration | — |
| RF-009 | T-040, T-041, T-042 | test_vacancy_process_stage_migration | — |
| RF-010 | T-052, T-053, T-070, T-072 | VacancyBadges.test | — |
| RF-011 | T-050, T-051, T-070 | vacanciesConfig.test | — |
| RF-012 | T-050, T-051, T-070 | vacanciesConfig.test | — |
| RF-013 | T-050, T-051, T-070 | vacanciesConfig.test | — |
| RF-014 | T-052, T-053, T-070 | VacancyBadges.test | — |
| RF-015 | T-050, T-051, T-070 | vacanciesConfig.test | — |
| RF-016 | T-050, T-051, T-070 | vacanciesConfig.test | — |
| RF-017 | T-001, T-003, T-022, T-023, T-030, T-050, T-051, T-052, T-053, T-072 | test_vacancy_process_stage · vacanciesConfig.test · VacancyBadges.test | — |
| RF-018 | T-050, T-070 | vacanciesConfig.test · revisión UX (contraste medido) | — |
| RF-019 | T-050, T-051, T-052, T-053 | vacanciesConfig.test · VacancyBadges.test | — |
| RF-020 | T-050, T-051, T-052 | vacanciesConfig.test · VacancyBadges.test | — |
| RF-021 | T-002, T-003, T-020, T-021, T-030, T-072 | test_vacancy_process_stage | — |
| RF-022 | T-002, T-003, T-020, T-021, T-030 | test_vacancy_process_stage | — |
| RF-023 | T-002, T-003, T-010, T-012, T-020, T-021, T-024, T-025, T-030 | test_vacancy_process_stage | — |
| RF-024 | T-040, T-041, T-042, T-071 | test_vacancy_process_stage_migration | — |
| RF-025 | T-050, T-051, T-052 | vacanciesConfig.test · VacancyBadges.test | — |
| doc: career-search/README | T-060 | — | — |
| doc: 05-BUILDING-BLOCK-VIEW | T-061 | — | — |
