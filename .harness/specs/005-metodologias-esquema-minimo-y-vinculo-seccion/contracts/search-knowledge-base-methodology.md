# Contrato — extractos de `search_knowledge_base type=methodology` (spec 005)

Feature 005. Enmienda el shape que fijó **spec 003 RF-016** (Bloque J).

## Antes (003)

```json
{ "record_id": "opm-61", "title": "…", "section": "Búsqueda de empleo",
  "score": 0.42, "shared": false, "excerpt": "…", "read_full": "get_career_record …" }
```

## Después (005)

```json
{ "record_id": "opm-61", "title": "…", "sections": ["Búsqueda de empleo", "Networking"],
  "score": 0.42, "shared": false, "excerpt": "…",
  "read_full": "get_career_record resource_key=operational-methodologies record_id=opm-61" }
```

- `section` (string, texto libre) → **eliminado**.
- `sections` (array de strings): labels resueltos de `section_ids` del payload Qdrant
  (`sec-N` → `get_section_spec(sec_id).label`).
- `sec-N` presente en el payload pero desconocido en el catálogo en código → **omitido**
  de `sections` (RF-030), sin error.
- `section_ids` vacío → `sections: []`.

## Payload Qdrant de la metodología (origen de `sections`)

`extra_payload` en `CareerRepository._index_for_search` para
`resource_type == "methodology"`:

```json
{ "agent_profile_ids": ["agent_networking"], "section_ids": ["sec-5", "sec-8"], "title": "…" }
```

- `section` **eliminado** del payload.
- `section_ids`: los `sec-N` **crudos** (sin resolver a label) — RF-013.

## Parseo de prefijos del `excerpt`

`_methodology_snippet` salta las líneas de metadatos al inicio del `text` embebido.
Tupla de prefijos: `("title:", "section_ids:", "description:", "agent_profile_ids:")`
— sin `section:` ni `subsection:` (RF-026), alineada con lo que `_record_to_text`
emite tras el `DROP COLUMN`.
