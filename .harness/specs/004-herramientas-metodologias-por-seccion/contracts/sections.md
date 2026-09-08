# Contrato — Secciones del Admin de cara a los agentes (spec 004)

Feature 004. Referencia humana; el gate no ancla OpenAPI todavía.

## GET `/bedrock/sections/{section_id}`

Estado de una sección: herramientas **derivadas** (código) + metodologías **ligadas**.

Respuesta `200`:

```json
{
  "section_id": "sec-32",
  "system_name": "career-projects",
  "label": "Proyectos",
  "section_type": "table",
  "resource_key": "projects",
  "agent_profile_id": "agent_professional_identity",
  "derived_tools": ["bulk_update_career_record", "count_career_records", "create_career_record",
                    "delete_career_record", "describe_resource_schema", "get_career_record",
                    "list_career_record", "search_knowledge_base", "update_career_record"],
  "methodology_ids": ["opm-29", "opm-33"],
  "methodologies": [{"id": "opm-29", "title": "Proceso 5 - Portafolio", "section": "Identidad Profesional"}]
}
```

- `404` si `section_id` no es una sección conocida (`sec-N`).

## PUT `/bedrock/sections/{section_id}/methodologies`

Liga a la sección **exactamente** las metodologías de `methodology_ids` (reemplazo total
de la pertenencia de este `sec-N`; añade/quita `section_id` del `section_ids` de cada
metodología del usuario).

```json
{ "methodology_ids": ["opm-29", "opm-33"] }
```

- Respuesta `200`: mismo shape que el GET.
- `400` si algún `methodology_id` no existe para el usuario.
- `404` si `section_id` no es una sección conocida.
- Re-indexa en Qdrant (best-effort) las metodologías tocadas.

## Endpoints de agente (feature 003) — comportamiento para L2

- `PUT /bedrock/agent-profiles/{id}/tools` y `PUT .../methodologies`:
  - `id` es **L2** → `409 Conflict` (recibe herramientas/metodologías de sus secciones;
    edítalas en `/settings/sections/:id`).
  - `id` es **L1/L3** → comportamiento de la feature 003.
- `GET /bedrock/agent-profiles/{id}/tools`:
  - **L2** → `{ default_tools, effective_tools, override_tools: null, by_section:
    [{section_id, label, tools}] }` (lectura, con procedencia).
  - **L1/L3** → como en 003, `by_section: null`.

## GET `/bedrock/tools/catalog` — campo `scope`

Cada tool integrada trae `scope ∈ {"section", "agent", "both"}`. Las CRUD genéricas de
carrera y `describe_resource_schema` son `section`; `delegate_to_specialist` es `agent`;
el resto `both`. `PUT /bedrock/agent-profiles/{L1|L3}/tools` con una tool `scope=section`
→ `400`.
