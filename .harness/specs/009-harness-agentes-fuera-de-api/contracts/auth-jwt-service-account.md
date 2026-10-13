---
titulo: "Contrato de autenticación Admin → harness → API (spec 009)"
tipo: contrato
feature_id: "009"
fecha: 2026-10-13
---

# Autenticación compartida, claim `role` y rol `service`

Decisiones: D-09 (JWT compartido), D-17 (rol `service`), D-18 (claim `role`), RF-018/019.

Hechos verificados (2026-10-13): el JWT lo firma la API (`AuthService._create_token`,
HS256, `SECRET_KEY`); hoy el payload es `{"sub", "exp"}` (+ `"type": "refresh"`; `owner_id`
opcional en tokens de agente) y **no lleva rol**. `middleware/auth.get_current_user` valida
firma, busca al usuario, exige `is_active` y, si `access_role == "agent"`, limita a `/career/*`
y devuelve al **dueño** (`owner_id` o `PUBLIC_PORTAL_USER_ID`).

## 1. Claim `role` (RF-019)

- Toda emisión de token de la API (`_create_token`, login, refresh, tokens de agente y de
  servicio) añade `"role": "user" | "agent" | "service"`, derivado de `access_role` del
  usuario (`user` por defecto).
- **Compatibilidad:** un token válido **sin** claim `role` se trata como `user` en API y
  harness (tokens emitidos antes del despliegue siguen funcionando hasta su expiración).
  Un valor de `role` desconocido → 401.
- El claim es informativo para el harness; la API **sigue** consultando al usuario en BD y
  su `access_role` (fuente de verdad); si el claim y la BD discrepan, manda la BD.
- Se descarta `GET /auth/session` (D-18).

## 2. Entrada Admin → harness (RF-002, D-09)

1. El Admin envía el mismo `Authorization: Bearer <access_token>`.
2. `cjhirashi-career-ai/src/middleware/auth.py` decodifica con `SECRET_KEY` + `ALGORITHM`
   compartidos (misma variable, un solo `.env`). Falla → **401** sin procesar el cuerpo:
   firma inválida, `exp` vencido, `type == "refresh"`, `sub` ausente, `role` desconocido.
3. `role == "agent"` o `role == "service"` → **403** en las rutas de chat y gestión
   (D-14: los tokens de agente y de servicio no usan el chat). Sin claim = `user`.
4. Pone `Principal(user_id=sub, token)` en `contextvars`.
5. Limitación aceptada: el harness no consulta la BD de usuarios (no hay `is_active` en el
   JWT). Un usuario desactivado conserva acceso al harness hasta la expiración del access
   token (corta duración), mientras que la API lo rechaza en cada llamada; **las acciones
   del harness sobre datos pasan siempre por la API con ese mismo token**, así que no
   obtienen datos de un usuario inactivo. Registrado en el plan (riesgo R6).

## 3. Salida harness → API (RF-004, D-09)

| Origen de la acción | Credencial hacia la API | Dónde se decide |
|---|---|---|
| Petición de un usuario (chat, `POST /agent-tasks/{id}/run`, catálogo) | **JWT del usuario**, reenviado tal cual | `clients/api_client.py` toma `Principal.token` del contexto |
| Tarea programada (`task_scheduler`, sin sesión) | **Cuenta de servicio**: `AI_SERVICE_TOKEN` (`role: service`) | `ServiceContext` explícito al arrancar el runner; nunca por defecto |

- `ApiClient` NO tiene credencial por defecto: sin `Principal` ni `ServiceContext` lanza
  `MissingCredentialError` (test).
- Las delegaciones L1→L2/L3 y subtareas heredan el contexto de credencial del turno.
- Una tarea cuyo `user_id` ≠ dueño efectivo de la cuenta de servicio se marca `failed` con
  error explícito.

## 4. Rol `service` (D-17, RF-018)

- Usuario con `access_role = "service"` y `owner_id` = dueño del portafolio. Se genera
  **fuera de banda** por el operador (no se versiona) y se entrega al harness como
  `AI_SERVICE_TOKEN` en `.env`. Procedimiento en `docs/ENVIRONMENT-SECURITY.md`. Distinto del
  token `agent` del agente externo (se revocan por separado).
- **Lista explícita de rutas permitidas** (en la API, `middleware/auth.py`, constante
  `SERVICE_ALLOWED_PREFIXES`): `/career/*`, `/files`, `/pdf-templates`, `/pdf-template-styles`,
  `/linkedin`, `/admin/sections`, `/settings/error-reports`, `/notifications` y `/audit-log`
  (literal; hoy la ruta es `/bedrock/audit-log` y pasa a `/audit-log` por RF-021; ver
  `harness-api-dependencies.md`). Cualquier otra → **403**.
- `POST /notifications` (RF-020): **sólo** `role == service` (usuario/agent → 403).
- El token `agent` sigue limitado a `/career/*`; pierde `POST /bedrock/chat`.
- Esta lista debe confirmarse contra las tools reales en la implementación (Fase 3): si una
  tool programada necesita otra ruta, se añade a la lista con cambio de spec, no en silencio.

## 5. Pruebas del contrato

| Capa | Prueba |
|---|---|
| ai/middleware | sin header, firma inválida, expirado, refresh, `role` desconocido → 401; `role` agent/service → 403; sin claim → user; token válido → `Principal`; **sin llamada a la API** |
| ai/clients | usuario → API recibe el mismo bearer; scheduler → `AI_SERVICE_TOKEN`; sin contexto → `MissingCredentialError` |
| ai/e2e | JWT real firmado con secreto de prueba contra API simulada (`httpx.MockTransport`) |
| api/auth | tokens emitidos llevan `role` correcto; token sin claim = user; claim desconocido → 401; discrepancia claim/BD manda la BD |
| api/middleware | `agent`: `/career/*` 200, todo lo demás 403; `service`: cada prefijo de la lista 200 y rutas fuera (p. ej. `/auth/*` de gestión, `/users`) 403; `POST /notifications` sólo `service` |
