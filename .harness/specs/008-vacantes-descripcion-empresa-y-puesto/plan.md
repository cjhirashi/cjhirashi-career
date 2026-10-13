---
titulo: "Plan — Vacantes: quiénes son, qué buscan, qué ofrecen y cultura laboral"
tipo: plan
estado: approved
fecha: 2026-10-13
feature_id: "008"
spec: ./spec.md
---

# Plan de implementación

Conforme al patrón por capas (Constitución Art. 1–2): API `routes → services →
repositories → models`; Admin `components → config/types`. Feature de datos puros: no hay
lógica de negocio nueva salvo la normalización de texto (trim, vacío → `NULL`, tope de
longitud), que vive en el **schema** (frontera de validación de entrada) y no en rutas ni
modelo. Sin cambios en `cjhirashi-career-ai` ni en el Portfolio.

## 1 · Diseño por capa

### API (`cjhirashi-career-api`)

| Capa | Archivo | Cambio |
|---|---|---|
| models | `src/models/vacancy.py` | Cuatro `Column(Text, nullable=True)` sin default: `company_overview`, `candidate_profile`, `offer_summary`, `work_culture`, junto a `analysis_notes`. |
| schemas | `src/schemas/career_search.py` | Alias `VacancyLongText = Annotated[Optional[str], BeforeValidator(_trim_or_none), StringConstraints(max_length=10_000)]` (o `field_validator` equivalente declarado una vez y reutilizado). `_trim_or_none`: `str` → `strip()`, vacío → `None`; no-str pasa tal cual (que Pydantic rechace). La longitud se valida **después** del trim (10 000 caracteres de contenido útil). Se declaran en `VacancyBase` (por tanto en `VacancyResponse`, RF-002) y en `VacancyUpdate` como `Optional[...] = None`. `null` explícito en Update llega a `None` y borra (§5); omitir el campo no lo incluye en `model_dump(exclude_unset=True)` (RF-003). |
| repositories | `src/repositories/career_repository.py` | Una línea: `_KB_EXCLUDED_COLUMNS["vacancies"]` pasa de `frozenset({"process_stage_updated_at"})` a incluir además los cuatro campos (RF-006, transitorio, D-05; comentario `# TRANSITORIO: se retira con la spec 009`). Sin otra lógica: `create_for_user`/`update_for_user` ya persisten cualquier columna válida; `_indexable_columns` (campos válidos de las tools) no cambia, así que los agentes de Bedrock **pueden** escribirlos. |
| routes | `src/routes/career_search.py`, `career_common.py` | **Sin cambios.** El 422 lo da el handler global de validación (formato `{"detail","errors"}`, 007 D-14). |
| tools Bedrock | `services/bedrock_service.py` | **Sin cambios.** `create/update_career_record` pasan por el repositorio, pero **no por Pydantic**: el trim, el vacío → `NULL` y el tope de 10 000 NO se aplicarían por esa vía. Decisión D-07: la normalización y el tope rigen sólo para REST; la spec 009 mueve el harness y escribirá vía REST. Riesgo R-1. |
| services (existente) | `services/job_discovery/service.py` | **Sin cambios**; no rellena los campos (fuera de alcance). |
| migración | `alembic/versions/d8f2b5a13c97_vacancy_descriptive_texts.py` | Ver §3. |

### Admin (`cjhirashi-career-admin`)

| Capa | Archivo | Cambio |
|---|---|---|
| types | `src/types/career.ts` | En `Vacancy`: `company_overview?`, `candidate_profile?`, `offer_summary?`, `work_culture?` como `string \| null`, junto a `analysis_notes`. |
| config | `src/config/careerResources.ts` | `vacanciesConfig.fields`: cuatro campos `type: 'textarea'`, `fullWidth: true`, **contiguos** y en el orden canónico, con etiquetas "Quiénes son", "Qué buscan", "Qué ofrecen", "Cultura laboral". Posición propuesta: tras `contact_id` y antes de `analysis_notes` (UX confirma, §7). `vacanciesConfig.columns` **no cambia** (RF-010). `helpText`/alto de las áreas: pendiente de `experto-ux-ui` (§7). |
| components | `src/components/career/CareerResourceView.tsx` | **Sin cambios** (D-06): la ficha usa el renderizado Markdown vigente del `textarea`; un salto simple se colapsa y los párrafos se separan con línea en blanco. |

## 2 · Fronteras y contratos

- **REST `/career/vacancies`** (OpenAPI generado por FastAPI; no hay `openapi.yaml`
  committeado → ningún gate de contrato REST aplica, Art. 6). Request: cuatro campos
  opcionales; Response: los devuelve siempre (valor o `null`); 422 si > 10 000.
- **BD `vacancies`**: cuatro columnas `text` nullable sin default (RF-007).
- **Tools Bedrock**: sin cambio de esquema de tool (D-07).
- **KB**: exclusión transitoria en `_KB_EXCLUDED_COLUMNS` (RF-006).
- **Sin archivos en `contracts/`**: no hay catálogo compartido API↔Admin que fijar (los
  cuatro nombres y etiquetas son estáticos; los tests de ambos lados los citan literalmente).
- `cjhirashi-career-ai` y Portfolio: sin impacto (verificar con grep en Fase 3: sin lectura
  de `vacancies` fuera de la API).

## 3 · Migración `d8f2b5a13c97`

- Revision ID **`d8f2b5a13c97`** (verificado: no existe en `alembic/versions/`);
  `down_revision = "c7e1a4d92b60"` (head actual: nadie lo referencia; 007). Re-verificar el
  head con script sobre `alembic/versions/*.py` al implementar.
- **Antes de aplicar (Art. 4):** en la BD real consultar `alembic_version` y `\d vacancies`.
  Si `alembic_version` ≠ `c7e1a4d92b60` o el esquema difiere del grafo, PARAR y reportar (sin
  `alembic stamp` sin autorización humana). `pg_dump` previo (RNF-003).
- `upgrade()` idempotente (patrón `f8a9b1c2d3e4`, `sa.inspect`): por cada una de las cuatro
  columnas, `ADD COLUMN ... TEXT NULL` sólo si no existe. Sin backfill, sin default → las filas
  existentes quedan en `NULL` (RF-007). DDL transaccional de PG.
- `downgrade()`: `DROP COLUMN` de las cuatro sólo si existen (pierde su contenido: documentado
  en el docstring).

## 4 · Secuenciación (tests antes que código)

Tareas indicativas para `tasks.md` (Fase 3); `[T]`=test rojo primero, `[I]`=implementación.

1. **[T] API:** `tests/unit/test_vacancy_descriptive_texts.py` y
   `tests/unit/test_vacancy_descriptive_texts_migration.py` (rojos).
2. **[I] API:** modelo → schemas → línea en `_KB_EXCLUDED_COLUMNS` → migración. Verde.
3. **[T] Admin:** ampliar `src/tests/config/vacanciesConfig.test.ts` y
   `src/tests/components/career/VacancyBadges.test.tsx` o archivo nuevo
   `VacancyDescriptiveTexts.test.tsx` (rojos).
4. **[I] Admin:** `types/career.ts` → `careerResources.ts` (campos).
5. **[V] BD real:** pre-chequeo (§3), respaldo, `alembic upgrade head`, verificación de
   `\d vacancies`; `downgrade`/`upgrade` en clon desechable (`TEST_DATABASE_URL`), nunca en
   prod primero.
6. **[doc]** tareas de §8.
7. **Fase 4:** revisión `experto-ux-ui` (§7) y verificador independiente (cobertura ≥ 80 %
   por módulo tocado).
8. **Operativa post-deploy:** backup, rebuild api+admin, smoke en vivo (RNF-003). No hay
   reindex de la KB (spec §2).

## 5 · Implementación por requisito

### Implementación de RF-001
`models/vacancy.py` (columnas), `schemas/career_search.py` (`VacancyBase`/`VacancyUpdate`),
`career_repository.py` (persistencia genérica existente). Test (ruta): POST y PUT con cada uno
de los cuatro campos devuelven y persisten el valor (GET posterior igual); también con los
cuatro a la vez.

### Implementación de RF-002
Campos en `VacancyBase` ⇒ heredados por `VacancyResponse`. Test: GET/list/POST/PUT de una
vacante sin valores devuelven las cuatro claves con `null` (no ausentes).

### Implementación de RF-003
`VacancyUpdate` los declara con default `None` y el repositorio usa `exclude_unset`. Test: PUT
que sólo cambia `company` deja los cuatro intactos; PUT con uno solo no toca los otros tres;
PUT con `null` explícito sí lo borra (§5).

### Implementación de RF-004
Normalizador `_trim_or_none` en `schemas/career_search.py`. Test parametrizado: `""`, `"   "`,
`"\n\t"` → `null`; `"  hola  "` → `"hola"`; saltos de línea internos, viñetas y emojis se
conservan; aplica en Create y Update.

### Implementación de RF-005
`StringConstraints(max_length=10_000)` tras el trim. Test: 10 000 caracteres → 201/200;
10 001 → 422 con formato `{"detail","errors"}` y la fila no cambia (GET posterior);
10 000 + espacios alrededor → válido (se mide tras trim).

### Implementación de RF-006
`_KB_EXCLUDED_COLUMNS["vacancies"]` en `career_repository.py`. Test (unit, sin Bedrock/Qdrant,
RNF-002): `_record_to_text(Vacancy con los cuatro campos rellenos)` no contiene ninguno de los
cuatro nombres ni su texto; sí sigue conteniendo `process_stage` y `analysis_notes`;
`process_stage_updated_at` sigue excluida (no regresión de 007 D-13). Recorre también la ruta
de `reindex` (comparte `_record_to_text`).

### Implementación de RF-007
`alembic/versions/d8f2b5a13c97_vacancy_descriptive_texts.py`. Test de migración (dobles,
patrón `test_vacancy_process_stage_migration.py`): `down_revision == "c7e1a4d92b60"`; upgrade
emite `ADD COLUMN` de las cuatro y es idempotente (no repite si existen); downgrade las
elimina; sin `UPDATE` de filas. Clon PG: filas previas intactas con `NULL`, ciclo
upgrade → downgrade → upgrade.

### Implementación de RF-008
`vacanciesConfig.fields` en `careerResources.ts` + `types/career.ts`. Test de config: los
cuatro `name` existen, `type === 'textarea'`, `fullWidth === true`, etiquetas literales de §3,
índices consecutivos y en orden canónico. Test de render del formulario: cuatro textareas con
esas etiquetas.

### Implementación de RF-009
Sin código nuevo (D-06): los cuatro campos son `textarea` y la ficha ya los renderiza con
Markdown. Test de render de la ficha: el DOM muestra los cuatro en orden canónico con su
etiqueta; un valor con párrafos separados por línea en blanco produce párrafos distintos.

### Implementación de RF-010
`vacanciesConfig.columns` sin cambios. Test de config: ninguna columna con key
`company_overview|candidate_profile|offer_summary|work_culture`; el array de claves es
exactamente el de 007 RF-015.

## 6 · Estrategia de pruebas por capa

Anotación: pytest `@pytest.mark.requisito("RF-0NN")`; Vitest `describe("RF-0NN: …")`.

| Capa | Archivo | Cubre |
|---|---|---|
| schemas (unit) | `cjhirashi-career-api/tests/unit/test_vacancy_descriptive_texts.py` | RF-002, 003, 004, 005 (trim, vacío, 10 000/10 001, `null`, omitido) |
| repositorio (integración, `db_session`) | mismo archivo | RF-001, 003; vía tools (sin Pydantic): documenta D-07: sin trim/tope por esa vía |
| ruta (integración, `async_client` + JWT) | mismo archivo | RF-001..005: POST/PUT/GET `/career/vacancies`, 422 sin persistir (fixture PG-only si el cliente lo exige) |
| KB (unit) | mismo archivo | RF-006 (`_record_to_text`, reindex) |
| migración (unit con dobles) | `cjhirashi-career-api/tests/unit/test_vacancy_descriptive_texts_migration.py` | RF-007, cadena `down_revision`, idempotencia |
| migración (clon PG, manual en T de verificación) | `TEST_DATABASE_URL` desechable | RF-007 contra Postgres real; evidencia pegada |
| Admin config (Vitest) | `cjhirashi-career-admin/src/tests/config/vacanciesConfig.test.ts` | RF-008, RF-010 |
| Admin render (Vitest) | `cjhirashi-career-admin/src/tests/components/career/VacancyDescriptiveTexts.test.tsx` (nuevo) | RF-008 (formulario), RF-009 (ficha, saltos, orden), RF-010; no regresión de textarea Markdown |
| Admin tipos/lint | `npm run type-check`, `npm run lint` | tipo `Vacancy` |
| Verificación real (Art. 3) | arranque api+admin, `GET /health`, flujo CRUD en vivo | RNF-003: crear, actualizar, limpiar y consultar una vacante con los cuatro campos; evidencia pegada |

Regresión: tests existentes que tocan `Vacancy` (`test_vacancy_process_stage.py`,
`test_vacancy_duplicate_url.py`, `test_vacancy_target_company_fk.py`, `test_job_discovery.py`),
`CareerResourceView.test.tsx`, `VacancyBadges.test.tsx`. Cobertura ≥ 80 % por módulo tocado
(RNF-001).

## 7 · UX (spec §8) — aporta `experto-ux-ui` en esta Fase 2 y se revisa en Fase 4

Admin toca interfaz (Art. 8). **Pendiente de `experto-ux-ui`** (marcado, no inventado aquí):

- `helpText` de cada área (¿qué escribir en cada una?; evitar duplicar la etiqueta).
- Alto de las áreas (filas) y si se agrupan bajo un encabezado de sección en el formulario.
- Posición definitiva en el formulario (propuesta: tras `contact_id`, antes de `analysis_notes`).
- Ficha de detalle: etiquetas en el orden canónico, comportamiento con valor vacío (¿se
  oculta el campo o muestra "—"? lo que haga hoy `FieldValue` para vacíos; no cambiarlo sin
  decisión), legibilidad de párrafos largos (hasta 10 000 caracteres), contraste.
- Contador de caracteres cerca del tope (¿necesario? hoy el 422 llega al enviar).
- Resultado se registra en el §8 de `spec.md`.

## 8 · Impacto en documentación (Art. 11)

| Documento | Ruta | Qué queda obsoleto | Tarea |
|---|---|---|---|
| Sección Career Search (API) | `cjhirashi-career-api/docs/sections/career-search/README.md` | La tabla de `vacancies` no lista los cuatro campos descriptivos ni la regla trim/vacío → `NULL`/10 000 ni la exclusión transitoria de la KB | `[doc]` Añadir los cuatro campos a la tabla y una nota con las reglas y el carácter transitorio de RF-006 |

No tocan documentación (verificar con grep en Fase 3): `docs/05-BUILDING-BLOCK-VIEW.md`
(sin detalle de columnas de texto de `vacancies`), `docs/BEDROCK-SYSTEM.md` (tools sin
cambio de contrato), `src/models/README.md`, `docker-compose.yml` y `caddy.json` (sin
variables, puertos ni servicios nuevos), ADRs.

## 9 · Operativa de datos y despliegue

Backup `pg_dump` → pre-chequeo (§3) → `alembic upgrade head` → rebuild `api` y `admin`
(`docker compose build/up`) → smoke en vivo (RNF-003). Sin reindex de la KB (las vacantes
existentes no cambian y los campos no se indexan). Si 009 se despliega después, retira la
exclusión de RF-006 y decide el indexado (fuera de 008).

## 10 · Preguntas abiertas y riesgos

- Sin preguntas abiertas: OQ-1 y OQ-2 resueltas por el usuario (D-07 y D-06).
- **R-1 (tools Bedrock).** Resuelto por D-07: las tools escriben sin trim ni tope; aceptado.
- **R-2 (RF-006 transitorio).** La línea de exclusión debe retirarse con la spec 009; queda
  comentada con la referencia. Si 009 no llega, los campos nunca serán recuperables por la KB.
- **R-3 (BD real).** La dev DB no trackea Alembic del todo (state.md, Art. 4): pre-chequeo
  obligatorio; la columna `text` sin default es un `ALTER` de metadatos en PG (sin reescritura de
  tabla).
- **R-4 (`anchor_commit: null`).** El gate avisa; se re-ancla al cerrar (política advisory).
