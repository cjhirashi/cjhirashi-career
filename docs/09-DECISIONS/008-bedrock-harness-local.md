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

- Eliminar dependencia de `BEDROCK_HARNESS_ARN` en despliegues nuevos
- IAM: `bedrock:InvokeModel` (Converse) y opcionalmente `bedrock:InvokeModelWithResponseStream` (ConverseStream) en modelos e inference profiles del catálogo
- Feature flag `BEDROCK_USE_LOCAL_HARNESS` (default true)
