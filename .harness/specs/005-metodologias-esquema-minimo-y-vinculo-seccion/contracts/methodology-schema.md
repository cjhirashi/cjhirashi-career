# Contrato — esquema de `operational-methodologies` y error 422 (spec 005)

Feature 005. Referencia humana; el gate no ancla OpenAPI todavía.

## Esquema tras el retiro de campos

`OperationalMethodologyBase` (heredan `Create`, `Response`):

| Campo | Tipo | Nulabilidad |
|---|---|---|
| `title` | `str` (≤255) | requerido |
| `description` | `str \| null` | opcional |
| `content` | `str` | requerido (`NOT NULL`) |
| `agent_profile_ids` | `list[str] \| null` | opcional — ids `agent_*`, sólo L1/L3 (spec 004) |
| `section_ids` | `list[str] \| null` | opcional — ids `sec-N`, `⊆ known_section_ids()` |

`OperationalMethodologyResponse` añade `id`, `user_id`, `created_at`, `updated_at`.
`Response` **no** valida `agent_profile_ids`/`section_ids` (un registro con ids
obsoletos debe seguir siendo legible).

**Retirados** (ya no son campos, `DROP COLUMN` en migración): `section`, `subsection`,
`notes`.

## `extra="forbid"`

`model_config = ConfigDict(extra="forbid")` en `Base` y `Update`. Cualquier clave no
listada arriba → error de validación. Aplica a `POST` y `PUT`
`/career/operational-methodologies[/{id}]`.

## Respuesta de error — 422 RFC 9457 (`application/problem+json`)

```
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/problem+json
```
```json
{
  "type": "about:blank",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "Error de validación",
  "errors": [
    {"type": "extra_forbidden", "loc": ["body", "section"], "msg": "Extra inputs are not permitted", "input": "..."}
  ]
}
```

- `errors` es un miembro de extensión: se conserva el array de `RequestValidationError.errors()`
  para no romper clientes que ya lo leen.
- `section_ids` con un `sec-N` inexistente → mismo 422; `errors[].msg` contiene
  `"section_ids desconocidos: [...]"`.

## Path tool L2 (`create_career_record` / `update_career_record`)

No es HTTP; la tool devuelve al agente:

```json
{ "error": "Unknown field(s) ['notes', 'section'] for this resource.",
  "valid_fields": ["agent_profile_ids", "content", "description", "section_ids", "title"] }
```
o, para `sec-N` inexistente en `fields.section_ids`:
```json
{ "error": "section_ids desconocidos: ['sec-99']" }
```
En ambos casos **no se persiste nada**.
