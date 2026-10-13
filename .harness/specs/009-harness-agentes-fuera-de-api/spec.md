---
titulo: "Harness de agentes fuera de la API (cjhirashi-career-ai) y sin indexación"
tipo: spec
estado: draft
fecha: 2026-10-13
feature_id: "009"
anchor_mode: advisory
anchor_commit: null
covers:
  - .harness/specs/009-harness-agentes-fuera-de-api/**
---

# Harness de agentes fuera de la API y sin indexación

## 1 · Contexto del dominio

**Problema:** la API de carrera (`cjhirashi-career-api`) mezcla dos responsabilidades:
el CRUD de datos de carrera (lo que consume el agente externo vía REST) y el *harness*
de agentes sobre AWS Bedrock (bucle de agente, perfiles, prompts, tools, delegación,
memoria, costes, generación de imágenes) más una base de conocimiento vectorial
(Qdrant) que se alimenta en cada escritura. La indexación gasta embeddings sin
consumidor real, y el harness acopla la API a un proveedor concreto.

**Objetivo:** la API queda como servicio de datos puro. El harness completo se traslada
a `cjhirashi-career-ai`, con su propia base de datos, una abstracción de proveedor de
modelos (Bedrock como primera implementación) y acceso a los datos de carrera **sólo**
vía la API REST. La indexación y Qdrant desaparecen. El Admin conserva todas sus
pantallas de agentes, pero habla directamente con `cjhirashi-career-ai`.

Inventario actual (solo lectura, 2026-10-13):
- API `services/bedrock/` (~7.8k líneas), `bedrock_service.py`, `qdrant_service.py`,
  `routes/bedrock.py`, `routes/bedrock_tasks.py`, `schemas/bedrock*.py`.
- 10 tablas `bedrock_*` (conversation, settings, task, usage_log, usage_round_log,
  custom_tool, agent_delegation, profile_photo, profile_prompt, profile_tool).
- Acoplamientos en `app.py`, `middleware/auth.py`, `career_repository.py` (hook de
  indexado, `_KB_EXCLUDED_COLUMNS`), `admin_sections`, `methodology_scope`,
  `section_catalog`, `task_scheduler`, `error_reporting`, `id_generator`,
  `pdf_template_styles`, `schemas/career_methodologies.py`.
- Infra: servicio `qdrant` en `docker-compose.yml`.
- Admin: `components/bedrock/*`, `SidebarRight`, páginas `Agent*`, partes de
  `AdminSectionsPage` y `TasksPage`.
- `cjhirashi-career-ai`: andamiaje ignorado por git, sin tests.

Revisa: ADR-025 (imágenes), specs 001–005 (agentes, metodologías por sección). → ADR nuevo.

## 2 · Alcance

### En alcance
- Versionar `cjhirashi-career-ai` en este monorepo (D-06) con su servicio en
  `docker-compose.yml`, reemplazando el andamiaje.
- Trasladar el harness completo a `cjhirashi-career-ai`: bucle, perfiles, prompts,
  tools, delegación, memoria, tareas programadas de agentes, uso/costes, generación de
  imágenes (D-05).
- Abstracción de proveedor de modelos con Bedrock como única implementación (D-05).
- BD propia del harness con sus migraciones; trasladar los datos de las 10 tablas
  `bedrock_*` y eliminarlas de `career_db` (D-02).
- Tools del harness que leen/escriben datos de carrera vía API REST (D-01).
- Admin: las pantallas y el chat de agentes llaman directo a `cjhirashi-career-ai` por
  una ruta pública nueva (D-03).
- Eliminar de la API todo lo de Bedrock, la KB, el hook de indexado y `qdrant_service`;
  eliminar el servicio y volumen `qdrant` (con snapshot previo) (D-04).

### Fuera de alcance
- Un segundo proveedor de modelos (specs posteriores).
- Cambios funcionales en las pantallas de agentes del Admin (sólo cambia a dónde llaman).
- Cambios en el CRUD de carrera, el Portfolio o el agente externo.
- Editar el bloque `cjhirashi_srv` de `caddy.json` o archivos de cjhirashi-srv.

## 3 · Fronteras y contratos

- **Admin → harness:** ruta pública `/ai/` → `cjhirashi-career-ai` dentro del servicio
  `admin` de nuestro bloque `servicios` de `caddy.json`, con SSE para el streaming del
  chat (D-08). Autenticación con el mismo JWT del Admin (secreto compartido) (D-09).
- **Harness → API:** REST; reenvía el JWT del usuario en acciones iniciadas por él y usa
  una cuenta de servicio para tareas programadas (D-09).
- **Metodologías y secciones** (`admin_sections`, `methodology_scope`,
  `section_catalog`): siguen siendo datos de la API; el harness las lee por REST (D-10).
- **Archivos** (imágenes generadas, adjuntos del chat, fotos de perfil): la API sigue
  siendo dueña de `file_upload` y MinIO; el harness sube y lee vía sus endpoints REST (D-12).
- **Corte por etapas** (D-11): 1) levantar el harness y copiar datos; 2) el Admin
  apunta a `/ai/`; 3) eliminar Bedrock/KB/Qdrant de la API. Cada etapa es desplegable y
  reversible por separado.

## 4 · Criterios de aceptación (EARS)

Pendiente de completar tras cerrar §3.

## 6 · Registro de decisiones y descartes

- **D-01 (usuario, 2026-10-13, Fase 1):** el harness accede a los datos de carrera
  sólo vía la API REST, como el agente externo. *Descartado:* conexión directa a
  `career_db` (vuelve a acoplar por la base).
- **D-02 (usuario, 2026-10-13, Fase 1):** BD propia del harness; los datos `bedrock_*`
  se exportan con el harness y luego se eliminan de `career_db`. *Descartado:* esquema
  aparte en `career_db`; conservar tablas sin uso.
- **D-03 (usuario, 2026-10-13, Fase 1):** el Admin llama directo a
  `cjhirashi-career-ai`; la API no conoce al harness. *Descartado:* la API como proxy.
- **D-04 (usuario, 2026-10-13, Fase 1):** se elimina la indexación y la KB por completo,
  y el contenedor/volumen Qdrant (snapshot previo). *Descartado:* que el harness
  conserve su propio índice.
- **D-05 (usuario, 2026-10-13, Fase 1):** todo lo de Bedrock (incluida la generación de
  imágenes) se aísla en el harness tras una abstracción de proveedor; sólo Bedrock se
  implementa en esta feature. *Descartado:* implementar ya un segundo proveedor.
- **D-06 (usuario, 2026-10-13, Fase 1):** `cjhirashi-career-ai` vive en este monorepo.
  *Descartado:* repositorio propio.
- **D-07 (usuario, 2026-10-13, Fase 1):** el Admin conserva todas sus pantallas de
  agentes; sólo se traslada el harness. *Descartado:* retirar la UI de agentes.
- **D-08 (usuario, 2026-10-13, Fase 1):** ruta `/ai/` en el servicio `admin` (mismo
  dominio, SSE). *Descartado:* subdominio propio (CORS y certificado aparte).
- **D-09 (usuario, 2026-10-13, Fase 1):** el harness valida el JWT del Admin (secreto
  compartido) y lo reenvía a la API; cuenta de servicio sólo para tareas programadas.
  *Descartado:* siempre cuenta de servicio (pierde quién originó la acción).
- **D-10 (usuario, 2026-10-13, Fase 1):** metodologías y secciones se quedan en la API;
  sólo salen las partes que referencian Bedrock. *Descartado:* moverlas al harness.
- **D-11 (usuario, 2026-10-13, Fase 1):** corte por etapas reversibles. *Descartado:*
  corte único con ventana de mantenimiento.
- **D-12 (usuario, 2026-10-13, Fase 1):** archivos vía endpoints de la API.
  *Descartado:* acceso propio del harness a MinIO.

## 7 · Requisitos no funcionales

- **RNF-001:** ninguna prueba llama a Bedrock reales; Qdrant deja de existir.
- **RNF-002:** backup de `career_db` y snapshot de Qdrant antes de migrar; toda
  operación sobre BD en vivo requiere OK explícito del usuario.
