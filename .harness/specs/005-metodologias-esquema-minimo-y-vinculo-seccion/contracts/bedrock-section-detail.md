# Contrato — `GET/PUT /bedrock/sections/{id}` tras el retiro de `section` (spec 005)

Feature 005. Enmienda `.harness/specs/004-herramientas-metodologias-por-seccion/contracts/sections.md`.

## GET `/bedrock/sections/{section_id}` — respuesta `200`

Igual que en 004 **salvo** el array `methodologies`:

```json
{
  "section_id": "sec-32",
  "system_name": "career-projects",
  "label": "Proyectos",
  "section_type": "table",
  "resource_key": "projects",
  "agent_profile_id": "agent_professional_identity",
  "derived_tools": ["..."],
  "methodology_ids": ["opm-29", "opm-33"],
  "methodologies": [ { "id": "opm-29", "title": "Proceso 5 - Portafolio" } ]
}
```

- Item de `methodologies`: `{ id, title }` — **sin** `section` (RF-016).
- `404` si `section_id` no es una sección conocida.
- Verificado: `SectionMethodologiesEditor` (Admin) sólo consume `id` y `title` →
  sin regresión (RF-010).

## PUT `/bedrock/sections/{section_id}/methodologies`

Sin cambio de request (`{ "methodology_ids": ["opm-29", ...] }`) ni de código de
estado. La respuesta es el mismo shape de `GET` (con `methodologies:[{id,title}]`).
Internamente el reindex final se delega en
`methodology_scope.reindex_user_methodologies` (camino único, plan.md §1.2) — sin
efecto observable en el contrato.

## `PUT /career/operational-methodologies/{id}` — efecto nuevo (hook)

Cuando el body incluye `section_ids`, tras persistir se dispara un `reindex_for_user`
**completo** del índice de conocimiento del usuario (no sólo la re-vectorización del
registro). No cambia el body ni la respuesta (`200` con
`OperationalMethodologyResponse`). Fallo de Qdrant → best-effort, el `200` se mantiene
(RF-031).
