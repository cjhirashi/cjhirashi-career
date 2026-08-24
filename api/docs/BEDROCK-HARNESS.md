# Bedrock Harness local — API

## Paquete

`src/services/bedrock/` — ver README del paquete.

## Endpoint principal

`POST /bedrock/chat` — SSE events:

- `status` — progreso
- `delegation_start` / `delegation_end` — chat general
- `done` — `{ reply, affected_resources }`
- `error`

Body (`BedrockChatRequest`):

```json
{
  "session_id": "uuid",
  "message": "texto",
  "chat_surface": "contextual|general",
  "page_context": { "route": "/career/vacancies", "resource_key": "vacancies" },
  "model_id": "opcional",
  "agent_profile_id": "opcional"
}
```

## Otros

- `GET /bedrock/conversations?session_type=general|contextual`
- `GET /bedrock/knowledge/search?q=...` — Qdrant (reemplazo memoria AgentCore)

Ver [docs/BEDROCK-SYSTEM.md](../../docs/BEDROCK-SYSTEM.md).
