# ADR-009: Multi-agente — dos chats y delegación

## Decisión

- Chat **contextual**: perfiles especialistas, sin delegación.
- Chat **general**: orquestador con `delegate_to_specialist` (max 3/turno).

Perfiles en `agent_profiles.py`. Sesiones separadas por `session_type`.
