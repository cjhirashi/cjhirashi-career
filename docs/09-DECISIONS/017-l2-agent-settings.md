# ADR-017: L2 `agent_settings` — Configuración (catálogo de agentes, secciones del Admin, prompts globales)

## Estado

Aceptado — 2026-08-27

Extiende el catálogo de [ADR-012](./012-bedrock-three-level-agents.md) sin cambiar las reglas de jerarquía (L1 delega a L2/L3; L2 delega solo a L3; delegación solo hacia abajo).

## Contexto

El Admin tiene un grupo de navegación **Settings** con tres pantallas: Catálogo de Agentes (`/settings/agents`), Secciones del Admin (`/settings/sections`) y Prompts Globales (`/settings/agent-prompts`). Ninguna de las tres tenía un L2 dueño: `_ROUTE_TO_PROFILE` no las mapeaba, así que su chat contextual caía al orquestador (la excepción documentada en los "Costos" de ADR-012). Además, no existía ninguna tool de Bedrock para tocar esas tres áreas — solo se editaban a mano desde los formularios del Admin (`useBedrockAgentProfilePromptUpdate`, `useAdminSectionUpdate`, `useBedrockInstructionsUpdate`, `useBedrockGlobalRulesUpdate`), todas contra endpoints REST directos, sin pasar por el loop de tool-calling.

Estas tres áreas no son dominio de carrera (no son CV, vacantes, identidad, etc.): son **metaconfiguración del propio harness de agentes**. Mezclarlas con `create_career_record`/`update_career_record` habría sido incorrecto — no son filas de `career_repository`, sino overrides puntuales (`bedrock_agent_profile_prompt`, `bedrock_agent_delegation`, `admin_section_overrides`, `bedrock_settings`).

## Decisión

Nuevo L2 **`agent_settings`** ("Configuración", `agent-19`), dueño de las tres pantallas de Settings. Tres tools nuevas, cada una envolviendo el servicio que ya usa el Admin — no hay lógica duplicada:

| Tool | Envuelve | Acciones |
|------|----------|----------|
| `agent_catalog_settings` | `profile_catalog`, `profile_prompts`, `profile_delegation`, `methodology_scope` | `list`, `get`, `update_prompt`, `update_delegation`, `update_methodologies` |
| `admin_section_settings` | `section_catalog` | `list`, `get`, `update` (agente dueño + descripción) |
| `bedrock_global_settings` | `bedrock_service` (system prompt + global rules) | `get`, `update_system_prompt`, `update_global_rules` |

Reglas:

- `agent_settings` **no** tiene `create_career_record`/`update_career_record`/etc. — sus tres tools son su única superficie de escritura.
- No toca fotos de agente (`agent_visual_design` ya lo hacía vía `attach_image_to_record` con `resource_key=agent-profile`) ni el contenido de `operational-methodologies` (sigue siendo de `agent_methodologies`); solo asigna cuáles metodologías consulta cada perfil.
- Routing: `_ROUTE_TO_PROFILE` mapea `/settings/agents`, `/settings/sections` y `/settings/agent-prompts` a `agent_settings` (antes sin mapear). Las tres secciones registradas en `admin_sections.py` bajo `group="Settings"` (`settings-agents`, `settings-sections`, y la nueva `settings-agent-prompts`) tienen `default_agent_profile_id=AGENT_SETTINGS`.
- El orquestador delega aquí para "configuración del sistema" (catálogo de agentes, secciones, prompts globales).

### Por qué

- Un agente, una responsabilidad: `agent_settings` opera metaconfiguración del harness, no datos de carrera — igual que `agent_methodologies` opera solo `operational-methodologies`.
- Reusar los servicios existentes (`profile_prompts.set_profile_prompt_suffix`, `section_catalog.update_section`, `bedrock_service.set_system_prompt`, …) evita dos caminos de escritura divergentes entre el Admin y el chat.
- Cerrar el hueco de routing documentado como costo en ADR-012: ahora las tres pantallas de Settings tienen chat contextual propio en vez de caer al orquestador.

## Consecuencias

### Positivas

- Carlos puede pedirle a un chat de Settings "cambia el prompt de X agente" o "reasigna esta sección a Y agente" sin salir del chat ni editar el formulario a mano.
- El catálogo de agentes (`/settings/agents`) ahora se ve a sí mismo: `agent_settings` aparece como fila `agent-19` con sus propias tools.

### Costos

- Tres tools nuevas que mantener en `tools.py` (schema + ejecución) además del `AgentProfile` en `agent_profiles.py` y su espejo en `agentProfiles.ts`.
- `agent-instructions` (`/agent/instructions`, grupo "Agente IA", editor legado de "Instrucciones por Especialista") sigue apuntando a `AGENT_ORCHESTRATOR` — es una pantalla duplicada del tab de prompt del catálogo, fuera del alcance de este ADR; no se tocó para no mezclar una posible consolidación de UI con esta decisión.

### Alternativas rechazadas

- Dejar estas tres tools dentro de `agent_methodologies` (único L2 "meta" existente): mezclaría contenido de metodologías con configuración de agentes/secciones/prompts — dominios distintos.
- Exponerlas como `resource_key` genéricos del CRUD de carrera (`create_career_record`/`update_career_record`): estas tablas no son `career_repository`; forzarlas ahí habría requerido registrar recursos falsos solo para reusar el tool genérico.

## Referencias

- Harness: `api/src/services/bedrock/agent_profiles.py`, `tools.py`
- Servicios envueltos: `api/src/services/bedrock/profile_catalog.py`, `profile_prompts.py`, `profile_delegation.py`, `api/src/services/methodology_scope.py`, `api/src/services/section_catalog.py`, `api/src/services/bedrock_service.py`
- Secciones: `api/src/services/admin_sections.py`
- Espejo UI: `admin/src/config/agentProfiles.ts`
- [ADR-012](./012-bedrock-three-level-agents.md) · [ADR-013](./013-l3-web-and-github-agents.md)

---

**Creado por**: Arquitecto de Soluciones
**Fecha de creación**: 2026-08-27
**Estado de vigencia**: Vigente
