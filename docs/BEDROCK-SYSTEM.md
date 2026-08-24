# Sistema Bedrock — Guía maestra

Documento índice del Harness Converse (ADR-008, ADR-009, ADR-010).

## 1. Resumen

- **Harness** en `api/src/services/bedrock/` — loop Converse, historial PG, tools, presupuesto.
- **AWS:** solo `bedrock-runtime` (Converse + Titan Embeddings + Titan Image).

## 2. Dos superficies de chat

| Superficie | UI | Agente | Delegación |
|------------|-----|--------|------------|
| contextual | Sidebar derecha | Especialista por sección | No |
| general | `/agent/chat` | Orquestador | Sí (`delegate_to_specialist`) |

## 3. Perfiles agente (9)

`orchestrator`, `identity`, `search`, `digital`, `networking`, `support`, `methodologies`, `pdf_design`, `visual_design`

Definidos en `api/src/services/bedrock/agent_profiles.py`.

## 4. Variables de entorno

Ver `.env.example` — `BEDROCK_DEFAULT_MODEL_ID`, `BEDROCK_DAILY_BUDGET_USD`, `AWS_ACCESS_KEY_ID`, etc.

## 5. Documentación relacionada

- [ADR-008](09-DECISIONS/008-bedrock-harness-local.md)
- [api/docs/BEDROCK-HARNESS.md](../api/docs/BEDROCK-HARNESS.md) — IAM y catálogo de modelos
- [api/docs/sections/bedrock/README.md](../api/docs/sections/bedrock/README.md)
- [admin/docs/BEDROCK-CHAT.md](../admin/docs/BEDROCK-CHAT.md)
