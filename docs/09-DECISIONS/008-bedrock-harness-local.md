# ADR-008: Bedrock Harness local (Converse API)

## Estado

Aceptado — 2026-08-23

## Contexto

AgentCore Harness (`invoke_harness`) generaba costos elevados (~$29/2 días), desconexiones y sin control de tokens/historial.

## Decisión

Reemplazar por Harness local en `api/src/services/bedrock/`:

- ConverseStream para inferencia
- PostgreSQL para historial y settings
- Qdrant para `search_knowledge_base`
- Presupuesto diario y logs granulares (`bedrock_usage_round_logs`)

## Consecuencias

- IAM: `bedrock:InvokeModel` (Converse) y opcionalmente `InvokeModelWithResponseStream`
- Historial y settings en PostgreSQL; memoria semántica en Qdrant
- **2026-08-24:** eliminado código y config legacy (`BEDROCK_HARNESS_ARN`, feature flag, schemas AgentCore)
