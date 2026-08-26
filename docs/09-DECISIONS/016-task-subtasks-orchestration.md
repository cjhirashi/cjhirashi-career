# ADR-016: Subtareas, orquestación por turno y notificaciones al usuario

## Estado

Aceptado — 2026-08-26

## Contexto

Las tareas de [ADR-015](./015-scheduled-agent-tasks.md) son filas planas: un responsable (Carlos o un agente) y, si es agente, ejecución a `scheduled_at`. Un plan de trabajo real necesita **subtareas** con distintos responsables, **dependencias de orden** (unas bloquean a las siguientes) y dos modos de disparo para el agente: hora programada **o** “cuando le toque el turno”. Si el responsable es el usuario, el sistema debe **avisarle** — el scheduler no puede “ejecutar” a Carlos.

## Decisión

1. **Misma tabla** `bedrock_tasks`. Una subtarea es una fila con `parent_id` apuntando a la tarea padre. Un solo nivel (el padre no puede ser a su vez subtarea). `sort_order` fija la secuencia. Borrar el padre cascada las hijas.

2. **`is_blocking`**. Recorriendo las hermanas en `sort_order`, una subtarea está bloqueada si alguna **anterior** con `is_blocking=True` no está en `done` ni `cancelled`. `failed` sigue bloqueando hasta reintentar o cancelar. Las no bloqueantes no detienen a las posteriores.

3. **El padre es el orquestador**. Si tiene hijas, el scheduler no ejecuta al padre como agente: avanza el turno entre subtareas y resume el estado del padre (`in_progress` mientras hay trabajo; `done` cuando todas están `done`/`cancelled`).

4. **Dos disparos para el agente**
   - `execute_on_turn=False` (default): igual que ADR-015 — `scheduled_at <= now` y no bloqueada.
   - `execute_on_turn=True`: al quedar desbloqueada se reclama y corre el harness **aunque no haya hora**, o aunque la hora aún no llegue. `scheduled_at` queda como planificación visible.

5. **Turno del usuario**. Subtarea (o tarea suelta) con `assignee_type=user`, pendiente y desbloqueada: se inserta `user_notifications` (`kind=task_turn`) y se marca `turn_notified_at` para no duplicar. El Admin muestra una campana; el aviso enlaza a `/tasks?task={id}`.

6. **Vista de registro**. El único campo editable en Vista es `status` (tarea y subtareas listadas). Alta/edición de subtareas vive en Edición.

### Por Qué

- Reutilizar `bedrock_tasks` evita un segundo CRUD, las tools del L3 gestor y el scheduler.
- Un nivel de anidación cubre el plan de trabajo sin un grafo de dependencias.
- Notificar en API (no en el SPA) funciona con el Admin cerrado; la campana es solo la bandeja.

### Costos

- El scheduler hace más trabajo por tick (árbol + avisos). Sigue siendo un operador y pocas filas.
- `failed` bloqueante puede dejar un plan parado a propósito hasta que Carlos actúe.

### Alternativas rechazadas

- **Tabla `subtasks` aparte**: duplica assignee/fechas/ejecución.
- **Grafo libre de dependencias**: más potente, innecesario para un plan lineal con excepciones no bloqueantes.
- **Email/push externo**: un solo usuario; basta la bandeja del Admin.

## Referencias

- [ADR-015](./015-scheduled-agent-tasks.md)
- `cjhirashi-career-api/src/services/task_scheduler.py`
- `cjhirashi-career-api/src/models/user_notification.py`

---

**Creado por**: Arquitecto de Soluciones
**Fecha de creación**: 2026-08-26
**Estado de vigencia**: Vigente
