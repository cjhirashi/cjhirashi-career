# Estado del trabajo — ADR-023 (Jerarquía de Secciones + Vistas)

> Reemplaza al `ESTADO.md` de scratchpad de la sesión anterior (quedó desactualizado: describía
> el backend como "modelos parciales, sin migración/seeder/endpoints/tests". Verificado en esta
> sesión (2026-08-28) contra el working tree real: el backend está bastante más avanzado.

## Documentos de referencia (este mismo directorio)
- `023-spec-modelo.md` — modelo/racional original del arquitecto.
- `023-contrato-implementacion.md` — contrato de implementación (manda sobre la spec); su §8
  define las fases y el orden de archivos; su sección final "RULINGS DEL ARQUITECTO" resuelve
  los 7 puntos abiertos del contrato.
- `023-admin-sections-hierarchy-views.md` — el ADR en sí (ya redactado por
  `documentacion-especialista`).

## Verificado en working tree (git status, sin commitear, rama `develop`)

### Backend — Fases 1 a 5 del contrato (§8): **completas y verificadas**
- 5 modelos nuevos (`admin_section_group.py`, `admin_section_l1/l2/l3.py`, `admin_view.py`) +
  registrados en `models/__init__.py`.
- Migración `alembic/versions/c4d5e6f7a8b9_admin_sections_hierarchy_views.py`
  (`revision=c4d5e6f7a8b9`, `down_revision=b2c3d4e5f6a7` — coincide con el contrato).
- Seeder `services/admin_sections_seed.py::sync_structure()` (nuevo).
- `services/section_catalog.py`, `routes/admin_sections.py`, `schemas/admin_sections.py`,
  `services/admin_sections.py`, `database.py` (llamada a `sync_structure` en `init_db`) —
  todos modificados.
- `models/admin_section_override.py` y `tests/unit/test_admin_sections_rekey_surfaces.py`
  **borrados** (correcto, ADR-023 los retira).
- Bedrock: tool `admin_view_settings` confirmada en `services/bedrock/tools.py` (reemplaza a
  `admin_section_settings`, dispatch y `_resource_key_for_changelog` incluidos); suffix real es
  `_CONFIGURATION_SUFFIX` en `services/bedrock/agent_profiles.py` (el contrato dudaba entre ese
  nombre y `_SETTINGS_SUFFIX` — **confirmado `_CONFIGURATION_SUFFIX`**); `profile_catalog.py`
  actualizado.
- Tests nuevos: `test_admin_sections_hierarchy.py`, `test_admin_sections_seed.py`,
  `bedrock/test_admin_view_settings.py`, `tests/unit/conftest.py` (fixtures `hier_engine` /
  `hier_db` con SQLite in-memory + `PRAGMA foreign_keys=ON`, tal como pide el contrato §7).
- **Ejecutado en esta sesión**: los 94 tests del set relacionado con ADR-023 (los de arriba +
  `test_admin_sections.py`, `test_admin_sections_migration_map.py`,
  `bedrock/test_profile_catalog.py`, `bedrock/test_agent_profiles_router.py`) **pasan en su
  totalidad** (`python3 -m pytest tests/unit/test_admin_sections*.py
  tests/unit/bedrock/test_admin_view_settings.py tests/unit/bedrock/test_profile_catalog.py
  tests/unit/bedrock/test_agent_profiles_router.py -q` → 94 passed).

### Hallazgo — regresión PREEXISTENTE, no introducida por ADR-023
Al correr la suite completa (`pytest -q`) aparecen ~55 errores + 11 failed en
`test_database.py`, `test_middleware.py`, `test_repositories.py`,
`integration/test_auth_integration.py`, `integration/test_auth_routes.py`. Causa raíz:
`tests/conftest.py::test_db` hace `Base.metadata.create_all` sobre **todos** los modelos, y
varios modelos preexistentes (`achievement.py`, `project.py`, `error_report.py`,
`competencies.py`, `bedrock_agent_delegation.py`, etc.) usan `postgresql.JSONB` **sin**
`with_variant` de fallback a SQLite → `UnsupportedCompilationError` en el `create_all` contra
`sqlite+aiosqlite`. **Confirmado con `git stash -u`**: este fallo ya existe en `develop` HEAD
(commit `8227848`), sin ninguno de los cambios de este lote. **No es responsabilidad de ADR-023
arreglarlo** (los 5 modelos nuevos SÍ usan `JSON().with_variant(postgresql.JSONB, "postgresql")`
correctamente, como pide el contrato §0.3) — pero conviene abrir un issue/lote aparte, porque
bloquea toda la suite "clásica" de auth/db/middleware en local (probablemente en CI corre contra
Postgres real y por eso no se ha notado).
Nota aparte, sin relación: `tests/unit/test_models.py` y `test_models_extended.py` fallan al
importar `Evidence` desde `models` — modelo que ya no existe (preexistente, nada que ver con este
lote).

### Documentación — prácticamente completa
- ADR-023 redactado (`023-admin-sections-hierarchy-views.md`).
- Notas añadidas en ADR-012, ADR-017, ADR-020, ADR-021 y en `docs/09-DECISIONS/README.md`.
- Bullet de `CLAUDE.md` (2026-08-28, jerarquía de secciones) **corregido en esta sesión**: tenía
  3 marcas `⚠️ verificar` (nombre del seeder, nombre de la tool/suffix, nombre de la migración) —
  las tres se verificaron contra el código real y coinciden con el contrato; marcas retiradas y
  la nota actualizada para reflejar que el backend está cerrado y falta el frontend.

### Frontend (`admin-panel-specialist`) — **NO iniciado**
`git status` solo muestra un cambio de 2 líneas en `AgentCatalogPage.tsx`
(`delegateOptions`/`allowed_delegation_ids`) que es una corrección **no relacionada** con ADR-023
(no toca "vistas que gestiona"). Falta todo lo de la spec §Admin / contrato §8 "Después":
- `Sidebar.tsx`: reconstruir el árbol de 4 niveles (grupo→L1→L2→L3) desde `GET /admin/nav-tree`.
- Pantalla "Secciones del Admin": mostrar árbol + edición de orden/anidamiento (mismo nivel).
- Pantalla/panel "Vistas": tabla de `admin_views`, edición de `responsible_agent_profile_id`
  (selector restringido a L2) + `instructions`.
- `AgentCatalogPage.tsx`: "secciones que gestiona" → "vistas que gestiona" (derivado, solo
  lectura) — usa `profile_catalog.py::_attach_views` ya implementado en backend.
- Hooks: `useAdminSections` → `useNavTree` + `useAdminViews`.
- `config/agentProfiles.ts`: exponer qué perfiles son L2 (para el selector de responsable).

### Sin verificar en esta sesión (requiere Postgres real, no disponible aquí)
- `alembic upgrade head` contra una base con datos reales de `admin_section_overrides` (Fase 6
  del contrato, "verificación"). El backend solo se probó contra SQLite in-memory vía los
  fixtures nuevos.
- Cobertura global ≥80% del proyecto (el run parcial da 53-65% porque mide solo los archivos
  tocados; hay que correr `pytest --cov` completo una vez resuelto el problema de JSONB/SQLite
  de arriba, o medir cobertura solo sobre los archivos de este lote).

## Próximos pasos (orden del contrato §8, ajustado al estado real)
1. **`admin-panel-specialist`** — implementar el frontend descrito arriba. Es el bloque de
   trabajo más grande que falta.
2. **`code-quality-guardian`** — review de todo el diff (backend ya estable + frontend nuevo).
3. **`qa-engineer`** — validar cobertura ≥80% del lote (no de todo el repo, dado el problema
   preexistente de JSONB/SQLite) y decidir si el hallazgo de JSONB/SQLite amerita su propio ticket.
4. **`git-especialista`** — commit(s) en `develop` (revisar si conviene separar el commit del
   hallazgo/fix de JSONB del commit de ADR-023, si se decide tocarlo).
5. Anotar en ADR-023 §Seguimiento el hallazgo de JSONB/SQLite si se decide no arreglarlo en este
   lote.

## Pendientes ya anotados en ADR-023 §Seguimiento (sin cambio)
- Cambio de nivel de sección desde el Admin (drag L1↔L2↔L3) — follow-up inmediato.
- Catálogo de componentes UI ligado a tablas para construir vistas desde el Admin.
- Migrar `bedrock_agent_delegation.target_ids` a `JSON` portable.
- Retirar `resolve_agent_profile` + mapas `_ROUTE_TO_PROFILE`/`_RESOURCE_TO_DOMAIN`/`_DOMAIN_TO_PROFILE`.
