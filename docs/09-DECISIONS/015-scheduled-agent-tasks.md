# ADR-015: Tareas de primer nivel y ejecución autónoma de agentes

## Estado

Aceptado — 2026-08-26

## Contexto

`bedrock_tasks` era un plan interno del agente (pasos de un turno largo) expuesto solo bajo **Agente IA → Tareas**. Carlos necesita un tablero de trabajo de primer nivel — lista, calendario, kanban y Gantt — donde una tarea pueda asignarse **al usuario** o **a un agente del catálogo**.

Si la tarea es de un agente, debe ejecutarse el día y a la hora programados **aunque el Admin Panel esté cerrado**. El harness actual solo corre dentro de un `POST /bedrock/chat` autenticado; eso no cumple el requisito.

## Decisión

1. **Tareas es sección principal del Admin** (`/tasks`), al mismo nivel que Dashboard, Métricas y Archivos. `/agent/tasks` redirige a `/tasks`. El recurso REST sigue siendo `/agent-tasks` (tools genéricas y L3 `agent_task_manager` no cambian de `resource_key`).

2. **Un solo modelo** (`bedrock_tasks`) cubre recordatorios del usuario y trabajo autónomo de agentes. Campos nuevos: `assignee_type` (`user` | `agent`), `agent_profile_id`, `scheduled_at`, `due_at`, `priority`, `execution_result`, `executed_at`, `error_message`. Status añade `failed`.

3. **Ejecución sin sesión humana**: un scheduler asyncio en el lifespan de la API (mismo patrón que `linkedin_scheduler`, un worker uvicorn) reclama filas `assignee_type=agent` con `status=pending` y `scheduled_at <= now`, e invoca `run_single_turn_sync` con el `user_id` dueño de la fila. No hay JWT ni SPA.

   - L1/L2: historial en sesión `scheduled-task-{id}`.
   - L3: `record_history=False` (ADR-012: L3 no tiene chat de usuario).

4. **Ejecutar ahora** (`POST /agent-tasks/{id}/run`) reclama la tarea y dispara el mismo runner en background.

### Por Qué

- Reutilizar `linkedin_scheduler` evita Celery/Redis en un sistema de un operador y un worker.
- Invocar el harness existente (no un segundo loop) conserva tools, presupuesto, auditoría y delegación L1→L2→L3.
- Unificar en `bedrock_tasks` evita dos sistemas de “tareas” competidores.

## Consecuencias

### Positivas

- Los agentes trabajan con el Admin cerrado.
- Cuatro vistas sobre la misma fuente de verdad.
- El presupuesto diario de Bedrock sigue aplicando (si se agota, la tarea queda `failed`).

### Costos

- El scheduler vive en el proceso de la API: requiere `--workers 1` (ya es el caso).
- Una tarea de agente mal descrita puede gastar tokens sin supervisión en vivo.

### Alternativas rechazadas

- **Cron en el Admin Panel**: falla si Carlos no está en sesión.
- **Celery / worker extra**: infra innecesaria para un único operador.
- **Tabla `tasks` aparte de `bedrock_tasks`**: duplica CRUD, tools y el L3 gestor.

## Referencias

- [ADR-012](./012-bedrock-three-level-agents.md) — L3 sin chat
- `cjhirashi-career-api/src/services/task_scheduler.py`
- `cjhirashi-career-api/src/services/linkedin_scheduler.py`

## Implicaciones

- [x] Extender `BedrockTask` + migración Alembic
- [x] Scheduler en lifespan + `POST /{id}/run`
- [x] Admin: `/tasks` con lista, kanban, calendario y Gantt
- [x] Quitar Tareas del acordeón Agente IA

---

**Creado por**: Arquitecto de Soluciones
**Fecha de creación**: 2026-08-26
**Estado de vigencia**: Vigente
