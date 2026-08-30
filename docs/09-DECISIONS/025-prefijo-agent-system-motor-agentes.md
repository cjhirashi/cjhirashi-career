# ADR-025: Prefijo `agent_system_` para las tablas del motor de agentes

## Estado

Aceptado — 2026-08-30

Reemplaza el esquema de nombrado de [ADR-024](./024-desacoplar-nombrado-motor-agentes-de-bedrock.md) (que queda `Deprecado` en cuanto a la tabla de mapeo, no en cuanto a su razonamiento de fondo: Bedrock sigue siendo únicamente el proveedor de inferencia, nunca el nombre del motor de agentes — eso no cambia). No afecta a ADR-008, ADR-012, ADR-017 ni ADR-022.

## Contexto

ADR-024 decidió renombrar `bedrock_*` → `agent_*`, pero tuvo que introducir una excepción: `bedrock_settings` no podía llamarse `agent_settings` porque ese `system_name` ya existe como identidad de un perfil de agente real (`AGENT_SETTINGS = "agent_settings"`, L2 "Incidencias y Bitácora", ADR-022). La solución fue nombrar esa tabla `engine_settings`, rompiendo la uniformidad del prefijo para un solo caso.

Carlos señaló que el prefijo correcto para todo el grupo debería expresar que estas tablas pertenecen al **sistema de agentes** como unidad (no solo "un agente" genérico): `agent_system_`. Revisando esa propuesta contra el catálogo de perfiles (`agent_profiles.py`), un prefijo compuesto de tres partes (`agent_system_<algo>`) no colisiona con ningún `system_name` existente — todos los perfiles usan el patrón de dos partes `agent_<rol>` (`agent_settings`, `agent_configuration`, `agent_task_manager`, `agent_changelog`, etc.). Esto **elimina la necesidad de la excepción `engine_settings`**: con el prefijo de tres partes, incluso la tabla de configuración global puede llamarse `agent_system_settings` sin ambigüedad frente al perfil `agent_settings`.

## Decisión

Usar `agent_system_` / `AgentSystem` como prefijo uniforme para las 10 tablas/clases del motor de agentes, sin excepciones:

| Tabla ADR-024 | Tabla nueva (ADR-025) | Clase ADR-024 | Clase nueva (ADR-025) |
|---|---|---|---|
| `engine_settings` | **`agent_system_settings`** | `EngineSettings` | `AgentSystemSettings` |
| `agent_profile_prompts` | `agent_system_profile_prompts` | `AgentProfilePrompt` | `AgentSystemProfilePrompt` |
| `agent_profile_photos` | `agent_system_profile_photos` | `AgentProfilePhoto` | `AgentSystemProfilePhoto` |
| `agent_delegation` | `agent_system_delegation` | `AgentDelegation` | `AgentSystemDelegation` |
| `agent_custom_tools` | `agent_system_custom_tools` | `AgentCustomTool` | `AgentSystemCustomTool` |
| `agent_conversations` | `agent_system_conversations` | `AgentConversation` | `AgentSystemConversation` |
| `agent_conversation_messages` | `agent_system_conversation_messages` | `AgentConversationMessage` | `AgentSystemConversationMessage` |
| `agent_usage_logs` | `agent_system_usage_logs` | `AgentUsageLog` | `AgentSystemUsageLog` |
| `agent_usage_round_logs` | `agent_system_usage_round_logs` | `AgentUsageRoundLog` | `AgentSystemUsageRoundLog` |
| `agent_tasks` | `agent_system_tasks` | `AgentTask` | `AgentSystemTask` |

La excepción `engine_settings` de ADR-024 queda retirada: ya no aporta nada frente al prefijo de tres partes, y generaba una inconsistencia visual (9 tablas `agent_*` + 1 tabla `engine_*`) sin necesidad.

### Por qué

- **Elimina la excepción sin perder la protección contra colisión**: el prefijo de tres partes (`agent_system_`) es, por construcción, disjunto de cualquier `system_name` de dos partes (`agent_<rol>`) del catálogo de perfiles — no hace falta revisar caso por caso ni dejar una tabla con nombre distinto al resto.
- **Nombra con precisión lo que es**: estas tablas no describen "un agente" sino la infraestructura del **sistema de agentes** completo (configuración global, catálogo, conversaciones, tareas, logs) — `agent_system_` es más preciso que `agent_` a secas.
- **Uniformidad**: las 10 tablas comparten el mismo prefijo sin excepciones, más fácil de reconocer y de filtrar (`grep agent_system_`) que un esquema con un caso especial.

## Consecuencias

### ✅ Positivas

- Prefijo uniforme en las 10 tablas, sin casos especiales que recordar ni documentar como excepción.
- Menor superficie de confusión: `agent_system_settings` (configuración del sistema de agentes) vs. `agent_settings` (identidad de un perfil de agente) son claramente distintos a simple vista, más que `engine_settings` vs. `agent_settings`.

### ⚠️ Negativas

- Nombres de tabla más largos (`agent_system_conversation_messages`, 33 caracteres) — sin impacto funcional, es una tabla más de PostgreSQL, pero es más tecleo en migraciones/queries manuales.
- Segunda vuelta de edición sobre `docs/arquitectura-tablas/sistema/README.md`, que ya se había actualizado una vez con el esquema de ADR-024 en la misma sesión. El código real (`src/models/bedrock_*.py`) sigue sin tocarse — ambos ADR (024 y 025) documentan estado objetivo, no estado actual; la migración de código solo necesita ejecutarse una vez, directo al esquema de este ADR-025.

### 🤷 Neutras

- No cambia nada del contenido técnico de ADR-008/012/017/022; solo el nombrado de tablas.

## Alternativas Consideradas

### Alternativa 1: Mantener el esquema de ADR-024 (`agent_*` + excepción `engine_settings`)
- ✅ Pro: cero trabajo adicional, ya estaba aplicado.
- ❌ Contra: inconsistencia de una tabla con prefijo distinto al resto del grupo; decisión explícita de Carlos de usar `agent_system_` en su lugar.

### Alternativa 2 (ELEGIDA): Prefijo uniforme `agent_system_`, sin excepciones
- ✅ Pro: uniformidad total, elimina la necesidad de la excepción, más preciso semánticamente ("sistema de agentes" como unidad).

## Referencias

- [ADR-024](./024-desacoplar-nombrado-motor-agentes-de-bedrock.md) (razonamiento de fondo sobre desacoplar de Bedrock, sigue vigente; solo su tabla de mapeo queda reemplazada)
- [ADR-022](./022-l2-split-configuration-vs-incidents.md) (origen del `system_name` `agent_settings`, causa de la colisión que este ADR resuelve de raíz)
- `docs/arquitectura-tablas/sistema/README.md`
- `api/src/services/bedrock/agent_profiles.py`

## Implicaciones

- [ ] `docs/arquitectura-tablas/sistema/README.md`: aplicar el mapeo de este ADR-025 sobre lo ya renombrado por ADR-024 (índice, encabezados `###`, bloques `mermaid`, prosa de `**Atributos:**`, relaciones cruzadas).
- [ ] Retirar la nota de excepción de `engine_settings` (ya no aplica) y reemplazarla, si aporta valor, por una nota breve señalando que `agent_system_settings` es distinto de el perfil `agent_settings`.
- [ ] Migración Alembic futura (trabajo de implementación pendiente, no de esta sesión): usar directamente los nombres de este ADR-025, no los de ADR-024.
- [ ] `docs/09-DECISIONS/README.md`: agregar fila 025 y marcar 024 como reemplazado en cuanto a nombrado.

## Seguimiento

Igual que ADR-024: el nombrado aquí fijado es el estado objetivo de la arquitectura. La migración real de código y base de datos se hace en el plan de implementación, directo a este esquema (`agent_system_*`), sin pasar por el intermedio `agent_*`/`engine_settings` de ADR-024.

---

**Creado por**: Arquitecto de Soluciones
**Aprobado por**: Carlos Jiménez Hirashi
**Fecha de creación**: 2026-08-30
**Estado de vigencia**: Aceptado — pendiente de implementación (migración de código y BD)
