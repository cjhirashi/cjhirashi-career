# Carrera — Metodologías Operativas

Metodologías de trabajo documentadas, indexadas en Qdrant para que el agente las consulte semánticamente.

**Prefijo:** `/career/operational-methodologies`  
**Tag OpenAPI:** `Career - Methodologies`  
**Auth:** JWT requerido

## Arquitectura

```mermaid
flowchart LR
    Admin[Admin Panel] --> Route[routes/career_methodologies.py]
    Route --> Factory[build_crud_router]
    Factory --> Schema[schemas/career_methodologies.py]
    Factory --> Repo[CareerRepository]
    Repo --> Model[operational_methodology]
    Model --> PG[(PostgreSQL)]
    Repo -->|vectorize| Qdrant[(Qdrant)]
    Agent[search_knowledge_base] --> Qdrant
```

---

## Archivos fuente

| Capa | Archivo |
|------|---------|
| Rutas | `src/routes/career_methodologies.py` |
| Schemas | `src/schemas/career_methodologies.py` |
| Modelo | `src/models/operational_methodology.py` |

---

## Recurso (1)

| Resource key | Path | Modelo |
|--------------|------|--------|
| `operational-methodologies` | `/career/operational-methodologies` | `OperationalMethodology` |

CRUD estándar de 6 endpoints. **`vectorize=True`** — cada write indexa en Qdrant.

---

## Campos típicos

| Campo | Descripción |
|-------|-------------|
| `title` | Nombre de la metodología |
| `section` | Agrupación (ej. "Identidad Profesional", "Diseño PDF") |
| `subsection` | Subagrupación opcional |
| `description` | Resumen corto |
| `content` | Texto Markdown de la metodología |
| `agent_profile_ids` | Lista de ids `agent_*` destinatarios. Vacío o `null` = todos los agentes |
| `notes` | Notas internas |

---

## Agente Bedrock

Perfil **`methodologies`** — especializado en consultar y editar metodologías.

Tool principal: `search_knowledge_base` con `type=methodology` para búsqueda semántica.

El Admin Panel muestra metodologías por sección. El campo `agent_profile_ids` es la fuente de verdad de **qué agente consulta qué metodología**:

- Lista con ids `agent_*` → solo esos agentes la asumen como suya.
- Vacío o `null` → compartida (todos los agentes).
- El L2 `agent_methodologies` ve y mantiene todas.

Cada turno, `compose_system_prompt` inyecta el catálogo asignado al caller. Si Carlos crea una metodología nueva y se la asigna a un agente **desde el catálogo de agentes** (`/agent/catalog`) o desde esta tabla (campo Agentes), ese agente la consulta en el siguiente mensaje — no hace falta nombrarla en código.

`search_knowledge_base` (type=methodology) filtra por el mismo campo.

---

## Ejemplo

```bash
curl -s "http://localhost:8001/career/operational-methodologies?search=STAR&limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

Ver también: [bedrock](../bedrock/README.md) (memoria Qdrant)
