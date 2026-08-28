# ADR-022: División del L2 `agent_settings` — Configuración vs. Incidencias/Bitácora

## Estado

Aceptado — 2026-08-28

Reemplaza parcialmente a [ADR-017](./017-l2-agent-settings.md) (que creó `agent_settings` como L2 único de metaconfiguración). No cambia las reglas de jerarquía de [ADR-012](./012-bedrock-three-level-agents.md) (L1 delega a L2/L3; L2 delega solo a L3; delegación solo hacia abajo). Convive con [ADR-018](./018-error-reports-registry.md) (registro `error_reports`) y [ADR-021](./021-admin-sections-synthetic-pk.md) (PK `sec-N`).

## Contexto

[ADR-017](./017-l2-agent-settings.md) creó un solo L2 `agent_settings` ("Configuración", `agent-19`) dueño de tres pantallas del grupo **Settings** (Catálogo de Agentes, Secciones del Admin, Prompts Globales). [ADR-018](./018-error-reports-registry.md) le añadió una cuarta responsabilidad — **Reportes de Falla** (`/settings/error-reports`, tool `error_report_settings`) — por proximidad de UI, no por afinidad de dominio.

Esas cuatro áreas no son un dominio homogéneo:

- **Configuración del harness**: catálogo de agentes (prompt suffix, delegación, metodologías por perfil), secciones del Admin (agente dueño + descripción) y prompts globales (system prompt base + reglas). Es *metaconfiguración*: cambia cómo se comportan los agentes.
- **Incidencias y auditoría**: reportes de falla (`error_reports`, ADR-018) y la **Bitácora** de escrituras del agente (`/agent/audit-log`, tools `list_recent_changes` / `restore_deleted_record`). Es *observación de lo que pasó*: no cambia comportamiento, se consulta y se resuelve/restaura.

Además, la sección **Bitácora** (`sec-15`) tenía como `default_agent_profile_id` el L3 `agent_changelog`, que **no tiene chat** — su sidebar caía al orquestador (la excepción de "Costos" de ADR-012 que ADR-017 pretendía cerrar, reabierta para esa pantalla).

Un chat de "Configuración" y un chat de "Incidencias" quieren contextos, prompts y tono distintos: uno edita definiciones con cuidado transaccional; el otro tría errores y decide si un reporte ya está resuelto en el código. Mantenerlos en un mismo perfil obliga a un suffix largo con cuatro modos y diluye la responsabilidad única.

## Decisión

Partir `agent_settings` en **dos L2**:

| Perfil | Record | Label | Tools | Rutas (chat contextual) | Delega a |
|--------|--------|-------|-------|-------------------------|----------|
| `agent_configuration` *(nuevo)* | `agent-20` | Configuración | `agent_catalog_settings`, `admin_section_settings`, `bedrock_global_settings`, `search_knowledge_base` | `/settings/agents`, `/settings/sections`, `/settings/agent-prompts` | `agent_changelog` (L3) |
| `agent_settings` *(se reusa el slot)* | `agent-19` | Incidencias y Bitácora | `error_report_settings`, `search_knowledge_base` | `/settings/error-reports`, `/agent/audit-log` | `agent_changelog` (L3) |

Reglas:

- Se **conserva el system-name `agent_settings`** para el perfil de incidencias (solo cambian `label`, `allowed_tool_names` y `system_prompt_suffix`). Ese string es FK en `bedrock_conversation.agent_profile_id` (historial de chat de la sidebar), `bedrock_agent_profile_prompts.profile_id` (override de prompt), `operational_methodology.agent_profile_ids` (JSONB) y `admin_section_overrides.agent_profile_id`. Renombrarlo huérfana esos registros y exige una migración de datos que no aporta valor. El perfil **nuevo** toma el nombre libre `agent_configuration` y el record `agent-20`.
- `agent_configuration` **no** tiene `create_career_record`/`update_career_record`/etc. — sus tres tools de settings son su única superficie de escritura (igual que el `agent_settings` de ADR-017).
- `agent_settings` deja de exponer `agent_catalog_settings`, `admin_section_settings` y `bedrock_global_settings`. Solo `error_report_settings` (+ `search_knowledge_base` para sus metodologías) y delegación a `agent_changelog` para la Bitácora.
- Routing (`_ROUTE_TO_PROFILE` y su espejo TS): `/settings/agents`, `/settings/sections`, `/settings/agent-prompts` → `agent_configuration`; `/settings/error-reports` y `/agent/audit-log` → `agent_settings`.
- Secciones del Admin (`admin_sections.py`): `settings-agents` (`sec-16`), `settings-sections` (`sec-17`) y `settings-agent-prompts` (`sec-18`) pasan a `default_agent_profile_id=AGENT_CONFIGURATION`; `settings-error-reports` (`sec-19`) queda en `AGENT_SETTINGS`; **`agent-audit-log` (`sec-15`) pasa de `AGENT_CHANGELOG` (L3, sin chat) a `AGENT_SETTINGS` (L2)** — así esa pantalla gana chat contextual propio y `agent_settings` puede pedir la bitácora al L3.
- El orquestador (`_ORCHESTRATOR_SUFFIX`) separa los dos destinos: "catálogo de agentes / secciones del Admin / prompts globales → `agent_configuration`"; "reportes de falla / bitácora de cambios → `agent_settings`".
- La numeración de records de agente sigue **congelada y asignada a mano** (como los `sec-N` de ADR-021): `agent_configuration` es el siguiente entero libre (`agent-20`); si en el futuro se elimina un perfil, su número se retira (hueco, nunca se reutiliza).

### Por qué

- **Un agente, una responsabilidad** (principio rector de ADR-012): configurar el harness y auditar lo que hizo son oficios distintos. `agent_configuration` edita definiciones; `agent_settings` observa y tría.
- **Cerrar (de verdad) el hueco de routing de la Bitácora**: `sec-15` apuntaba a un L3 sin chat. Con un L2 dueño real, su sidebar deja de caer al orquestador.
- **Coste de migración cero**: reusar el slot `agent_settings` para incidencias evita tocar cuatro tablas con FKs de texto e historial de conversaciones. El nombre queda algo genérico para su nuevo alcance, pero es un tradeoff consciente y barato frente a una migración de datos.
- **Prompts más cortos y enfocados**: dos suffixes de un modo cada uno en vez de uno de cuatro modos; menos tokens de sistema por turno y menos ambigüedad para el modelo.
- **Simetría con el resto del catálogo**: `agent_methodologies` opera solo `operational-methodologies`; ahora `agent_configuration` opera solo configuración y `agent_settings` solo incidencias/bitácora.

## Consecuencias

### ✅ Positivas

- Cada pantalla de Settings y la Bitácora hablan con un L2 de responsabilidad única.
- El catálogo de agentes (`/settings/agents`) se sigue viendo a sí mismo y ahora muestra dos filas de metaconfiguración (`agent-19` incidencias, `agent-20` configuración) en vez de una sobrecargada.
- La Bitácora (`/agent/audit-log`) gana chat contextual con un L2 que delega la lectura al L3 `agent_changelog`.
- Menos tokens de system prompt en los turnos de Settings (suffix por modo único).

### ⚠️ Negativas

- El system-name `agent_settings` queda semánticamente desalineado con su nuevo alcance (incidencias/bitácora, no "settings"). Se documenta aquí y en `agent_profiles.py` para que nadie asuma que "settings" = configuración.
- Un perfil más que mantener en `agent_profiles.py` + su espejo `agentProfiles.ts` + tests en ambos lados.
- Overrides existentes de prompt para `agent_settings` (si los hubiera en `bedrock_agent_profile_prompts`) ahora aplican al perfil de incidencias, no al de configuración. Al momento de esta decisión no hay overrides guardados; si los hubiera, se revisan a mano tras el deploy.

### 🤷 Neutras

- Los L2 de dominio (`agent_methodologies`, etc.) siguen delegando la bitácora directamente al L3 `agent_changelog` (L2→L3 sigue siendo válido); no se les fuerza a pasar por `agent_settings`.
- No hay cambio de base de datos ni migración Alembic: el catálogo de agentes es código (`_PROFILES`), no una tabla sembrada.

## Alternativas Consideradas

### Alternativa 1: Dejar las cuatro áreas en `agent_settings`
- ✅ Pro: cero cambios.
- ❌ Contra: responsabilidad difusa, suffix de cuatro modos, y la Bitácora sigue sin L2 real.

### Alternativa 2: Renombrar `agent_settings` → `agent_incident_log` y crear `agent_settings` nuevo para configuración
- ✅ Pro: nombres perfectamente alineados con el alcance.
- ❌ Contra: migración de `bedrock_conversation`, `bedrock_agent_profile_prompts`, `operational_methodology.agent_profile_ids` y `admin_section_overrides`; riesgo de orfandad de historial de chat. Coste alto para un beneficio cosmético.

### Alternativa 3 (ELEGIDA): Reusar el slot `agent_settings` para incidencias/bitácora y crear `agent_configuration` (`agent-20`) para la configuración
- ✅ Pro: responsabilidad única en ambos, cierra el hueco de la Bitácora, coste de migración cero.
- ✅ Pro: la numeración `agent-N` congelada absorbe el alta sin secuencia de BD.

## Referencias

- Harness: `api/src/services/bedrock/agent_profiles.py` (`_PROFILES`, `_AGENT_RECORD_IDS`, `_ROUTE_TO_PROFILE`, `_ORCHESTRATOR_SUFFIX`), `tools.py` (docstrings de `_run_*_settings`)
- Secciones: `api/src/services/admin_sections.py` (`sec-15`..`sec-19`)
- Espejo UI: `admin/src/config/agentProfiles.ts` + `admin/src/tests/config/agentProfiles.test.ts`
- Tests: `api/tests/unit/bedrock/test_agent_profiles_router.py`
- [ADR-012](./012-bedrock-three-level-agents.md) · [ADR-017](./017-l2-agent-settings.md) (reemplazado parcialmente) · [ADR-018](./018-error-reports-registry.md) · [ADR-021](./021-admin-sections-synthetic-pk.md)

## Implicaciones

- [ ] `agent_profiles.py`: nueva constante `AGENT_CONFIGURATION`, entrada `agent-20` en `_AGENT_RECORD_IDS`, `_CONFIGURATION_TOOL_NAMES`, recorte de `_SETTINGS_TOOL_NAMES` a `{error_report_settings, search_knowledge_base}`, nuevo `_CONFIGURATION_SUFFIX` + recorte de `_SETTINGS_SUFFIX`, entrada en `_PROFILES` (L2, Haiku 4.5), remapeo de `_ROUTE_TO_PROFILE` (+ `/agent/audit-log`), actualización de `_ORCHESTRATOR_SUFFIX`.
- [ ] `admin_sections.py`: `default_agent_profile_id` de `sec-15` → `AGENT_SETTINGS`; `sec-16`/`sec-17`/`sec-18` → `AGENT_CONFIGURATION`; `sec-19` sin cambio.
- [ ] `tools.py`: docstrings "(L2 agent_settings)" → "(L2 agent_configuration)" en `_run_agent_catalog_settings`, `_run_admin_section_settings`, `_run_bedrock_global_settings`; `_run_error_report_settings` sin cambio.
- [ ] `agentProfiles.ts` + `agentProfiles.test.ts`: espejo de constante, lista `AGENT_PROFILES`, `ROUTE_TO_PROFILE`.
- [ ] `test_agent_profiles_router.py`: partir `test_settings_routes_resolve_to_agent_settings`, actualizar `test_agent_settings_owns_its_tools_only`, añadir cobertura de `agent_configuration`.
- [ ] `CLAUDE.md`: entrada en Procesos Aprendidos + bump de versión.
- [ ] `docs/09-DECISIONS/README.md`: fila 022 en el Registro de Decisiones.
- [ ] Foto de catálogo de `agent-20`: opcional, puede quedar sin foto inicial.

## Seguimiento

- La pantalla legada `agent-instructions` (`/agent/instructions`) sigue apuntando a `AGENT_ORCHESTRATOR` (ya señalado como fuera de alcance en ADR-017); su posible consolidación con el tab de prompt del catálogo es trabajo aparte.

---

**Creado por**: Arquitecto de Soluciones
**Aprobado por**: Carlos Jiménez Hirashi
**Fecha de creación**: 2026-08-28
**Estado de vigencia**: Pendiente implementación
