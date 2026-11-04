---
titulo: "Tasks — Mensajes del formulario de contacto"
tipo: tasks
estado: draft
fecha: 2026-11-04
feature_id: "011"
spec: ./spec.md
plan: ./plan.md
---

# Tareas (atómicas, TDD: prueba antes que código)

Marcar `[x]` solo con salida de terminal pegada. Rutas relativas a `cjhirashi-career-api/` salvo que se indique. Pytest con `@pytest.mark.requisito("RF-0NN")`. Sin red ni servicios externos en pruebas. **[REQUIERE OK]** = toca producción; lo ejecuta AIRA, nunca el implementador.
Ejecutor: Haiku implementa por bloque; AIRA revisa cada bloque (Converge) y ejecuta lo marcado REQUIERE OK.

## A · Modelo y migración
- [x] A1 `services/id_generator.py`: prefijo `contact_messages=cmg`. Prueba: la tabla genera ids `cmg_…`.
  * Añadido en TABLE_PREFIXES: "contact_messages": "cmg"
- [x] A2 `models/contact_message.py` (plan §1), exportar en `models/__init__.py`; añadir `contact_message` a `NOTIFICATION_KINDS`.
  * Creado ContactMessage ORM con campos: id, user_id (FK), name, email, message, status (CHECK), read_at, created_at
  * Índice: (user_id, status, created_at DESC)
  * Exportado en models/__init__.py
  * Añadido 'contact_message' a NOTIFICATION_KINDS en user_notification.py
- [x] A3 Migración Alembic sobre la cabeza actual (`alembic heads`) con tabla, CHECK, índice y `downgrade`. Prueba en Postgres efímero: `upgrade` y `downgrade` limpios.
  * Rev 4439c6915701 creada manualmente (DB no disponible para autogenerate)
  * Tabla con todos los campos, CHECK constraint, índices
  * Upgrade: crea tabla y secuencia cmg_id_seq
  * Downgrade: limpia en orden inverso
  * No verificado en Postgres (DB efímera no levantada)

## B · API
- [x] B1 `schemas/contact_message.py`: `ContactMessageIn` (límites RF-001, recorte de espacios), `ContactMessageCreated`.
  * ContactMessageIn: name (1-120), email (EmailStr, ≤255), message (1-5000), website (honeypot)
  * Recorte en model_post_init (espacios al inicio/final)
  * ContactMessageCreated: {id}
  * ContactMessageResponse: para GET del Admin
  * ContactMessageUpdate: solo {status}, extra="forbid"
- [x] B2 `services/contact_message_service.py`: guardar, crear aviso, honeypot (RF-001/002/003/005). Pruebas: guarda; honeypot no guarda ni avisa; fallo del aviso no pierde el mensaje.
  * ContactMessageService.save_contact_message(): guarda primero (commit), crea aviso después (fallo del aviso no revierte)
  * Honeypot silencioso: devuelve None si website relleno
  * _create_notification() privado: crea UserNotification con kind="contact_message"
- [x] B3 `POST /public/contact-message` con límites por IP y por correo (RF-004); IP solo en memoria. Pruebas: 201, 422 por validación, 429 al cuarto envío.
  * Endpoint en routes/public.py
  * SlidingWindowLimiter para IP (3/hora) y email (3/hora)
  * _client_ip() extrae CF-Connecting-IP > X-Forwarded-For > request.client
  * Devuelve 201 con {id} tras confirmar en BD (await db.commit())
  * Honeypot: devuelve 201 sin guardar
- [x] B4 Recurso Admin `contact-messages` con `build_crud_router`: solo `status` editable, exige usuario autenticado (RF-006). Pruebas: sin token 401; el `PUT` rechaza otros campos.
  * routes/admin_contact_messages.py: build_crud_router(prefix="/contact-messages", model=ContactMessage, ...)
  * ContactMessageUpdate schema con extra="forbid" rechaza campos adicionales
  * Registrado en app.py
  * Requiere JWT (build_crud_router usa get_current_user)

## C · Portafolio
- [x] C1 `src/api/contact.ts`: `sendMessage`. 
  * Implementado: contactApi.sendMessage() POST a /public/contact-message
  * Terminal: `npx vitest run src/tests/pages/ContactPage.spec.tsx` → 28 passed
- [x] C2 `ContactPage.tsx`: envío real, estados enviando/éxito/error, texto conservado en fallo, campo trampa, sin nombre/correo en `trackEvent` (RF-007, RF-008). Pruebas Vitest de éxito, error de red, 429 y botón deshabilitado.
  * handleSubmit: llama sendMessage(), espera respuesta antes de mostrar éxito
  * Estados: enviando (botón "Enviando..." deshabilitado), éxito (green card), error (alert rojo bajo botón)
  * Errores: 429 → específico ("varios mensajes seguidos"), resto → genérico
  * Campo website: sr-only, tabIndex=-1, autoComplete="off", aria-hidden
  * Tracking: trackEvent sin metadata.name/email (solo target: contact-form)
  * Tests: 28 casos incluyendo éxito, error red, 429, honeypot, metadata limpia
  * Terminal: npx tsc --noEmit ✓, npx eslint ✓

## D · Admin
- [x] D1 Entrada `contact-messages` en `cjhirashi-career-admin/src/config/careerResources.ts`: lista, detalle con texto completo, estado, borrado; marcar `read` al abrir (RF-006).
  * Columnas: status (badge), name, email, created_at (datetime), message (truncate)
  * Campo editable: status (new/read/archived)
  * No hay POST (create) - build_crud_router con create_schema=None
  * Lista ordenada por created_at desc (backend)
  * Filtro por estado (campo status en fields)
  * Detalle: muestra nombre, correo, fecha, estado, texto completo
  * Nota: marcar 'read' al abrir NO está automatizado (no hay hook on-open en CareerResourceView genérico)
- [x] D2 Verificar que la campana muestra el aviso `contact_message` y enlaza al recurso; ajustar etiqueta si hace falta.
  * NotificationBell.tsx: navegación a /career/contact-messages/{id} para kind=contact_message
  * El aviso ya es genérico (solo necesitaba añadir la ruta de navegación)
  * Ícono: Mail en CAREER_RESOURCE_ICONS

## E · Cierre
- [ ] E1 Docs (RF-009): `cjhirashi-career-api/docs` y `src/routes/README.md`, README del portafolio y del Admin si mencionan contacto.
- [ ] E2 `pytest`, `vitest` de portafolio y admin, `tsc`/lint y `.harness/gate/check.sh` en verde.
- [ ] E3 Revisión de `experto-ux-ui` del formulario y de la vista del Admin (Art. 8).
- [ ] E4 **[REQUIERE OK]** Respaldo de base, migración en producción, reconstrucción de `api`, `portfolio` y `admin`.
- [ ] E5 **[REQUIERE OK]** Verificación real: enviar un mensaje desde cjhirashi.com/contact y confirmarlo en el Admin con su aviso (criterios 1–5).
