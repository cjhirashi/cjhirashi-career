---
titulo: "Plan 011 — Mensajes del formulario de contacto"
tipo: plan
estado: draft
fecha: 2026-11-04
feature_id: "011"
spec: ./spec.md
---

# Plan 011 — Mensajes del formulario de contacto

## 0 · Decisiones de diseño
1. **Guardar primero, avisar después.** La fila de `contact_messages` se confirma (commit) antes de crear el aviso; el aviso va en el mismo commit solo si no añade riesgo, y si falla se registra y no revierte el mensaje (RF-005). Ningún mensaje se pierde por un fallo secundario.
2. **Reutilizar patrones existentes**, sin infraestructura nueva: `SlidingWindowLimiter` (`services/portal_ratelimit.py`) para el límite; `_client_ip` y la lógica de CF-Connecting-IP de `routes/events.py` (extraer a helper compartido si hace falta, sin duplicar); `build_crud_router` + `register_resource` para el recurso del Admin; `UserNotification` para la campana.
3. **IP solo en memoria** (RF-002, RF-004); no hay columna ni log con IP.
4. **Honeypot silencioso** (RF-003): campo `website`; el frontend lo renderiza oculto con `tabIndex=-1` y `autoComplete="off"`.
5. **Aislamiento:** `user_id = settings.PUBLIC_PORTAL_USER_ID`, igual que el resto de `/public`.

## 1 · Esquema
Prefijo de id `cmg` en `services/id_generator.TABLE_PREFIXES` (`contact_messages=cmg`).

### contact_messages
`id` (String(20), PK), `user_id` (FK users, CASCADE, índice), `name` (String 120), `email` (String 255), `message` (Text), `status` (String 20, default `new`, CHECK en `new|read|archived`), `read_at` (timestamptz nullable), `created_at` (timestamptz, default now). Índice `(user_id, status, created_at DESC)`.

`NOTIFICATION_KINDS` en `models/user_notification.py` pasa a `("task_turn", "contact_message")`.

## 2 · API
- `POST /public/contact-message` en `routes/public.py` (o `routes/contact_messages.py` incluido bajo `/public`), esquema `ContactMessageIn` (Pydantic, `EmailStr` si ya está en dependencias, si no regex simple) y `ContactMessageCreated {id}`. Lógica en `services/contact_message_service.py`.
- Recurso Admin `contact-messages` vía `build_crud_router` (list/get/update/delete; sin POST desde Admin): el `PUT` solo admite cambiar `status`. Marcado `read` al abrir lo hace el Admin llamando a `PUT`.
- Registrar el recurso donde se registran los demás (`register_resource`, `app.py`) con `vectorize=False`.

## 3 · Portafolio
- `src/api/contact.ts`: `sendMessage(payload)` → `POST /public/contact-message`.
- `ContactPage.tsx`: estado `error`, `await` real, no limpiar el formulario hasta el 201, campo trampa, quitar `metadata` con nombre/correo del `trackEvent` (RF-007, RF-008).
- Pruebas Vitest actualizadas en `ContactPage.spec.tsx`.

## 4 · Admin
- Entrada `contact-messages` en `src/config/careerResources.ts` (columnas: estado, nombre, correo, fecha; detalle con el texto completo; acciones estado/borrado). El framework de recursos no tenía soporte para recursos que otro proceso escribe: se añaden a `ResourceConfig` tres opciones genéricas (`canCreate`, `readOnlyFields`, `markOnOpen`) y `build_crud_router` acepta `create_schema=None` para omitir `POST`. La campana ya muestra cualquier `kind`; se añade el enlace para `resource_key="contact-messages"`.

## 5 · Despliegue y verificación
Migración con respaldo previo de la base (**REQUIERE OK** de Carlos: toca producción; lo ejecuta AIRA). Reconstruir imágenes `api`, `portfolio` y `admin` con el procedimiento de `docker-compose.yml`. Verificación: enviar un mensaje real desde `https://cjhirashi.com/contact` y verlo en el Admin.
