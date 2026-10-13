---
titulo: "Vacantes: etapa del proceso y estado calculado"
tipo: spec
estado: approved
fecha: 2026-10-12
feature_id: "007"
anchor_mode: advisory
anchor_commit: null
covers:
  - cjhirashi-career-api/src/models/vacancy.py
  - cjhirashi-career-api/src/schemas/career_search.py
  - cjhirashi-career-api/src/services/vacancy_stage.py
  - cjhirashi-career-api/src/repositories/career_repository.py
  - cjhirashi-career-api/alembic/versions/c7e1a4d92b60_vacancy_process_stage.py
  - cjhirashi-career-api/tests/unit/test_vacancy_process_stage.py
  - cjhirashi-career-api/tests/unit/test_vacancy_process_stage_migration.py
  - cjhirashi-career-admin/src/types/career.ts
  - cjhirashi-career-admin/src/config/careerResources.ts
  - cjhirashi-career-admin/src/components/career/CareerResourceView.tsx
  - cjhirashi-career-admin/src/tests/config/vacanciesConfig.test.ts
  - cjhirashi-career-admin/src/tests/components/career/VacancyBadges.test.tsx
  - cjhirashi-career-api/docs/sections/career-search/README.md
  - docs/05-BUILDING-BLOCK-VIEW.md
  - .harness/specs/007-vacantes-etapa-y-estado/**
---

# Vacantes: etapa del proceso y estado calculado

## 1 · Contexto del dominio

**Problema:** en la tabla de Vacantes no se ve en qué punto del proceso va cada
oportunidad (por postular, en proceso, cerrada) ni en qué etapa concreta está.

Hoy existe `vacancies.application_status` (spec 006, varchar(30) libre, sin catálogo;
en `career_db` las 3 filas valen `not_applied`). La tabla `applications` tiene su propio
`current_status`, pero está vacía (0 filas, 2026-10-12).

Dependencias: API (`models/vacancy.py`, `schemas/career_search.py`), Alembic, Admin
(`careerResources.ts`). Sin impacto en `cjhirashi-career-ai` ni en el Portfolio.

## 2 · Alcance

### En alcance
- Un atributo almacenado **`process_stage`** (etapa) con catálogo cerrado de 13 valores.
- Un atributo **`vacancy_status`** (estado) **calculado sólo** a partir de la etapa,
  de sólo lectura, expuesto en la respuesta de la API.
- Un atributo **`process_stage_updated_at`** (fecha del último cambio de etapa), de
  sólo lectura, que mantiene la API.
- Renombrar `application_status` → `process_stage`, con CHECK en BD y backfill.
- Admin: columnas Estado y Etapa con badge; selector de etapa en el formulario.
  Detalle de UX → sección §8 (la aporta `experto-ux-ui`).

### Fuera de alcance
- Sincronizar con `applications.current_status` (la vacante es la única fuente del
  estado del proceso; `applications` queda para el detalle de cada postulación).
- Historial de cambios de etapa / línea de tiempo por vacante.
- Enum nativo de PostgreSQL (se usa CHECK, más barato de extender).
- Cambiar `evaluation` o `is_active`.

## 3 · Modelo de datos y contratos de E/S

| Campo | Almacenado | Tipo | Nulabilidad | Escritura |
|---|---|---|---|---|
| `process_stage` | sí | varchar(30) + CHECK | NOT NULL, default `not_applied` | Create / Update |
| `vacancy_status` | **no** (calculado) | `pending \| in_process \| closed` | nunca nulo | sólo lectura |
| `process_stage_updated_at` | sí | timestamptz (UTC) | NOT NULL | sólo lectura (la fija la API) |

**Catálogo de etapas (orden canónico) y estado derivado:**

| # | `process_stage` | Etiqueta | `vacancy_status` |
|---|---|---|---|
| 0 | `not_applied` | Sin postular | `pending` — Por postular |
| 1 | `applied` | Postulación (CV enviado) | `in_process` — En proceso |
| 2 | `screening` | Screening (llamada inicial con reclutador) | `in_process` |
| 3 | `hr_interview` | Entrevista RH | `in_process` |
| 4 | `technical_interview` | Entrevista técnica | `in_process` |
| 5 | `technical_test` | Prueba técnica / assessment | `in_process` |
| 6 | `final_interview` | Entrevista final | `in_process` |
| 7 | `offer` | Oferta recibida | `in_process` |
| 8 | `hiring_process` | Proceso de contratación | `in_process` |
| 9 | `hired` | Contratado | `closed` — Cerrada |
| 10 | `rejected` | Rechazado | `closed` |
| 11 | `withdrawn` | Me retiré / decliné | `closed` |
| 12 | `no_response` | Sin respuesta / vacante cerrada | `closed` |

El estado depende **únicamente** de `process_stage` (función pura etapa → estado);
ni `evaluation` ni `is_active` intervienen.

Fronteras:
- **REST `/vacancies`** (CRUD genérico): Create/Update aceptan `process_stage`;
  Response añade `vacancy_status` y `process_stage_updated_at`. Valor fuera de catálogo → 422 con el formato de error de validación vigente del API (`{"detail", "errors"}`; D-14).
- **BD `vacancies`**: renombre de columna + CHECK + NOT NULL default + columna
  `process_stage_updated_at`.

## 4 · Criterios de aceptación (EARS)

- **RF-001** CUANDO se crea o actualiza una vacante con un `process_stage` del catálogo,
  el sistema DEBE persistirlo y devolverlo en la respuesta.
- **RF-002** SI se envía un `process_stage` fuera del catálogo, ENTONCES el sistema DEBE
  responder 422 sin persistir el cambio.
- **RF-003** CUANDO se crea una vacante sin `process_stage`, el sistema DEBE asignar
  `not_applied`.
- **RF-004** El sistema DEBE devolver en cada vacante un `vacancy_status` igual al
  mapeo de §3 para su `process_stage`.
- **RF-005** SI un Create/Update incluye `vacancy_status`, ENTONCES el sistema NO DEBE
  persistirlo ni alterar `process_stage` por ello.
- **RF-006** La BD DEBE rechazar por CHECK cualquier `process_stage` fuera del catálogo.
- **RF-007** La migración DEBE renombrar `application_status` a `process_stage`
  conservando los valores existentes y convertir los NULL a `not_applied`.
- **RF-008** SI la migración detecta un valor existente fuera del catálogo, ENTONCES
  DEBE abortar antes de crear el CHECK y reportar los valores encontrados.
- **RF-009** La migración DEBE poder bajar, restaurando `application_status` con sus
  valores y eliminando `process_stage_updated_at`.
- **RF-021** CUANDO se crea una vacante, o se actualiza con un `process_stage` distinto
  del almacenado, el sistema DEBE fijar `process_stage_updated_at` al instante actual (UTC).
- **RF-022** CUANDO un Update no cambia `process_stage` (omitido o igual al actual), el
  sistema NO DEBE alterar `process_stage_updated_at`.
- **RF-023** SI un Create/Update incluye `process_stage_updated_at`, ENTONCES el sistema
  NO DEBE persistir ese valor.
- **RF-024** La migración DEBE añadir `process_stage_updated_at` NOT NULL rellenando las
  filas existentes con `updated_at`, o `created_at` si aquél es nulo, o el instante de
  la migración si ambos lo son.
- **RF-010** La tabla de Vacantes del Admin DEBE mostrar las columnas Estado y Etapa
  con badge por valor.
- **RF-011** El formulario de Vacante del Admin DEBE ofrecer la etapa como selector con
  las 13 opciones en el orden canónico, sin campo editable para el estado.
- RF de UX adicionales (filtro por estado, colores, accesibilidad) → §8.

## 5 · Casos límite y errores

- `process_stage: null` explícito en Update → 422 (la columna es NOT NULL).
- Saltar etapas (p. ej. `applied` → `offer`) o retroceder está **permitido**: el
  proceso real no es lineal; no se valida la transición.
- Vacante con `evaluation = do_not_apply` y etapa `not_applied` → Estado "Por postular"
  (el estado sólo mira la etapa — D-06). Para cerrarla, el usuario la pasa a `withdrawn`.
- `is_active` y etapa son **independientes**: pasar a una etapa terminal no desactiva
  la vacante ni al revés (D-07).
- Update que reenvía la misma etapa → no mueve `process_stage_updated_at` (RF-022).

## 6 · Registro de decisiones y descartes

- **D-01 (usuario, 2026-10-12):** se almacena sólo la etapa; el estado se calcula.
  *Descartado:* guardar ambos campos con validación de consistencia (dos fuentes de
  verdad que pueden contradecirse).
- **D-02 (usuario, 2026-10-12):** reutilizar/renombrar
  `application_status` en vez de añadir una columna nueva. Revisa la D-03 de la spec
  006 **sólo para este campo**: pasa de string libre a catálogo cerrado con CHECK.
- **D-03 (usuario, 2026-10-12):** `applications.current_status` no se
  sincroniza; la vacante es la fuente del estado del proceso.
- **D-04 (usuario, 2026-10-12):** spec nueva 007 en vez de ampliar la
  006, que sigue abierta.
- **D-05:** CHECK en vez de enum PostgreSQL — añadir una etapa es una migración de una
  línea.
- **D-06 (usuario, 2026-10-12):** el estado se calcula **sólo** desde la etapa.
  *Descartado:* que `evaluation = do_not_apply` fuerce "Cerrada" (segunda entrada al
  cálculo).
- **D-07 (usuario, 2026-10-12):** `is_active` independiente de la etapa. *Descartado:*
  auto-desactivar al llegar a etapa terminal (efecto oculto, ambiguo al retroceder).
- **D-08 (usuario, 2026-10-12):** `process_stage_updated_at` entra en esta feature.
  *Descartado:* diferirla junto al historial de etapas.
- **D-09 (usuario, 2026-10-12):** vocabulario de etapas "Postulación" (`applied`) y
  "Screening" (`screening`), en vez de `cv_sent` / `screening_call`.
- **D-10 (usuario, 2026-10-12, Fase 2):** filtro por Estado **incluido** (RF-017
  enmendado). *Descartado:* diferirlo.
- **D-11 (usuario, 2026-10-12, Fase 2):** se acepta que no se pueda ordenar por Estado
  y que la Etapa se ordene alfabéticamente. *Descartado:* orden canónico en el
  repositorio genérico (amplía alcance).
- **D-12 (usuario, 2026-10-12, Fase 2):** "En etapa desde" sólo fecha. *Descartado:*
  fecha y hora.
- **D-13 (usuario, 2026-10-12, Fase 2):** `process_stage_updated_at` **no** entra al
  texto indexado de la base de conocimiento. *Descartado:* indexarla (recalcula el
  embedding en cada cambio de etapa sin aportar a la búsqueda). El reindex de la KB
  tras el deploy (renombre de `application_status`) requiere autorización del usuario
  en ese momento (coste Bedrock).
- **D-14 (usuario, 2026-10-13, Fase 4):** el 422 usa el formato de error de validación
  vigente del API (`{"detail": "Error de validación", "errors": [...]}`), no Problem
  Details RFC 9457. La contradicción con la Constitución es **preexistente y de todo el
  API** (handler global `app.py:144-162`); se trata en una tarea aparte (deuda en
  `state.md`). *Descartado:* migrar el handler global dentro de 007 (cambia la respuesta
  de error de todas las rutas).

## 8 · UX (Admin)

**Hallazgos sobre el ResourceConfig genérico (hoy):** (a) el badge pinta `String(value)`
(`CareerResourceView.tsx:1262`), es decir el código crudo (`hr_interview`), no la etiqueta
en español; (b) ~~no existe filtro por columna~~ — *corregido en Fase 2:* sí existe
(`ColumnFilterButton`, `listFilters.ts`) para columnas `select`/`fk-select`/`boolean`,
pero no para columnas calculadas; ordenar sólo funciona sobre columnas reales; (c) `badgeColor` sólo
admite `cyan|slate|success|error|warning`; (d) `vacancy_status` es columna calculada, no
campo. **Alternativa mínima:** añadir a `ColumnConfig` un `badgeLabel?: (v) => string`
(extensión documentada, reutilizable).

- **RF-012** La columna Estado (`vacancy_status`) DEBE usar `format: 'badge'` con color
  `slate` para Por postular, `warning` para En proceso y `slate` para Cerrada; el texto del
  badge DEBE ser la etiqueta española, nunca el código.
- **RF-013** La columna Etapa (`process_stage`) DEBE colorear: `hired` y `offer` →
  `success`; `rejected` → `error`; `withdrawn` y `no_response` → `slate`; `not_applied` →
  `slate`; las etapas 1-6 y 8 → `warning`.
- **RF-014** El texto del badge de Etapa y de Estado DEBE ser la etiqueta española del
  catálogo de §3 (p. ej. "Entrevista RH", "Cerrada"), de modo que el significado no
  dependa del color (WCAG 1.4.1); `ColumnConfig` DEBE ganar `badgeLabel` para ello.
- **RF-015** La tabla DEBE ordenar las columnas: Empresa, Rol, Estado, Etapa, En etapa
  desde, Fit %,
  Evaluación, Ubicación, Encontrada, Activa (Estado y Etapa contiguas, tras el rol).
- **RF-016** El selector de etapa DEBE etiquetarse "Etapa del proceso", listar las 13
  opciones en orden canónico con las etiquetas de §3 y mostrar el helpText: "Dónde va esta
  vacante en tu proceso. Puedes saltar o retroceder etapas. El estado (Por postular / En
  proceso / Cerrada) se calcula solo."
- **RF-017** La tabla de Vacantes DEBE ofrecer filtro por Estado con las opciones Por
  postular / En proceso / Cerrada; CUANDO se aplica, el API DEBE devolver sólo las
  vacantes cuya `process_stage` mapea a los estados elegidos (§3). El campo que lo
  habilite NO DEBE aparecer en el formulario. La Etapa DEBE ser filtrable por sus 13
  valores. No se exige ordenar por Estado ni por orden canónico de Etapa (D-11).
- **RF-018** Cada badge DEBE tener contraste de texto ≥ 4.5:1 sobre su fondo (WCAG 2.1 AA)
  usando únicamente los colores del componente `Badge` existente; no se añaden colores nuevos.
- **RF-019** SI `process_stage` está vacío o fuera de catálogo en el cliente, ENTONCES
  el badge DEBE mostrar "Sin definir" en `slate`, sin romper la fila.
- **RF-020** El formulario DEBE mostrar `vacancy_status` sólo como texto informativo no
  editable (o no mostrarlo), nunca como control de entrada.

- **RF-025** La columna "En etapa desde" (`process_stage_updated_at`) DEBE mostrarse con
  formato **sólo fecha** (`format: 'date'`, sin hora) y NO DEBE aparecer como campo
  editable en el formulario.

Nota: `success` para `offer` coincide con `badgeByStatusGeneric`. §5 resuelto (D-06,
D-07): RF-012 no cambia.
