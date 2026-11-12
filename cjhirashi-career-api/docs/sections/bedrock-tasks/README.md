# Tareas — `/agent-tasks`

Tablero de trabajo de Carlos: tareas con vistas de lista, kanban, calendario y Gantt. Ya no se asignan a agentes ni se ejecutan solas ([ADR-033](../../../../docs/09-DECISIONS/033-retiro-del-subsistema-bedrock.md)).

**Prefijo:** `/agent-tasks`  
**Tag OpenAPI:** `Agent - Tasks`  
**Auth:** JWT requerido.

## Arquitectura

```mermaid
flowchart LR
    Admin[Admin /tasks] --> Route[routes/bedrock_tasks.py]
    Route --> Factory[build_crud_router]
    Factory --> Schema[schemas/bedrock_task.py]
    Factory --> Repo[CareerRepository]
    Repo --> Model[BedrockTask]
    Model --> PG[(PostgreSQL)]
```

---

## Archivos fuente

| Capa | Archivo |
|------|---------|
| Rutas | `src/routes/bedrock_tasks.py` |
| Schemas | `src/schemas/bedrock_task.py` |
| Modelo | `src/models/bedrock_task.py` |

---

## Endpoints

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/agent-tasks` | Listar tareas |
| `GET` | `/agent-tasks/count` | Contar |
| `GET` | `/agent-tasks/{id}` | Obtener una |
| `POST` | `/agent-tasks` | Crear |
| `PUT` | `/agent-tasks/{id}` | Actualizar |
| `DELETE` | `/agent-tasks/{id}` | Eliminar |
| `POST` | `/agent-tasks/{id}/run` | Reclamar y ejecutar ahora (agente, pending/failed) |

Resource key: `agent-tasks` → modelo `BedrockTask`.

---

## Campos

| Campo | Descripción |
|-------|-------------|
| `title` | Título |
| `description` | Detalle (el agente lo usa como instrucción si es suya) |
| `status` | pending / in_progress / done / cancelled / failed |
| `scheduled_at` | Inicio / hora de ejecución (UTC) |
| `due_at` | Fecha límite (Gantt) |
| `priority` | low / medium / high |
| `error_message` | Si `failed` |


---

## Uso en Admin Panel

Ruta **`/tasks`** (sidebar principal). `/agent/tasks` redirige ahí. Vistas: lista, kanban, calendario, Gantt.

---

## Ejemplo

```bash
curl -s -X POST http://localhost:8000/agent-tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Revisar mi CV", "scheduled_at": "2026-11-20T15:00:00Z", "priority": "high"}'
```
