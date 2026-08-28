# ADR-023 — Contrato de API (por api-rest-specialist) + rulings del Arquitecto

> **NÚMERO DE ADR: 023.** El 022 lo tomó una sesión paralela
> (`022-l2-split-configuration-vs-incidents.md`), por eso este trabajo es el 023.

Modelo base: [`023-spec-modelo.md`](023-spec-modelo.md). Este archivo es el **contrato de
implementación**. Al final, la sección "RULINGS DEL ARQUITECTO" resuelve los 7 puntos abiertos:
esas decisiones **mandan** sobre cualquier "DECISIÓN ABIERTA" del cuerpo.

---

## 0. Hallazgos que corrigen la spec del arquitecto

1. **NO se crea ninguna tabla de perfiles de agente** (instrucción del usuario 2026-08-28). El
   catálogo de agentes ya existe como registro en código `services/bedrock/agent_profiles.py`
   (`agent-1`…`agent-20`) + su tabla de configuración `bedrock_agent_profile_prompts`
   (PK `profile_id String(50)`, "una fila por perfil", `profile_id` coincide con `agent_profiles.py`).
   `admin_views.responsible_agent_profile_id`:
   - Tipo `String(50)`; guarda el **`profile_id`** canónico (mismo dominio que
     `bedrock_agent_profile_prompts.profile_id`), resuelto vía `canonical_profile_id()`.
   - **Validación en app** en cada `PUT`/tool: `get_profile(v)` existe **y** `level == 2`.
   - **Sin FK dura de BD**: la fuente de verdad del catálogo es el registro en código, y
     `bedrock_agent_profile_prompts` solo tiene fila cuando hay override de prompt (no garantiza
     una por perfil) → una FK rompería asignar un responsable a un perfil sin override.
   - Idéntico patrón al `admin_section_overrides.agent_profile_id` actual.
2. **`init_db()` usa `create_all` y NO corre migraciones.** Con ADR-023 las 6 tablas quedarían
   vacías en dev/CI/tests. **Solución: seeder idempotente compartido**
   `services/admin_sections_seed.py::sync_structure()` llamado (a) al final de `init_db()` tras
   `create_all`, y (b) desde la migración Alembic tras crear tablas. La migración añade encima la
   conversión de datos de `admin_section_overrides` + `DROP`.
3. **`postgresql.JSONB`/`ARRAY` no compilan en SQLite.** Todas las columnas JSON usan
   `sa.JSON().with_variant(postgresql.JSONB, "postgresql")`.

---

## 1. DDL de las 6 tablas

### 1.1 Prefijos en `services/id_generator.py::TABLE_PREFIXES`
```
"admin_section_groups": "grp",
"admin_sections_l1":    "s1",
"admin_sections_l2":    "s2",
"admin_sections_l3":    "s3",
"admin_views":          "vw",
```
`init_db()` crea `{prefix}_id_seq` solo. La API **nunca hace INSERT** en estas tablas; los ids los
asigna el seeder de forma determinista y congelada (`sec-N → s1-N`, `grp-1..grp-11`, `vw-1..vw-M`).
`register_id_listener` se registra igual en los 6 modelos (para el futuro catálogo de componentes).
Registrar los 6 modelos en `src/models/__init__.py`.

### 1.2 `admin_section_groups` (PK `grp-N`)
`id String(20) PK` · `system_name String(60) UNIQUE NOT NULL` (clave de código para el upsert) ·
`name String(120) UNIQUE NOT NULL` (label sidebar, código) · `sort_order Integer NOT NULL DEFAULT 0`
(operator-owned, insert-only en seeder) · `created_at/updated_at`.
Índices: unique(system_name), unique(name), ix(sort_order).

### 1.3 `admin_sections_l1` (PK `s1-N`)
`id String(20) PK` · `group_id String(20) NOT NULL` FK→`admin_section_groups.id` **ON DELETE
RESTRICT** (operator-owned re-parent) · `system_name String(80) UNIQUE NOT NULL` (código) ·
`label String(120) NOT NULL` (código) · `path String(120) NULL UNIQUE` (índice unique parcial
`WHERE path IS NOT NULL`; nullable = nodo agrupador sin layout; único **global** L1/L2/L3 vía
seeder+runtime) · `section_type String(20) NOT NULL` CHECK IN (table,functional,metrics,bucket)
(código) · `sort_order Integer NOT NULL DEFAULT 0` (operator-owned, insert-only) · timestamps.
Índices: unique(system_name), unique(path) parcial, ix(group_id, sort_order).

### 1.4 `admin_sections_l2` (PK `s2-N`)
Igual a L1 pero `parent_l1_id String(20) NOT NULL` FK→`admin_sections_l1.id` **ON DELETE CASCADE**
en vez de `group_id`. ix(parent_l1_id, sort_order). **Vacía tras el seed.**

### 1.5 `admin_sections_l3` (PK `s3-N`)
Igual a L2 con `parent_l2_id` FK→`admin_sections_l2.id` **ON DELETE CASCADE**. ix(parent_l2_id,
sort_order). **Vacía tras el seed.**

### 1.6 `admin_views` (PK `vw-N`)
`id String(20) PK` ·
`owner_l1_id / owner_l2_id / owner_l3_id String(20) NULL` FK→`admin_sections_l{1,2,3}.id` **ON
DELETE CASCADE** ·
`key String(40) NOT NULL` (única dentro de la sección dueña) ·
`label String(120) NOT NULL` ·
`sort_order Integer NOT NULL DEFAULT 0` (código; el seeder lo sobrescribe siempre) ·
`has_controls_window Boolean NOT NULL DEFAULT false` (código) ·
`tool_names JSON variant JSONB NOT NULL server_default '[]'` (código; lista de nombres de tools) ·
`data_source String(20) NOT NULL DEFAULT 'crud'` CHECK IN (crud,computed,singleton,external) (código) ·
`resource_key String(80) NULL` (código; solo si `data_source IN (crud,singleton)` — ver ruling #3) ·
`responsible_agent_profile_id String(50) NULL` (**Admin-owned**; system name de perfil **L2**;
NULL ⇒ chat contextual off en la vista) ·
`instructions Text NULL` (**Admin-owned**; NULL/"" ⇒ panel de instrucciones off) ·
`created_at/updated_at`.

**CHECK "exactamente un owner"** (portable, testeable en SQLite):
```sql
CONSTRAINT ck_admin_views_single_owner CHECK (
 (CASE WHEN owner_l1_id IS NOT NULL THEN 1 ELSE 0 END
+ CASE WHEN owner_l2_id IS NOT NULL THEN 1 ELSE 0 END
+ CASE WHEN owner_l3_id IS NOT NULL THEN 1 ELSE 0 END) = 1)
```
**Unicidad de `key` por sección** — 3 índices únicos parciales:
```
uq_admin_views_l1_key UNIQUE (owner_l1_id, key) WHERE owner_l1_id IS NOT NULL
uq_admin_views_l2_key UNIQUE (owner_l2_id, key) WHERE owner_l2_id IS NOT NULL
uq_admin_views_l3_key UNIQUE (owner_l3_id, key) WHERE owner_l3_id IS NOT NULL
```
Índices extra: ix(owner_l1_id, sort_order), ix(owner_l2_id,...), ix(owner_l3_id,...),
ix(responsible_agent_profile_id) [respalda "vistas que gestiona un agente"].

### 1.8 `tool_names` = `JSON` (variant `JSONB` en PG), NO `ARRAY(String)` — portabilidad SQLite.
Se lee entero y se compara en Python. Nota de seguimiento (fuera de alcance): migrar
`bedrock_agent_delegation.target_ids` al mismo patrón.

---

## 2. Máx 10 / mín 0 vistas por sección
- Mín 0: implícito (owner nullable, 0 filas posible). Sin validación.
- Máx 10: **validación en el seeder + test unit del registro de código**
  (`test_no_section_declares_more_than_10_views`). La API no crea vistas → el seeder es el único
  camino de alta. **Sin trigger PG** (ver ruling #7).

---

## 3. Endpoints REST (prefijo `/admin`, JWT en todos, router en `routes/admin_sections.py`)

### 3.1 `GET /admin/nav-tree` — árbol del sidebar izquierdo
Sin params. Cacheado en memoria por `section_catalog`, invalidado en cada PUT de 3.2/3.3/3.4.
```jsonc
{ "groups": [ {
   "id":"grp-1","system_name":"metrics","name":"Métricas","sort_order":10,
   "sections":[ {
     "id":"s1-1","level":1,"system_name":"dashboard","label":"Dashboard","path":"/dashboard",
     "section_type":"metrics","sort_order":10,
     "has_layout":true,            // len(views) >= 1
     "view_count":1,
     "views":[ { "id":"vw-1","key":"main","label":"Principal","sort_order":0,
        "data_source":"computed","resource_key":null,"has_controls_window":false,
        "tool_names":[],"responsible_agent_profile_id":null,
        "has_instructions":false,  // instructions no vacío
        "chat_enabled":false } ], // == responsible_agent_profile_id is not null
     "children":[ { "id":"s2-3","level":2, "...":"...", "views":[...], "children":[
        { "id":"s3-1","level":3, "...":"...", "views":[...], "children":[] } ] } ]
   } ] } ],
  "generated_at":"2026-08-28T12:00:00Z" }
```
`sections` de un grupo = filas L1 con ese `group_id` ordenadas por `sort_order,label`. `children`
recursivo L1→L2→L3 (sin campos de grupo). L3 siempre `children:[]`. `views` ordenadas
`sort_order,key`. **`instructions` NO va entera en el árbol** — solo `has_instructions`; el texto
completo en `GET /admin/views/{id}`. Solo `200`, sin `404`.

### 3.2 Grupos — `admin_section_groups`
- `GET /admin/section-groups` → `200 [{id,system_name,name,sort_order}]` ordenado.
- `PUT /admin/section-groups/order` `{ "order": ["grp-3","grp-1",...] }` → asigna `sort_order =
  idx*10`. `400` id desconocido / lista incompleta. **(batch, ver ruling: batch + por-fila)**
- `PUT /admin/section-groups/{grp_id}` `{ "sort_order": 20 }` → `200`; `404`; `422`.
`system_name`/`name` NO editables por API.

### 3.3 Secciones — `admin_sections_l1|l2|l3`
`system_name`,`label`,`path`,`section_type` NO editables. Editable: `sort_order` + re-parent
**dentro del mismo nivel** (ver ruling #1: cambio de nivel por API DIFERIDO).
- `GET /admin/sections/l1|l2|l3` → lista de esa tabla (campos de nav-tree sin views/children).
- `GET /admin/sections/{sid}` (`sid` = s1-N|s2-N|s3-N; nivel por prefijo) → `200` sección + `views`; `404`.
- `PUT /admin/sections/{sid}` body (todos opcionales):
  ```jsonc
  { "sort_order": 12,
    "group_id": "grp-1",     // solo L1: mover a otro grupo
    "parent_id": "s1-3" }    // solo L2 (un s1-*) / L3 (un s2-*): mover a otro padre del MISMO nivel
  ```
  `404` sid; `400` group_id/parent_id inexistente o de nivel incorrecto; `409` ciclo o `path`
  duplicado resultante; `422` shape. Invalida caché.
- `PUT /admin/sections/order` batch por nivel + contenedor:
  `{ "container_id": "grp-1"|"s1-3"|"s2-7", "order": ["s1-2","s1-9",...] }` → `sort_order=idx*10`
  para las secciones hijas de ese contenedor. `400` container/ids inválidos.

### 3.4 Vistas — `admin_views`
- `GET /admin/views?section_id=s1-3&responsible=agent_x&data_source=crud` → `200 [AdminViewItem]`.
- `GET /admin/views/{vw_id}` → `AdminViewItem` con `instructions` completo; `404`.
- `PUT /admin/views/{vw_id}` body (`extra="forbid"` — ver ruling #4):
  ```jsonc
  { "responsible_agent_profile_id": "agent_search_operations",  // "" => NULL; omitir => sin cambio
    "instructions": "..." }                                     // "" => NULL; omitir => sin cambio
  ```
  Validaciones:
  - `responsible_agent_profile_id`: "" → NULL. Valor → `get_profile(v)` debe existir (acepta system
    name o `agent-N`; se persiste el **system name canónico** vía `canonical_profile_id`) **y**
    `level == 2`. No existe → `400 "unknown agent profile: <v>"`. Existe pero no L2 →
    `400 "agent profile <v> is not L2; contextual chat views can only be owned by a level-2 specialist"`.
  - `instructions`: "" o solo espacios → NULL; else `.strip()`.
  - Ninguno de los dos en el body → `400` (o dejar pasar como no-op; preferible `400
    "update requiere responsible_agent_profile_id y/o instructions"`).
  - Campo extra (p.ej. `tool_names`) → `422` (`extra="forbid"`).
  - `404` vw_id.

`AdminViewItem`:
```jsonc
{ "id":"vw-12",
  "owner":{ "level":1,"section_id":"s1-6","section_system_name":"linkedin-publish",
            "section_label":"LinkedIn · Publicar","section_path":"/linkedin" },
  "key":"main","label":"LinkedIn · Publicar","sort_order":0,
  "data_source":"external","resource_key":null,"has_controls_window":false,
  "tool_names":["get_linkedin_status","list_linkedin_posts","create_linkedin_post","delete_scheduled_linkedin_post"],
  "responsible_agent_profile_id":"agent_digital_presence","responsible_agent_label":"Presencia Digital",
  "responsible_is_l2":true,"instructions":"...","chat_enabled":true,"instructions_enabled":true }
```

### 3.5 `sec-N` desaparece
Identificador de sección ahora `s1-N`/`s2-N`/`s3-N`. `GET/PUT /admin/sections/{sid}` se conserva con
semántica nueva (reorder/re-parent); **ya no** edita agente ni instrucciones (→ `PUT
/admin/views/{id}`). `description` de sección desaparece del contrato (se fusiona en
`admin_views.instructions` de la vista principal en la migración). Compat URL SPA
(`/settings/sections/:id`): el mapa es `sec-N == s1-N` (mismo entero) → lo resuelve el front, sin
endpoint de resolución. `schemas/admin_sections.py` se reescribe: `NavTreeResponse`, `NavGroup`,
`NavSection`, `NavView`, `AdminViewItem`, `AdminViewUpdateRequest`, `SectionReorderRequest`,
`SectionReparentRequest`, `SectionGroupUpdateRequest`.

---

## 4. Tool Bedrock: `admin_section_settings` → `admin_view_settings`

Confirmar antes con `harness-agentes` (patrón `list|get|update` de una sola tool sigue siendo el
recomendado — lo es) y `aws-bedrock` (límites `toolConfig`/`description` de los modelos en
`BEDROCK_AVAILABLE_MODELS`). No se introduce forma nueva de tool: mismo `{"name","description",
"schema"}` + patrón `action=` que `agent_catalog_settings`/`error_report_settings`.

### 4.1 Definición (reemplaza el bloque `admin_section_settings` en `_TOOLS`/`_RAW_TOOLS`)
```python
{ "name":"admin_view_settings",
  "description":(
    "Vistas del Admin: qué agente L2 lleva el chat contextual de cada vista y sus instrucciones. "
    "Una 'vista' es una pestaña dentro de una sección (lista, kanban, ficha…). action=list|get|update. "
    "view_id es el PK vw-N (p.ej. vw-12); tómalo del campo id de action=list. Solo perfiles de "
    "nivel 2 pueden ser responsables. view_id requerido salvo en list."),
  "schema":{ "type":"object","properties":{
    "action":{"type":"string","enum":["list","get","update"]},
    "view_id":{"type":"string","description":"PK de la vista, p.ej. vw-12 (NO el key ni el system_name de la sección)"},
    "section_id":{"type":"string","description":"list: filtra a las vistas de una sección (s1-N | s2-N | s3-N)"},
    "responsible_agent_profile_id":{"type":"string","description":"update: system name de un perfil L2 (agent_search_operations) o su record id (agent-3). String vacío = quitar responsable."},
    "instructions":{"type":"string","description":"update: texto del panel de instrucciones. String vacío = quitar."}
  }, "required":["action"] } }
```
`_WRITE_TOOLS`: −`"admin_section_settings"` +`"admin_view_settings"`. Dispatch: `if name ==
"admin_view_settings": return await _run_admin_view_settings(db, tool_input)`.
`_resource_key_for_changelog` (~L1259): `if name=="admin_view_settings" and action=="update":
return "admin-views"`.

### 4.2 `_run_admin_view_settings(db, tool_input)`
```
list:   items = section_catalog.list_views(db, section_id=tool_input.get("section_id") or None)
        -> {"items": items}   # AdminViewItem serializado; instructions recortado ~280 chars + "…"
        section_id dado inexistente -> {"error":"unknown section: 's9-9'. Usa s1-N | s2-N | s3-N."}
get:    view_id requerido -> falta: {"error":"view_id (PK vw-N) is required for this action"}
        inexistente: {"error":"unknown admin view: 'vw-999'. Usa action=list y toma el campo 'id'."}
        -> {"item": <AdminViewItem con instructions completo>}
update: view_id requerido (idem get).
        responsible_agent_profile_id presente:
          "" -> NULL
          valor: get_profile(v) KeyError -> {"error":"unknown agent profile: 'x'"}
                 profile.level != 2 -> {"error":"agent profile 'x' is L{n}; el chat contextual de una vista solo lo puede llevar un especialista L2 (p.ej. agent_professional_identity, agent_search_operations)"}
                 ok -> persistir canonical_profile_id(v)
        instructions presente: "" / solo espacios -> NULL; else strip y guardar
        ninguno presente -> {"error":"update requiere responsible_agent_profile_id y/o instructions"}
        -> {"item": <AdminViewItem actualizado>}; invalidar caché
default -> {"error": f"unknown action: {action}"}
```
Imports: `from services import section_catalog`, `from services.bedrock.agent_profiles import
get_profile, canonical_profile_id`.

### 4.3 Dueño de la tool y suffix
Dueño sigue siendo **`AGENT_CONFIGURATION`** (L2 `agent_configuration`, `agent-20`).
`_CONFIGURATION_TOOL_NAMES`: −`admin_section_settings` +`admin_view_settings`.
Sustituir el **punto 2** de `_CONFIGURATION_SUFFIX` (NO `_SETTINGS_SUFFIX`):
```
2) **Vistas del Admin** — qué agente L2 lleva el chat contextual de cada vista del panel y las
   instrucciones que se muestran en su sidebar. Tool `admin_view_settings` (action=list|get|update,
   view_id, responsible_agent_profile_id, instructions). `view_id` es el PK `vw-N` (toma el campo
   `id` de action=list). Una vista es una pestaña de una sección (lista, kanban, ficha…). Solo
   puedes poner como responsable un perfil de NIVEL 2; string vacío en responsible_agent_profile_id
   quita el chat de esa vista, string vacío en instructions borra el panel. No editas la estructura
   de secciones (grupos, anidamiento, rutas): eso vive en código.
```
Los puntos de `agent_catalog_settings` y `bedrock_global_settings` quedan igual.
[NOTA ARQUITECTO: el contrato menciona `_CONFIGURATION_SUFFIX`/`AGENT_CONFIGURATION`; en el árbol
puede llamarse `_SETTINGS_SUFFIX`/`AGENT_SETTINGS` según ADR-017. Usar el que exista; el punto 2 es
el de "Secciones del Admin". Verificar el nombre real antes de editar.]

### 4.4 `profile_catalog.py`: `sections` → `views`
`_attach_sections` → `_attach_views(item, owned_views)` con `owned_views` = filas de `admin_views`
con `responsible_agent_profile_id == profile.id` (vía `section_catalog.list_views(db)`).
`item["views"]` reemplaza `item["sections"]`:
```jsonc
"views":[ { "id":"vw-12","key":"main","label":"LinkedIn · Publicar","section_id":"s1-6",
   "section_system_name":"linkedin-publish","section_path":"/linkedin","data_source":"external",
   "resource_key":null } ]
```
`item["resource_keys"]` = `[v["resource_key"] for v in owned_views if v["resource_key"]]` (fallback
`profile.resource_keys`). `list_catalog`/`get_catalog_item`: `owned_by_agent`(sección) →
`owned_views_by_agent`(vista). **Eliminar** `section_catalog.set_agent_sections` /
`sections_for_agent` y el endpoint que lo llama desde `AgentCatalogPage` (`grep set_agent_sections`
— probablemente `routes/bedrock.py` o `routes/agent_profiles*`). "Vistas que gestiona" = lista
derivada **solo-lectura** en el Catálogo de Agentes.

---

## 5. `resolve_profile_for_turn` / `match_section` — ruta → sección → vista activa → L2

### 5.1 `match_active_view` (en `section_catalog`, tablas + caché)
```python
@dataclass(frozen=True)
class ActiveView:
    section_id: str; section_level: int; section_path: str
    view_id: str | None; view_key: str | None
    responsible_agent_profile_id: str | None
    instructions: str | None; has_controls_window: bool

async def match_active_view(db, route: str, view_key: str | None = None) -> ActiveView | None
```
1. Normalizar `route` (sin query, `rstrip('/')`).
2. Match exacto contra índice en memoria `{path: (level, section_id)}` (secciones con path no nulo).
   Si no, match por **prefijo más largo** (`route.startswith(f"{path}/")`) — como el `match_section`
   actual.
3. Sin match → `None`.
4. Cargar vistas de la sección (orden `sort_order,key`). 0 vistas → `ActiveView(view_id=None,
   responsible=None, ...)`.
5. Vista activa: `view_key` del contexto si existe en la sección; si no y `route` es de detalle
   (hubo prefijo, no exacto) y hay vista con key en (`view`,`record`) → esa (conserva comportamiento
   actual para `/career/vacancies/vac-1`); si no → la de menor `sort_order`.
6. Devolver `ActiveView` con datos de esa vista.
`view_key` llega en `page_context` (SPA sabe la pestaña activa). `schemas/bedrock.py::page_context`
es `Dict[str,Any]` libre → sin cambio de schema, solo convención; documentar en
`services/bedrock/README.md`.

### 5.2 `resolve_profile_for_turn`
```python
async def resolve_profile_for_turn(db, *, chat_surface, agent_profile_id, page_context):
    if chat_surface == "general": return get_profile(AGENT_ORCHESTRATOR)
    if agent_profile_id: return get_profile(agent_profile_id)          # override explícito
    ctx = page_context or {}
    active = await match_active_view(db, ctx.get("route") or "", ctx.get("view_key"))
    if active and active.responsible_agent_profile_id:
        prof = get_profile(active.responsible_agent_profile_id)
        if prof.level == 2: return prof
        # perfil dejó de ser L2: degradar a orquestador + logging.warning
    return get_profile(AGENT_ORCHESTRATOR)                             # sin vista / sin responsable
```
Se **elimina** el fallback a `resolve_agent_profile(...)` (mapas `_ROUTE_TO_PROFILE` /
`_RESOURCE_TO_DOMAIN` / `_DOMAIN_TO_PROFILE`) para la superficie contextual — fuente única = vista
activa. `resolve_agent_profile` se marca **deprecated** (ruling #6), no se borra este lote.
`chat_agent_id()` / `_L3_CHAT_FALLBACK` de `admin_sections.py` salen del runtime; el mapa
`_L3_CHAT_FALLBACK` se **embebe en el seeder** (ver 6.1 y ruling correspondiente).

### 5.3 `task_scheduler.py` arma `page_context` sin `route` → `match_active_view` → `None` →
orquestador, salvo `agent_profile_id` explícito (lo que ya hace). Sin cambios en el scheduler.

---

## 6. Migración Alembic

**Archivo:** `alembic/versions/c4d5e6f7a8b9_admin_sections_hierarchy_views.py`
`revision="c4d5e6f7a8b9"`, `down_revision="b2c3d4e5f6a7"`. **No corre en `init_db`.** Nota de deploy
igual a ADR-019/021: tras rebuild, `alembic upgrade head` en el mismo paso.

### 6.1 `upgrade()`
1. `op.create_table` de las 6 tablas (columnas §1), CHECKs (`section_type`, `data_source`,
   `ck_admin_views_single_owner`, + `resource_key` ruling #3), FKs con `ondelete`, índices
   (incl. los 3 parciales únicos con `postgresql_where`/`sqlite_where`). Guard `if not
   inspector.has_table(...)`.
2. `CREATE SEQUENCE IF NOT EXISTS grp_id_seq START 1` … `s1/s2/s3/vw`.
3. **Seed de estructura** con **mapas congelados embebidos** (la migración NO importa
   `services.admin_sections`):
   - **11 grupos** → `admin_section_groups`. `_FROZEN_GROUPS` (validar en review, ruling #2):
     ```
     "Métricas":             ("grp-1","metrics",10)
     "Principal":            ("grp-2","principal",15)
     "Almacenamiento":       ("grp-3","storage",20)
     "Presencia Digital":    ("grp-4","digital-presence",30)
     "Operativa de Búsqueda":("grp-5","search-ops",31)
     "Diseño PDF":           ("grp-6","pdf-design",40)
     "Agente IA":            ("grp-7","agent-ai",51)
     "Settings":             ("grp-8","settings",90)
     "Identidad Profesional":("grp-9","professional-identity",100)
     "Networking":           ("grp-10","networking",150)
     "Soporte":              ("grp-11","support",160)
     ```
   - **54 secciones** → `admin_sections_l1`, **re-key `sec-N → s1-N`** (mismo entero). `_SEC_TO_S1`
     = copia congelada de la tabla `sec-N ↔ system_name` de ADR-021 (test lo verifica contra el
     registro vivo). Cada fila: `group_id` del mapa, `system_name/label/path/section_type/sort_order`
     de un **snapshot embebido** de los 54 specs.
   - **Vistas** → `admin_views`, `owner_l1_id=s1-N`. De cada `AdminSectionSpec.views` embebido:
     `key`, `label`, `sort_order`(idx), `has_controls_window=false`, `tool_names`=`related_tools`
     de la sección (o `[]`). `data_source`:
     `metrics→computed`; `bucket→external`; `functional→external`;
     `table` + singleton (marca embebida) → `singleton`; `table` resto → `crud`.
     `resource_key = spec.resource_key` solo si `data_source in (crud,singleton)` si no `NULL`.
   - `responsible_agent_profile_id` de cada **vista principal** (menor `sort_order`):
     `spec.default_agent_profile_id` L2 → ese; L1 → `NULL`; L3 → `_L3_CHAT_FALLBACK` embebido
     (linkedin_publishing→digital_presence, vacancy_search→search_operations, github→digital_presence,
     task_manager→orchestrator[L1⇒NULL], changelog→NULL); si el fallback es L1/no hay → `NULL`.
     Vistas no principales → `NULL`. `_PROFILE_LEVELS` embebido.
4. **Conversión de `admin_section_overrides`** fila a fila (`section_id` = `sec-N` → `s1-N`):
   - `.description` (no vacío) → **prepend** a `admin_views.instructions` de la vista principal de
     `s1-N` (`\n\n`).
   - `.views` JSONB `{view_key:{sidebar_title,sidebar_body,description}}`: para cada `view_key` que
     exista en `admin_views(owner_l1_id=s1-N, key=view_key)`, `instructions` = `"\n\n".join(filter(
     None,[sidebar_title,sidebar_body,description]))` y concatenar. `view_key` inexistente →
     `logging.warning`.
   - `.agent_profile_id` (no NULL): L2 → `responsible_agent_profile_id` de la vista principal (pisa
     el seed). No L2 → descartar + `logging.warning`.
   - `section_id` fuera de `_SEC_TO_S1` → `logging.warning`, ignorar.
5. `op.drop_table("admin_section_overrides")`.
6. `admin_sections_l2` / `admin_sections_l3` quedan **vacías**.

### 6.2 `downgrade()` (best-effort, no round-trip perfecto)
1. `create_table("admin_section_overrides", ...)` esquema post-ADR-021 (`section_id String(40) PK`,
   `agent_profile_id String(50)`, `description Text`, `views JSON`, `updated_at`).
2. Por cada `admin_sections_l1` `s1-N` + sus `admin_views`: `responsible_agent_profile_id` no nulo y
   != default de código (snapshot embebido) → `admin_section_overrides(section_id="sec-N").
   agent_profile_id`; `instructions` no nulas → `views[view_key] = {"sidebar_body": instructions}`.
   Todo default → no crear override.
3. `drop_table` de `admin_views`, `admin_sections_l3`, `admin_sections_l2`, `admin_sections_l1`,
   `admin_section_groups` (ese orden).
4. `DROP SEQUENCE IF EXISTS grp_id_seq … vw_id_seq`.
5. **Pérdida documentada**: anidamiento L2/L3 del operador, `sort_order` reordenados, desglose fino
   de instrucciones.

### 6.3 Seeder compartido `services/admin_sections_seed.py`
`async def sync_structure(session_or_conn) -> None` — idempotente; **NUNCA** toca
`responsible_agent_profile_id` ni `instructions`:
- **Grupos**: upsert por `system_name`. INSERT con `sort_order` de código; UPDATE solo `name`.
  `sort_order` existente intacto.
- **Secciones L1**: upsert por `system_name`. INSERT con `group_id,label,path,section_type,
  sort_order`. UPDATE solo `label,path,section_type`. `group_id`/`sort_order` existentes intactos.
  **Prune**: L1 en DB cuyo `system_name` no está en código → DELETE + warning (CASCADE borra vistas
  y L2/L3 hijas). Ver ruling #5 (`origin='code'`).
- **L2/L3**: el seeder NO siembra filas (no hay estructura L2/L3 en código este lote); prune por
  CASCADE.
- **Vistas**: upsert por `(owner_l*_id, key)`. INSERT/UPDATE de TODAS las columnas de código
  (`label,sort_order,has_controls_window,tool_names,data_source,resource_key`). NUNCA los 2
  admin-owned. **Prune**: vista cuyo `key` ya no está en el spec de su sección → DELETE + warning.
- **Aserciones** (abortan si el código está mal): `path` único global; `key` único por sección;
  `len(views) <= 10`; `data_source` en enum.
- Llamado desde `init_db()` (tras `create_all`, mismo `engine.begin()`) y desde `upgrade()` (paso
  3, con snapshot embebido). Ambos caminos deben producir el mismo resultado — test lo verifica.

---

## 7. Tests (cobertura ≥80% de lo nuevo; `qa-engineer` valida)
- **Unit puros**: `test_admin_sections.py` (ampliar) + `test_admin_sections_seed.py` (nuevo):
  `len(views)<=10`; `path` único global; `key` único/sección; `data_source` ∈ enum; `resource_key`
  solo si crud/singleton; `responsible` semilla es L2 o NULL; `_SEC_TO_S1` identidad sobre el
  entero, cuadra con `_FROZEN_MAP` de ADR-021; `_FROZEN_GROUPS` cuadra con los `group=` del
  registro; inferencia `data_source`↔`section_type`; `_L3_CHAT_FALLBACK` produce L2 o NULL.
- **Contrato/integración SQLite** (`test_admin_views_api.py`, `test_nav_tree.py`,
  `test_resolve_profile_for_turn.py`): fixture SQLite in-memory + `create_all` de los 6 modelos
  nuevos (metadata acotada para esquivar el `JSONB` de otros modelos) + `PRAGMA foreign_keys=ON`
  vía `event.listens_for(engine.sync_engine,"connect")` para poder probar CASCADE. Poblar con el
  seeder o filas explícitas (`id="s1-1"`, `vw-1`…). Casos: nav-tree shape/orden/recursión/derivados;
  reorder grupos y secciones; re-parent válido / `409` ciclo / `400` nivel incorrecto;
  `GET/PUT /admin/views` incl. `400` responsable L3, `400` inexistente, `""` limpia, `422`
  `extra="forbid"`; CHECK single-owner (0 y 2 owners → IntegrityError); índices parciales únicos;
  `match_active_view` (exacto, prefijo→`view`, `view_key` gana, 0 vistas → view_id None, sin match →
  None); `resolve_profile_for_turn` (general→orquestador, override gana, L2→ese, sin responsable→
  orquestador, dejó de ser L2→orquestador+warning).
- **Tool Bedrock** `test_admin_view_settings.py` (retirar el bloque `admin_section_settings` de
  `test_admin_sections_rekey_surfaces.py`): list/get/update, error L3 con "L2" en el mensaje, perfil
  inexistente, "" limpia, sin campos → error; dispatch en `_WRITE_TOOLS`;
  `_resource_key_for_changelog(...,"update")=="admin-views"`; `_CONFIGURATION_TOOL_NAMES` contiene
  `admin_view_settings` y no `admin_section_settings`.
- **`profile_catalog`** `test_profile_catalog.py`: `item["views"]` (no `["sections"]`); L2 con vista
  asignada la ve; `resource_keys` derivados.
- **Migración** `test_admin_sections_migration_map.py` (ampliar): `_SEC_TO_S1`, `_FROZEN_GROUPS`,
  `_PROFILE_LEVELS`, snapshot de 54 specs cuadran 1:1 con el registro vivo; `sync_structure` vivo y
  el seed embebido de la migración producen el mismo conjunto de filas; simular conversión de
  overrides (L2→vista principal; L3→descartado+warning; `views[k].sidebar_*`→`instructions`;
  `view_key` inexistente→warning).
- **NO testeable en SQLite** (documentar): CASCADE/RESTRICT necesitan `PRAGMA foreign_keys=ON`
  (activarlo en el fixture); trigger PG (no se añade); `JSONB` operadores (no se usan); `nextval`
  (la API no inserta).

---

## 8. Archivos y orden para `api-rest-developer`
**Fase 1 — modelos + tipos:** `id_generator.py` (prefijos) · 5 modelos nuevos
(`admin_section_group.py`, `admin_section_l1.py`, `admin_section_l2.py`, `admin_section_l3.py`,
`admin_view.py` con `__table_args__` CHECK+índices parciales + `register_id_listener`) ·
`models/__init__.py` · `schemas/admin_sections.py` (reescribir).
**Fase 2 — registro de código + seeder:** `services/admin_sections.py` (`AdminViewSpec` +
`has_controls_window/tool_names/data_source/resource_key`; `singleton:bool` en `AdminSectionSpec`;
asserts; sacar `chat_agent_id`/`_L3_CHAT_FALLBACK` del runtime) · `services/admin_sections_seed.py`
(nuevo) · `database.py::init_db` (llamar `sync_structure`).
**Fase 3 — catálogo runtime + endpoints:** `services/section_catalog.py` (reescribir: lee tablas +
caché; `list_nav_tree`, `list_views`, `get_view`, `update_view`, `list_l1/l2/l3`, `update_section`,
`update_group`, `ActiveView`+`match_active_view`, `resolve_profile_for_turn`; eliminar
`set_agent_sections`/`sections_for_agent`/`_serialize` viejo) · `routes/admin_sections.py`
(endpoints §3; eliminar endpoint que llama `set_agent_sections`) · `services/bedrock/agent_loop.py`
(verificar propagación de `view_key`).
**Fase 4 — Bedrock:** `services/bedrock/tools.py` (`admin_view_settings` §4.1/4.2) ·
`services/bedrock/agent_profiles.py` (`_CONFIGURATION_TOOL_NAMES` / punto 2 del suffix;
`resolve_agent_profile` deprecated) · `services/bedrock/profile_catalog.py`
(`_attach_views`) · `services/bedrock/README.md` (`page_context.view_key`, resolución de perfil,
rename tool).
**Fase 5 — migración + limpieza:** `alembic/versions/c4d5e6f7a8b9_*.py` (§6, snapshots congelados) ·
**borrar** `models/admin_section_override.py` · tests §7.
**Fase 6 — verificación:** `alembic upgrade head` en PG limpio con datos de prueba de
`admin_section_overrides`; revisar warnings; `pytest --cov`; entregar a `code-quality-guardian` +
`qa-engineer`.

Después: `admin-panel-specialist` (sidebar en árbol, pantalla de Vistas, Catálogo de Agentes,
`useNavTree`/`useAdminViews`) y `documentacion-especialista`.

---

# RULINGS DEL ARQUITECTO (mandan sobre las "DECISIONES ABIERTAS" del cuerpo)

1. **Cambio de nivel de sección por API (L1↔L2↔L3): DIFERIDO a un lote posterior.** En este lote la
   API solo reordena y re-parenta **dentro del mismo nivel**. El anidamiento inicial L1/L2/L3 se
   hace en el registro de código + re-seed. Anotar como primer pendiente en ADR-023 §Seguimiento.
   (El usuario quiere anidar desde el Admin; se le comunica que en batch 1 el anidamiento entre
   niveles es por código y el drag entre niveles llega en el follow-up inmediato.)
2. **11 grupos `_FROZEN_GROUPS`**: aprobados los valores de §6.1 como permanentes (estilo
   `_SLUG_TO_PK`). Si al implementar aparece un `group=` no listado, PARAR y avisar.
3. **CHECK `resource_key IS NULL OR data_source IN ('crud','singleton')`: SÍ.**
4. **`PUT /admin/views/{id}` con `extra="forbid"`: SÍ** (rechaza con `422` cualquier campo no
   editable).
5. **Añadir columna `origin String(16) NOT NULL DEFAULT 'code'`** a `admin_sections_l1/l2/l3` y
   `admin_views` **ya en este lote**. El prune del seeder solo borra filas con `origin='code'`. Es
   seguro forward-compat para el catálogo de componentes pendiente y evita una migración de
   backfill después. El prune queda **activo** en este lote (todas las filas son `origin='code'`).
6. **`resolve_agent_profile` y los mapas `_ROUTE_TO_PROFILE` / `_RESOURCE_TO_DOMAIN` /
   `_DOMAIN_TO_PROFILE`: marcar `# deprecated`, NO borrar este lote.** Se retiran en el lote del
   Frente A o en un cleanup dedicado.
7. **Trigger PG de máx-10: NO.** Validación en seeder + test unit del registro. Suficiente mientras
   no exista alta de vistas por API.

**Aceptados sin cambio** (los "decididos" del contrato): referencia blanda `String(50)` sin FK para
`responsible_agent_profile_id` + validación L2 en app; `JSON`/`JSONB` variant (no `ARRAY`); seeder
idempotente compartido `init_db`+migración; CHECK single-owner por `CASE WHEN … = 1`; 3 índices
únicos parciales para `key`/sección; `system_name` en grupos y en las 3 tablas de sección; endpoints
de reorden **batch + por-fila**; "vistas que gestiona un agente" = derivado solo-lectura, se elimina
`set_agent_sections`; el seeder aplica `_L3_CHAT_FALLBACK` para conservar el chat contextual de
`/linkedin` y `/job-discovery`.

**Pendientes para ADR-023 §Seguimiento:** (a) cambio de nivel de sección desde el Admin
(drag L1↔L2↔L3); (b) catálogo de componentes UI ligado a tablas para construir vistas desde el
Admin (columnas `data_source`/`resource_key`/`tool_names`/`origin` ya lo preparan); (c) migrar
`bedrock_agent_delegation.target_ids` al tipo `JSON` portable; (d) retirar `resolve_agent_profile`
y sus mapas.
