# ADR-024: Desacoplar el nombrado del motor de agentes de "Bedrock"

## Estado

Aceptado — 2026-08-30

🔶 Tabla de mapeo de nombres reemplazada por [ADR-025](./025-prefijo-agent-system-motor-agentes.md) (prefijo `agent_system_` uniforme, sin la excepción `engine_settings`). El razonamiento de fondo de este ADR-024 — desacoplar el nombre del motor de agentes del proveedor Bedrock — sigue vigente; solo cambian los nombres concretos de tabla/clase, ver ADR-025.

No reemplaza a [ADR-008](./008-bedrock-harness-local.md) ni a [ADR-012](./012-bedrock-three-level-agents.md) en su contenido técnico (Converse API, jerarquía L1/L2/L3), solo corrige el nombrado de las tablas y clases que documentan. Es una decisión de **nombrado**, no de arquitectura de agentes.

## Contexto

El motor de agentes (harness local, historial, catálogo de perfiles, tareas, logs de uso) nació documentado como "Bedrock": tablas `bedrock_settings`, `bedrock_conversations`, `bedrock_tasks`, etc., clases `BedrockSettings`, `BedrockConversation`, etc., y el propio ADR-008 se titula "Bedrock Harness local".

Ese nombre confunde dos capas distintas:

- **El motor de agentes**: harness local en `api/src/services/bedrock/`, con su propio historial, catálogo de perfiles (`agent_profiles.py`, todos con prefijo `agent_*`: `agent_orchestrator`, `agent_settings`, `agent_task_manager`, etc. — ver ADR-012/017/022), tareas y logs.
- **AWS Bedrock**: el proveedor de inferencia LLM usado *hoy* por ese motor (Converse API), intercambiable en el futuro por otro proveedor (OpenAI, Anthropic directo, Vertex AI, etc.) sin que el motor de agentes en sí cambie de identidad.

Nombrar tablas/clases del motor como "Bedrock" ata el nombre del sistema al proveedor de turno. Si el proveedor cambia, todo el esquema y el código quedan con un nombre que ya no describe lo que hacen — exactamente el problema que ADR-008 arrastra en su propio título ("Bedrock Harness local": el harness es local, "Bedrock" ahí describe solo el proveedor de Converse API).

## Decisión

Renombrar las tablas y clases del motor de agentes con prefijo `agent_` / `Agent`, en vez de `bedrock_` / `Bedrock`. "Bedrock" queda reservado exclusivamente para referirse al proveedor de inferencia LLM (SDK boto3, Converse API, modelos), nunca al motor de agentes en sí.

| Tabla actual | Tabla nueva | Clase actual | Clase nueva |
|---|---|---|---|
| `bedrock_settings` | **`engine_settings`** (excepción, ver abajo) | `BedrockSettings` | `EngineSettings` |
| `bedrock_agent_profile_prompts` | `agent_profile_prompts` | `BedrockAgentProfilePrompt` | `AgentProfilePrompt` |
| `bedrock_agent_profile_photos` | `agent_profile_photos` | `BedrockAgentProfilePhoto` | `AgentProfilePhoto` |
| `bedrock_agent_delegation` | `agent_delegation` | `BedrockAgentDelegation` | `AgentDelegation` |
| `bedrock_custom_tools` | `agent_custom_tools` | `BedrockCustomTool` | `AgentCustomTool` |
| `bedrock_conversations` | `agent_conversations` | `BedrockConversation` | `AgentConversation` |
| `bedrock_conversation_messages` | `agent_conversation_messages` | `BedrockConversationMessage` | `AgentConversationMessage` |
| `bedrock_usage_logs` | `agent_usage_logs` | `BedrockUsageLog` | `AgentUsageLog` |
| `bedrock_usage_round_logs` | `agent_usage_round_logs` | `BedrockUsageRoundLog` | `AgentUsageRoundLog` |
| `bedrock_tasks` | `agent_tasks` | `BedrockTask` | `AgentTask` |

**Excepción — `bedrock_settings` → `engine_settings`, no `agent_settings`:** el catálogo de perfiles de agente (`agent_profiles.py`, ADR-012/017/022) ya usa el `system_name` **`agent_settings`** para el perfil L2 "Incidencias y Bitácora" (`AGENT_SETTINGS = "agent_settings"`, FK de texto en `agent_conversations.agent_profile_id`, `agent_profile_prompts.profile_id`, `operational_methodologies.agent_profile_ids`). Nombrar la tabla de configuración global igual (`agent_settings`) crearía un choque semántico entre "la tabla de configuración del motor" y "la identidad de un agente concreto que se llama así". Esa tabla guarda configuración del *motor de inferencia* (modelo activo, presupuesto, prompts base) — `engine_settings` describe exactamente eso sin colisionar con el namespace de perfiles.

Fuera de esa excepción, ningún otro nombre nuevo (`agent_profile_prompts`, `agent_conversations`, `agent_tasks`, etc.) colisiona con los `system_name` existentes del catálogo de perfiles (verificado contra la lista completa en `agent_profiles.py`).

También se corrige el nombre de grupo temático en la documentación de arquitectura de tablas: "Motor de Agentes Bedrock" → **"Motor de Agentes"**.

### Por qué

- **El nombre debe describir el rol, no el proveedor de turno**: el motor de agentes es una pieza propia (harness local, historial, catálogo, tareas); Bedrock es un detalle de infraestructura reemplazable, igual que hoy PostgreSQL o MinIO son reemplazables sin que eso obligue a renombrar `users` o `file_uploads`.
- **Habilita multi-proveedor sin deuda de nombrado**: si en el futuro se integra otro proveedor de LLM (o varios, seleccionables), las tablas `agent_*` siguen siendo correctas sin importar qué proveedor esté detrás en ese momento.
- **Evita el choque con el catálogo de perfiles**: la excepción `engine_settings` deja claro que "configuración del motor" y "perfil de agente llamado agent_settings" son dos conceptos distintos que no deben compartir nombre.

## Consecuencias

### ✅ Positivas

- El nombrado de tablas/clases queda desacoplado del proveedor de inferencia; migrar de proveedor no exige tocar el esquema de datos del motor de agentes.
- Consistencia con el prefijo `agent_*` ya establecido en el catálogo de perfiles (`agent_profiles.py`) y en el propio dominio conceptual ("motor de agentes IA" en `CLAUDE.md`).
- La excepción documentada (`engine_settings`) previene un choque de nombres real, no hipotético.

### ⚠️ Negativas

- Requiere una migración Alembic real (`RENAME TABLE` + actualización de FKs de texto que referencian nombres de tabla en comentarios/docs, no en constraints) y renombrar clases SQLAlchemy, servicios (`services/bedrock/` → posible renombre futuro), imports y tests en todo el backend. Es trabajo de implementación pendiente, no cubierto por este ADR.
- Todo el código actual (`src/models/bedrock_*.py`, `services/bedrock/`, imports en API/Admin) sigue usando el nombre viejo hasta que se ejecute esa migración — hay una ventana donde la documentación de arquitectura (`docs/arquitectura-tablas/`) describe el estado objetivo y el código todavía no coincide.
- ADR-008 conserva su título histórico ("Bedrock Harness local") porque un ADR aceptado no se edita; queda superado en cuanto a nombrado por este ADR-024, no en cuanto a su contenido técnico.

### 🤷 Neutras

- AWS Bedrock sigue siendo el proveedor de inferencia activo; este ADR no cambia el proveedor, solo el nombre de lo que lo rodea.
- `services/bedrock/` como ruta de carpeta puede conservarse o renombrarse en la implementación; no es una decisión de este ADR (es detalle de organización de código, no de esquema de datos).

## Alternativas Consideradas

### Alternativa 1: Mantener el nombrado `bedrock_*`
- ✅ Pro: cero migración.
- ❌ Contra: ata el nombre del sistema al proveedor de turno; ADR-008 ya evidencia la confusión ("harness local" pero tablas "Bedrock").

### Alternativa 2: Prefijo genérico distinto, ej. `ai_engine_*`
- ✅ Pro: enfatiza "motor de IA" en vez de "agente" puntual.
- ❌ Contra: menos consistente con el prefijo `agent_*` ya establecido en el catálogo de perfiles (`agent_profiles.py`); introduciría dos convenciones de prefijo conviviendo en el mismo dominio.

### Alternativa 3 (ELEGIDA): Prefijo `agent_*`, con excepción `engine_settings` para la config global
- ✅ Pro: consistente con el catálogo de perfiles ya existente.
- ✅ Pro: la única colisión real (`bedrock_settings` → `agent_settings`) se resuelve con un nombre igual de preciso (`engine_settings`) sin inventar un prefijo nuevo para el resto de la familia.

## Referencias

- [ADR-008](./008-bedrock-harness-local.md) (harness local — contenido técnico no afectado, título queda con nombrado histórico)
- [ADR-012](./012-bedrock-three-level-agents.md) (jerarquía de agentes L1/L2/L3)
- [ADR-017](./017-l2-agent-settings.md) y [ADR-022](./022-l2-split-configuration-vs-incidents.md) (origen del `system_name` `agent_settings` como perfil, causa de la excepción `engine_settings`)
- `docs/arquitectura-tablas/sistema/README.md` (clasificación de tablas de sistema, ya actualizada con el nombrado nuevo)
- `api/src/services/bedrock/agent_profiles.py` (catálogo completo de `system_name` verificado contra colisiones)

## Implicaciones

- [x] `docs/arquitectura-tablas/sistema/README.md`: tablas, clases y grupo temático renombrados al esquema `agent_*` / `engine_settings`.
- [ ] Migración Alembic: `bedrock_*` → `agent_*` / `engine_settings` (renombrar tablas, no recrear — preservar datos e índices).
- [ ] `src/models/bedrock_*.py` → renombrar archivos y clases; actualizar imports en `src/models/__init__.py` y en todo el backend que importe estas clases.
- [ ] `src/services/bedrock/` y sus referencias en API/Admin: evaluar si se renombra la carpeta/servicio o solo las tablas/clases (decisión de implementación, no de este ADR).
- [ ] `src/models/README.md`: actualizar nombres de tabla en los diagramas una vez ejecutada la migración de código (no antes, para no desincronizar la documentación del código real).
- [ ] `docs/09-DECISIONS/README.md`: agregar fila 024 al Registro de Decisiones.
- [ ] `CLAUDE.md`: sin cambios necesarios (ya usa "motor de agentes IA" de forma genérica).

## Seguimiento

Este ADR fija el nombrado objetivo. La ejecución real del rename (migración Alembic + código) se hace como parte del plan de implementación cuando se aborde ese trabajo — no en esta sesión, que se centró en arquitectura y documentación. Hasta que esa migración corra, el código fuente sigue usando `bedrock_*`/`Bedrock*` y `docs/arquitectura-tablas/` documenta el estado objetivo, no el estado actual del código.

---

**Creado por**: Arquitecto de Soluciones
**Aprobado por**: Carlos Jiménez Hirashi
**Fecha de creación**: 2026-08-30
**Estado de vigencia**: Aceptado — pendiente de implementación (migración de código y BD)
