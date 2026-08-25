# ADR-009: Multi-agente — dos chats y delegación

## Estado

**Deprecado** — reemplazado por [ADR-012](./012-bedrock-three-level-agents.md) (2026-08-25).

## Decisión

- Chat **contextual**: perfiles especialistas, sin delegación.
- Chat **general**: orquestador con `delegate_to_specialist` (max 3/turno).

Perfiles en `agent_profiles.py`. Sesiones separadas por `session_type`.
