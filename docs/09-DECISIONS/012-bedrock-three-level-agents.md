# ADR-012: Jerarquía de agentes en 3 niveles

## Estado

Aceptado — 2026-08-25

Reemplaza [ADR-009](./009-bedrock-multi-agent-profiles.md) (delegación binaria: solo el orquestador, solo en chat general).

## Contexto

El harness tenía dos capas rígidas: el orquestador (chat general) podía llamar especialistas; esos especialistas no podían delegar. El orquestador además tenía todas las tools (CRUD, PDF, discovery), de modo que era un todólogo. Hacía falta separar **quién habla con el usuario** de **quién ejecuta una tarea**, y que cada agente tenga una sola responsabilidad.

## Decisión

Tres niveles, delegación **solo hacia abajo**:

| Nivel | Rol | Superficie | ¿Habla con el usuario? | Puede delegar a |
|-------|-----|------------|------------------------|-----------------|
| 1 | Orquestador (`agent_orchestrator`) | Chat general (`/agent/chat`) | Sí | L2 y L3 |
| 2 | Especialista de área | Chat contextual (sidebar) | Sí | Solo L3 |
| 3 | Especialista de tarea | Ninguna | No | Nadie |

Reglas:

- L1 **no hace CRUD**. Solo `delegate_to_specialist`.
- L2 es dueño de su dominio. No llama a otro L2 ni al orquestador.
- L3 es worker interno: sin sesión, sin historial de usuario, sin `POST /bedrock/chat` como agente principal.
- Profundidad máxima 2 (L1 → L2 → L3). L1 puede saltar a L3 si la petición es claramente de tarea.

### Catálogo inicial

**L2:** `agent_professional_identity`, `agent_search_operations`, `agent_digital_presence`, `agent_networking`, `agent_support`, `agent_methodologies`, `agent_pdf_design`.

**L3:**

- `agent_pdf_render` — genera el PDF de un registro (`cv-versions`, `cover-letter-versions`) o preview de plantilla. No edita HTML/CSS.
- `agent_visual_design` — imágenes (antes aparecía como chat; ahora sin UI).
- `agent_changelog` — bitácora (`list_recent_changes`, `restore_deleted_record`).
- `agent_task_manager` — plan `agent-tasks`.
- `agent_linkedin_publishing` — publica, programa o elimina posts de LinkedIn. No edita perfil ni portal.
- `agent_vacancy_search` — discovery de vacantes (`run_job_discovery`, `import_job_url`, `save_job_listings`). No opera CVs ni aplicaciones.
- `agent_cv_writing` — redacta y persiste `cv-versions` (`content` Markdown). No genera PDF.
- `agent_cover_letter_writing` — redacta y persiste `cover-letter-versions` (`body_content`). No genera PDF.

**PDF:** un L2 (`agent_pdf_design`) coordina plantillas y estilos (un estilo, muchas plantillas). No hay L3 por tabla. El L3 `agent_pdf_render` es el ejecutor.

**LinkedIn / vacantes:** L2 `agent_digital_presence` y `agent_search_operations` hablan con Carlos; los L3 `agent_linkedin_publishing` y `agent_vacancy_search` ejecutan.

**CVs / cover letters:** L2 `agent_search_operations` coordina; `agent_cv_writing` y `agent_cover_letter_writing` redactan; `agent_pdf_render` emite el PDF.

### Por qué

- Un agente, una responsabilidad: el orquestador coordina; el de área opera su dominio; el de tarea ejecuta un oficio.
- Plantillas y estilos son un solo sistema de diseño (FK `style_id` + `style_guide`). Partirlos en dos L3 crearía hops inútiles.
- Renderizar un PDF a partir de un registro es otra responsabilidad (ejecución, no diseño).
- L3 sin chat evita que el usuario converse con workers y que esas sesiones ensucien el historial.

## Consecuencias

### Positivas

- L1 deja de tocar tablas.
- L2 contextual puede pedir bitácora, PDF o imagen sin ser todólogo.
- El Admin solo lista L1/L2; L3 aparece en eventos `delegation_*` y en Instrucciones (suffix editable).

### Costos

- Un turno general con CRUD implica al menos un hop extra (L1 → L2).
- Páginas Admin sin L2 mapeado siguen cayendo al orquestador en la sidebar (excepción documentada).

### Alternativas rechazadas

- L3 por tabla PDF (templates vs styles): acoplamiento `style_guide` ↔ HTML.
- Dejar `generate_pdf` en `agent_pdf_design` y `agent_search_operations`: mezcla diseño y ejecución.
- Dejar `create_linkedin_post` / `run_job_discovery` en L2: mezcla conversación de dominio y control de API externa.
- L3 con chat propio: viola “solo L1 y L2 hablan con el usuario”.

## Referencias

- Harness: `api/src/services/bedrock/agent_profiles.py`, `agent_loop.py`, `delegation.py`
- Espejo UI: `admin/src/config/agentProfiles.ts`
- [ADR-008](./008-bedrock-harness-local.md) · [ADR-009](./009-bedrock-multi-agent-profiles.md) (deprecado) · [ADR-010](./010-bedrock-visual-pdf-agents.md)

---

**Creado por**: Arquitecto de Soluciones  
**Fecha de creación**: 2026-08-25  
**Estado de vigencia**: Vigente
