# Sistema Bedrock — Guía maestra

Documento índice del Harness local post-rediseño (ADR-008, ADR-009, ADR-010).

## 1. Resumen

- **Harness local** en `api/src/services/bedrock/` — loop Converse, historial PG, tools, presupuesto.
- **AWS:** solo `bedrock-runtime` (ConverseStream + Titan Embeddings + Titan Image).
- **Sin AgentCore Harness** cuando `BEDROCK_USE_LOCAL_HARNESS=true`.

## 2. Dos superficies de chat

| Superficie | UI | Agente | Delegación |
|------------|-----|--------|------------|
| contextual | Sidebar derecha | Especialista por sección | No |
| general | `/agent/chat` | Orquestador | Sí (`delegate_to_specialist`) |

## 3. Perfiles agente (9)

`orchestrator`, `identity`, `search`, `digital`, `networking`, `support`, `methodologies`, `pdf_design`, `visual_design`

Definidos en `api/src/services/bedrock/agent_profiles.py`.

## 4. Variables de entorno

Ver `.env.example` — `BEDROCK_USE_LOCAL_HARNESS`, `BEDROCK_DEFAULT_MODEL_ID`, `BEDROCK_DAILY_BUDGET_USD`, etc.

## 5. Documentación relacionada

- [ADR-008](09-DECISIONS/008-bedrock-harness-local.md)
- [api/docs/BEDROCK-HARNESS.md](../api/docs/BEDROCK-HARNESS.md)
- [admin/docs/BEDROCK-CHAT.md](../admin/docs/BEDROCK-CHAT.md)
