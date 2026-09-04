---
titulo: Sidebar contextual configurable por sección del Admin
tipo: spec
estado: implemented
fecha: 2026-09-04
feature_id: "001"
covers:
  - cjhirashi-career-api/src/models/admin_section_override.py
  - cjhirashi-career-api/src/schemas/admin_sections.py
  - cjhirashi-career-api/src/services/admin_sections.py
  - cjhirashi-career-api/src/services/section_catalog.py
  - cjhirashi-career-api/src/routes/admin_sections.py
  - cjhirashi-career-api/src/routes/bedrock.py
  - cjhirashi-career-api/src/services/bedrock/agent_profiles.py
  - cjhirashi-career-api/src/services/bedrock/agent_loop.py
  - cjhirashi-career-api/src/services/bedrock/tools.py
  - cjhirashi-career-api/pytest.ini
  - cjhirashi-career-api/alembic/versions/*admin_section_override_description*.py
  - cjhirashi-career-api/tests/unit/test_admin_sections*.py
  - cjhirashi-career-api/tests/unit/test_admin_section_catalog.py
  - cjhirashi-career-api/tests/unit/test_admin_section_migration.py
  - cjhirashi-career-api/tests/unit/bedrock/test_section_profile_resolution*.py
  - cjhirashi-career-admin/src/types/adminSections.ts
  - cjhirashi-career-admin/src/config/agentProfiles.ts
  - cjhirashi-career-admin/src/hooks/useBedrockChat.ts
  - cjhirashi-career-admin/src/pages/AdminSectionsPage.tsx
  - cjhirashi-career-admin/src/components/SidebarRight.tsx
  - cjhirashi-career-admin/src/components/Layout.tsx
  - cjhirashi-career-admin/src/tests/pages/AdminSectionsPage.test.tsx
  - cjhirashi-career-admin/src/tests/pages/AgentCatalogPage.test.tsx
  - cjhirashi-career-admin/src/tests/config/agentProfiles.test.ts
  - cjhirashi-career-admin/src/tests/components/SidebarRight.test.tsx
  - cjhirashi-career-admin/src/tests/components/Layout.test.tsx
  - docs/09-DECISIONS/024-sidebar-contextual-por-seccion.md
  - docs/09-DECISIONS/021-admin-sections-synthetic-pk.md
  - docs/BEDROCK-SYSTEM.md
  - cjhirashi-career-api/src/services/bedrock/README.md
anchor_commit: c42afb78f4c1ce4d25534395476f9266fd07e449
anchor_mode: advisory
---

# Sidebar contextual configurable por sección del Admin

## 1 · Contexto del dominio

**Problema (una frase):** hoy el agente del chat contextual y el texto de instrucciones
del sidebar derecho del Admin se **derivan de código** (tabla de fallback L3→L2 y
`sidebar_body` por vista en `services/admin_sections.py`); el operador no puede decidir
por sección **qué agente L2 atiende ese chat** ni **redactar las instrucciones en
Markdown**, y el sidebar se muestra siempre aunque no aporte nada.

**Meta:** que la fila de una sección en **Secciones del Admin** (`/settings/sections`)
gobierne, de forma editable, el sidebar derecho de esa sección: (a) el **agente L2**
ligado a su chat contextual y (b) las **instrucciones Markdown por vista**. Ambos
campos vacíos ⇒ sidebar oculto.

**Límites / dependencias de infra:**
- Servicio dueño del schema: `cjhirashi-career-api` (SQLAlchemy + Alembic sobre la
  Postgres compartida). Overrides en `admin_section_overrides` (PK sintético `sec-N`,
  ADR-021).
- Front: `cjhirashi-career-admin` (Vite SPA). `react-markdown` + `remark-gfm` ya son
  dependencias — no se añaden librerías.
- Chat contextual: harness Bedrock (`services/bedrock/*`, `resolve_profile_for_turn`).
- Sin `openapi.yaml` committeado: el contrato REST se valida contra `/openapi.json` en
  runtime (bloque `rest-http` del gate). Igual se versiona el ejemplo de request/response
  en `contracts/`.

## 2 · Alcance

### En alcance
- Reconvertir el campo **`agent_profile_id`** ("Agente con dominio") de la sección en
  **el agente del chat contextual**: selector restringido a **agentes L2**, `NULL`
  permitido, sin derivación ni fallback L3→L2.
- Re-mapear en el **registro de código** (`_SECTIONS` / `_CAREER_ROWS` de
  `services/admin_sections.py`) el `default_agent_profile_id` de las 11 secciones que
  hoy apuntan a un agente L1/L3 (tabla en §6, aprobada).
- Campo **instrucciones Markdown por vista**: `sidebar_body` se **reinterpreta** y
  renderiza como Markdown (GFM). Se conservan las claves JSON actuales
  (`sidebar_title` / `sidebar_body`); `sidebar_title` sigue siendo texto plano.
- Edición de agente + instrucciones + título por vista desde la ficha de la sección,
  con "Restablecer al código".
- Reglas de visibilidad del sidebar derecho (chat / instrucciones / panel completo).
- Endpoint `PUT /admin/sections/{id}`: validación de agente L2, errores RFC 9457.
- `resolve_profile_for_turn` y su espejo en el front (`agentProfiles.ts`,
  `SidebarRight.tsx`) usan el agente asignado a la sección como única fuente; si la
  sección no tiene agente, el turno contextual **degrada al orquestador**.
- Migración Alembic que **elimina la columna `description`** de
  `admin_section_overrides`. **Sin siembra**: el texto por defecto de las
  instrucciones sigue viniendo del registro de código en runtime.
- Override de instrucciones por vista con **3 estados**: heredar (sin override),
  texto explícito, y **vacío explícito** (`""`) que oculta la pestaña.
- Retirar el campo **Descripción** editable de la sección y su render en la ficha del
  catálogo (el propósito lo cubren las instrucciones del sidebar).

### Fuera de alcance
- Editar **títulos, rutas, tipo, grupo o vistas** de una sección (siguen en código).
- Crear o borrar secciones desde la UI.
- Cambiar el modelo Bedrock por perfil de chat (`chatSectionProfiles.ts` /
  `section_profiles.py`) — sólo se ajusta el enrutado de *perfil de agente*, no el de
  *modelo*.
- Markdown en `sidebar_title` o en la `description` de código.
- Editor Markdown WYSIWYG: el campo es un `<textarea>`; el render es de sólo lectura.
- Permisos por rol sobre quién edita el catálogo (hoy cualquier usuario autenticado).
- Historial/versionado de instrucciones.
- Cambios en el portal público (`cjhirashi-career-portfolio`).

## 3 · Modelo de datos y contratos de E/S

### 3.1 Persistencia — `admin_section_overrides`
Tabla existente. Cambios:
- `agent_profile_id VARCHAR(50) NULL` — **sin cambio de tipo**; cambia la semántica
  (antes "agente con dominio" con derivación; ahora "agente L2 del chat contextual",
  `NULL` = sin chat propio). Se mantiene la regla actual: fila totalmente vacía se
  borra.
- `views JSONB NULL` — **sin cambio de forma ni de claves**:
  `{ view_key: { sidebar_title?, sidebar_body? } }` (más `description` de la forma
  vieja, que deja de escribirse y se ignora al leer). `sidebar_body` pasa a
  interpretarse como Markdown en el render; en la DB sigue siendo texto. **3 estados
  por sub-campo:** clave ausente = heredar el valor de código; clave con contenido =
  override; clave con `""` = **override vacío explícito** (para `sidebar_body`, oculta
  la pestaña de instrucciones).
- `description TEXT` — **se elimina la columna** (override retirado del alcance). La
  migración sólo hace `drop_column`; correrla dos veces es no-op.

### 3.2 Frontera de salida — catálogo efectivo (`section_catalog.py`)
`AdminSectionItem` (respuesta de `GET /admin/sections` y `.../{id}`):
- **se elimina** `chat_agent_profile_id` (ya no hay derivación).
- **se elimina** `description`, `description_is_default`.
- `agent_profile_id: str | null`, `agent_label: str | null`, `agent_is_default: bool`
  — el `agent_profile_id` efectivo **siempre** es L2 o `null`.
- `default_agent_profile_id: str | null` — el de código, ya re-mapeado a L2/`null`.
- Cada `views[]`: `{ key, label, sidebar_title, sidebar_body, is_default }`.
  `sidebar_body`/`sidebar_title` = el texto efectivo: override explícito (incluido
  `""`) si la clave está presente, si no el valor de código. `is_default` = no hay
  override para `sidebar_title` ni para `sidebar_body` en esa vista. Cadena vacía sólo
  se produce por override explícito.
- Nuevos derivados por sección: `sidebar_has_chat: bool` (= `agent_profile_id` no nulo),
  `sidebar_has_instructions: bool` (= alguna vista con `sidebar_body` efectivo no
  vacío).

### 3.3 Frontera de entrada — `PUT /admin/sections/{id}`
Request (`AdminSectionUpdateRequest`), todos los campos opcionales:
```json
{
  "agent_profile_id": "agent_configuration | \"\" | null",
  "views": {
    "main": { "sidebar_title": "string", "sidebar_body": "string" }
  }
}
```
- `agent_profile_id` ausente/`null` ⇒ no se toca. `""` ⇒ limpia (vuelve al default de
  código). Un id ⇒ debe existir **y ser nivel 2**.
- `views[k]` con `k` no perteneciente a la sección ⇒ se ignora esa clave.
- `views[k]` **sin** la clave `sidebar_body` (o `sidebar_title`) ⇒ ese sub-campo
  vuelve a **heredar** el valor de código.
- `views[k].sidebar_body = ""` ⇒ **override vacío explícito** (persiste, oculta la
  pestaña). Cadena con contenido ⇒ override de texto.
- "Restablecer al código" envía `views: {}` ⇒ borra todos los overrides de vistas de
  la sección.
- Se retira `description` del request.
- Respuesta: `200` con el `AdminSectionItem` recalculado.

### 3.4 Errores — RFC 9457 (Problem Details)
| Situación | HTTP | `title` |
|---|---|---|
| `section_id` desconocido | 404 | `Unknown admin section` |
| `agent_profile_id` inexistente | 400 | `Unknown agent profile` |
| `agent_profile_id` existe pero no es L2 | 400 | `Agent profile is not L2` |
| body no parseable / tipos inválidos | 422 | (validación FastAPI estándar) |

### 3.5 Enrutado del chat contextual
- `resolve_profile_for_turn(chat_surface="contextual", …)`: si la ruta hace *match*
  con una sección y ésta tiene `agent_profile_id` ⇒ ese perfil (L2). Si la sección
  existe pero `agent_profile_id` es `null`, o la ruta no hace match con ninguna
  sección ⇒ **degrada al orquestador** (`agent_orchestrator`, L1). Nunca error.
- Se elimina `chat_agent_id()` y `_L3_CHAT_FALLBACK` de `agent_profiles.py`; los
  llamadores usan el `agent_profile_id` efectivo del catálogo.

## 4 · Criterios de aceptación (EARS)

- **RF-001** — El sistema DEBE exponer en `AdminSectionItem.agent_profile_id` un valor
  que es el id de un agente de nivel 2 o `null`, nunca un agente L1 ni L3.
- **RF-002** — CUANDO `PUT /admin/sections/{id}` recibe `agent_profile_id` con el id de
  un agente que no es nivel 2, el sistema DEBE responder `400` con Problem Details
  `title = "Agent profile is not L2"` y NO DEBE persistir el cambio.
- **RF-003** — CUANDO `PUT /admin/sections/{id}` recibe `agent_profile_id = ""`, el
  sistema DEBE borrar el override de agente de esa sección y devolver
  `agent_profile_id` igual al `default_agent_profile_id` de código.
- **RF-004** — El sistema DEBE devolver `default_agent_profile_id` como el id de un
  agente nivel 2 o `null` para las 54 secciones del registro.
- **RF-005** — El sistema NO DEBE incluir el campo `chat_agent_profile_id` en las
  respuestas de `GET /admin/sections` ni de `GET /admin/sections/{id}`.
- **RF-006** — CUANDO `PUT /admin/sections/{id}` recibe `views[k].sidebar_body` con
  contenido y `k` es una vista de la sección, el sistema DEBE persistir ese texto y
  devolverlo en `views[k].sidebar_body` con `is_default = false`.
- **RF-007** — CUANDO `PUT /admin/sections/{id}` recibe `views[k].sidebar_body = ""`,
  el sistema DEBE persistir un override vacío explícito y devolver
  `views[k].sidebar_body = ""` con `is_default = false`.
- **RF-007b** — CUANDO `PUT /admin/sections/{id}` envía `views[k]` sin la clave
  `sidebar_body`, el sistema NO DEBE dejar override de `sidebar_body` para esa vista
  (queda heredado de código).
- **RF-008** — MIENTRAS una vista tiene `sidebar_body` efectivo no vacío, el sidebar
  derecho de esa ruta DEBE renderizar ese texto como Markdown (GFM) en la pestaña de
  instrucciones.
- **RF-009** — SI el `sidebar_body` efectivo de la vista activa está vacío ENTONCES
  el Admin NO DEBE mostrar la pestaña de instrucciones del sidebar derecho para esa
  ruta.
- **RF-010** — SI la sección de la ruta activa tiene `agent_profile_id = null` ENTONCES
  el Admin NO DEBE mostrar la pestaña de chat del sidebar derecho para esa ruta.
- **RF-011** — SI la sección de la ruta activa no tiene chat (RF-010) ni instrucciones
  (RF-009) ENTONCES el Admin NO DEBE renderizar el panel del sidebar derecho ni su
  botón de apertura para esa ruta.
- **RF-012** — CUANDO un turno de chat `contextual` se resuelve sobre una ruta que
  hace match con una sección con `agent_profile_id` asignado, el harness Bedrock DEBE
  usar ese perfil, sin consultar la tabla de rutas ni la de fallback.
- **RF-013** — La ficha de una sección en `/settings/sections/{id}` NO DEBE mostrar un
  campo "Descripción" ni permitir editarlo.
- **RF-014** — El selector de agente de la ficha de sección DEBE ofrecer únicamente
  agentes de nivel 2 y la opción "sin agente".
- **RF-015** — CUANDO el operador pulsa "Restablecer al código" en una sección, el
  sistema DEBE dejar `agent_profile_id`, todos los `views[].sidebar_title` y todos los
  `views[].sidebar_body` heredados del registro de código (`is_default = true` en toda
  vista).
- **RF-016** — DONDE una sección no tiene ninguna fila en `admin_section_overrides`
  tras la migración, el sistema DEBE seguir devolviendo `views[].sidebar_body` no vacío
  para toda vista que tuviera texto en código antes de esta feature.
- **RF-022** — CUANDO un turno de chat `contextual` se resuelve sobre una ruta cuya
  sección tiene `agent_profile_id = null` o que no hace match con ninguna sección, el
  harness Bedrock DEBE usar `agent_orchestrator`.

## 5 · Casos límite y manejo de errores

- **RF-017** — SI `PUT /admin/sections/{id}` trae una clave en `views` que no
  pertenece a la sección ENTONCES el sistema DEBE ignorar esa clave y aplicar el resto
  del payload.
- **RF-018** — SI el resultado de aplicar un `PUT` deja la fila de override sin agente
  y con `views` vacío o nulo ENTONCES el sistema DEBE eliminar la fila de
  `admin_section_overrides`. Un `views` con un override vacío explícito
  (`{"main": {"sidebar_body": ""}}`) NO cuenta como vacío: la fila se conserva.
- **RF-019** — SI un `sidebar_body` contiene HTML embebido ENTONCES el render del
  sidebar NO DEBE ejecutar ese HTML (sin `rehype-raw`; Markdown plano + GFM).
- **RF-020** — SI se solicita un turno de chat `contextual` sobre una sección con
  `agent_profile_id = null` ENTONCES el sistema NO DEBE responder `5xx` (degrada al
  orquestador, RF-022).
- **RF-021** — La migración DEBE limitarse a `drop_column("description")` sobre
  `admin_section_overrides` (y su inversa en `downgrade`); NO DEBE tocar `views` ni
  `agent_profile_id` de ninguna fila.

## 6 · Registro de decisiones y descartes

| # | Decisión | Porqué | Descartado |
|---|---|---|---|
| D-1 | Reutilizar `agent_profile_id` como agente del chat contextual (no un campo nuevo) | El operador confirmó que el L2 dueño de la sección **es** el del chat; un campo extra duplicaría concepto | Campo `sidebar_agent_profile_id` separado |
| D-2 | Selector restringido a **L2** | Petición explícita del operador ("agente de nivel L2"); los L3 no tienen chat y el L1 es sólo para el chat general | Permitir L1+L2 / permitir todos con fallback |
| D-3 | Instrucciones **por vista** en Markdown, no un campo único de sección | En secciones funcionales cada vista tiene funcionalidad distinta; en tablas se repite el texto y no molesta | Un campo de instrucciones único a nivel sección |
| D-4 | Conservar `sidebar_title` (texto plano) por vista | El operador lo pidió; encabeza la pestaña de instrucciones | Fundir el título dentro del Markdown |
| D-5 | Eliminar el override + render de **Descripción** de sección | Gana espacio vertical para el área de trabajo; el propósito lo cubren las instrucciones del sidebar | Mantenerlo / convertirlo a Markdown |
| D-6 | **Sin siembra.** El texto por defecto sigue viniendo del registro de código en runtime; el override de vista tiene 3 estados (heredar / texto / vacío explícito `""`) | Evita congelar ~130 textos en la migración y que los defaults de código queden inertes tras migrar (parche, no raíz) | Sembrar la DB desde la migración (D-6 original, GATE 1) |
| D-7 | Sin `rehype-raw` en el render | Evita XSS por Markdown con HTML embebido | Permitir HTML embebido |
| D-8 | Conservar las claves JSON `sidebar_title`/`sidebar_body` (GATE 1) | Mínima huella de migración y de espejos TS/schema/tests; sólo cambia la interpretación de `sidebar_body` | Renombrar a `title`/`instructions_md` |
| D-9 | Turno contextual sin agente ⇒ **degradar al orquestador** (GATE 1) | Tolerante a fallos; nunca error visible aunque el front oculte la pestaña | Problem `409`/`422` |
| D-10 | El nuevo `default_agent_profile_id` vive en el **registro de código** `_SECTIONS` (GATE 1) | El "default" sigue siendo de código y testeable; la migración sólo dropea `description` | Inyectarlo como data de la migración |

### Re-mapeo de `default_agent_profile_id` (aprobado en GATE 1)
Secciones que hoy apuntan a L1/L3:

| Sección | Hoy | Nuevo `default_agent_profile_id` | Nota |
|---|---|---|---|
| sec-1 Dashboard | orchestrator (L1) | `null` | pantalla de sólo lectura, sin dueño L2 |
| sec-2 Métricas | orchestrator (L1) | `null` | idem |
| sec-4 Costo y Uso | orchestrator (L1) | `null` | idem |
| sec-5 Archivos | orchestrator (L1) | `null` | bucket sin dueño L2 |
| sec-6 LinkedIn · Publicar | linkedin_publishing (L3) | `agent_digital_presence` (L2) | coincide con `ROUTE_TO_PROFILE` |
| sec-7 Descubrir vacantes | vacancy_search (L3) | `agent_search_operations` (L2) | coincide con `ROUTE_TO_PROFILE` |
| sec-10 Tareas | task_manager (L3) | `null` | sin chat contextual (no hay L2 de tareas) |
| sec-11 Chat General | orchestrator (L1) | `null` | la pantalla ya ES el chat general |
| sec-12 Memoria | orchestrator (L1) | `agent_configuration` (L2) | meta-config del harness |
| sec-13 Instrucciones | orchestrator (L1) | `agent_configuration` (L2) | idem |
| sec-14 Herramientas | orchestrator (L1) | `agent_configuration` (L2) | idem |

Las 43 secciones restantes ya apuntan a un L2 y no cambian.

## 7 · Requisitos no funcionales

- **RNF-001** — El render Markdown del sidebar DEBE hacerse sólo con `react-markdown` +
  `remark-gfm` ya presentes; el `package.json` de `cjhirashi-career-admin` NO DEBE
  ganar dependencias nuevas.
- **RNF-002** — `GET /admin/sections` DEBE seguir resolviéndose en una sola consulta a
  `admin_section_overrides` (sin N+1 por sección), como hoy.
