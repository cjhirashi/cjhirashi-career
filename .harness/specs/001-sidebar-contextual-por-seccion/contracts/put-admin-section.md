# Contrato — `PUT /admin/sections/{section_id}`

Recorte del contrato existente para la feature 001. Auth: `get_current_user` (JWT).
Sin `openapi.yaml` committeado — este archivo es la referencia humana y la base de los
tests de ruta (`tests/unit/test_admin_sections_update.py`).

## Request

Todos los campos opcionales. `application/json`.

```json
{
  "agent_profile_id": "agent_configuration",
  "views": {
    "main": {
      "sidebar_title": "Secciones del Admin",
      "sidebar_body": "## Qué hace esta pantalla\n\n- Asigna el **agente L2** ..."
    }
  }
}
```

Semántica:

| Campo | Valor | Efecto |
|---|---|---|
| `agent_profile_id` | ausente / `null` | no se toca el override de agente |
| `agent_profile_id` | `""` | borra el override → vuelve al `default_agent_profile_id` de código |
| `agent_profile_id` | id de agente **L2** | override; debe existir y ser `level == 2` |
| `views[k]` | `k` no es vista de la sección | se ignora esa clave |
| `views[k].sidebar_body` | ausente | ese sub-campo vuelve a heredar el texto de código |
| `views[k].sidebar_body` | `""` | override vacío explícito → la pestaña de instrucciones se oculta |
| `views[k].sidebar_body` | texto | override de texto (se renderiza como Markdown/GFM) |
| `views` | `{}` | borra todos los overrides de vistas de la sección |

`description` (de sección) **ya no se acepta**.

## 200 OK — `AdminSectionItem`

Ver `admin-section-item.schema.json`. Cambios vs. antes:
- **fuera:** `chat_agent_profile_id`, `description`, `description_is_default`.
- **dentro:** `sidebar_has_chat: bool`, `sidebar_has_instructions: bool`.
- `agent_profile_id` y `default_agent_profile_id` sólo pueden ser id de agente **L2** o `null`.
- `views[].sidebar_body` puede ser `""` (override vacío explícito).

## Errores — RFC 9457 (Problem Details, `application/problem+json`)

| HTTP | `title` | Cuándo |
|---|---|---|
| 404 | `Unknown admin section` | `section_id` no está en el registro de código |
| 400 | `Unknown agent profile` | `agent_profile_id` no existe |
| 400 | `Agent profile is not L2` | `agent_profile_id` existe pero `level != 2` |
| 422 | (validación FastAPI) | body no parseable / tipos inválidos |
