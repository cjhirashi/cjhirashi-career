# ADR-021: PK sintético `sec-N` para las secciones del Admin (`system_name` como nombre legible)

## Estado

Aceptado — 2026-08-27

Complementa a [ADR-017](./017-l2-agent-settings.md) (L2 `agent_settings`, dueño de la pantalla
"Secciones del Admin") y a [ADR-020](./020-admin-section-templates.md) (plantilla compartida de
las vistas de tabla). No cambia ninguna regla de esos ADR — solo re-identifica las secciones.

## Contexto

"Secciones del Admin" **no es una tabla**: es un registro en código
(`cjhirashi-career-api/src/services/admin_sections.py` — `AdminSectionSpec`, `_SECTIONS`,
`_CAREER_ROWS`). La única tabla real es `admin_section_overrides`, que guarda los overrides
editables (agente dueño, textos del sidebar, descripción) con PK `section_id`.

Hasta ahora ese `section_id` era el **slug legible** de la sección: `dashboard`, `career-projects`,
`settings-error-reports`, etc. Ese slug era a la vez:

- la clave primaria de `admin_section_overrides`;
- el identificador de propiedad de secciones por agente (`set_agent_sections`,
  `known_section_ids`);
- el argumento `section_id` de la tool de Bedrock `admin_section_settings` (ADR-017);
- el segmento `:id` de la URL del Admin `/settings/sections/:id`.

Problemas de usar el slug como clave canónica:

1. **Un renombrado de slug rompe todo el cableado**: filas de `admin_section_overrides`
   huérfanas, punteros de agente rotos, URLs guardadas inválidas, referencias en historial de
   chat que ya no resuelven. El slug es descriptivo y por tanto *querible* — es exactamente el
   tipo de valor que se acaba renombrando.
2. **Longitud variable y semántica embebida**: `career-application-interactions` son 30
   caracteres; el slug mezcla "qué es" con "cómo se llama la clave".
3. **Incoherencia con el resto del sistema**: los reportes de falla ya usan IDs sintéticos
   `err-N` (ADR-018) y el catálogo de agentes usa `agent-N`. Las secciones eran la excepción.

Se necesitaba una clave **estable, corta y opaca** para las secciones, conservando el slug
como nombre legible visible.

## Decisión

### 1. `id` = PK sintético `sec-N`; `system_name` = el slug de antes

`AdminSectionSpec` gana el campo `system_name: str` y su `id` pasa a ser `sec-<n>` (prefijo
`sec-`, análogo a `err-N` / `agent-N`):

- `id` (`sec-1`, `sec-2`, …) es la **clave canónica en TODO**: PK de
  `admin_section_overrides.section_id`, propiedad por agente, tool `admin_section_settings`
  (`section_id=`), y URL `/settings/sections/:id`.
- `system_name` (`dashboard`, `career-projects`, `settings-error-reports`, …) conserva
  **exactamente** los valores que antes tenía `id`. Es un nombre legible, no una clave: se
  expone en `list` / `get` de la tool y en `profile_catalog`, y en la UI del Admin figura como
  la columna **"Nombre de sistema"**. `get_section_by_system_name()` existe solo para
  migración / depuración.
- Para las 35 secciones de carrera, `system_name = "career-" + resource_key`.

### 2. Regla de numeración — CONGELADA

Los `sec-N` se asignan **explícitamente en código**, uno por sección, en orden de declaración:
`_SECTIONS` ocupa `sec-1`..`sec-19` y `_CAREER_ROWS` ocupa `sec-20`..`sec-54` (el primer
elemento de cada tupla de `_CAREER_ROWS` es el entero congelado).

- **No hay secuencia de base de datos.** El número vive en el código fuente.
- **Permanente**: un `sec-N` no se reordena ni se reutiliza.
- **Sección nueva** → siguiente entero libre (`sec-55`, `sec-56`, …), al final.
- **Sección eliminada** → su número queda **retirado** (hueco permanente); nunca se recicla.

Dos `assert` de arranque en `admin_sections.py` garantizan unicidad de `id` y de `system_name`.

### 3. Migración `b2c3d4e5f6a7`

`cjhirashi-career-api/alembic/versions/b2c3d4e5f6a7_admin_section_overrides_synthetic_pk.py`
(revision `b2c3d4e5f6a7`, `down_revision = b1c2d3e4f5a6`).

- Lleva un **mapa estático `slug → sec-N` incrustado** (copia congelada de la tabla de abajo).
  **No importa** `services.admin_sections` — el historial de migraciones no debe acoplarse al
  código de la app.
- `upgrade`: `UPDATE admin_section_overrides SET section_id = :new WHERE section_id = :old`
  por cada par del mapa, y después estrecha la columna de `String(80)` a `String(40)`.
- `downgrade`: invierte ambos pasos (ensancha la columna y re-mapea `sec-N → slug`).
- Filas cuyo `section_id` no está en el mapa (ni es ya un `sec-N` conocido) se **dejan
  intactas** y se registran con `logging.warning` — un override huérfano no rompe nada porque
  el catálogo lo ignora al serializar.

### 4. Re-key del resto del cableado

| Punto | Antes | Ahora |
|---|---|---|
| `models/admin_section_override.py` | `section_id = Column(String(80/…), pk)` = slug | `Column(String(40), pk)` = `sec-N` (docstring actualizado) |
| `section_catalog._serialize` | `"id"` = slug | `"id"` = `sec-N`, **nuevo** `"system_name"` = slug |
| `section_catalog` (`set_agent_sections`, `sections_for_agent`, `_overrides_map`, `_get_or_create_row`, `known_section_ids`) | operan con slug | operan con `sec-N` |
| Bedrock `tools.py` → `admin_section_settings` | `section_id` = slug | `section_id` = `sec-N`; `description` y mensajes de error lo aclaran ("`system_name` es solo el nombre legible") |
| Bedrock `agent_profiles.py` → `_SETTINGS_SUFFIX` (punto 2) | — | texto ajustado: `section_id` = `sec-N` (campo `id` de `action=list`), `system_name` = nombre legible |
| Bedrock `profile_catalog.py` (`_attach_sections`) | `"id"` = slug | `"id"` = `sec-N`, adjunta `system_name` |
| `schemas/admin_sections.py` → `AdminSectionItem` | — | añade `system_name: str` |
| URL Admin `/settings/sections/:id` | `:id` = slug | `:id` = `sec-N` (navegación y `DetailSectionTemplate` ya usan `data.id`, sin cambios de lógica) |

### 5. Frontend (UI mínima — sin tocar el Frente A)

- `src/types/adminSections.ts` — `AdminSection` añade `system_name: string`.
- `src/pages/AdminSectionsPage.tsx` — `SECTION_COLUMNS` mantiene `{ key: 'id', label: 'ID' }`
  (ahora `sec-N`) y añade `{ key: 'system_name', label: 'Nombre de sistema' }` justo después;
  `searchAccessor` incluye `row.system_name`; la vista de detalle añade el campo
  **"Nombre de sistema"** bajo "ID".
- `src/pages/AgentCatalogPage.tsx` — el multiselect de secciones ya usa `row.id` (ahora
  `sec-N`); la etiqueta de cada opción pasa a `label · system_name (tipo)`.

## Nota de deploy (IMPORTANTE)

> La migración `b2c3d4e5f6a7` **NO** corre en `init_db` (que usa `create_all`). Tras
> reconstruir la imagen de la API hay que ejecutar **`alembic upgrade head`** manualmente para
> re-mapear `admin_section_overrides` y estrechar la columna — mismo procedimiento que la
> migración `b1c2d3e4f5a6` de [ADR-019](./019-bedrock-prompt-caching.md). **Correr la migración
> inmediatamente después del rebuild**, en el mismo paso de despliegue.

### Ventana de regresión entre el deploy de código y la migración (R2, code review)

Mientras la migración `b2c3d4e5f6a7` no corra, **todas** las filas de
`admin_section_overrides` siguen keyeadas con el slug antiguo, mientras que el código nuevo
(`section_catalog`) ya busca los overrides por `sec-N`. Como ninguna fila hace match, durante
esa ventana **cada sección revierte temporalmente a sus valores por defecto de código**:

- el agente dueño (`default_agent_profile_id` en vez del override),
- la descripción de la sección,
- los textos de instrucciones del sidebar por vista (`sidebar_title` / `sidebar_body` /
  `description` de cada `AdminViewSpec`).

**No hay pérdida de datos**: las filas de `admin_section_overrides` quedan intactas y el match
se restablece en cuanto se aplica la migración (que solo traduce `section_id` slug → `sec-N`).
Es una regresión **funcional y visible** limitada a esa ventana — de ahí la recomendación de
encadenar `alembic upgrade head` justo después del rebuild.

## Tabla congelada `sec-N ↔ system_name`

Fuente de verdad: `_SECTIONS` y `_CAREER_ROWS` en
`cjhirashi-career-api/src/services/admin_sections.py`. Copia congelada en el mapa `_SLUG_TO_PK`
de la migración `b2c3d4e5f6a7`. Ambas deben coincidir.

| `sec-N` | `system_name` | | `sec-N` | `system_name` |
|---|---|---|---|---|
| sec-1  | dashboard              | | sec-28 | career-achievements               |
| sec-2  | metrics               | | sec-29 | career-star-stories               |
| sec-3  | search-metrics        | | sec-30 | career-career-reviews             |
| sec-4  | agent-metrics         | | sec-31 | career-role-gap-analysis          |
| sec-5  | files                | | sec-32 | career-projects                   |
| sec-6  | linkedin-publish      | | sec-33 | career-fit-scoring-factors        |
| sec-7  | job-discovery         | | sec-34 | career-market-segments            |
| sec-8  | pdf-templates         | | sec-35 | career-role-narratives            |
| sec-9  | pdf-styles            | | sec-36 | career-search-plans               |
| sec-10 | agent-tasks          | | sec-37 | career-networking-contacts        |
| sec-11 | agent-chat           | | sec-38 | career-target-companies           |
| sec-12 | agent-memory         | | sec-39 | career-vacancies                  |
| sec-13 | agent-instructions   | | sec-40 | career-cv-versions                |
| sec-14 | agent-tools          | | sec-41 | career-cover-letter-versions      |
| sec-15 | agent-audit-log      | | sec-42 | career-applications               |
| sec-16 | settings-agents      | | sec-43 | career-application-interactions    |
| sec-17 | settings-sections    | | sec-44 | career-interviews                 |
| sec-18 | settings-agent-prompts | | sec-45 | career-linkedin-profile          |
| sec-19 | settings-error-reports | | sec-46 | career-github-profile            |
| sec-20 | career-personal-profile | | sec-47 | career-portal-home             |
| sec-21 | career-differentiators  | | sec-48 | career-portal-about            |
| sec-22 | career-identity         | | sec-49 | career-portal-contact          |
| sec-23 | career-identity-reflections | | sec-50 | career-publications        |
| sec-24 | career-competencies     | | sec-51 | career-contact-interactions   |
| sec-25 | career-certifications   | | sec-52 | career-networking-activities  |
| sec-26 | career-target-roles     | | sec-53 | career-tags                   |
| sec-27 | career-work-history     | | sec-54 | career-operational-methodologies |

`sec-55` en adelante quedan libres para futuras secciones.

## Consecuencias

### ✅ Positivas

- Renombrar un `system_name` (o un `resource_key` de carrera) ya **no toca ninguna clave**:
  overrides, punteros de agente, URLs guardadas y referencias de chat siguen resolviendo.
- Clave corta, opaca y de longitud acotada (`String(40)`) — coherente con `err-N` (ADR-018) y
  `agent-N`.
- El slug sigue visible y buscable como "Nombre de sistema", sin perder legibilidad para
  Carlos ni para el agente `agent_settings`.

### ⚠️ Negativas

- **Paso de deploy manual obligatorio** (`alembic upgrade head`); si se omite, los overrides
  quedan en formato viejo y se ignoran hasta aplicarlo.
- **Doble mantenimiento del mapa**: la asignación `sec-N ↔ system_name` vive tanto en
  `admin_sections.py` como (congelada) en la migración. Añadir una sección nueva con override
  preexistente en producción requeriría una migración adicional; el caso normal (sección nueva
  sin overrides) no necesita nada.
- Los `sec-N` no dicen nada por sí solos: hay que mirar la columna "Nombre de sistema" o
  `action=list` de la tool para saber qué es cada uno.
- La regla de numeración congelada deja **huecos** cuando se borra una sección — es
  intencional, pero la lista de `_CAREER_ROWS` deja de ser "posición = número" si eso ocurre.

### 🤷 Neutras

- Los `sort_order` de las secciones son independientes del `sec-N`: el orden de la UI no
  cambia por esta decisión.
- `match_section()` sigue resolviendo por `path`, no se ve afectado.

## Alternativas Consideradas

### Alternativa 1: mantener el slug como PK

Dejar `section_id` = `dashboard` / `career-projects` y no añadir `system_name`.
- ✅ Pro: cero migración, cero cableado nuevo.
- ❌ Contra: es justo el problema que se quería resolver — cualquier renombrado de un valor
  descriptivo rompe overrides, ownership, URLs e historial de chat. Incoherente con `err-N` /
  `agent-N`.

### Alternativa 2: numeración por posición en la lista / autoincrement

Calcular `sec-N` en tiempo de carga como `enumerate(_SECTIONS)` o delegar a un `SERIAL` de la
base de datos.
- ✅ Pro: no hay que asignar el número a mano.
- ❌ Contra: la clave dejaría de ser estable — reordenar `_SECTIONS`, insertar una sección en
  medio o borrar una desplazaría todos los números siguientes, rompiendo exactamente lo que se
  quiere proteger. Un `SERIAL` además volvería a meter estado en la base de datos para un
  registro que vive en código.

### Alternativa 3 (ELEGIDA): PK `sec-N` asignado a mano y congelado en código

- ✅ Pro: clave estable e independiente del orden, la posición y los renombrados.
- ✅ Pro: sin estado en base de datos; la única tabla (`admin_section_overrides`) solo
  referencia la clave.
- ✅ Pro: coherente con `err-N` (ADR-018).

## Referencias

- API: `src/services/admin_sections.py` (`AdminSectionSpec.id` / `system_name`, `_SECTIONS`,
  `_CAREER_ROWS`, `get_section_by_system_name`, `known_section_ids`),
  `src/services/section_catalog.py` (`_serialize`, ownership),
  `src/models/admin_section_override.py` (`section_id = String(40)`),
  `src/schemas/admin_sections.py` (`AdminSectionItem.system_name`)
- Migración: `alembic/versions/b2c3d4e5f6a7_admin_section_overrides_synthetic_pk.py`
  (`_SLUG_TO_PK`)
- Bedrock: `src/services/bedrock/tools.py` (`admin_section_settings`),
  `src/services/bedrock/agent_profiles.py` (`_SETTINGS_SUFFIX`),
  `src/services/bedrock/profile_catalog.py` (`_attach_sections`)
- Admin: `src/types/adminSections.ts`, `src/pages/AdminSectionsPage.tsx` (columna
  "Nombre de sistema"), `src/pages/AgentCatalogPage.tsx` (etiqueta del multiselect)
- Tests: `cjhirashi-career-api/tests/` (`admin_section`, `settings-sections`),
  `cjhirashi-career-admin/src/tests/pages/AdminSectionsPage.test.tsx`,
  `AgentCatalogPage.test.tsx`
- [ADR-017](./017-l2-agent-settings.md) · [ADR-018](./018-error-reports-registry.md) (patrón
  `err-N`) · [ADR-019](./019-bedrock-prompt-caching.md) (misma nota de deploy) ·
  [ADR-020](./020-admin-section-templates.md)

## Seguimiento

- El **Frente A** (`SectionPageTemplate`: unificación del sidebar derecho como contenido de la
  sección, migración de todas las pantallas del Admin a una sola plantilla de página) se
  trabaja en una sesión aparte y **consumirá** `sec-N` como `sectionId` y `system_name` para
  mostrarlo — no introduce cambios en las claves definidas aquí.

---

**Creado por**: Arquitecto de Soluciones
**Fecha de creación**: 2026-08-27
**Estado de vigencia**: Vigente (requiere `alembic upgrade head` en cada entorno donde ya
existan filas en `admin_section_overrides`)
