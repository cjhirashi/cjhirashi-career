# ADR-024: El sidebar contextual del Admin lo gobierna la sección

## Estado

Aceptado — 2026-09-04

Enmienda [ADR-020](./020-admin-section-templates.md) y
[ADR-021](./021-admin-sections-synthetic-pk.md) en lo relativo al override editable
de las secciones del Admin. Implementado por la feature `001-sidebar-contextual-por-seccion`
(`.harness/specs/`).

## Contexto

Cada pantalla del Admin Panel tiene un **sidebar derecho** con dos pestañas: el
**chat contextual** (Agent Bedrock) y las **instrucciones de la pantalla**. Hasta
ahora:

- El **agente del chat contextual** se *derivaba* del "agente con dominio" de la
  sección: si ese agente era user-facing (L1/L2) se usaba tal cual; si era un L3 (sin
  chat) se caía a un L2 por una tabla fija en código (`_L3_CHAT_FALLBACK` en
  `services/admin_sections.py`). El operador no podía elegir ese agente.
- Las **instrucciones** por vista (`sidebar_body` de cada `AdminViewSpec`) eran texto
  plano, sin formato.
- El sidebar se mostraba **siempre**, aunque su contenido no aportara nada.
- Las secciones tenían además un override editable de **descripción** que sólo se
  usaba en la ficha del catálogo.

El operador quería poder **asignar explícitamente** el agente L2 del chat de cada
sección y **redactar las instrucciones en Markdown**, y que el sidebar desapareciera
cuando no hay ni chat ni instrucciones.

## Decisión

**La fila de una sección en "Secciones del Admin" (`/settings/sections`) gobierna su
sidebar derecho.**

1. **Agente L2 del chat contextual = `agent_profile_id` de la sección.** El campo se
   reinterpreta: ya no es "agente con dominio con derivación", es directamente el
   agente que atiende el chat del sidebar. El selector ofrece **sólo agentes de nivel
   2** más "sin agente". `NULL` = la sección no tiene chat contextual.
2. **Se retiran `chat_agent_id()` y `_L3_CHAT_FALLBACK`.** El turno de chat
   `contextual` resuelve el perfil desde el catálogo de secciones
   (`resolve_profile_for_turn`): agente L2 de la sección de la ruta si lo hay; si la
   sección no tiene agente, o la ruta no hace match con ninguna sección, **degrada al
   orquestador** (L1). Nunca lanza.
3. **`sidebar_body` por vista se renderiza como Markdown** (GFM, sin HTML embebido —
   sin `rehype-raw`). Se conserva `sidebar_title` como texto plano. El override tiene
   3 estados por sub-campo: heredar (sin override), texto explícito, y **vacío
   explícito (`""`)** — que oculta la pestaña de instrucciones.
4. **Visibilidad del sidebar derecho:**
   - sin agente L2 → sin pestaña de chat;
   - vista sin instrucciones efectivas → sin pestaña de instrucciones;
   - ambas ausentes → no se renderiza el panel ni su botón.
5. **Se elimina el override editable de `description`** de la sección (columna
   `admin_section_overrides.description`, migración `c4d5e6f7a8b9`). El registro de
   código conserva la descripción de cada sección para el catálogo; el propósito de
   "contexto de la pantalla" lo cubren las instrucciones del sidebar. Gana espacio
   vertical el área de trabajo.
6. **El re-mapeo de los defaults de código.** Las 11 secciones que apuntaban a un
   agente L1/L3 pasan a un L2 o a `NULL` (en el registro `_SECTIONS`):

   | Sección | Antes | Ahora |
   |---|---|---|
   | Dashboard, Métricas, Costo y Uso, Archivos, Tareas, Chat General | orquestador / L3 | `NULL` (sin chat contextual) |
   | LinkedIn · Publicar | `agent_linkedin_publishing` (L3) | `agent_digital_presence` (L2) |
   | Descubrir vacantes | `agent_vacancy_search` (L3) | `agent_search_operations` (L2) |
   | Memoria, Instrucciones, Herramientas | orquestador (L1) | `agent_configuration` (L2) |

7. **`set_agent_sections`** (editor "secciones que gestiona este agente" del catálogo
   de agentes) también rechaza un `profile_id` que no sea L2: el agente de una sección
   es L2-only en todas las superficies que lo escriben.

### Por qué reutilizar el campo y no añadir uno nuevo

El operador confirmó que el L2 dueño de un área **es** el que atiende su chat
contextual. Un `sidebar_agent_profile_id` separado duplicaría el concepto sin ganancia.

### Por qué sin siembra en la migración

Sembrar la DB con el texto de instrucciones de código exigía congelar ~130 bloques de
texto en el archivo de migración (que no puede importar código de la app) y dejaba los
defaults de código inertes tras migrar. El texto por defecto sigue viniendo del
registro de código en runtime; el "vacío explícito" da el control de ocultar la
pestaña sin siembra.

## Consecuencias

### Positivas

- El operador controla, por sección y desde una sola pantalla, qué agente L2 atiende
  el chat y qué instrucciones (Markdown) muestra el sidebar.
- El sidebar deja de ocupar espacio en pantallas donde no aporta.
- Menos código mágico: se va la tabla de fallback L3→L2 y la derivación.
- Un campo menos que mantener (`description` de override).

### Negativas / a vigilar

- Las secciones sin agente L2 asignado (Dashboard, Métricas, Archivos, Tareas, Chat
  General, Costo y Uso) pierden el chat contextual hasta que el operador les asigne un
  L2. Es el comportamiento buscado.
- `AdminSectionItem` cambia de forma (fuera `chat_agent_profile_id`, `description`,
  `description_is_default`; dentro `sidebar_has_chat`, `sidebar_has_instructions`).
  Consumidores: Admin SPA y la tool Bedrock `admin_section_settings`.
- Deploy: la migración `c4d5e6f7a8b9` **no** corre en `init_db`; hay que
  `alembic upgrade head` tras el rebuild.
