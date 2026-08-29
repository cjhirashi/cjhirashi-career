# ADR-023: Jerarquía de secciones del Admin + configuración por vista, en tablas reales

## Estado

Aceptado — 2026-08-28

Supersede parcialmente a [ADR-021](./021-admin-sections-synthetic-pk.md): "Secciones del Admin"
deja de ser un registro en código y pasa a **seis tablas reales**; el consecutivo entero de
`sec-N` se conserva re-keyado a `s1-N` (mismo entero). Ajusta el modelo de **propiedad** de
[ADR-012](./012-bedrock-three-level-agents.md) y [ADR-017](./017-l2-agent-settings.md): la
"propiedad de secciones por agente" pasa a ser `responsible_agent_profile_id` (perfil **L2**) por
**vista**, no por sección. Sobre [ADR-022](./022-l2-split-configuration-vs-incidents.md): el L2
`agent_configuration` sigue siendo dueño de la tool de configuración de secciones, que aquí se
renombra `admin_section_settings` → `admin_view_settings` y cambia de unidad (vista en vez de
sección). Prepara el terreno para el **Frente A** de [ADR-020](./020-admin-section-templates.md)
(`SectionPageTemplate`), que consumirá este árbol.

> Nota de numeración: esta decisión se redactó como "ADR-022" en su sesión de diseño; el número
> 022 quedó ocupado ese mismo día por [ADR-022](./022-l2-split-configuration-vs-incidents.md), así
> que se formaliza como **ADR-023**. Los archivos internos de diseño (`spec-adr022-*`,
> `contrato-adr022-*`) conservan el nombre viejo; el contenido es este ADR.

## Contexto

[ADR-021](./021-admin-sections-synthetic-pk.md) dejó "Secciones del Admin" como un registro en
código (`cjhirashi-career-api/src/services/admin_sections.py`) con PK sintético `sec-N`, y una
única tabla real (`admin_section_overrides`) para los pocos campos editables por el operador
(agente dueño, textos del sidebar, descripción). Ese modelo tiene dos límites que Carlos ya está
pidiendo cruzar:

1. **Navegación plana y no editable.** El sidebar izquierdo se arma de `group` (string) + sección.
   El anidamiento real (grupo → sección de primer nivel → subsección → sub-subsección) y su orden
   viven en constantes de código. Carlos quiere un **árbol anidado editable desde el Admin** que
   ordene el sidebar sin tocar el repositorio.
2. **La unidad de configuración es la sección, no la vista.** Hoy una sección tiene un
   `default_agent_profile_id` y unos textos de sidebar. Pero una sección puede tener varias
   **vistas** (pestañas: lista, kanban, calendario, ficha…) y cada vista quiere su propio chat
   contextual (agente responsable) y sus propias instrucciones. `admin_section_overrides` no
   modela eso más allá de un blob JSON por `view_key`.

Los **datos de dominio** de cada vista —de qué recurso salen sus datos, con qué tools, si es CRUD /
calculada / singleton / externa— **no** son configuración de operador: los define el componente por
código. Lo único que el Admin edita es **quién lleva el chat de la vista** y **qué instrucciones
muestra**.

Restricciones heredadas que condicionan el diseño:

- **No existe tabla `agent_profiles`.** Los perfiles Bedrock viven en código
  (`services/bedrock/agent_profiles.py`). Cualquier "FK a perfil" es una **referencia blanda**
  validada en la aplicación (igual que `admin_section_overrides.agent_profile_id` hoy).
- **`init_db()` usa `create_all` y no corre migraciones** (ADR-019, ADR-021). Tablas nuevas
  nacerían vacías en desarrollo, CI y tests si el seed viviera solo en la migración Alembic.
- **SQLite en tests**: `JSONB`, `ARRAY(String)`, índices parciales y triggers de PostgreSQL no son
  portables sin cuidado.

Alternativas de fondo consideradas: mantener el registro en código de ADR-021; una tabla
`admin_view_overrides` separada para los dos campos editables; FK real a una tabla `agent_profiles`;
`ARRAY(String)` para la lista de tools; un trigger PostgreSQL para el tope de vistas por sección.
Se descartaron (ver [Alternativas Consideradas](#alternativas-consideradas)).

## Decisión

### 1. Seis tablas para el árbol de navegación + las vistas

> ⚠️ verificar tras implementación — los nombres exactos de tablas y columnas los fija el contrato
> de `api-rest-specialist` y pueden ajustarse.

| Tabla | PK | Rol | Padre |
|---|---|---|---|
| `admin_section_groups` | `grp-N` | Agrupador del sidebar. **Nunca tiene vistas.** | — |
| `admin_sections_l1` | `s1-N` | Sección de primer nivel. 0–10 vistas · puede tener hijas L2. | `group_id` → `admin_section_groups` |
| `admin_sections_l2` | `s2-N` | Subsección. 0–10 vistas · puede tener hijas L3. | `parent_l1_id` → `admin_sections_l1` |
| `admin_sections_l3` | `s3-N` | Sub-subsección (hoja). 0–10 vistas. | `parent_l2_id` → `admin_sections_l2` |
| `admin_views` | `vw-N` | Una pestaña dentro de una sección. | exactamente uno de `owner_l1_id` / `owner_l2_id` / `owner_l3_id` (CHECK) |

El árbol es **grupo → L1 → L2 → L3**. Cada sección (L1/L2/L3) tiene **0–10 vistas** y puede tener a
la vez subsecciones. El anidamiento más el `sort_order` de cada nivel **es** el orden del sidebar
izquierdo.

- **0 vistas** ⇒ nodo de navegación sin layout (se comporta como un grupo).
- **≥1 vista** ⇒ layout habilitado (ventana de vistas + sidebar derecho ajustado a la vista activa).

Prefijos de PK (`services/id_generator.py::TABLE_PREFIXES`): `grp` / `s1` / `s2` / `s3` / `vw`,
coherentes con `err-N` (ADR-018), `agent-N` y `sec-N` (ADR-021). La API **nunca hace INSERT** en
estas tablas: los ids los asigna el seeder de forma determinista y congelada.

### 2. Qué es de código y qué es del operador

La **estructura** —qué secciones existen, su `system_name` / `label` / `path` / `section_type`, qué
vistas tiene cada una y los datos de dominio de esas vistas— la **siembra el código** vía un seeder
idempotente compartido (ver punto 5). La API no la crea nunca.

Solo **dos columnas de `admin_views` son editables desde el Admin**, ambas *nullable*:

| Columna | `NULL` significa | Editable por |
|---|---|---|
| `responsible_agent_profile_id` | chat contextual **deshabilitado** en esa vista | Admin (UI + tool Bedrock) |
| `instructions` | panel de instrucciones **deshabilitado** en esa vista | Admin (UI + tool Bedrock) |

El seeder hace un upsert **acotado por columna**: escribe/actualiza solo las columnas de código y
**nunca** toca esas dos. Por eso **no** hace falta una tabla `admin_view_overrides` separada — los
dos campos editables viven en la misma fila que describe la vista.

### 3. La propiedad de agente es de la vista, y solo de perfiles L2

`responsible_agent_profile_id` es una **referencia blanda `String(50)`** (⚠️ verificar tras
implementación) al **`profile_id` canónico** del catálogo de agentes — el mismo dominio de valores
que `bedrock_agent_profile_prompts.profile_id` y que las constantes de
`services/bedrock/agent_profiles.py` (`agent-1`…`agent-20`), resuelto vía `canonical_profile_id()`.
**No se crea ninguna tabla de perfiles**: el catálogo sigue siendo un registro en código. Por eso
**no hay FK de BD** — `bedrock_agent_profile_prompts` solo tiene fila cuando hay override de prompt,
así que una FK impediría asignar como responsable a un perfil sin override. La integridad se valida
en la aplicación en cada `PUT` / llamada de tool: `get_profile(v)` debe existir **y** tener
`level == 2`. Es el mismo patrón que `admin_section_overrides.agent_profile_id` hoy.

- Un perfil **L1** o **L3** **no puede** ser responsable de una vista (L1 solo orquesta; L3 no
  tiene chat).
- **"Vistas que gestiona un agente"** es una lista **derivada de solo lectura**:
  `SELECT … FROM admin_views WHERE responsible_agent_profile_id = :perfil`. Reemplaza
  `set_agent_sections` / `sections_for_agent` / `default_agent_profile_id`. El multiselect
  "secciones que gestiona" del Catálogo de Agentes pasa a "vistas que gestiona", derivado y no
  editable desde ahí.

### 4. Re-key `sec-N` → `s1-N` (mismo entero)

Las **54 secciones actuales** pasan a `admin_sections_l1` conservando el entero: `sec-1` → `s1-1`,
… `sec-54` → `s1-54`; `system_name` intacto. Los **11 grupos actuales** pasan a
`admin_section_groups` con PK congelada `grp-1`..`grp-11` (mapa `_FROZEN_GROUPS` — ⚠️ verificar tras
implementación).

`admin_sections_l2` / `admin_sections_l3` nacen **vacías**: el anidamiento inicial entre niveles se
hará en el registro de código + re-seed (ver [Seguimiento](#seguimiento) (a)). La compatibilidad de
URLs del SPA (`/settings/sections/:id`) la resuelve el front con el mapa `sec-N == s1-N`, sin
endpoint de resolución.

### 5. Seeder idempotente compartido

> ⚠️ verificar tras implementación — nombre y módulo, previstos como
> `services/admin_sections_seed.py::sync_structure()`.

- Se llama **(a)** al final de `init_db()` tras `create_all`, y **(b)** desde la migración Alembic
  tras crear las tablas. Ambos caminos deben producir el mismo conjunto de filas — un test lo
  verifica.
- Upsert por `system_name` (grupos y secciones) y por `(owner, key)` (vistas). INSERT con todas las
  columnas de código; UPDATE solo las de código; `sort_order` y las dos columnas admin-owned
  existentes quedan intactos.
- **Prune**: filas con `origin = 'code'` cuyo `system_name` / `key` ya no está en el registro →
  DELETE + `warning` (CASCADE limpia vistas y subsecciones).
- Se añade `origin String` (default `'code'`) a las tres tablas de sección y a `admin_views`
  **ya en este lote**: es forward-compat para el catálogo de componentes pendiente y evita una
  migración de backfill posterior. El prune solo borra `origin = 'code'`.
- **Aserciones de arranque** (abortan si el registro de código está mal): `path` único global
  L1/L2/L3; `key` único por sección; `len(views) <= 10`; `data_source` en el enum; `resource_key`
  solo si `data_source IN ('crud','singleton')`.

### 6. Columnas de dominio de la vista (de código; preparan el futuro)

`admin_views` lleva, además de las dos columnas editables: `key`, `label`, `sort_order`,
`has_controls_window` (bool), `tool_names` (**`JSON`**, variant `JSONB` en PostgreSQL — **no
`ARRAY(String)`**, por SQLite), `data_source` (enum `crud` / `computed` / `singleton` / `external`),
`resource_key` (nullable; CHECK: no-NULL solo si `data_source IN ('crud','singleton')`). Hoy estos
valores son implícitos en el componente; explicitarlos ahora es lo que permitirá, más adelante,
**ensamblar vistas desde el Admin** sin tocar código ([Seguimiento](#seguimiento) (b)).

### 7. Tool Bedrock: `admin_section_settings` → `admin_view_settings`

> ⚠️ verificar tras implementación — nombre exacto de la tool, del suffix y de la constante de
> perfil.

- La tool `admin_section_settings` (ADR-017, mantenida por ADR-022) se reemplaza por
  **`admin_view_settings`**, con el mismo patrón de una sola tool `action = list | get | update`.
  Argumentos: `view_id` (PK `vw-N`), `section_id` (filtro en `list`),
  `responsible_agent_profile_id` (system name de un perfil **L2**; `""` = quitar), `instructions`
  (`""` = quitar).
- **Dueño**: sigue siendo el L2 `agent_configuration` (`agent-20`) de
  [ADR-022](./022-l2-split-configuration-vs-incidents.md). En su suffix, el punto que hoy habla de
  "Secciones del Admin" pasa a describir **vistas** (qué agente L2 lleva el chat de cada vista y sus
  instrucciones); la estructura del árbol (grupos, anidamiento, rutas) **no** se edita desde el chat
  — vive en código. ⚠️ verificar tras implementación: la constante puede llamarse
  `_CONFIGURATION_SUFFIX` (ADR-022) o `_SETTINGS_SUFFIX` (ADR-017) según el estado del código al
  implementar.
- `profile_catalog` deja de adjuntar `sections` por agente y adjunta `views`; `set_agent_sections`
  / `sections_for_agent` y su endpoint se eliminan.
- Antes de tocar `services/bedrock/`, consultar a los agentes globales `harness-agentes` (patrón de
  tool) y `aws-bedrock` (límites de `toolConfig` / `description` de los modelos en
  `BEDROCK_AVAILABLE_MODELS`).

### 8. Resolución de perfil por turno: ruta → sección → vista activa → agente L2

`resolve_profile_for_turn` (chat contextual del sidebar) pasa a resolver así: normaliza `route` →
match exacto o por prefijo más largo contra el índice de `path` de secciones → carga las vistas de
la sección → elige la **vista activa** (`view_key` del `page_context` si viene; si no, heurística de
detalle; si no, la de menor `sort_order`) → devuelve su `responsible_agent_profile_id` si es L2. Sin
vista, sin responsable, o si el perfil dejó de ser L2 → **orquestador** (con `warning` en el último
caso).

Se **elimina** el fallback a `resolve_agent_profile(...)` (mapas `_ROUTE_TO_PROFILE` /
`_RESOURCE_TO_DOMAIN` / `_DOMAIN_TO_PROFILE`) para la superficie contextual: la fuente única pasa a
ser la vista activa. `resolve_agent_profile` queda marcado `# deprecated` (no se borra este lote).
`set_agent_sections` se elimina.

## Nota de deploy (IMPORTANTE)

> La migración `c4d5e6f7a8b9` (⚠️ verificar tras implementación: nombre exacto del archivo y de la
> revisión; previsto `down_revision = b2c3d4e5f6a7`, la de ADR-021) **NO** corre en `init_db` (que
> usa `create_all` + el seeder de estructura). Tras reconstruir la imagen de la API hay que
> ejecutar **`alembic upgrade head`** manualmente, **en el mismo paso del despliegue** — mismo
> procedimiento que las migraciones `b1c2d3e4f5a6` ([ADR-019](./019-bedrock-prompt-caching.md)) y
> `b2c3d4e5f6a7` ([ADR-021](./021-admin-sections-synthetic-pk.md)).

`upgrade()`: crea las 6 tablas + CHECKs + FKs + índices → `sync_structure()` con **snapshots
congelados embebidos** (la migración **no** importa `services.admin_sections`) → convierte
`admin_section_overrides` fila a fila (`section_id` `sec-N` → `s1-N`; `description` y textos de
sidebar → `admin_views.instructions` de la vista principal; `agent_profile_id` →
`responsible_agent_profile_id` **solo si es L2**, si no `warning`) → **`DROP TABLE
admin_section_overrides`**. `downgrade()`: recrea `admin_section_overrides`, vuelca lo posible
(best-effort, sin round-trip) y elimina las 6 tablas.

### Ventana de regresión entre el deploy de código y la migración

Entre el arranque del código nuevo y `alembic upgrade head`, `init_db()` habrá creado y sembrado
las 6 tablas con la **estructura** (grupos, secciones, vistas, datos de dominio), pero la
**conversión de `admin_section_overrides`** —el agente responsable y las instrucciones ya
personalizados por Carlos— **no** se habrá aplicado. Durante esa ventana esas vistas muestran sus
valores de código (sin responsable / sin instrucciones personalizadas). **No hay pérdida de
datos**: `admin_section_overrides` permanece intacta hasta el `DROP` de la migración, que es la que
traslada esos valores a `admin_views`. De ahí la recomendación de encadenar `alembic upgrade head`
justo después del rebuild.

## Consecuencias

### ✅ Positivas

- **Árbol de navegación editable** desde el Admin: grupos, orden y (tras el follow-up inmediato)
  anidamiento L1/L2/L3 sin tocar el repositorio.
- **Configuración por vista**: cada pestaña de una sección tiene su propio chat contextual (agente
  L2) e instrucciones; `NULL` en cualquiera de los dos deshabilita esa pieza sin casos especiales.
- El re-key `sec-N` → `s1-N` **conserva el consecutivo entero** de ADR-021: URLs guardadas,
  historial de chat y punteros de agente siguen resolviendo.
- `data_source` / `resource_key` / `tool_names` / `origin` dejan el modelo **preparado para
  construir vistas 100 % desde el Admin** (catálogo de componentes, ADR posterior).
- Resolución de perfil con **fuente única** (la vista activa) en vez de tres mapas de heurística que
  había que mantener sincronizados.
- PKs sintéticas prefijadas (`grp-N` / `s1-N` / `s2-N` / `s3-N` / `vw-N`), coherentes con el resto
  del sistema.

### ⚠️ Negativas

- **6 tablas nuevas** + un **seeder dual** (código en `init_db` / snapshot congelado en la
  migración) que hay que mantener en sync; un test verifica que ambos caminos coinciden.
- El `downgrade` es **best-effort**, sin round-trip: no recupera el anidamiento L2/L3 hecho por el
  operador, los `sort_order` reordenados ni el desglose fino de instrucciones.
- **Ventana de regresión** hasta correr `alembic upgrade head` (ver arriba).
- Paso de deploy manual obligatorio (`alembic upgrade head`), como en ADR-019 / ADR-021.
- Un `sec-N` borrado deja hueco permanente (heredado de ADR-021), ahora también en `s1-N`.
- Referencia blanda sin FK para `responsible_agent_profile_id`: la integridad "es un perfil L2
  conocido" depende de la validación en la aplicación, no de la BD.

### 🤷 Neutras

- `resolve_agent_profile` y los mapas `_ROUTE_TO_PROFILE` / `_RESOURCE_TO_DOMAIN` /
  `_DOMAIN_TO_PROFILE` quedan **deprecated** (no se borran este lote).
- `admin_sections_l2` / `admin_sections_l3` nacen vacías; el árbol "real" tiene un solo nivel de
  secciones hasta que se siembre anidamiento en código o llegue el drag entre niveles.
- El tope de 10 vistas por sección se valida en el seeder + un test unit, sin trigger PostgreSQL.
- `match_section()` por `path` se mantiene como mecanismo de match; solo cambia lo que devuelve
  (vista activa, no sección).

## Alternativas Consideradas

### Alternativa 1: Mantener el registro en código de ADR-021

- ✅ Pro: cero tablas nuevas, cero migración.
- ❌ Contra: es justo lo que bloquea al operador — el árbol de navegación y su orden no se pueden
  editar sin tocar el repositorio, y la unidad de configuración sigue siendo la sección, no la
  vista.

### Alternativa 2: Tabla `admin_view_overrides` separada para los dos campos editables

- ✅ Pro: separación limpia "código escribe X, operador escribe Y" en tablas distintas.
- ❌ Contra: un JOIN extra en cada lectura del árbol y del catálogo, y una fila-fantasma por vista
  para dos columnas. Con un seeder acotado por columna (que nunca toca esas dos) las columnas
  *nullable* en `admin_views` logran lo mismo sin la tabla.

### Alternativa 3: FK real de `responsible_agent_profile_id` a una tabla `agent_profiles`

- ✅ Pro: integridad referencial en la BD.
- ❌ Contra: **no existe** esa tabla — los perfiles son código. Crearla solo para esta FK es un
  proyecto aparte (sembrar perfiles, mantener sync código ↔ tabla). Referencia blanda + validación
  L2 en la aplicación es el patrón que ya usa `admin_section_overrides`.

### Alternativa 4: `ARRAY(String)` para `tool_names`

- ✅ Pro: tipo nativo en PostgreSQL, consultable con operadores de array.
- ❌ Contra: no compila en SQLite → rompe los tests unitarios. `JSON` con variant `JSONB` en
  PostgreSQL se lee entero y se compara en Python; no se necesitan operadores de array.

### Alternativa 5: Trigger PostgreSQL para el tope de 10 vistas por sección

- ✅ Pro: lo garantiza la BD pase lo que pase.
- ❌ Contra: no es portable a SQLite y la API **nunca inserta vistas** (solo el seeder). Validar en
  el seeder + un test unit del registro de código es suficiente mientras no exista alta de vistas
  por API.

### Alternativa 6 (ELEGIDA): 6 tablas sembradas por un seeder idempotente compartido, con 2 columnas *nullable* editables en `admin_views`

- ✅ Pro: árbol editable y configuración por vista, con el mismo resultado en `init_db` y en la
  migración.
- ✅ Pro: sin tabla de overrides, sin FK a una tabla inexistente, portable a SQLite.
- ✅ Pro: `origin` + `data_source` + `resource_key` + `tool_names` dejan preparado el catálogo de
  componentes.

## Referencias

- Diseño: spec + contrato de implementación de `api-rest-specialist` (sesión de diseño 2026-08-28).
- API (⚠️ verificar tras implementación): `src/services/id_generator.py` (`TABLE_PREFIXES`:
  `grp` / `s1` / `s2` / `s3` / `vw`), 5 modelos nuevos (`admin_section_group.py`,
  `admin_section_l1.py`, `admin_section_l2.py`, `admin_section_l3.py`, `admin_view.py`),
  `src/models/__init__.py`, `src/schemas/admin_sections.py` (reescrito),
  `src/services/admin_sections.py` (pasa a *seed source* + helpers de árbol),
  `src/services/admin_sections_seed.py` (nuevo, `sync_structure`),
  `src/services/section_catalog.py` (lee tablas + caché; `match_active_view`,
  `resolve_profile_for_turn`), `src/routes/admin_sections.py` (`GET /admin/nav-tree`,
  `/admin/section-groups`, `/admin/sections/l1|l2|l3`, `/admin/views`),
  `src/database.py` (`init_db` llama `sync_structure`)
- Migración: `alembic/versions/c4d5e6f7a8b9_admin_sections_hierarchy_views.py` (snapshots
  congelados `_FROZEN_GROUPS`, `_SEC_TO_S1`, `_PROFILE_LEVELS`, `_L3_CHAT_FALLBACK`)
- Bedrock: `src/services/bedrock/tools.py` (`admin_view_settings`),
  `src/services/bedrock/agent_profiles.py` (punto "Vistas del Admin" del suffix de
  `agent_configuration`; `resolve_agent_profile` deprecated),
  `src/services/bedrock/profile_catalog.py` (`_attach_views`),
  `src/services/bedrock/README.md` (`page_context.view_key`, resolución de perfil, rename de tool)
- Admin: `src/components/Sidebar.tsx` (árbol de 4 niveles desde `GET /admin/nav-tree`), pantalla
  "Secciones del Admin" (árbol + orden/anidamiento), panel "Vistas" (agente responsable +
  instrucciones por vista), `src/pages/AgentCatalogPage.tsx` ("vistas que gestiona"), hooks
  `useNavTree` / `useAdminViews`, `src/config/agentProfiles.ts` (perfiles L2 para el selector)
- Modelo eliminado: `src/models/admin_section_override.py`
- [ADR-012](./012-bedrock-three-level-agents.md) · [ADR-017](./017-l2-agent-settings.md) ·
  [ADR-018](./018-error-reports-registry.md) (patrón `err-N`) ·
  [ADR-019](./019-bedrock-prompt-caching.md) (misma nota de deploy) ·
  [ADR-020](./020-admin-section-templates.md) (el `SectionPageTemplate` consumirá este árbol) ·
  [ADR-021](./021-admin-sections-synthetic-pk.md) (supersedido parcialmente) ·
  [ADR-022](./022-l2-split-configuration-vs-incidents.md) (`agent_configuration` es dueño de
  `admin_view_settings`)

## Implicaciones

- [ ] `api-rest-developer`: 5 modelos + `schemas/admin_sections.py` reescrito + seeder +
  `section_catalog` + endpoints + migración `c4d5e6f7a8b9` + tests (cobertura ≥ 80 % de lo nuevo).
- [ ] Bedrock: `admin_section_settings` → `admin_view_settings`; punto del suffix de
  `agent_configuration`; `profile_catalog` `sections` → `views`; eliminar `set_agent_sections`.
- [ ] `admin-panel-specialist`: sidebar en árbol, pantalla de Vistas, Catálogo de Agentes
  ("vistas que gestiona"), `useNavTree` / `useAdminViews`.
- [ ] Deploy: `alembic upgrade head` inmediatamente después del rebuild de la API, en el mismo
  paso.
- [ ] Borrar `models/admin_section_override.py` tras verificar la migración en PostgreSQL con datos
  de prueba.
- [ ] `code-quality-guardian` + `qa-engineer`: review + cobertura.

## Seguimiento

- **(a) Cambio de nivel de sección desde el Admin (drag L1 ↔ L2 ↔ L3)** — diferido a un
  **follow-up inmediato**. En este lote la API solo reordena y re-parenta *dentro del mismo nivel*;
  el anidamiento inicial L1/L2/L3 se hace en el registro de código + re-seed. Es el primer
  pendiente.
- **(b) Catálogo de componentes UI ligado a tablas** para ensamblar vistas 100 % desde el Admin —
  un registro de componentes reutilizables, cada uno ligado a un recurso/tabla, que el operador
  combina en una vista sin tocar código. Las columnas `data_source` / `resource_key` / `tool_names`
  / `origin` ya dejan el modelo preparado; se aborda en un ADR posterior.
- **(c) Migrar `bedrock_agent_delegation.target_ids` a `JSON` portable** (mismo patrón `JSON` +
  variant `JSONB` que `admin_views.tool_names`), para quitar el último `ARRAY(String)` no portable.
- **(d) Retirar `resolve_agent_profile` y sus mapas** (`_ROUTE_TO_PROFILE` / `_RESOURCE_TO_DOMAIN`
  / `_DOMAIN_TO_PROFILE`) — quedan `# deprecated` en este lote; se borran en el lote del Frente A o
  en un cleanup dedicado.
- El **Frente A** de ADR-020 (`SectionPageTemplate`) consumirá `GET /admin/nav-tree` y
  `admin_views` como fuente del layout de cada página; no introduce cambios en las claves definidas
  aquí.

## Corrección — Grupos/Secciones pasan a gestión 100% Admin (2026-08-28, post-QA en producción)

Tras el primer despliegue, Carlos probó la pantalla "Secciones del Admin" en producción y corrigió
la decisión original de este ADR (§Decisión punto 2, "Qué es de código y qué es del operador"): la
estructura de **grupos y secciones (L1/L2/L3) NO debía quedar sembrada/gobernada por código**. Se
revierte esa parte; el resto del ADR (6 tablas, PKs `grp-N`/`s1-N`/`s2-N`/`s3-N`/`vw-N`, el modelo
de vistas con sus 3 paneles del sidebar derecho) queda intacto y confirmado correcto.

**Modelo corregido:**

- **Grupos y Secciones (L1/L2/L3)** = estructura de navegación pura, propiedad 100% del operador.
  CRUD completo (crear, editar `label`/`system_name`/`path`/`section_type`, eliminar, reordenar,
  **mover entre niveles** — no solo dentro del mismo nivel) se hace **desde el Admin, sin tocar
  código ni redeploy**. El seeder deja de resincronizar grupos/secciones en cada arranque — la
  migración `c4d5e6f7a8b9` (+ su `sync_structure()` de este lote) fue la **única** carga inicial;
  de aquí en adelante la BD es la única fuente de verdad para el árbol. Mover una sección entre
  niveles implica migrar la fila entre `admin_sections_l1/l2/l3` (cambia el prefijo de PK
  `s1-N`→`s2-N`, etc.) y recalcular las referencias de sus hijas/vistas — no es un simple UPDATE de
  columna.
- **Vistas** = lo único que sigue naciendo en código (una vista es una pantalla/funcionalidad real:
  Carlos la pide por chat, un especialista la construye y la registra como fila de `admin_views`).
  Las vistas ya creadas se conservan tal cual. Lo que **deja de ser fijo por código** es su
  `owner`/sección: Carlos elige desde el Admin en qué grupo/sección(es) mostrar cada vista, y puede
  reasignarla cuando quiera. El modelo de los 3 paneles del sidebar derecho por vista **no cambia**
  y queda confirmado correcto tal como se implementó: chat contextual (activado al asignar
  `responsible_agent_profile_id`), panel de instrucciones (activado al cargar `instructions`) y
  panel de controles especiales (`has_controls_window`, construido en código cuando la vista lo
  requiere). Sidebar derecho inactivo si ninguno de los 3 aplica.
- **Grupo protegido `admin`** (nuevo): contiene la sección/tabla "Secciones del Admin" (esta misma
  pantalla de gestión). Visible y editable **solo para usuarios `is_superuser`** — el resto de
  grupos/secciones (las 54 actuales incluidas) quedan completamente editables/eliminables por
  cualquier usuario del Admin. Requiere una columna nueva `is_superuser` en `users` (migración con
  backfill `true` para las filas existentes, para no romper el acceso actual).

**Implicaciones para implementación** (reemplazan los pendientes de `api-rest-developer` /
`admin-panel-specialist` de más arriba en lo que toca a grupos/secciones; lo de Bedrock/vistas de
esas listas sigue vigente):

- [ ] `api-rest-specialist` + `api-rest-developer`: `POST`/`DELETE` para `admin_section_groups` y
  `admin_sections_l1/l2/l3`; ampliar `PUT` para editar campos (no solo `sort_order`/`parent_id`);
  soporte de mover una sección entre niveles (migración de fila entre tablas + recálculo de PKs
  referenciadas); `AdminViewUpdateRequest` gana el campo para reasignar `owner` (sección dueña);
  columna `is_superuser` en `users` + gate en las rutas del grupo `admin`; retirar la llamada a
  sync de grupos/secciones de `init_db()` (dejar solo el sync de vistas, si aplica cuando se
  registre una vista nueva por código).
- [ ] `admin-panel-specialist`: formularios de crear/editar/eliminar grupo y sección en
  `AdminSectionsPage.tsx`, control de mover entre niveles, reasignación de sección dueña en
  `AdminViewsPage.tsx`, ocultar el grupo `admin` en `Sidebar.tsx` para usuarios no-superuser,
  reescribir el copy de la pantalla (ya no dice "lo siembra el código").
- [ ] Actualizar el punto (a) de §Seguimiento ("drag L1↔L2↔L3 diferido") — queda resuelto por esta
  corrección, no diferido.

---

**Creado por**: Arquitecto de Soluciones
**Aprobado por**: Carlos Jiménez Hirashi
**Fecha de creación**: 2026-08-28
**Estado de vigencia**: Pendiente implementación (requiere `alembic upgrade head` en cada entorno
donde ya existan filas en `admin_section_overrides`)
**Corrección**: 2026-08-28 — ver "Corrección — Grupos/Secciones pasan a gestión 100% Admin" arriba.
