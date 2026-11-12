# ADR-008: Bedrock Harness local (Converse API)

> **Estado (2026-11-10, [ADR-032](032-agentes-externos-y-bedrock-fuera-de-operacion.md)):** el subsistema de agentes con AWS Bedrock está **fuera de operación**. Los agentes de IA son externos y entran por la API con el rol `agent`. Este documento se conserva como referencia del diseño y no describe el comportamiento operativo actual.

## Estado

Aceptado — 2026-08-23. Revisado parcialmente por [ADR-029](./029-harness-agentes-fuera-de-api.md): el harness sale de la API, la memoria pasa a Postgres y se retira Qdrant (en ejecución, etapa 3 pendiente) **Retirado por el [ADR-033](./033-retiro-del-subsistema-bedrock.md) (2026-11-11).**

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
