# Chat Admin — Harness local

## Superficies y niveles (ADR-012)

- **General** (`/agent/chat`): L1 orquestador; sin CRUD; delega a L2 (área) y L3 (tarea).
- **Contextual** (sidebar derecha): L2 de la sección; puede delegar a L3.
- **L3** (agent_pdf_render, agent_visual_design, agent_changelog, agent_task_manager, agent_linkedin_publishing, agent_vacancy_search, agent_cv_writing, agent_cover_letter_writing): sin chat; solo sub-turnos.

## Historial por agente

Cada especialista contextual y el orquestador tienen su propia lista de sesiones. El store guarda un `session_id` por cubo `sessionType:agentProfileId` (p. ej. `contextual:agent_professional_identity`, `general:agent_orchestrator`). La API lista con `?session_type=&agent_profile_id=`.

Al cambiar de sección cambia el cubo. No hay override manual de agente: la pantalla determina el especialista.

## Preferencias por sesión

`bedrockChatStore` guarda el override de modelo por `session_id` en localStorage.
