---
titulo: "Contrato /ai/ — paridad con /bedrock/* y /agent-tasks/* (spec 009)"
tipo: contrato
feature_id: "009"
fecha: 2026-10-13
---

# Contrato de rutas del harness (`/ai/`)

Inventario **verificado el 2026-10-13** importando la app de la API y leyendo su
`openapi()`: **47 operaciones** (39 en `/bedrock/*` + 8 en `/agent-tasks/*`), no 22.

**Regla de paridad (D-13, RF-001):** misma ruta relativa, mismo cuerpo y misma respuesta.
Externamente el Admin llama a `/ai/<ruta-actual>` (p. ej. `/ai/bedrock/chat`,
`/ai/agent-tasks`). Caddy usa `quitar_prefijo: true` (contrato `caddy.json`), así que el
harness sirve **internamente** las rutas sin prefijo (`/bedrock/chat`, `/agent-tasks`),
idénticas a las de la API. Los nombres `bedrock` en las rutas se conservan por paridad;
renombrarlos a neutros queda para una spec posterior (D-13).

Todas exigen `Authorization: Bearer <JWT>` salvo `GET /health` (RF-002).

Columna **Disposición**: `P` = paridad exacta · `P*` = paridad con cambio interno sin
efecto visible · `X` = NO se porta (confirmado, D-16) · `S` = paridad de contrato con búsqueda de
texto completo de Postgres en lugar de vectorial (D-15, RF-022).

## `/bedrock/*` (39)

| # | Método y ruta | Router destino (ai) | Disp. | Nota |
|---|---|---|---|---|
| 1 | POST `/bedrock/chat` | `routes/bedrock.py` | P | SSE (`text/event-stream`: `status`/`done`/`error`, ping `: ping` cada 15 s, `X-Accel-Buffering: no`). Reenvía el JWT del usuario a la API (RF-004). |
| 2 | GET `/bedrock/model` | `routes/bedrock.py` | P | |
| 3 | POST `/bedrock/model` | `routes/bedrock.py` | P | |
| 4 | GET `/bedrock/usage-metrics` | `routes/bedrock.py` | P | Lee `bedrock_usage_logs` propias. |
| 5 | GET `/bedrock/budget` | `routes/bedrock.py` | P | |
| 6 | GET `/bedrock/instructions` | `routes/bedrock.py` | P | |
| 7 | PUT `/bedrock/instructions` | `routes/bedrock.py` | P | |
| 8 | PUT `/bedrock/global-rules` | `routes/bedrock.py` | P | |
| 9 | GET `/bedrock/agent-profiles` | `routes/agent_profiles.py` | P | |
| 10 | GET `/bedrock/agent-profiles/catalog` | `routes/agent_profiles.py` | P* | Cruza con metodologías y secciones: lee la API por REST. |
| 11 | PUT `/bedrock/agent-profiles/{profile_id}/prompt` | `routes/agent_profiles.py` | P | |
| 12 | GET `/bedrock/agent-profiles/{profile_id}/catalog` | `routes/agent_profiles.py` | P* | REST a la API. |
| 13 | PUT `/bedrock/agent-profiles/{profile_id}/photo` | `routes/agent_profiles.py` | P* | Valida `photo_url` vía API `/files`. |
| 14 | PUT `/bedrock/agent-profiles/{profile_id}/delegation` | `routes/agent_profiles.py` | P | |
| 15 | PUT `/bedrock/agent-profiles/{profile_id}/sections` | `routes/agent_profiles.py` | P* | Escribe overrides en la API (`PUT /admin/sections/{id}`). |
| 16 | PUT `/bedrock/agent-profiles/{profile_id}/methodologies` | `routes/agent_profiles.py` | P* | Escribe `agent_profile_ids` en metodologías vía API; ya no reindexa (D-04). |
| 17 | GET `/bedrock/agent-profiles/{profile_id}/tools` | `routes/agent_profiles.py` | P* | Deriva tools por sección desde `/admin/sections`. |
| 18 | PUT `/bedrock/agent-profiles/{profile_id}/tools` | `routes/agent_profiles.py` | P | |
| 19 | GET `/bedrock/sections/{section_id}` | `routes/agent_profiles.py` | P* | |
| 20 | PUT `/bedrock/sections/{section_id}/methodologies` | `routes/agent_profiles.py` | P* | Vía API; sin reindexado. |
| 21 | GET `/bedrock/agent-profiles/{profile_id}/memory` | `routes/memory.py` | S | Memoria del agente en `bedrock_agent_memory` (D-15). |
| 22 | POST `/bedrock/agent-profiles/{profile_id}/memory/notes` | `routes/memory.py` | S | FTS Postgres (D-15). |
| 23 | DELETE `/bedrock/agent-profiles/{profile_id}/memory/notes/{note_id}` | `routes/memory.py` | S | FTS Postgres (D-15). |
| 24 | GET `/bedrock/tools` | `routes/tools.py` | P | |
| 25 | POST `/bedrock/tools` | `routes/tools.py` | P | |
| 26 | GET `/bedrock/tools/catalog` | `routes/tools.py` | P* | El catálogo deja de listar `search_knowledge_base` (D-15). |
| 27 | PUT `/bedrock/tools/{tool_id}/enabled` | `routes/tools.py` | P | |
| 28 | DELETE `/bedrock/tools/{tool_id}` | `routes/tools.py` | P | |
| 29 | POST `/bedrock/knowledge-base/reindex` | — | X | El Admin no la llama (grep 2026-10-13). Desaparece con la KB (D-04). Excepción confirmada a RF-001 (D-16). |
| 30 | GET `/bedrock/knowledge/search` | — | X | Idem (D-16). |
| 31 | GET `/bedrock/memory/events` | `routes/memory.py` | P | Eventos de corto plazo: salen de `bedrock_conversation_messages` (sin Qdrant). |
| 32 | GET `/bedrock/memory/records` | `routes/memory.py` | S | Búsqueda por texto completo (D-15). |
| 33 | POST `/bedrock/memory/manual` | `routes/memory.py` | S | FTS Postgres (D-15). |
| 34 | GET `/bedrock/conversations` | `routes/conversations.py` | P | |
| 35 | GET `/bedrock/conversations/{session_id}/messages` | `routes/conversations.py` | P | |
| 36 | PUT `/bedrock/conversations/{session_id}` | `routes/conversations.py` | P | |
| 37 | DELETE `/bedrock/conversations/{session_id}` | `routes/conversations.py` | P | |
| 38 | GET `/bedrock/audit-log` | `routes/audit_log.py` | P* | Lee el historial por REST de la API (`GET /audit-log`, D-19/RF-021). |
| 39 | POST `/bedrock/audit-log/{audit_id}/restore` | `routes/audit_log.py` | P* | Delega en `POST /audit-log/{audit_id}/restore` de la API (D-19). |

## `/agent-tasks/*` (8)

| # | Método y ruta | Router destino (ai) | Disp. | Nota |
|---|---|---|---|---|
| 40 | GET `/agent-tasks` | `routes/agent_tasks.py` | P | Mismos query params que `build_crud_router` (paginación, `filters` JSON, orden). |
| 41 | POST `/agent-tasks` | `routes/agent_tasks.py` | P | Con `subtasks` anidadas (ADR-016). |
| 42 | GET `/agent-tasks/count` | `routes/agent_tasks.py` | P | |
| 43 | GET `/agent-tasks/distinct/{field}` | `routes/agent_tasks.py` | P | |
| 44 | GET `/agent-tasks/{item_id}` | `routes/agent_tasks.py` | P | |
| 45 | PUT `/agent-tasks/{item_id}` | `routes/agent_tasks.py` | P | Dispara `enqueue_advance` (equivalente a `after_write`). |
| 46 | DELETE `/agent-tasks/{item_id}` | `routes/agent_tasks.py` | P | |
| 47 | POST `/agent-tasks/{item_id}/run` | `routes/agent_tasks.py` | P | Ejecución inmediata con el JWT del usuario (RF-004). |

## Rutas nuevas del harness (no parte de la paridad)

- `GET /health` (sin auth): comprueba BD propia y alcanzabilidad de la API.
- `GET /metrics` (Prometheus, interno; no se enruta por Caddy).

## Errores

Problem Details (RFC 9457) como el resto del proyecto (Art. 6). Las respuestas de error
heredadas (`{"detail": ...}`) se conservan donde el Admin ya las lee (paridad; el Admin
usa `data.detail` en el chat). 401 sin/ con JWT inválido (RF-002); 403 si el JWT lleva `role` `agent` o `service` (D-14, D-17).

## Pruebas de paridad (RF-001)

`tests/contract/test_ai_route_parity.py` (ai) lee **este archivo** y verifica que
`app.openapi()` del harness contiene exactamente las filas `P`/`P*`/`S` y que no contiene
las `X` . Un test espejo en
el Admin (`src/tests/api/aiRoutes.test.ts`) verifica que cada llamada de `api/bedrock.ts` y
`api/agentTasks.ts` usa una ruta de esta tabla.
