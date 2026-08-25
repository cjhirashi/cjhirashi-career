# Chat Admin — Harness local

## Superficies

- **Contextual** (sidebar derecha): especialista fijo de la sección; selector de modelo.
- **General** (`/agent/chat`): orquestador fijo; delegación a especialistas.

## Historial por agente

Cada especialista contextual y el orquestador tienen su propia lista de sesiones. El store guarda un `session_id` por cubo `sessionType:agentProfileId` (p. ej. `contextual:identity`, `general:orchestrator`). La API lista con `?session_type=&agent_profile_id=`.

Al cambiar de sección cambia el cubo. No hay override manual de agente: la pantalla determina el especialista.

## Preferencias por sesión

`bedrockChatStore` guarda el override de modelo por `session_id` en localStorage.
