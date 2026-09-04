---
titulo: Plan — Sidebar contextual configurable por sección del Admin
tipo: plan
estado: verified
fecha: 2026-09-04
feature_id: "001"
spec: ./spec.md
---

# Plan de implementación (patrón por capas)

## 0 · Enfoque

Cambio **transversal acotado**, sin tabla nueva: se reinterpreta el campo
`agent_profile_id` de `admin_section_overrides` como "agente **L2** del chat
contextual", se retira la derivación en código (`chat_agent_id()` /
`_L3_CHAT_FALLBACK`), `sidebar_body` pasa a renderizarse como Markdown, se elimina la
columna/override `description`, y el sidebar derecho del Admin se vuelve condicional
(chat / instrucciones / panel completo). Una migración Alembic sólo dropea
`description`.

Capas tocadas (todas ya existen): **model → migración → service (catálogo + bedrock) →
route/schema → SPA (tipos, api, hook, página, sidebar, layout)**. Sin fronteras de
integración nuevas (no MCP, no otro servicio, no cliente Bedrock nuevo): la única
"salida" es la Postgres compartida vía el repo/servicio existente.

## 1 · Fronteras y archivos por capa

| Capa | Archivo | Cambio |
|---|---|---|
| Modelo | `cjhirashi-career-api/src/models/admin_section_override.py` | Quitar `description` (columna). Docstring: nueva semántica de `agent_profile_id`. |
| Migración | `cjhirashi-career-api/alembic/versions/<rev>_drop_admin_section_override_description.py` | `op.drop_column("admin_section_overrides","description")` + inversa `add_column(... sa.Text())`. `down_revision = b2c3d4e5f6a7`. No corre en `init_db` (nota de deploy, igual que b1c2d3e4f5a6). |
| Servicio · registro | `cjhirashi-career-api/src/services/admin_sections.py` | Re-mapear `default_agent_profile_id` de sec-1/2/4/5/10/11 → `None`, sec-6→`agent_digital_presence`, sec-7→`agent_search_operations`, sec-12/13/14→`agent_configuration`. `_career(...)` acepta `agent_id: Optional[str]`. **Eliminar** `chat_agent_id()` y `_L3_CHAT_FALLBACK`. `default_agent_profile_id` de `AdminSectionSpec` → `Optional[str]`. Nuevo helper `is_l2(profile_id) -> bool`. Assert en carga: todo `default_agent_profile_id` no nulo es L2. |
| Servicio · catálogo | `cjhirashi-career-api/src/services/section_catalog.py` | `_serialize`: quitar `chat_agent_profile_id`, `description`, `description_is_default`; añadir `sidebar_has_chat`, `sidebar_has_instructions`. `_view_override`: 3 estados por sub-campo (clave ausente = código; `""` = vacío explícito; texto = override); `is_default` = sin override de title ni body. `update_section`: quitar params `description`/`clear_description`; `views` admite `""` explícito; `_row_is_empty` no cuenta un `views` con `""` como vacío; validar `is_l2` del agente. `resolve_profile_for_turn`: contextual → `get_section` de la ruta → si `agent_profile_id` → ese perfil; si `None` o sin match → `agent_orchestrator`. Quitar el `import chat_agent_id`. |
| Servicio · bedrock | `cjhirashi-career-api/src/services/bedrock/agent_profiles.py` | Nada que exportar cambia salvo que ya no se importa `chat_agent_id` desde aquí (vivía en `admin_sections.py`). Confirmar que `resolve_agent_profile` sigue igual (lo usa `general`). |
| Servicio · bedrock loop | `cjhirashi-career-api/src/services/bedrock/agent_loop.py` | Sin cambio de código (ya llama `resolve_profile_for_turn`); sólo cubre-tests de que un contextual sin agente degrada a orquestador y no lanza el error de "L3 sin chat". |
| Schema | `cjhirashi-career-api/src/schemas/admin_sections.py` | `AdminSectionItem`: quitar `chat_agent_profile_id`, `description`, `description_is_default`; añadir `sidebar_has_chat: bool`, `sidebar_has_instructions: bool`. `AdminSectionView`: quitar `description` (de vista) si se decide — **NO**, se conserva (`description` de vista ≠ `description` de sección). `AdminSectionViewUpdate`: mantener `sidebar_title`/`sidebar_body`, quitar `description` de vista sólo si el arquitecto confirma que no se usa. `AdminSectionUpdateRequest`: quitar `description`. |
| Route | `cjhirashi-career-api/src/routes/admin_sections.py` | `update_admin_section`: quitar manejo de `description`/`clear_description`. Validar agente: existe **y** `is_l2` → si no, `400` Problem `Agent profile is not L2`. Pasar `views` tal cual (con `""`). |
| SPA · tipos | `cjhirashi-career-admin/src/types/adminSections.ts` | `AdminSection`: quitar `chat_agent_profile_id`, `description`, `description_is_default`; añadir `sidebar_has_chat`, `sidebar_has_instructions`. `AdminSectionUpdate`: quitar `description`. `matchAdminSection` sin cambio. |
| SPA · api | `cjhirashi-career-admin/src/api/adminSections.ts` | Sin cambio (pasa el payload tipado). |
| SPA · config | `cjhirashi-career-admin/src/config/agentProfiles.ts` | Nuevo `l2AgentSelectOptions()` (sólo `level === 2`). `resolveAgentProfileId`: para `contextual`, si hay match de sección sin agente → `AGENT_ORCHESTRATOR` (ya es el fallback final); quitar la rama que dependía de `chat_agent_profile_id`. |
| SPA · hook chat | `cjhirashi-career-admin/src/hooks/useBedrockChat.ts` | `effectiveAgentProfileId`: usar `match.section.agent_profile_id ?? AGENT_ORCHESTRATOR` en vez de `chat_agent_profile_id`. |
| SPA · página | `cjhirashi-career-admin/src/pages/AdminSectionsPage.tsx` | Quitar campo/estado `description` y su fila en `recordGroups`. Selector de agente: `l2AgentSelectOptions()` + "sin agente". Quitar la línea "Chat contextual: …" derivada. `sidebar_body` en modo vista → render Markdown (`<ReactMarkdown remarkPlugins={[remarkGfm]}>`). `save()` sin `description`. "Restablecer al código" sin `description`. |
| SPA · sidebar | `cjhirashi-career-admin/src/components/SidebarRight.tsx` | Instrucciones: `matched.view.sidebar_body` → render Markdown. Pestaña instrucciones oculta si `sidebar_body` efectivo vacío. Pestaña chat oculta si `matched.section.agent_profile_id` es `null`. Exponer al `Layout` (vía prop/callback o hook) si el panel debe existir. |
| SPA · layout | `cjhirashi-career-admin/src/components/Layout.tsx` | La condición de "hay sidebar derecho" pasa de `!hideContextualChat` a `!hideContextualChat && sectionHasSidebar(pathname, sections)` (sin chat **ni** instrucciones ⇒ ni panel ni botón `PanelRight`). `Navbar` `onRightPanelToggle` idem. |

## 2 · Fronteras de salida

- **Postgres compartida** — vía SQLAlchemy async (`AsyncSession`) y el modelo
  `AdminSectionOverride` ya existentes. La migración es DDL puro (`drop_column`). No hay
  repositorio dedicado: `section_catalog.py` consulta el modelo directo (patrón actual,
  se respeta). Sin N+1: `_overrides_map` sigue haciendo un único `select`.
- **Harness Bedrock** — `resolve_profile_for_turn` ya es el único punto de entrada del
  perfil de un turno contextual (lo llama `agent_loop.py`). No se añade cliente ni
  llamada AWS nueva.
- **SPA → API** — `PUT /admin/sections/{id}` (contrato existente, se recorta). Sin
  endpoint nuevo.

## 3 · Contratos y gates de CI

- `cjhirashi-career-api/openapi.yaml` **no existe** committeado → el bloque `rest-http`
  del gate corre los tests de los servicios Python tocados; **no** hay Spectral/oasdiff.
- Se versiona el ejemplo del contrato recortado en
  `contracts/put-admin-section.md` (request + 200 + los 3 Problem Details), como
  referencia humana y base de los tests de ruta. No es un gate ejecutable.
- `contracts/admin-section-item.schema.json` — el shape de `AdminSectionItem` tras el
  recorte (sin `chat_agent_profile_id`/`description`, con `sidebar_has_*`). Los tests
  de `section_catalog` afirman contra él.
- Gate `rest-http`: `cd cjhirashi-career-api && venv_test/bin/python -m pytest -q`.
- Gate front (implícito en revisión, no en `check.sh` fast): `cd cjhirashi-career-admin
  && npx vitest run && npm run type-check`.

## 4 · Estrategia de pruebas por capa

| Capa | Archivo de test | Cubre |
|---|---|---|
| Registro (unit, sin DB) | `cjhirashi-career-api/tests/unit/test_admin_sections.py` | RF-004 (todo `default_agent_profile_id` es L2 o `None`), re-mapeo exacto de las 11 secciones, `is_l2`, ausencia de `chat_agent_id`. Actualizar `test_linkedin_is_functional_*` (ya no hay `chat_agent_id`). |
| Catálogo (unit, `_serialize`/`_view_override` con filas mock) | `cjhirashi-career-api/tests/unit/test_admin_section_catalog.py` (nuevo) | RF-001, RF-005, RF-006, RF-007, RF-007b, RF-016, RF-018, `sidebar_has_chat`/`sidebar_has_instructions`, 3 estados del override. |
| Servicio `update_section` + ruta (integración con DB de test / `AsyncSession`) | `cjhirashi-career-api/tests/unit/test_admin_sections_update.py` (nuevo o extender) | RF-002, RF-003, RF-006, RF-007, RF-007b, RF-015, RF-017, RF-018, RF-021 (migración), Problem Details RFC 9457. |
| Bedrock resolución | `cjhirashi-career-api/tests/unit/bedrock/test_section_profile_resolution.py` (nuevo) | RF-012, RF-020, RF-022 (contextual con agente → ese L2; sin agente / sin match → orquestador; nunca 5xx ni el error de L3). |
| Migración | dentro de `test_admin_sections_update.py` o `tests/unit/test_migrations_smoke.py` si existe | RF-021 (upgrade→downgrade→upgrade deja el schema esperado; no toca `views`/`agent_profile_id`). |
| SPA página | `cjhirashi-career-admin/src/tests/pages/AdminSectionsPage.test.tsx` | RF-013 (sin campo Descripción), RF-014 (selector sólo L2), RF-008 (render Markdown en vista), edición de `sidebar_body`, "Restablecer al código". Actualizar el `sample` (quitar `chat_agent_profile_id`/`description`, añadir `sidebar_has_*`). |
| SPA sidebar | `cjhirashi-career-admin/src/tests/components/SidebarRight.test.tsx` | RF-008, RF-009 (sin pestaña instrucciones), RF-010 (sin pestaña chat), render Markdown, HTML embebido inerte (RF-019). Requiere envolver con `QueryClientProvider` + mock de `useAdminSections`. |
| SPA layout | `cjhirashi-career-admin/src/tests/components/Layout.test.tsx` (nuevo) | RF-011 (ruta sin chat ni instrucciones ⇒ ni panel ni botón). |

**TDD:** por cada RF, primero el test en rojo (con `@pytest.mark.requisito("RF-NNN")`
/ `describe('RF-NNN: …')`), luego el mínimo código, luego refactor.

## 5 · Secuenciación (test antes que código)

1. **Backend – registro y helpers.** `is_l2`, re-mapeo de defaults, quitar
   `chat_agent_id`/`_L3_CHAT_FALLBACK`. (RF-004, RF-001 parcial)
2. **Backend – catálogo.** `_view_override` 3 estados, `_serialize` recortado +
   `sidebar_has_*`. (RF-001, RF-005, RF-006, RF-007, RF-007b, RF-016)
3. **Backend – update + schema + ruta.** Validación L2, quitar `description`, Problem
   Details. (RF-002, RF-003, RF-015, RF-017, RF-018)
4. **Backend – migración.** `drop_column("description")`. (RF-021) + quitar `description`
   del modelo.
5. **Backend – resolución Bedrock.** `resolve_profile_for_turn` contextual desde el
   catálogo con fallback orquestador. (RF-012, RF-020, RF-022)
6. **Frontend – tipos + config + hook.** `AdminSection` recortado, `l2AgentSelectOptions`,
   `useBedrockChat`. (compilación)
7. **Frontend – página.** Quitar Descripción, selector L2, render Markdown. (RF-008,
   RF-013, RF-014)
8. **Frontend – sidebar + layout.** Pestañas condicionales, panel condicional, Markdown
   seguro. (RF-008, RF-009, RF-010, RF-011, RF-019)
9. **Docs** (§ Impacto).
10. Gate completo + `anchor_commit` al commit de cierre.

## 6 · Implementación por RF

### RF-001 / RF-004 — `agent_profile_id` y `default_agent_profile_id` siempre L2 o null
`admin_sections.py`: `default_agent_profile_id: Optional[str]` en `AdminSectionSpec`;
`_career` acepta `Optional[str]`. Re-mapeo (tabla §6 spec). `is_l2(pid)` usa
`get_profile(pid).level == 2`. Assert de módulo: `all(s.default_agent_profile_id is None
or is_l2(s.default_agent_profile_id) for s in _SECTIONS)`. `section_catalog._serialize`:
`agent_id` efectivo ya sólo puede ser L2 (override validado en `update_section`) o
`None`.

### RF-002 — PUT con agente no-L2 → 400 Problem
`routes/admin_sections.py`: tras `get_profile(agent_id)` (404-guard existente para
inexistente → 400 `Unknown agent profile`), añadir `if not is_l2(agent_id): raise
HTTPException(400, "Agent profile is not L2")`. `services.update_section` repite la
guarda (defensa en profundidad) y **no** hace `flush` si falla.

### RF-003 — PUT `agent_profile_id=""` limpia el override
Ya existe (`clear_agent`). Mantener: `row.agent_profile_id = None`; la respuesta
recae en `default_agent_profile_id` de código.

### RF-005 — sin `chat_agent_profile_id` en las respuestas
Quitar la clave de `_serialize`, del schema `AdminSectionItem`, del tipo TS y de los
mocks de test. `useBedrockChat` deja de leerla.

### RF-006 / RF-007 / RF-007b — 3 estados del override de `sidebar_body`
`_view_override(raw, view)`: 
- `data = raw.get(view.key)` → dict o `{}`.
- Para cada sub-campo (`sidebar_title`, `sidebar_body`): si `key in data` → valor tal
  cual (incluye `""`); si no → `getattr(view, key)` (código).
- `is_default = not ("sidebar_title" in data or "sidebar_body" in data)`.
`update_section`: construir `entry` incluyendo sub-campos **presentes** en el payload
(no sólo los truthy); un `""` se guarda como `""`. `row.views = cleaned or None`.

### RF-008 / RF-019 — render Markdown seguro
`SidebarRight.tsx` y `AdminSectionsPage.tsx` (modo vista): 
`<ReactMarkdown remarkPlugins={[remarkGfm]}>{sidebar_body}</ReactMarkdown>` dentro de un
contenedor con estilos `prose`-like ya existentes. **Sin** `rehype-raw` → el HTML
embebido se escapa (RF-019). `sidebar_title` sigue como `<h2>` texto plano.

### RF-009 / RF-010 / RF-011 — visibilidad del sidebar
`SidebarRight.tsx`: 
- `hasInstructions = !!matched?.view.sidebar_body?.trim()` (para rutas sin match de
  sección, cae al `getPageInstructions` de hoy → `hasInstructions = true`).
- `hasChat = matched ? matched.section.agent_profile_id != null : true`.
- Render de la píldora: sólo los botones cuyo `has*` sea `true`; `activeTab` inicial =
  el primero disponible.
`Layout.tsx`: `sectionHasSidebar = hasChat || hasInstructions`; si `false` (y no es
`/agent/chat`) no se monta `<SidebarRight>` ni el botón `PanelRight`, y
`onRightPanelToggle` es `undefined`. `Layout` obtiene `sections` de `useAdminSections()`
y reusa `matchAdminSection`.

### RF-012 / RF-020 / RF-022 — resolución del chat contextual
`section_catalog.resolve_profile_for_turn`:
```
if chat_surface == "general": return get_profile("agent_orchestrator")
if agent_profile_id: return get_profile(agent_profile_id)   # override explícito de la request
matched = match_section(route)
if matched:
    item = await get_section(db, matched[0].id)
    pid = item["agent_profile_id"]
    if pid: return get_profile(pid)
return get_profile("agent_orchestrator")                    # RF-022: sin agente / sin match
```
Se elimina la llamada a `resolve_agent_profile` desde aquí y el `import chat_agent_id`.
`agent_loop.py`: el guard `profile.level == 3` deja de dispararse por esta vía (los
únicos perfiles posibles son L2 o el orquestador L1). No se toca su código; se cubre
con test.

### RF-013 — ficha de sección sin Descripción
`AdminSectionsPage.tsx`: quitar `description`/`setDescription`, la fila
`{ label: 'Descripción', … }` de `recordGroups`, el `<textarea aria-label="Descripción
de la sección">`, `descriptionDirty`, y `description` de `save()` y del reset.

### RF-014 — selector sólo L2
`agentProfiles.ts`: `export function l2AgentSelectOptions()` = `AGENT_PROFILES.filter(p
=> p.level === 2).map(...)`. `AdminSectionsPage.tsx`: `agentOptions = [{ value:'',
label:'— Sin agente (sin chat contextual) —' }, ...l2AgentSelectOptions()]`.

### RF-015 — "Restablecer al código"
`update.mutate({ sectionId, payload: { agent_profile_id: '', views: {} } })` (sin
`description`). El backend borra la fila si queda vacía (RF-018).

### RF-016 — sección sin fila de override
`_view_override` con `raw = None` → todo desde código; `sidebar_body` no vacío para las
vistas que hoy tienen texto. Test con `_serialize(spec, None)` sobre las 54 secciones.

### RF-017 — clave de vista desconocida
`update_section`: `allowed = {v.key for v in spec.views}`; `if key not in allowed:
continue`. Ya existe; añadir test explícito.

### RF-018 — fila vacía se borra; `""` no cuenta como vacío
`_row_is_empty(row)`: `views = row.views or {}`; vacío ⟺ `row.agent_profile_id is None
and not views`. Un `views = {"main": {"sidebar_body": ""}}` → `views` truthy → **no**
vacío → fila se conserva.

### RF-019 — ver RF-008.

### RF-021 — migración mínima
`alembic/versions/<rev>_drop_admin_section_override_description.py`:
`upgrade` = `op.drop_column(_TABLE, "description")`; `downgrade` =
`op.add_column(_TABLE, sa.Column("description", sa.Text(), nullable=True))`.
`down_revision = "b2c3d4e5f6a7"`. Docstring con la nota de deploy (no corre en
`init_db`; `alembic upgrade head` tras rebuild). Test: aplicar upgrade sobre una DB de
test con una fila que tenga `views` y `agent_profile_id`, verificar que siguen intactos
y que `description` ya no está.

## 7 · § Impacto en documentación *(obligatorio, Art. 11)*

| Documento | Por qué queda obsoleto | Cómo se actualiza | Tarea |
|---|---|---|---|
| `docs/09-DECISIONS/024-sidebar-contextual-por-seccion.md` (**nuevo ADR**) | La decisión no está registrada | ADR: sección `agent_profile_id` = agente L2 del chat contextual; se retira `chat_agent_id()`/`_L3_CHAT_FALLBACK` y el override `description`; `sidebar_body` es Markdown; sidebar derecho condicional. Enlaza a spec 001. | `[doc]` T-D1 |
| `cjhirashi-career-api/src/services/bedrock/README.md` | Describe la escalera de resolución de perfil (`resolve_agent_profile`, ruta→perfil, L3 sin chat) que para el turno **contextual** deja de aplicar | Añadir que el turno contextual resuelve el perfil desde el catálogo de Secciones del Admin (`resolve_profile_for_turn` → `agent_profile_id` L2 de la sección), con fallback al orquestador; ya no hay tabla de respaldo L3→L2 | `[doc]` T-D2 |
| `docs/09-DECISIONS/021-admin-sections-synthetic-pk.md` | Menciona `description`/`sidebar_*` de `AdminViewSpec` y el catálogo de overrides con el modelo previo | Nota "Enmienda (feature 001, 2026-09-04)": el override pierde `description`; `sidebar_body` se renderiza como Markdown; el agente del override es el L2 del chat contextual (sin `chat_agent_profile_id` derivado) | `[doc]` T-D3 |
| `docs/BEDROCK-SYSTEM.md` | La fila "L2 · Especialista de área · Sidebar contextual" es correcta pero no dice de dónde sale ese L2 | Una línea: "el L2 del sidebar de cada sección se asigna en Settings → Secciones del Admin; sin asignación, no hay chat contextual en esa sección" | `[doc]` T-D3 (misma tarea) |
| `docs/06-RUNTIME-VIEW.md` | Revisado: el escenario 4 es de alto nivel y no describe la resolución de perfil | **Sin cambio** (declarado) | — |
| `docs/05-BUILDING-BLOCK-VIEW.md` | Revisado: no describe `admin_section_overrides` ni `section_catalog` a nivel campo | **Sin cambio** (declarado) | — |
| `docs/ADMIN_PANEL_SETUP.md`, `docs/12-GLOSSARY.md`, `cjhirashi-career-admin/README.md` | Revisados: sin referencias al override `description`, a `chat_agent_profile_id` ni a la visibilidad del sidebar | **Sin cambio** (declarado) | — |

## 8 · `covers` (fijado en el front-matter de `spec.md`)

Coincide con §1 + tests + rutas de doc:
```
cjhirashi-career-api/src/models/admin_section_override.py
cjhirashi-career-api/src/schemas/admin_sections.py
cjhirashi-career-api/src/services/admin_sections.py
cjhirashi-career-api/src/services/section_catalog.py
cjhirashi-career-api/src/services/bedrock/agent_profiles.py
cjhirashi-career-api/src/services/bedrock/agent_loop.py
cjhirashi-career-api/src/routes/admin_sections.py
cjhirashi-career-api/alembic/versions/*sidebar*section*.py    # el nuevo rev (drop description)
cjhirashi-career-api/tests/unit/test_admin_sections*.py
cjhirashi-career-api/tests/unit/test_admin_section_catalog.py
cjhirashi-career-api/tests/unit/bedrock/test_section_profile_resolution*.py
cjhirashi-career-admin/src/types/adminSections.ts
cjhirashi-career-admin/src/config/agentProfiles.ts
cjhirashi-career-admin/src/hooks/useBedrockChat.ts
cjhirashi-career-admin/src/pages/AdminSectionsPage.tsx
cjhirashi-career-admin/src/components/SidebarRight.tsx
cjhirashi-career-admin/src/components/Layout.tsx
cjhirashi-career-admin/src/tests/pages/AdminSectionsPage.test.tsx
cjhirashi-career-admin/src/tests/components/SidebarRight.test.tsx
cjhirashi-career-admin/src/tests/components/Layout.test.tsx
docs/09-DECISIONS/024-sidebar-contextual-por-seccion.md
docs/09-DECISIONS/021-admin-sections-synthetic-pk.md
docs/BEDROCK-SYSTEM.md
cjhirashi-career-api/src/services/bedrock/README.md
```

> Nota: el nombre real del archivo de migración se conocerá al crearlo; el glob
> `*sidebar*section*.py` del `covers` de `spec.md` se ajustará al slug definitivo en
> Fase 3.

## 9 · Riesgos / notas para Fase 4

- `AdminSectionView.description` (de **vista**, no de sección) sigue existiendo y se
  usa en `recordGroups` ("Descripción de la vista"). No confundir con el `description`
  de sección que se retira. El arquitecto/implementador confirma que
  `AdminSectionViewUpdate.description` (de vista) se mantiene.
- `SidebarRight` y `Layout` pasan a depender de `useAdminSections()` (React Query);
  sus tests necesitan `QueryClientProvider`. Verificar el helper `../utils` de vitest
  (ya envuelve QueryClient en otros tests de página).
- `useChatPageContext` / `chatSectionProfiles.ts` (perfil de **modelo**) quedan fuera
  de alcance; no tocar salvo que `type-check` obligue por el recorte de tipos.
- Dev DB: la columna `description` puede haberse creado por `create_all` sin registro
  Alembic (hazard conocido). El `downgrade` debe ser tolerante (`IF EXISTS` no está en
  la API de Alembic op; usar `op.drop_column` y aceptar que en dev se corre a mano).
