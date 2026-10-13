---
titulo: "Plan — Vacantes: etapa del proceso y estado calculado"
tipo: plan
estado: verified
fecha: 2026-10-12
feature_id: "007"
spec: ./spec.md
---

# Plan de implementación

Conforme al patrón por capas (Constitución Art. 1–2): API `routes → services →
repositories → models`; Admin `components → config/types`. La lógica de negocio (catálogo,
mapeo etapa→estado, reglas de escritura) vive en `services/`, no en rutas ni en el modelo.

## 1 · Diseño por capa

### API (`cjhirashi-career-api`)

| Capa | Archivo | Cambio |
|---|---|---|
| services (nuevo) | `src/services/vacancy_stage.py` | Funciones puras y sin BD: `PROCESS_STAGES` (tupla en orden canónico), `STAGE_TO_STATUS`, tipos `ProcessStage` / `VacancyStatus` (Literal), `vacancy_status_for(stage)`, `READ_ONLY_VACANCY_FIELDS = {"vacancy_status", "process_stage_updated_at"}`, `stages_for_statuses(values)` (estados → etapas, inverso de `STAGE_TO_STATUS`; ignora estados desconocidos), `prepare_vacancy_write(data, current_stage=None, now=None)` (quita campos de sólo lectura, valida el catálogo, rechaza `process_stage=None`, fija `process_stage_updated_at` sólo si es Create o la etapa cambia). Precedente de modelo→services: `services.id_generator`. |
| models | `src/models/vacancy.py` | `application_status` → `process_stage = Column(String(30), nullable=False, default="not_applied", server_default="not_applied", index=True)`; nueva `process_stage_updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())`; `CheckConstraint(... IN (<catálogo>), name="ck_vacancies_process_stage")` construido desde `PROCESS_STAGES` (un solo canon en código). |
| schemas | `src/schemas/career_search.py` | `VacancyBase`: `process_stage: ProcessStageLiteral = "not_applied"` (sustituye a `application_status`). `VacancyUpdate`: `process_stage: Optional[ProcessStageLiteral] = None` + `model_validator(mode="after")` que da 422 si `process_stage` está en `model_fields_set` con valor `None` (§5). `VacancyResponse`: `process_stage_updated_at: datetime` y `@computed_field vacancy_status` = `vacancy_status_for(process_stage)`. Create/Update NO declaran `vacancy_status` ni `process_stage_updated_at`: Pydantic (extra=ignore por defecto) los descarta (RF-005, RF-023). |
| repositories | `src/repositories/career_repository.py` | En `create_for_user` / `update_for_user`, rama `resource_key == "vacancies"` (mismo patrón que `agent-tasks`/`projects`) que delega en `vacancy_stage.prepare_vacancy_write`. Razón: el repositorio es el único punto común a REST **y** a las tools de Bedrock (`create_career_record`/`update_career_record` en `bedrock_service.py:468/493`, que no pasan por Pydantic y hoy podrían escribir `process_stage_updated_at` o una etapa inválida, provocando `IntegrityError` y sesión sin rollback). **Filtro por Estado (RF-017, D-10):** `_apply_filters` expande, solo para `resource_key == "vacancies"`, la clave virtual `vacancy_status` a `process_stage IN (stages_for_statuses(...))` (mismo mapeo, un solo canon); si además llega un filtro `process_stage`, se intersectan (AND); si se pide `vacancy_status` y ninguno de sus valores es válido, no devuelve filas (no se ignora el filtro). Cubre `list` y `count`, que comparten `_apply_filters`. **Exclusión de la KB (D-13):** `_record_to_text` omite las columnas listadas en un mapa `_KB_EXCLUDED_COLUMNS = {"vacancies": {"process_stage_updated_at"}}`; `_indexable_columns` (lista de campos válidos de las tools) no cambia. `vacancy_status` no es columna, así que nunca entra al texto. `updated_at`/`created_at` ya se indexaban y quedan fuera de D-13. El `ValueError` ya se traduce a 400 en la ruta genérica y a error de tool en el agente; en REST el 422 llega antes, por Pydantic. |
| routes | `src/routes/career_search.py`, `career_common.py` | **Sin cambios.** El router genérico ya usa los schemas; el 422 lo da el handler global de validación existente. |
| services (existente) | `services/job_discovery/service.py:257` | **Sin cambios de código:** `Vacancy(...)` toma los defaults del modelo (`not_applied`, `now()`); se fija con test (RF-003). |
| migración | `alembic/versions/c7e1a4d92b60_vacancy_process_stage.py` | Ver §3. |

### Admin (`cjhirashi-career-admin`)

| Capa | Archivo | Cambio |
|---|---|---|
| types | `src/types/career.ts` | Uniones `ProcessStage` (13) y `VacancyStatus` (3). En `Vacancy`: quitar `application_status`; añadir `process_stage: ProcessStage`, `vacancy_status: VacancyStatus`, `process_stage_updated_at: ISODateTime`. |
| config | `src/config/careerResources.ts` | `ColumnConfig.badgeLabel?: (value: unknown) => string` (RF-014). Constantes `VACANCY_STAGE_OPTIONS` (orden canónico, etiquetas §3), `VACANCY_STATUS_LABELS` y funciones `vacancyStageBadgeColor`, `vacancyStatusBadgeColor`, `vacancyStageLabel`, `vacancyStatusLabel` con respaldo "Sin definir"/`slate` (RF-019). `vacanciesConfig.columns` en el orden de RF-015: Empresa, Rol, Estado (`vacancy_status`), Etapa (`process_stage`), En etapa desde (`process_stage_updated_at`, `format: 'date'`), Fit %, Evaluación, Ubicación, Encontrada, Activa. Nuevo `ResourceConfig.filterFields?: FieldConfig[]` (campos **solo de filtro**, no del formulario ni de la ficha) y en `vacanciesConfig` uno `{ name: 'vacancy_status', type: 'select', label: 'Estado', options: [Por postular/En proceso/Cerrada] }` (RF-017). `fields`: reemplazar `application_status` por `process_stage` (`type: 'select'`, label "Etapa del proceso", `options` = `VACANCY_STAGE_OPTIONS`, helpText de RF-016). `vacancy_status` y `process_stage_updated_at` NO son `fields` (RF-020, RF-025). |
| components | `src/components/career/CareerResourceView.tsx` (`renderListCell`, ~1250, y `listHeaderExtra`, ~1269) | Hoy la rama `isSelectField(field)` va antes que la de badge, así que `process_stage` (campo `select`) se pintaría como cápsula y no como badge coloreado. Cambio mínimo y opt-in: si la columna define `badgeLabel`, la rama badge tiene prioridad sobre la de select y se ejecuta también con valor vacío/fuera de catálogo; el texto es `col.badgeLabel(value)` (si no hay `badgeLabel`, se conserva `String(value)` → el resto de recursos, p. ej. `cv-versions.status`, no cambia). `listHeaderExtra` busca el campo filtrable primero en `config.filterFields` y luego en `config.fields`; así `vacancy_status` obtiene `ColumnFilterButton` sin ser campo de formulario y sin tocar `ResourceListFilters.tsx` ni `utils/listFilters.ts` (el tipo `select` ya es filtrable y el payload `filters` viaja tal cual al API). |

## 2 · Fronteras y contratos

- **REST `/career/vacancies`** (OpenAPI generado por FastAPI; no hay `openapi.yaml` committeado
  → ningún gate de contrato REST aplica, Art. 6). Request: `process_stage`; Response añade
  `vacancy_status` y `process_stage_updated_at`. 422 (formato vigente del handler global, D-14) fuera de catálogo.
- **BD `vacancies`**: renombre + CHECK `ck_vacancies_process_stage` + NOT NULL/default +
  `process_stage_updated_at` (RF-006/007/024).
- **Tools de Bedrock** (`create_career_record` / `update_career_record`): sin cambio de
  esquema de tool; el repositorio aplica las mismas reglas (ver §1).
- **Catálogo compartido API↔Admin:** `contracts/process-stage-catalog.json` (13 etapas con
  etiqueta y estado + 3 estados). Es el canon de los **tests**: el de API comprueba que
  `PROCESS_STAGES`/`STAGE_TO_STATUS` coinciden; el de Admin que `VACANCY_STAGE_OPTIONS`
  (valor, etiqueta, orden) y las etiquetas de estado coinciden. Detecta deriva sin generar
  código ni añadir dependencias.
- `cjhirashi-career-ai` y Portfolio: sin impacto (verificado con grep: ni `application_status`
  ni lectura de `vacancies` fuera de la API).

## 3 · Migración `c7e1a4d92b60`

- Revision ID **`c7e1a4d92b60`** (verificado: no existe en `alembic/versions/`);
  `down_revision = "a9b1c2d3e4f5"` (único head del grafo de archivos, comprobado con
  script sobre `alembic/versions/*.py`). Archivo `c7e1a4d92b60_vacancy_process_stage.py`.
- **Antes de aplicar (Art. 4):** en la BD real consultar `alembic_version`, `\d vacancies`
  y `SELECT application_status, count(*) FROM vacancies GROUP BY 1`. Si `alembic_version`
  ≠ `a9b1c2d3e4f5` o el esquema difiere del grafo, PARAR y reportar (no hacer
  `alembic stamp` sin autorización humana). Respaldo con `pg_dump` previo.
- `upgrade()` idempotente (patrón `f8a9b1c2d3e4`: `sa.inspect` para detectar el estado) y
  transaccional (DDL de PG), en este orden:
  1. **Preflight (RF-008):** sobre la columna que exista (`application_status` o
     `process_stage`), `SELECT DISTINCT` de valores no nulos fuera del catálogo; si hay,
     `RuntimeError` con la lista, **antes de cualquier DDL**.
  2. `RENAME COLUMN application_status → process_stage` y del índice
     `ix_vacancies_application_status → ix_vacancies_process_stage` (sólo si existen).
  3. `UPDATE ... SET process_stage='not_applied' WHERE process_stage IS NULL`;
     `server_default='not_applied'`; `NOT NULL` (RF-007).
  4. Añadir `process_stage_updated_at` nullable; `UPDATE ... = COALESCE(updated_at, created_at, now())`;
     `server_default=now()`; `NOT NULL` (RF-024).
  5. `CREATE CHECK ck_vacancies_process_stage` si no existe (RF-006). Los 13 valores se
     **copian literalmente** en la migración (una migración no debe importar el catálogo vivo,
     que podría cambiar después); el test de migración compara la copia con el contrato JSON.
- `downgrade()` (RF-009): drop CHECK, drop `process_stage_updated_at`, quitar NOT NULL y
  default de la columna, renombrar `process_stage → application_status` e índice de vuelta.
  Los NULL convertidos a `not_applied` no se restauran (pérdida aceptada, documentada en el
  docstring). Cada paso condicionado a su existencia.

## 4 · Secuenciación (tests antes que código)

Tareas indicativas para `tasks.md` (Fase 3); `[T]`=test rojo primero, `[I]`=implementación.

1. **[T] API:** `tests/unit/test_vacancy_process_stage.py` y
   `tests/unit/test_vacancy_process_stage_migration.py` (rojos). Incluye lectura del
   contrato JSON.
2. **[I] API:** `services/vacancy_stage.py` → modelo → schemas → rama en repositorio (escritura,
   expansión del filtro `vacancy_status`, exclusión KB) → migración. Verde de lo anterior.
3. **[T] Admin:** `src/tests/config/vacanciesConfig.test.ts` y
   `src/tests/components/career/VacancyBadges.test.tsx` (rojos).
4. **[I] Admin:** `types/career.ts` → `careerResources.ts` (`ColumnConfig.badgeLabel`,
   catálogo, columnas, campo, `filterFields`) → `CareerResourceView.tsx` (badge y
   `listHeaderExtra`).
5. **[V] BD real:** pre-chequeo (§3), respaldo, `alembic upgrade head`, verificación de
   esquema, `downgrade`/`upgrade` en clon desechable (`TEST_DATABASE_URL`), nunca en prod
   primero.
6. **[doc]** tareas de §6.
7. **Fase 4:** revisión `experto-ux-ui` (§7) y verificador independiente (cobertura ≥ 80 %
   por módulo tocado; objetivo 90 % del código nuevo).
8. **Operativa post-deploy** (§8): rebuild api+admin, smoke en vivo, reindex KB.

## 5 · Implementación por requisito

### Implementación de RF-001
`schemas/career_search.py` (`process_stage` en Create/Update/Response), `models/vacancy.py`
(columna), rama `vacancies` del repositorio (persiste). Test: POST/PUT con cada etapa del
catálogo devuelve el valor persistido (parametrizado con el contrato JSON).

### Implementación de RF-002
`ProcessStageLiteral` en `schemas/career_search.py` → 422 antes de tocar BD; en el camino de
tools, `vacancy_stage.prepare_vacancy_write` lanza `ValueError` antes del flush. Test: 422 y
la fila no cambia (GET posterior igual); repositorio con valor inválido → `ValueError` sin
`IntegrityError`.

### Implementación de RF-003
Default Pydantic `"not_applied"` + `default`/`server_default` del modelo (cubre también
`services/job_discovery/service.py:257`, que construye `Vacancy` sin el campo). Tests: Create
sin campo; `Vacancy(...)` sin campo tras flush; fila insertada por SQL crudo sin el campo.

### Implementación de RF-004
`@computed_field vacancy_status` en `VacancyResponse` ← `vacancy_status_for()` de
`services/vacancy_stage.py` (función pura, un único mapeo). Test: las 13 etapas contra el
contrato JSON; nunca nulo.

### Implementación de RF-005
`VacancyCreate/Update` no declaran el campo y descartan extras; el repositorio además lo
elimina (camino tools). Test: POST/PUT con `vacancy_status: "closed"` no altera `process_stage`
ni se persiste (no es columna).

### Implementación de RF-006
`CheckConstraint` con nombre en `models/vacancy.py` + creación en la migración. Test: INSERT/UPDATE
directo con valor fuera de catálogo → `IntegrityError` (sqlite en unit; Postgres real en la
verificación de BD).

### Implementación de RF-007
`alembic/versions/c7e1a4d92b60_vacancy_process_stage.py` pasos 2–3. Test de migración con
dobles (patrón `test_methodology_section_ids_migration.py`) + clon PG: valores conservados,
NULL→`not_applied`.

### Implementación de RF-008
Paso 1 de la migración (preflight antes de DDL, `RuntimeError` con valores). Test: con un
valor `"foo"` el upgrade lanza y no se emitió `ALTER`/`CREATE CONSTRAINT`.

### Implementación de RF-009
`downgrade()` de la migración. Test: orden de operaciones y, en clon PG, ciclo
upgrade→downgrade→upgrade conserva valores y deja `application_status` sin
`process_stage_updated_at`.

### Implementación de RF-010
`vacanciesConfig.columns` (Estado y Etapa con `format: 'badge'`) y la prioridad de la rama
badge en `CareerResourceView.renderListCell`. Test de render: la fila muestra dos badges.

### Implementación de RF-011
`vacanciesConfig.fields`: `process_stage` `select` con `VACANCY_STAGE_OPTIONS` (13, orden
canónico); sin campo `vacancy_status`. Test de config (opciones == contrato JSON, ningún
field llamado `vacancy_status`/`process_stage_updated_at`) y de formulario.

### Implementación de RF-012
`vacancyStatusBadgeColor`: `pending`→`slate`, `in_process`→`warning`, `closed`→`slate`;
texto vía `vacancyStatusLabel` ("Por postular" / "En proceso" / "Cerrada"). Test unitario de
la función y de render.

### Implementación de RF-013
`vacancyStageBadgeColor`: `hired`,`offer`→`success`; `rejected`→`error`;
`withdrawn`,`no_response`,`not_applied`→`slate`; `applied`..`final_interview` y
`hiring_process`→`warning`. Test parametrizado de las 13 etapas.

### Implementación de RF-014
`ColumnConfig.badgeLabel` + uso en `CareerResourceView.renderListCell`; las columnas de Estado y
Etapa lo definen con las etiquetas de §3. Test: el DOM contiene "Entrevista RH"/"Cerrada" y
no `hr_interview`/`closed`.

### Implementación de RF-015
Orden del array `vacanciesConfig.columns`. Test: las claves en orden exacto
(`company, exact_role, vacancy_status, process_stage, process_stage_updated_at,
fit_percentage, evaluation, location, found_date, is_active`).

### Implementación de RF-016
Campo `process_stage` en `vacanciesConfig.fields`: label "Etapa del proceso", helpText literal
de RF-016. Test de config (label, helpText, 13 opciones en orden).

### Implementación de RF-017
Backend: `vacancy_stage.stages_for_statuses` + expansión en `CareerRepository._apply_filters`
(§1) → `GET /career/vacancies?filters={"vacancy_status":["closed"]}` devuelve solo vacantes
cuya etapa mapea a ese estado; `count` coherente. Admin: `ResourceConfig.filterFields` con
`vacancy_status` (3 opciones) y búsqueda del campo en `listHeaderExtra`; el campo no está en
`fields`, así que no aparece en el formulario (RF-020). Etapa: `process_stage` es `select`
con 13 opciones → filtrable sin código. Tests API: cada estado (y combinación de dos)
devuelve exactamente las etapas del contrato JSON; estado inválido → sin filas; estado +
`process_stage` se intersectan; `count` igual al `list`; ruta HTTP con `filters` JSON. Tests
Admin: `filterFields` contiene `vacancy_status` con 3 opciones y etiquetas correctas, no está
en `fields`; el encabezado de Estado muestra el botón de filtro y el de Etapa también; el
formulario no tiene el control. Sin ordenación por Estado ni por orden canónico (D-11).

### Implementación de RF-018
Sólo se usan los colores existentes de `Badge` (`slate`, `warning`, `success`, `error`); sin
colores nuevos. Verificación en Fase 4: calcular el contraste real texto/fondo de cada color
en `Badge` (tokens CSS del componente) y adjuntar los números; un test unitario fija que
`badgeColor` sólo devuelve valores de la unión existente.

### Implementación de RF-019
Funciones de `careerResources.ts` devuelven "Sin definir"/`slate` ante vacío, `null` o valor
fuera de catálogo; `renderListCell` ejecuta la rama badge también con valor vacío cuando la
columna define `badgeLabel`. Test: `process_stage` `null`/`''`/`'zzz'` no lanza y muestra
"Sin definir".

### Implementación de RF-020
`vacancy_status` no está en `fields`, por lo que el formulario no lo muestra ni lo envía.
Test: ningún control con `name="vacancy_status"` en el formulario de edición/creación.

### Implementación de RF-021
`vacancy_stage.prepare_vacancy_write` (Create: `now()` UTC; Update: sólo si
`data["process_stage"] != current_stage`), invocado desde `create_for_user`/`update_for_user`.
Test: Create fija el instante; Update con etapa distinta lo avanza (reloj inyectable).

### Implementación de RF-022
Misma función: omitida o igual → no incluye `process_stage_updated_at`. Además
`updated_at` (`onupdate`) no se reutiliza. Test: Update de otro campo y Update con la misma
etapa dejan `process_stage_updated_at` intacto.

### Implementación de RF-023
Schemas no declaran el campo (descartado) + el repositorio lo elimina de `data` (camino de
tools). Test: POST/PUT con `process_stage_updated_at` arbitrario no se persiste; llamada
directa al repositorio con el campo tampoco.

### Implementación de RF-024
Migración paso 4 (`COALESCE(updated_at, created_at, now())`). Test: filas con
`updated_at` nulo/no nulo/ambos nulos (en clon PG, donde las columnas pueden ser nulas por
diseño de datos heredados; en unit con dobles).

### Implementación de RF-025
Columna `process_stage_updated_at` con `format: 'date'` (formateador existente
`formatDate`, solo fecha, D-12) y ausente de `fields`. Test de config (`format === 'date'`, ausente de `fields`) + render del valor sin hora.

## 6 · Estrategia de pruebas por capa

Anotación: pytest `@pytest.mark.requisito("RF-0NN")`; Vitest `describe("RF-0NN: …")`.

| Capa | Archivo | Cubre |
|---|---|---|
| services (unit, puro) | `cjhirashi-career-api/tests/unit/test_vacancy_process_stage.py` | RF-004, RF-002, RF-021/022/023 (función `prepare_vacancy_write`); paridad con `contracts/process-stage-catalog.json` |
| models / schemas (unit) | mismo archivo | RF-001, RF-003, RF-005, RF-006 (CHECK en sqlite), §5 `null` en Update → 422 |
| repositorio (integración con `db_session`) | mismo archivo | RF-001/002/003/021/022/023 con el repositorio real, incluida la vía tools (campos de sólo lectura, etapa inválida) |
| ruta (integración, `async_client` + JWT) | mismo archivo | RF-001..005, 021..023: POST/PUT/GET sobre `/career/vacancies`, 422 sin persistir; si el cliente HTTP exige Postgres, marcar con el fixture PG-only existente |
| KB (unit) | `cjhirashi-career-api/tests/unit/test_vacancy_process_stage.py` | D-13 (sin RF propio; se traza a RF-021/023): `_record_to_text(Vacancy)` no contiene `process_stage_updated_at` ni `vacancy_status` y sí `process_stage`; las tools siguen sin poder fijarla (repositorio); recorre también el camino de `reindex` (comparte `_record_to_text`) |
| job discovery (unit) | mismo archivo | RF-003: la vacante guardada por discovery queda `not_applied` |
| migración (unit con dobles) | `cjhirashi-career-api/tests/unit/test_vacancy_process_stage_migration.py` | RF-007/008/009/024; cadena `down_revision = a9b1c2d3e4f5`; copia del catálogo == contrato JSON |
| migración (clon PG, manual en T de verificación) | `TEST_DATABASE_URL` desechable | RF-006/007/008/009/024 contra Postgres real; evidencia pegada |
| Admin config (Vitest) | `cjhirashi-career-admin/src/tests/config/vacanciesConfig.test.ts` | RF-011, 012, 013, 015, 016, 017, 019, 020, 025; paridad con el contrato JSON |
| Admin render (Vitest) | `cjhirashi-career-admin/src/tests/components/career/VacancyBadges.test.tsx` | RF-010, 014, 017 (botones de filtro), 019, 025 (+ no regresión: badge de `cv-versions.status` sigue como antes) |
| Admin tipos/lint | `npm run type-check`, `npm run lint` | tipos `ProcessStage`/`VacancyStatus` |
| Verificación real (Art. 3) | arranque de api y admin, `GET /health`, flujo CRUD en vivo | evidencia pegada, no "esperada" |

Se ejecutan además los tests existentes que tocan `Vacancy` (`test_vacancy_duplicate_url.py`,
`test_vacancy_target_company_fk.py`, `test_job_discovery.py`) y `CareerResourcePage.test.tsx`
como regresión.

## 7 · Revisión UX/UI (Art. 8) — hueco para Fase 4

La feature toca la interfaz del Admin → antes de `verified` pasa por `experto-ux-ui`.
Puntos a revisar: legibilidad y contraste de los 4 colores (RF-018) con números medidos;
dos badges `slate` con significado distinto (Por postular vs Cerrada) separados sólo por
texto (RF-014); filtro por Estado y por Etapa (RF-017; sin ordenación por Estado, D-11); posición del campo en el
formulario; vista de detalle del registro (muestra `process_stage` como cápsula de
`select`, no como badge). El resultado se registra en el §8 de `spec.md`.

## 8 · Operativa de datos y despliegue

- **Migración en BD real:** procedimiento de §3 (pre-chequeo, respaldo, upgrade, verificación
  de `\d vacancies` y de las 3 filas actuales = `not_applied`).
- **Reindex de la KB: paso de deploy que NO es automático.** `_record_to_text` serializa cada
  columna como `col: valor`; las 3 vacantes indexadas tienen `application_status: not_applied`
  en su texto/embedding y tras el renombre pasan a `process_stage: …`
  (`process_stage_updated_at` queda fuera por D-13). Tras el deploy corresponde
  `POST /bedrock/knowledge-base/reindex` y `scripts/check_kb_consistency.py` (0 huérfanos),
  pero el reindex llama a Bedrock embeddings (coste, Art. 5): **se ejecuta solo si el usuario
  lo autoriza explícitamente en ese momento**, registrando el coste. Sin autorización, las
  3 filas se refrescan solas en su próxima escritura.
- Reconstruir `api` y `admin` (`docker compose build/up`) y smoke en vivo: crear/actualizar
  una vacante, comprobar `vacancy_status` y `process_stage_updated_at`.

## 9 · Impacto en documentación (Art. 11)

| Documento | Ruta | Qué queda obsoleto | Tarea |
|---|---|---|---|
| Sección Career Search (API) | `cjhirashi-career-api/docs/sections/career-search/README.md` | Tabla de `vacancies` (línea ~47) y ejemplos no describen etapa/estado, el catálogo de 13 etapas, el cálculo de `vacancy_status` ni `process_stage_updated_at`; no refleja la regla 422 | `[doc]` Añadir subsección "Etapa y estado de la vacante" (catálogo, mapeo, campos de sólo lectura, reglas de actualización) |
| arc42 · vista de bloques | `docs/05-BUILDING-BLOCK-VIEW.md` | Línea 287 ("con estado del proceso"), línea 250 (`VacancyBoard` con estados `wishlist/applied/…`) y línea 323 (`idx_vacancies_status`) ya no coinciden con `process_stage` / `vacancy_status` ni con el índice `ix_vacancies_process_stage` | `[doc]` Actualizar las tres filas al vocabulario nuevo (nota: dos de ellas ya estaban desfasadas; se corrigen al tocar el mismo concepto) |

No tocan documentación: `src/models/README.md` (línea 74 es una descripción genérica de
`vacancy.py`), `docs/ADMIN_PANEL_SETUP.md`, `docs/ENVIRONMENT-SECURITY.md`, `caddy.json`,
`docker-compose.yml` (sin variables, puertos ni servicios nuevos), ADRs de producto (la
revisión de D-03 de spec 006 es una decisión de feature, registrada en D-02 de esta spec),
`docs/BEDROCK-SYSTEM.md` (las tools no cambian de contrato; sólo rechazan campos de sólo
lectura). `cjhirashi-career-api/docs/DATABASE.md` no lista columnas de `vacancies`.

## 10 · Preguntas abiertas y riesgos

- Sin preguntas abiertas: OQ-1..OQ-4 resueltas por el usuario (D-10..D-13).
- **Riesgo R-1 (BD real).** Grafo de archivos con único head `a9b1c2d3e4f5`, pero la dev DB
  no trackea Alembic del todo (state.md, Art. 4): la verificación previa de §3 es obligatoria.
- **Riesgo R-3 (tools de Bedrock).** `_invalid_fields_error` acepta `process_stage_updated_at`
  como "campo válido" (es columna) y el repositorio lo descarta en silencio; el agente verá un
  éxito sin efecto para ese campo. Aceptable; alternativa (rechazarlo con error) sería tocar
  `bedrock_service.py`.
- **Riesgo R-6 (filtro por Estado).** `_apply_filters` gana una rama específica de `vacancies`; el resto de recursos no cambia (test de regresión del filtro por columna). Un filtro `vacancy_status` con solo valores inválidos devuelve vacío por diseño.
- **Riesgo R-4 (contrato JSON).** Los tests leen
  `.harness/specs/007-vacantes-etapa-y-estado/contracts/process-stage-catalog.json` por ruta
  relativa al repo; si los servicios se testean en un contexto Docker sin `.harness/`, esos
  tests fallarían (no se saltan en silencio).
- **Riesgo R-5 (preferencias de columnas del Admin).** `useVisibleTableColumns` guarda claves
  de columnas por usuario; una selección guardada que incluya `application_status` dejará de
  encontrarla (se espera que el resolver las ignore: comprobar en el test de render).
