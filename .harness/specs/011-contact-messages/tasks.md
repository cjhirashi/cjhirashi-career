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
- [ ] A1 `services/id_generator.py`: prefijo `contact_messages=cmg`. Prueba: la tabla genera ids `cmg_…`.
- [ ] A2 `models/contact_message.py` (plan §1), exportar en `models/__init__.py`; añadir `contact_message` a `NOTIFICATION_KINDS`.
- [ ] A3 Migración Alembic sobre la cabeza actual (`alembic heads`) con tabla, CHECK, índice y `downgrade`. Prueba en Postgres efímero: `upgrade` y `downgrade` limpios.

## B · API
- [ ] B1 `schemas/contact_message.py`: `ContactMessageIn` (límites RF-001, recorte de espacios), `ContactMessageCreated`.
- [ ] B2 `services/contact_message_service.py`: guardar, crear aviso, honeypot (RF-001/002/003/005). Pruebas: guarda; honeypot no guarda ni avisa; fallo del aviso no pierde el mensaje.
- [ ] B3 `POST /public/contact-message` con límites por IP y por correo (RF-004); IP solo en memoria. Pruebas: 201, 422 por validación, 429 al cuarto envío.
- [ ] B4 Recurso Admin `contact-messages` con `build_crud_router`: solo `status` editable, exige usuario autenticado (RF-006). Pruebas: sin token 401; el `PUT` rechaza otros campos.

## C · Portafolio
- [ ] C1 `src/api/contact.ts`: `sendMessage`. 
- [ ] C2 `ContactPage.tsx`: envío real, estados enviando/éxito/error, texto conservado en fallo, campo trampa, sin nombre/correo en `trackEvent` (RF-007, RF-008). Pruebas Vitest de éxito, error de red, 429 y botón deshabilitado.

## D · Admin
- [ ] D1 Entrada `contact-messages` en `cjhirashi-career-admin/src/config/careerResources.ts`: lista, detalle con texto completo, estado, borrado; marcar `read` al abrir (RF-006).
- [ ] D2 Verificar que la campana muestra el aviso `contact_message` y enlaza al recurso; ajustar etiqueta si hace falta.

## E · Cierre
- [ ] E1 Docs (RF-009): `cjhirashi-career-api/docs` y `src/routes/README.md`, README del portafolio y del Admin si mencionan contacto.
- [ ] E2 `pytest`, `vitest` de portafolio y admin, `tsc`/lint y `.harness/gate/check.sh` en verde.
- [ ] E3 Revisión de `experto-ux-ui` del formulario y de la vista del Admin (Art. 8).
- [ ] E4 **[REQUIERE OK]** Respaldo de base, migración en producción, reconstrucción de `api`, `portfolio` y `admin`.
- [ ] E5 **[REQUIERE OK]** Verificación real: enviar un mensaje desde cjhirashi.com/contact y confirmarlo en el Admin con su aviso (criterios 1–5).
