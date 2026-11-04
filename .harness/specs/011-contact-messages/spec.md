---
titulo: "Formulario de contacto del portafolio: los mensajes llegan al Admin"
tipo: spec
estado: implemented
fecha: 2026-11-04
feature_id: "011"
anchor_mode: advisory
anchor_commit: null
covers:
  - .harness/specs/011-contact-messages/**
  - cjhirashi-career-api/src/models/contact_message.py
  - cjhirashi-career-api/src/models/user_notification.py
  - cjhirashi-career-api/src/schemas/contact_message.py
  - cjhirashi-career-api/src/routes/public.py
  - cjhirashi-career-api/src/routes/contact_messages.py
  - cjhirashi-career-api/src/services/contact_message_service.py
  - cjhirashi-career-api/alembic/versions/*contact_messages*.py
  - cjhirashi-career-api/tests/unit/test_contact_message*.py
  - cjhirashi-career-api/docs/**
  - cjhirashi-career-portfolio/src/pages/ContactPage.tsx
  - cjhirashi-career-portfolio/src/api/contact.ts
  - cjhirashi-career-portfolio/src/hooks/useContact.ts
  - cjhirashi-career-portfolio/src/tests/pages/ContactPage.spec.tsx
  - cjhirashi-career-admin/src/config/careerResources.ts
  - cjhirashi-career-admin/src/components/career/CareerResourceView.tsx
  - cjhirashi-career-admin/src/components/career/ResourceForm.tsx
  - cjhirashi-career-admin/src/components/NotificationBell.tsx
---

# Formulario de contacto del portafolio: los mensajes llegan al Admin

## 1 · Contexto

El formulario de `/contact` del portafolio público muestra «¡Mensaje enviado!» pero no envía nada: `handleSubmit` solo registra un evento de analítica (con nombre y correo en `metadata`, contra el principio de SPEC-0010 de no identificar personas) y descarta el texto del mensaje. No existe endpoint receptor, tabla ni canal de entrega. Detectado por Carlos el 2026-11-04 (no recibió ningún mensaje).

Decisión de Carlos (2026-11-04): por ahora la entrega es **solo en el Admin** (sin email ni Telegram).

## 2 · Alcance

### En alcance
- Endpoint público que recibe y guarda el mensaje.
- Tabla `contact_messages` con estado de lectura.
- Aviso en la campana del Admin y listado/gestión de mensajes en el Admin.
- El formulario del portafolio envía de verdad y solo muestra éxito si el servidor lo confirma.

### Fuera de alcance
- Entrega por email o Telegram (decisión posterior de Carlos; el modelo no lo impide).
- Responder desde el Admin.
- CAPTCHA externo (se usa campo trampa y límite de frecuencia).
- Adjuntos.

## 3 · Requisitos

- **RF-001** `POST /public/contact-message` (sin auth) acepta `name` (1–120), `email` (válido, ≤255), `message` (1–5000) y `website` (campo trampa, opcional). Recorta espacios. Devuelve 201 con `{id}` solo tras confirmar la escritura en base de datos.
- **RF-002** Cada mensaje se guarda en `contact_messages` ligado al dueño del portafolio (`PUBLIC_PORTAL_USER_ID`) con `status` (`new`, `read`, `archived`), `created_at`, `read_at`. No se guarda IP ni cabeceras.
- **RF-003** Si `website` viene con contenido, se responde 201 sin guardar ni avisar (el bot no aprende que fue detectado).
- **RF-004** Límite de frecuencia: 3 mensajes por hora por IP y 3 por hora por correo; el exceso devuelve 429 con mensaje comprensible. La IP solo vive en memoria para el límite (como en `/events/track`).
- **RF-005** Al guardar se crea un `UserNotification` (`kind="contact_message"`) para el dueño con título «Mensaje de {name}» y `resource_key="contact-messages"`. Si crear el aviso falla, el mensaje igual queda guardado y se responde 201 (se registra el fallo en logs).
- **RF-006** Admin: recurso `contact-messages` con listado paginado (más nuevos primero, filtro por estado), vista del mensaje completo, cambio de estado (`new`→`read`→`archived`) y borrado. Un mensaje nuevo se marca `read` al abrirlo (desde la lista o desde el aviso de la campana). Nombre, correo y mensaje se muestran pero no se editan. No hay botón «Nuevo». Solo el dueño autenticado accede.
- **RF-007** El formulario del portafolio llama al endpoint y espera la respuesta: muestra «¡Mensaje enviado!» solo con 201; con error de red, 429 o 5xx muestra un error claro, conserva lo escrito y permite reintentar; deshabilita el botón mientras envía.
- **RF-008** El evento de analítica `form_submit` del formulario deja de incluir nombre y correo (solo `target: contact-form`).
- **RF-009** README y docs del API, portafolio y Admin que describan el contacto quedan actualizados en el mismo commit (Art. 11).

## 4 · Criterios de aceptación

1. Un mensaje enviado desde `https://cjhirashi.com/contact` aparece en el Admin con su texto íntegro y dispara un aviso en la campana.
2. Con el API detenido, el formulario muestra error y no dice «enviado».
3. Un envío con `website` relleno devuelve 201 y no crea fila ni aviso.
4. El cuarto envío en una hora desde la misma IP devuelve 429.
5. Ninguna fila de `portal_events` nueva contiene nombre ni correo del formulario.

## 5 · UX (formulario y Admin)

Estados del formulario: reposo, enviando (botón deshabilitado, «Enviando...»), éxito (tarjeta actual), error (mensaje rojo bajo el botón, texto conservado). Admin: lista con insignia «Nuevo», vista de detalle con nombre, correo (texto, copiable), fecha en `America/Mexico_City` y texto completo respetando saltos de línea. Contraste WCAG AA; revisión de `experto-ux-ui` en Fase 4 (Art. 8).
