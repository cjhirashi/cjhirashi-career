# Spec — ADR-023 (el 022 lo tomó otra sesión): Jerarquía de Secciones + Vistas en tablas reales

Supersede casi por completo ADR-021 (el registro `sec-N` en código pasa a tablas reales).
Lote propio, ANTES del Frente A (`SectionPageTemplate`), que lo consumirá.

## Árbol

```
Grupo (grp-N)              ── nunca tiene vistas; solo agrupa secciones en el sidebar izquierdo
└─ Sección L1 (s1-N)       ── 0–10 vistas · puede tener hijas L2
   └─ Sección L2 (s2-N)    ── 0–10 vistas · puede tener hijas L3
      └─ Sección L3 (s3-N) ── 0–10 vistas · hoja
```

- **0 vistas** ⇒ nodo de navegación sin layout (se comporta como un grupo).
- **≥1 vista** ⇒ layout habilitado (ventana de vistas + sidebar derecho).
- Una sección puede tener vistas **y** sub-secciones a la vez.
- El anidamiento + `sort_order` de cada nivel = el orden del sidebar izquierdo.

## Tablas (todas con prefijo vía `services/id_generator.py` → añadir a `TABLE_PREFIXES`)

### `admin_section_groups` — PK `grp-N`
| col | tipo | origen |
|---|---|---|
| `id` | `String(20)` PK | id_generator `grp` |
| `name` | `String` unique | Admin |
| `sort_order` | `Integer` | Admin |

### `admin_sections_l1` — PK `s1-N`
| col | tipo | origen |
|---|---|---|
| `id` | PK | id_generator `s1` |
| `group_id` | FK → `admin_section_groups` | Admin (re-parent) |
| `system_name` | `String` unique | código (seed) |
| `label` | `String` | código |
| `path` | `String` unique (global entre L1/L2/L3) | código |
| `section_type` | `String` (`table`/`functional`/`metrics`/`bucket`) | código |
| `sort_order` | `Integer` | Admin |

### `admin_sections_l2` — PK `s2-N`
Igual que L1 pero `parent_l1_id` FK → `admin_sections_l1` en vez de `group_id`.

### `admin_sections_l3` — PK `s3-N`
Igual pero `parent_l2_id` FK → `admin_sections_l2`.

### `admin_views` — PK `vw-N`
| col | tipo | origen |
|---|---|---|
| `id` | PK | id_generator `vw` |
| `owner_l1_id` / `owner_l2_id` / `owner_l3_id` | 3 FK nullables + **CHECK: exactamente uno NOT NULL** | código |
| `key` | `String` (única dentro de la sección dueña) | código |
| `label` | `String` | código |
| `sort_order` | `Integer` | código |
| `has_controls_window` | `Boolean` default false | código |
| `tool_names` | `JSONB` / `String[]` (lista de nombres de tools builtin/MCP) | código |
| `data_source` | `String` enum: `crud` / `computed` / `singleton` / `external` | código (declara de dónde salen los datos de la vista; hoy implícito en el componente) |
| `resource_key` | `String` **nullable** (solo vistas `data_source=crud`) | código (baja desde la sección; liga la vista a su recurso CRUD) |
| `responsible_agent_profile_id` | `String` FK → `agent_profiles`, **nullable**, **debe ser un perfil L2** (validación app) | **Admin** |
| `instructions` | `Text` **nullable** | **Admin** |

- `responsible_agent_profile_id == NULL` ⇒ chat contextual **deshabilitado** en esa vista.
- `instructions == NULL/""` ⇒ ventana de instrucciones **deshabilitada** en esa vista.
- Máx. 10 vistas por sección: validación en seeder + API (opcional trigger/constraint).
- **NO hay tabla `admin_view_overrides`**: los 2 campos editables viven aquí; el seeder hace
  upsert que **solo** escribe las columnas de código y nunca `responsible_agent_profile_id` /
  `instructions`.

## Comportamiento derivado

- **Sidebar izquierdo** (`admin/src/components/Sidebar.tsx`): se reconstruye desde
  grupos → s1 → s2 → s3 ordenado por `sort_order`. Reemplaza la lógica `group` + sección plana.
- **"Vistas que gestiona un agente"** = `SELECT * FROM admin_views WHERE responsible_agent_profile_id = :id`.
  Reemplaza `set_agent_sections` / `sections_for_agent` / `default_agent_profile_id`.
  El multiselect del Catálogo de Agentes ("secciones que gestiona") → **"vistas que gestiona"**
  (editable por-vista, o lista derivada solo-lectura — decidir en diseño de contrato).
- **Sidebar derecho** ajusta TODO su contenido a la **vista activa**: chat contextual
  (`responsible_agent_profile_id`), instrucciones (`instructions`), ventana de controles
  (`has_controls_window`, contenido renderizado por código en Frente A).
- `resolve_profile_for_turn` / `match_section`: ruta → sección → vista activa → agente L2 de la vista.

## Migración (Alembic, NO corre en `init_db`; `alembic upgrade head` manual)

1. Crear las 6 tablas + CHECKs + FKs.
2. Seed desde el registro en código reformado (`services/admin_sections.py`):
   - 11 `group` actuales → `admin_section_groups` (con `sort_order`).
   - 54 secciones actuales → `admin_sections_l1` bajo su grupo. **Re-key `sec-N` → `s1-N`**
     (guardar mapa en la migración; `sec-1`→`s1-1`, … `sec-54`→`s1-54`). `system_name` intacto.
   - Vistas de cada sección (de `AdminSectionSpec.views`) → `admin_views` con `owner_l1_id`,
     `has_controls_window=false`, `tool_names` desde `related_tools` de la sección (o [] si no aplica).
   - `admin_section_overrides` (ADR-021):
     - `.views[k].sidebar_title` + `.sidebar_body` → `admin_views.instructions` (concatenado) de la vista `k`.
     - `.agent_profile_id` (dueño de sección) → `admin_views.responsible_agent_profile_id` de la
       vista principal SOLO si ese perfil es L2; si no, se descarta con `logging.warning`.
   - Luego `DROP TABLE admin_section_overrides`.
3. `admin_sections_l2` / `admin_sections_l3` se crean vacías.
4. `downgrade`: recrear `admin_section_overrides`, volcar de vuelta lo posible, drop de las 6 tablas.

## API

- Nuevos modelos (6) con `register_id_listener`. Añadir prefijos a `TABLE_PREFIXES`
  (`grp`, `s1`, `s2`, `s3`, `vw`) y `admin_views`/secciones a `models/__init__.py`.
- `services/admin_sections.py`: deja de ser la fuente viva; pasa a **seed source** (estructura) +
  helpers de árbol. `section_catalog.py` se reescribe para leer de las tablas (con caché).
- Endpoints (`routes/admin_sections.py` → renombrar/ampliar):
  - `GET /admin/nav-tree` — grupos→s1→s2→s3→vistas para el sidebar.
  - `GET/PUT /admin/section-groups`, `/admin/sections/l1|l2|l3` — orden y re-parent.
  - `GET /admin/views`, `GET /admin/views/{vw-N}`, `PUT /admin/views/{vw-N}`
    (solo `responsible_agent_profile_id` + `instructions`; valida L2).
  - Validación de máx. 10 vistas por sección donde aplique.
- Bedrock:
  - `admin_section_settings` → **`admin_view_settings`** (`action=list|get|update`, `view_id`,
    `responsible_agent_profile_id`, `instructions`). Actualizar `tools.py`, `_SETTINGS_SUFFIX`
    en `agent_profiles.py`, `profile_catalog.py` (sections→views).
  - `resolve_profile_for_turn`: ruta→sección→vista activa→agente L2.
- Consultar `harness-agentes` y `aws-bedrock` antes de tocar `services/bedrock/`.

## Admin

- `Sidebar.tsx`: árbol de 4 niveles (grupo/s1/s2/s3) con expand/collapse, desde `GET /admin/nav-tree`.
- Pantalla "Secciones del Admin": pasa a mostrar el árbol + edición de orden/anidamiento (grupos y
  las 3 listas de secciones). Cada sección lista sus vistas activas.
- Pantalla/panel "Vistas": tabla de `admin_views`; edición por vista de agente responsable
  (solo L2 en el selector) e instrucciones.
- `AgentCatalogPage`: "secciones que gestiona" → "vistas que gestiona".
- Tipos/h’ooks: `useAdminSections` → `useNavTree` + `useAdminViews`.
- `config/agentProfiles.ts`: exponer qué perfiles son L2 para el selector.

## Docs

- **Nuevo ADR-023 (el 022 lo tomó otra sesión)**; marcar **ADR-021 como "Supersedido por ADR-023 (el 022 lo tomó otra sesión)"** (y ADR-020 nota de que el
  template consumirá el árbol). Nota en **ADR-012 / ADR-017**: la propiedad de secciones por agente
  se reemplaza por `responsible_agent_profile_id` (L2) por vista.
- `docs/09-DECISIONS/README.md` alta ADR-023 (el 022 lo tomó otra sesión) + estado ADR-021.
- `CLAUDE.md` bullet.

## Pendiente (NO en este lote — anotar en ADR-023 (el 022 lo tomó otra sesión) § Seguimiento)
- **Catálogo de componentes ligado a tablas**: construir vistas 100% desde el Admin —
  un registro de componentes UI reutilizables, cada uno ligado a un recurso/tabla, que el
  operador ensambla en una vista sin tocar código. `data_source` + `resource_key` + `tool_names`
  ya dejan el modelo preparado para esto. Se aborda en un ADR posterior.

## Supuestos a validar en review
- `tool_names` como `JSONB` (portabilidad SQLite en tests) vs `ARRAY(String)`.
- `path` único global; una sección sin vistas puede no tener `path`.
- 10-máx: validación app; sin trigger salvo que se pida.
- Prefijos `grp/s1/s2/s3/vw` definitivos.
- L2/L3 vacías al inicio; el operador anida desde el Admin.

## Orden de delegación
1. `api-rest-specialist` — contrato: DDL exacto de las 6 tablas, CHECKs, endpoints, forma de
   `nav-tree`, tool `admin_view_settings`, plan de migración/seed/downgrade.
2. `api-rest-developer` — implementa modelos + migración + seeder + `section_catalog` + endpoints
   + bedrock + tests.
3. `admin-panel-specialist` — sidebar en árbol + pantalla de vistas + edición por vista + Catálogo
   de Agentes + tipos/hooks + tests.
4. `documentacion-especialista` — ADR-023 (el 022 lo tomó otra sesión) + updates 021/020/012/017 + README + CLAUDE.md.
5. `code-quality-guardian` + `qa-engineer` — review + cobertura ≥80%.
6. `git-especialista` — commit(s) en `develop`.
