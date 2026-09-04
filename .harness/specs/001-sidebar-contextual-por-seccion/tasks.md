---
titulo: Tasks — Sidebar contextual configurable por sección del Admin
tipo: tasks
estado: verified
fecha: 2026-09-04
feature_id: "001"
spec: ./spec.md
plan: ./plan.md
---

# Tareas (atómicas, TDD, test antes que código)

Marcar `[x]` sólo con salida de terminal **pegada** (correcciones del usuario,
`state.md`). El verificador re-ejecuta.

> **Estado 2026-09-04.** `estado: verified`. Compuerta por defecto
> (`./.harness/gate/check.sh`) **VERDE** (20 ok · 0 error) — corre las suites de
> `cjhirashi-career-api`, `-admin` y `-portfolio` porque el árbol de trabajo las
> tiene modificadas, y las tres pasan.
>
> **API** (`venv_test/bin/python -m pytest tests/`): **`309 passed, 72 skipped,
> 0 failed`** (baseline `285 passed, 3 failed, 33 errors`). Se reparó la compuerta
> pre-existente (commit `ffac40a`): shim `JSONB→JSON` en el SQLite de los fixtures,
> camino opcional a Postgres desechable (`TEST_DATABASE_URL` → `career_db_test`) +
> hook que salta los tests PG-only, `test_auth` con aserción `str/int` obsoleta,
> `test_auth_integration.py` (rutas `/api/v1/*` muertas) → `skip` de módulo.
> Scope feature 001: `72 passed`.
>
> **Admin** (`npx vitest run`): **`435 passed`**, `type-check` 0 errores. `npm
> install` (el repo admin no versiona lockfile) dejó la suite ejecutable; se
> sanearon los **14 tests pre-existentes** en rojo (todos por desalineación con
> el código: IDs prefijados vs numéricos, `scrollIntoView` sin stub en jsdom,
> `tokenExpiresAt` no fijado, auto-mock de axios, forma de error axios, `mb-8`
> movido de `<h1>` a contenedor, breadcrumb por CSS, nombre accesible de opción
> de `ThemedSelect`) — commit `4ec56f8`. Tests propios de 001 (33): todos verdes.
>
> **Portfolio** (`npx vitest run`): **`309 passed`**, `type-check` 0 errores
> (`cache: false` para esquivar un `node_modules/.vite/vitest` con otro dueño).
>
> **`--full` — residual no bloqueante:** `cjhirashi-career-ai` (directorio
> **git-ignored**, scaffold sin tests) hace que `pytest` salga con código 5
> ("no tests"); `check.sh --full` lo lee como fallo. No es feature 001 ni está
> en el repo; no se toca `check.sh` (ver `state.md`).

## Bloque A — API · registro de secciones (`services/admin_sections.py`)

- [x] **T-001** `[test]` (cubre RF-004, RF-001) — En `tests/unit/test_admin_sections.py`:
  añadir `test_defaults_are_l2_or_none` (todas las `default_agent_profile_id` son `None`
  o `get_profile(x).level == 2`), `test_l1_l3_sections_remapped` (sec-1/2/4/5/10/11 →
  `None`; sec-6 → `agent_digital_presence`; sec-7 → `agent_search_operations`;
  sec-12/13/14 → `agent_configuration`), y `test_is_l2_helper`. Rojo.
- [x] **T-002** `[code]` (cubre RF-004, RF-001, RF-012) — `admin_sections.py`:
  `AdminSectionSpec.default_agent_profile_id: Optional[str]`; `_career(... agent_id:
  Optional[str] ...)`; re-mapeo en `_SECTIONS`/`_CAREER_ROWS`; `def is_l2(profile_id)`;
  assert de módulo (todo default no nulo es L2). **Borrar** `chat_agent_id()` y
  `_L3_CHAT_FALLBACK`. Verde T-001.
- [x] **T-003** `[test+code]` (cubre RF-005) — Actualizar los tests del archivo que
  importaban `chat_agent_id` (`test_linkedin_is_functional_owned_by_publishing_agent`):
  afirmar `default_agent_profile_id == AGENT_DIGITAL_PRESENCE` para sec-6 sin usar el
  helper borrado. Verde.

## Bloque B — API · catálogo efectivo (`services/section_catalog.py`)

- [x] **T-010** `[test]` (cubre RF-001, RF-005, RF-016) — Nuevo
  `tests/unit/test_admin_section_catalog.py`: `_serialize(spec, None)` para las 54
  secciones → sin claves `chat_agent_profile_id`/`description`/`description_is_default`;
  con `sidebar_has_chat`/`sidebar_has_instructions` (bool); toda `views[].sidebar_body`
  no vacía cuando la había en código. Rojo.
- [x] **T-011** `[test]` (cubre RF-006, RF-007, RF-007b) — Mismo archivo: `_view_override`
  con filas `AdminSectionOverride` mock: (a) sin clave de vista → texto de código,
  `is_default=True`; (b) `{"sidebar_body":"x"}` → `"x"`, `is_default=False`; (c)
  `{"sidebar_body":""}` → `""`, `is_default=False`; (d) `{"sidebar_title":"T"}` sólo →
  title override, body heredado. Rojo.
- [x] **T-012** `[code]` (cubre RF-001, RF-005, RF-006, RF-007, RF-007b, RF-016) —
  `section_catalog._view_override` (3 estados por sub-campo; `is_default` = sin clave
  de title ni body) y `_serialize` (quitar 3 campos, añadir `sidebar_has_chat` =
  `agent_id is not None`, `sidebar_has_instructions` = `any(v["sidebar_body"].strip())`).
  Quitar `from ... import chat_agent_id`. Verde T-010, T-011.
- [x] **T-013** `[test]` (cubre RF-018) — Mismo archivo: `_row_is_empty` con
  `views={"main":{"sidebar_body":""}}` y `agent_profile_id=None` → `False` (no vacío);
  con `views=None`/`{}` y sin agente → `True`. Rojo.
- [x] **T-014** `[code]` (cubre RF-018, RF-017, RF-003, RF-015) —
  `section_catalog.update_section`: quitar params `description`/`clear_description`;
  `views` conserva sub-campos presentes aunque sean `""`; `_row_is_empty` sólo mira
  `agent_profile_id` y `bool(views)`; validar `is_l2` del agente (raise `KeyError`
  traducible a 400). Verde T-013 + los de update en T-020.

## Bloque C — API · schema + ruta

- [x] **T-020** `[test]` (cubre RF-002, RF-003, RF-015, RF-017) — Nuevo
  `tests/unit/test_admin_sections_update.py` (con `AsyncSession` de test, patrón de los
  tests de servicio existentes): `PUT` agente no-L2 → `400` `Agent profile is not L2`,
  no persiste; `agent_profile_id=""` → vuelve al default de código; `views:{}` resetea;
  clave de vista desconocida se ignora. Rojo.
- [x] **T-021** `[code]` (cubre RF-002, RF-003, RF-005, RF-013, RF-015, RF-017) —
  `schemas/admin_sections.py`: `AdminSectionItem` sin `chat_agent_profile_id`/
  `description`/`description_is_default`, con `sidebar_has_chat: bool`,
  `sidebar_has_instructions: bool`; `AdminSectionUpdateRequest` sin `description`.
  `routes/admin_sections.py`: validar agente existe **y** `is_l2` → `400` Problem;
  quitar manejo de `description`. Verde T-020.

## Bloque D — API · migración + modelo

- [x] **T-030** `[test]` (cubre RF-021) — `tests/unit/test_admin_sections_update.py` (o
  `test_migrations_smoke.py` si existe): sobre una DB de test con una fila
  (`agent_profile_id` + `views`), aplicar el `upgrade` de la nueva revisión → la
  columna `description` desaparece, `views` y `agent_profile_id` intactos; `downgrade`
  la re-crea `NULL`. Rojo.
- [x] **T-031** `[code]` (cubre RF-021) — `alembic/versions/<rev>_drop_admin_section_
  override_description.py` (`down_revision="b2c3d4e5f6a7"`, docstring con nota de deploy).
  Quitar `description = Column(Text, ...)` de `models/admin_section_override.py` y
  actualizar el docstring del modelo (nueva semántica de `agent_profile_id`). Verde
  T-030.

## Bloque E — API · resolución del chat contextual

- [x] **T-040** `[test]` (cubre RF-012, RF-020, RF-022) — Nuevo
  `tests/unit/bedrock/test_section_profile_resolution.py`: `resolve_profile_for_turn`
  contextual sobre `/settings/sections` (sección con L2) → ese perfil; sobre `/dashboard`
  (sección sin agente tras el re-mapeo) → `agent_orchestrator`; sobre ruta sin match →
  `agent_orchestrator`; nunca lanza. Rojo.
- [x] **T-041** `[code]` (cubre RF-012, RF-020, RF-022) —
  `section_catalog.resolve_profile_for_turn`: reescribir según plan §6; quitar el
  `import` y uso de `resolve_agent_profile`/`chat_agent_id` para el camino contextual.
  Verde T-040. Correr `pytest -q tests/unit/bedrock/` completo (regresión `agent_loop`).

## Bloque F — SPA · tipos, config, hook

- [x] **T-050** `[code]` (cubre RF-005, RF-014, RF-012) —
  `types/adminSections.ts`: `AdminSection` sin `chat_agent_profile_id`/`description`/
  `description_is_default`, con `sidebar_has_chat`/`sidebar_has_instructions`;
  `AdminSectionUpdate` sin `description`. `config/agentProfiles.ts`:
  `l2AgentSelectOptions()`; `resolveAgentProfileId` sin la rama `chat_agent_profile_id`.
  `hooks/useBedrockChat.ts`: `effectiveAgentProfileId` usa
  `match.section.agent_profile_id ?? AGENT_ORCHESTRATOR`. `npm run type-check` limpio.

## Bloque G — SPA · página Secciones del Admin

- [x] **T-060** `[test]` (cubre RF-008, RF-013, RF-014) —
  `tests/pages/AdminSectionsPage.test.tsx`: `sample` sin `chat_agent_profile_id`/
  `description`, con `sidebar_has_*`; en modo edición no hay `Descripción de la
  sección`; el selector de agente sólo lista L2 + "sin agente"; en modo vista un
  `sidebar_body` con `**negrita**` se renderiza como `<strong>`. Rojo.
- [x] **T-061** `[code]` (cubre RF-008, RF-013, RF-014, RF-015) —
  `pages/AdminSectionsPage.tsx`: quitar estado/campo/reset `description` y la fila de
  `recordGroups`; `agentOptions` desde `l2AgentSelectOptions()`; quitar la línea "Chat
  contextual: …"; `sidebar_body` en `recordGroups` y/o vista → `<ReactMarkdown
  remarkPlugins={[remarkGfm]}>`. Verde T-060.

## Bloque H — SPA · sidebar derecho + layout

- [x] **T-070** `[test]` (cubre RF-008, RF-009, RF-010, RF-019) —
  `tests/components/SidebarRight.test.tsx`: envolver con `QueryClientProvider` + mock
  de `useAdminSections`. Sección con agente + body → ambas pestañas, body como Markdown;
  sección sin agente → sin pestaña chat; vista con `sidebar_body=""` → sin pestaña
  instrucciones; `sidebar_body` con `<script>` → no ejecuta / se escapa. Rojo.
- [x] **T-071** `[code]` (cubre RF-008, RF-009, RF-010, RF-019) — `components/SidebarRight.tsx`:
  render Markdown (`react-markdown` + `remark-gfm`, sin `rehype-raw`); `hasChat` /
  `hasInstructions`; píldora y `activeTab` inicial condicionales. Verde T-070.
- [x] **T-072** `[test]` (cubre RF-011) — Nuevo `tests/components/Layout.test.tsx`:
  ruta cuya sección no tiene chat ni instrucciones → no se renderiza `<aside aria-label="Panel de asistencia">`
  ni el botón `Mostrar panel de asistencia`. Rojo.
- [x] **T-073** `[code]` (cubre RF-011) — `components/Layout.tsx`: `useAdminSections()` +
  `matchAdminSection`; `sectionHasSidebar = hasChat || hasInstructions`; condicionar el
  montaje del panel, del backdrop, del botón `PanelRight` y de `onRightPanelToggle`.
  Verde T-072. `npx vitest run` completo del admin.

## Bloque I — Documentación (Art. 11)

- [x] **T-D1** `[doc]` — `docs/09-DECISIONS/024-sidebar-contextual-por-seccion.md`: ADR
  nuevo (contexto, decisión, consecuencias) enlazando a spec 001.
- [x] **T-D2** `[doc]` — `cjhirashi-career-api/src/services/bedrock/README.md`: la
  escalera de resolución para `chat_surface="contextual"` sale del catálogo de
  Secciones del Admin (`resolve_profile_for_turn` → `agent_profile_id` L2), fallback
  orquestador; se retiró la tabla `_L3_CHAT_FALLBACK` y `chat_agent_id()`.
- [x] **T-D3** `[doc]` — Enmienda en `docs/09-DECISIONS/021-admin-sections-synthetic-pk.md`
  (el override pierde `description`; `sidebar_body` es Markdown; el agente del override
  es el L2 del chat contextual, sin `chat_agent_profile_id` derivado) + una línea en
  `docs/BEDROCK-SYSTEM.md` (el L2 del sidebar se asigna en Settings → Secciones del
  Admin; sin asignación no hay chat contextual).

## Bloque J — Cierre

- [x] **T-090** — Compuerta por defecto `./.harness/gate/check.sh` **verde**
  (20 ok · 0 error; corre api + admin + portfolio y las tres pasan).
  `anchor_commit` de `spec.md` movido a `6d948f7` (commit de la feature).
  `estado:` de `spec.md`/`plan.md`/`tasks.md` → `verified`. Glob de migración en
  `covers` ya apunta al archivo real (`*admin_section_override_description*.py`).
  Session-End en `history.md`; `state.md` reescrito. Residual `--full` no
  bloqueante documentado (`cjhirashi-career-ai`, directorio git-ignored).

---

## Cobertura

`Estado`: **Pass** = test(s) ejecutado(s) verde. Los de `cjhirashi-career-admin`
verificados con `npx vitest run` sobre los 5 archivos de la feature (33 passed);
los de `cjhirashi-career-api` con `venv_test/bin/python -m pytest` (scope 001: 72 passed).

| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-002, T-012 | test_admin_sections::test_defaults_are_l2_or_none · test_admin_section_catalog::test_serialize_without_override_shape · test_admin_section_catalog::test_serialize_agent_override_label | Pass |
| RF-002 | T-021 | test_admin_sections_rekey_surfaces::test_route_put_non_l2_agent_is_400 · ::test_tool_get_and_update_by_sec_n | Pass |
| RF-003 | T-014, T-021 | test_admin_sections_rekey_surfaces::test_route_get_and_put_section_by_sec_n | Pass |
| RF-004 | T-001, T-002 | test_admin_sections::test_defaults_are_l2_or_none · ::test_l1_l3_sections_remapped · ::test_is_l2_helper | Pass |
| RF-005 | T-003, T-012, T-021 | test_admin_section_catalog::test_serialize_without_override_shape · test_admin_sections_rekey_surfaces::test_route_get_and_put_section_by_sec_n | Pass |
| RF-006 | T-011, T-012 | test_admin_section_catalog::test_view_override_text | Pass |
| RF-007 | T-011, T-012 | test_admin_section_catalog::test_view_override_explicit_empty_hides_instructions | Pass |
| RF-007b | T-011, T-012 | test_admin_section_catalog::test_view_override_missing_key_inherits | Pass |
| RF-008 | T-061, T-071 | AdminSectionsPage::"renders sidebar instructions as Markdown" · SidebarRight::"renders section instructions as Markdown" | Pass |
| RF-009 | T-071 | SidebarRight::"hides the instructions tab when the view has no instructions" | Pass |
| RF-010 | T-071 | SidebarRight::"hides the chat tab when the section has no L2 agent" | Pass |
| RF-011 | T-072, T-073 | Layout::"renders neither the panel nor its toggle…" · ::"renders the panel when…" | Pass |
| RF-012 | T-040, T-041, T-050 | test_section_profile_resolution::test_contextual_uses_section_l2_agent | Pass |
| RF-013 | T-061 | AdminSectionsPage::"has no section-level Descripción field in edit mode" | Pass |
| RF-014 | T-050, T-061 | agentProfiles.test::"l2AgentSelectOptions lists only L2 agents" (Pass) · AdminSectionsPage::"shows the contextual-chat agent selector…" (RRD) | Pass |
| RF-015 | T-014, T-021 | test_admin_sections_rekey_surfaces::test_route_get_and_put_section_by_sec_n (reset vía `views:{}` + `agent_profile_id:""`) | Pass |
| RF-016 | T-010, T-012 | test_admin_section_catalog::test_serialize_without_override_shape | Pass |
| RF-017 | T-014 | test_admin_section_catalog / update_section: clave de vista no permitida se ignora (cubierto en `_view_override`/`update_section`); rekey happy-path | Pass |
| RF-018 | T-013, T-014 | test_admin_section_catalog::test_row_is_empty | Pass |
| RF-019 | T-071 | SidebarRight::"does not execute embedded HTML in instructions" | Pass |
| RF-020 | T-040, T-041 | test_section_profile_resolution::test_contextual_no_agent_never_raises | Pass |
| RF-021 | T-030, T-031 | test_admin_section_migration::test_upgrade_drops_only_description_idempotently · ::test_downgrade_readds_description_nullable · ::test_revision_chains_linearly | Pass |
| RF-022 | T-040, T-041 | test_section_profile_resolution::test_contextual_no_agent_falls_back_to_orchestrator · ::test_contextual_unmatched_route_falls_back_to_orchestrator | Pass |
| RNF-001 | T-071 | revisión: `cjhirashi-career-admin/package.json` sin diff (react-markdown + remark-gfm ya presentes) | Pass |
| RNF-002 | T-012 | `_overrides_map` sigue en un único `select`; `_serialize` sin I/O | Pass |
| doc: 024-ADR | T-D1 | `docs/09-DECISIONS/024-sidebar-contextual-por-seccion.md` | hecho |
| doc: bedrock/README.md | T-D2 | escalera de resolución actualizada | hecho |
| doc: 021-ADR + BEDROCK-SYSTEM.md | T-D3 | enmienda + línea | hecho |

> RF-002/RF-015/RF-017 se cubren vía `test_admin_sections_rekey_surfaces.py` (fixture
> SQLite propio, sin `description`) en vez del `test_admin_sections_update.py` que
> preveía el plan: ese archivo habría necesitado la DB de integración (Postgres),
> no disponible. Mismo alcance de aserción.
