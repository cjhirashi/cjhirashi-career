---
titulo: "Harness de agentes fuera de la API (cjhirashi-career-ai) y sin indexación"
tipo: spec
estado: approved
fecha: 2026-10-13
feature_id: "009"
anchor_mode: advisory
anchor_commit: null
covers:
  - .harness/specs/009-harness-agentes-fuera-de-api/**
  - cjhirashi-career-ai/src/**
  - cjhirashi-career-ai/tests/**
  - cjhirashi-career-ai/alembic/**
  - cjhirashi-career-ai/scripts/**
  - cjhirashi-career-ai/README.md
  - cjhirashi-career-api/src/app.py
  - cjhirashi-career-api/src/config.py
  - cjhirashi-career-api/src/middleware/auth.py
  - cjhirashi-career-api/src/routes/auth.py
  - cjhirashi-career-api/src/routes/career_common.py
  - cjhirashi-career-api/src/routes/admin_sections.py
  - cjhirashi-career-api/src/repositories/career_repository.py
  - cjhirashi-career-api/src/services/agent_registry.py
  - cjhirashi-career-api/src/services/admin_sections.py
  - cjhirashi-career-api/src/services/methodology_scope.py
  - cjhirashi-career-api/src/services/section_catalog.py
  - cjhirashi-career-api/src/services/error_reporting.py
  - cjhirashi-career-api/src/services/id_generator.py
  - cjhirashi-career-api/src/schemas/career_methodologies.py
  - cjhirashi-career-api/src/schemas/admin_sections.py
  - cjhirashi-career-api/alembic/versions/*_drop_bedrock_tables.py
  - cjhirashi-career-api/tests/unit/test_bedrock_routes_removed.py
  - cjhirashi-career-api/tests/unit/test_drop_bedrock_tables_migration.py
  - cjhirashi-career-api/tests/unit/test_agent_registry_contract.py
  - cjhirashi-career-admin/src/api/client.ts
  - cjhirashi-career-admin/src/api/bedrock.ts
  - cjhirashi-career-admin/src/api/agentTasks.ts
  - cjhirashi-career-admin/vite.config.ts
  - cjhirashi-career-admin/src/tests/api/aiRoutes.test.ts
  - cjhirashi-career-admin/src/tests/api/noLegacyAgentRoutes.test.ts
  - cjhirashi-career-api/src/services/auth_service.py
  - cjhirashi-career-api/src/routes/notifications.py
  - cjhirashi-career-api/src/routes/files.py
  - cjhirashi-career-api/tests/unit/test_file_metadata_route.py
  - cjhirashi-career-api/src/routes/audit_log.py
  - cjhirashi-career-api/src/services/audit_service.py
  - cjhirashi-career-api/tests/unit/test_jwt_role_claim.py
  - cjhirashi-career-api/tests/unit/test_jwt_hardening.py
  - cjhirashi-career-api/tests/unit/test_notifications_route.py
  - cjhirashi-career-api/tests/unit/test_audit_log_routes.py
  - cjhirashi-career-api/docs/ARCHITECTURE.md
  - cjhirashi-career-api/docs/API.md
  - cjhirashi-career-api/docs/DATABASE.md
  - cjhirashi-career-ai/docs/MEMORY.md
  - docs/09-DECISIONS/README.md
  - docker-compose.yml
  - caddy.json
  - prometheus.yml
  - .env.example
  - docs/09-DECISIONS/029-harness-agentes-fuera-de-api.md
  - docs/BEDROCK-SYSTEM.md
  - docs/ENVIRONMENT-SECURITY.md
  - AGENTS.md
  - README.md
  - cjhirashi-career-api/docs/BEDROCK-HARNESS.md
  - cjhirashi-career-admin/docs/BEDROCK-CHAT.md
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
- 11 tablas `bedrock_*` (conversation, conversation_message, settings, task, usage_log, usage_round_log,
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
- BD propia del harness con sus migraciones; trasladar los datos de las 11 tablas
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

- **Paridad de contrato (D-13):** el harness expone bajo `/ai/` las mismas rutas
  relativas, cuerpos y respuestas que hoy `/bedrock/*` y `/agent-tasks/*`; el Admin sólo
  cambia la URL base.
- **Tokens `access_role = "agent"`** (agente externo): quedan limitados a `/career/*`;
  el permiso de `POST /bedrock/chat` desaparece con la ruta. La cuenta de servicio del
  harness es un token `agent` (D-14).

## 4 · Criterios de aceptación (EARS)

### Harness (`cjhirashi-career-ai`)
- **RF-001** El harness DEBE servir bajo `/ai/` todas las operaciones que hoy sirven
  `/bedrock/*` y `/agent-tasks/*` de la API, con el mismo contrato (D-13), salvo
  `POST /bedrock/knowledge-base/reindex` y `GET /bedrock/knowledge/search`, que se
  retiran (D-16).
- **RF-002** SI una petición al harness no trae un JWT válido de la API, ENTONCES el
  harness DEBE responder 401 sin procesarla.
- **RF-003** El harness NO DEBE conectarse a `career_db`; DEBE leer y escribir datos de
  carrera, metodologías, secciones y archivos sólo vía la API REST (D-01, D-10, D-12).
- **RF-004** CUANDO una acción la origina un usuario, el harness DEBE llamar a la API con
  el JWT de ese usuario; CUANDO la origina una tarea programada, DEBE usar la cuenta de
  servicio (D-09).
- **RF-005** El bucle de agente, las tools, los costes y la generación de imágenes DEBEN
  depender de una interfaz de proveedor de modelos; sólo la implementación Bedrock DEBE
  importar el SDK de AWS (D-05).
- **RF-006** El harness DEBE persistir conversaciones, perfiles, prompts, tools, tareas,
  delegaciones y uso/costes en su propia BD, con migraciones propias (D-02).
- **RF-007** La migración de datos DEBE copiar las 11 tablas `bedrock_*` de `career_db`
  a la BD del harness conservando identificadores, y DEBE reportar el conteo por tabla en
  origen y destino; SI algún conteo difiere, ENTONCES DEBE terminar con error.
- **RF-022** El harness DEBE guardar la memoria del agente (notas y hechos) en su BD con
  búsqueda de texto completo de Postgres, y la migración DEBE trasladar el contenido
  actual de la memoria desde Qdrant antes de eliminarlo (D-15).
- **RF-008** CUANDO llega una petición de chat con streaming, el harness DEBE emitirla
  por SSE a través de `/ai/` (D-08).

### API (`cjhirashi-career-api`)
- **RF-009** La API NO DEBE exponer `/bedrock/*` ni `/agent-tasks/*` (404).
- **RF-010** CUANDO se crea, actualiza o elimina un registro de carrera, la API NO DEBE
  generar embeddings ni escribir en Qdrant; el código de Bedrock, de la KB y de Qdrant y
  sus dependencias DEBEN desaparecer de la API (D-04, D-05).
- **RF-011** La migración de la API DEBE eliminar las 11 tablas `bedrock_*` sólo después
  de verificar la copia (RF-007), y su `downgrade` DEBE recrear su estructura (los datos
  se restauran del backup).
- **RF-018** SI un token `agent` llama a una ruta fuera de `/career/*`, ENTONCES la API
  DEBE responder 403 (D-14). SI un token `service` llama a una ruta fuera de su lista
  explícita (`/career/*`, `/files`, `/pdf-*`, `/linkedin`, `/admin/sections`,
  `/settings/error-reports`, `/notifications`, `/audit-log`), ENTONCES la API DEBE
  responder 403 (D-17).
- **RF-019** Los tokens que emite la API DEBEN incluir el claim `role` (`user`, `agent`
  o `service`); SI un token válido no trae el claim, ENTONCES API y harness DEBEN
  tratarlo como `user` (D-18). API y harness DEBEN rechazar con 401 un token sin `exp` o
  con `type` distinto de `access` (ausente = `access`); la API DEBE emitir `"type":
  "access"` en los access tokens (D-27).
- **RF-020** CUANDO un token `service` hace `POST /notifications`, la API DEBE crear la
  notificación y el Admin DEBE mostrarla como hoy (D-20).
- **RF-021** La API DEBE conservar `audit_logs` y exponer por REST la lectura del
  historial y la restauración de cambios que hoy usa el agente (D-19).
- **RF-012** Los endpoints de metodologías y secciones DEBEN conservar su contrato sin
  importar código del harness (D-10).

### Admin
- **RF-013** Todas las pantallas de agentes, el chat lateral, las métricas de coste y
  las tareas de agentes DEBEN llamar al harness por `/ai/` y NO DEBEN llamar a
  `/api/bedrock` ni `/api/agent-tasks` (D-03, D-07).
- **RF-014** El comportamiento visible de esas pantallas NO DEBE cambiar (paridad).

### Infraestructura y corte
- **RF-015** `docker-compose.yml` DEBE incluir el servicio del harness y su BD, y NO DEBE
  incluir el servicio ni el volumen `qdrant` (eliminados tras snapshot) (D-04).
- **RF-016** El bloque `servicios` de `caddy.json` DEBE enrutar `/ai/` del servicio
  `admin` al harness con SSE habilitado, sin tocar el bloque `cjhirashi_srv` (D-08).
- **RF-017** El corte DEBE hacerse en tres etapas desplegables por separado (D-11):
  (1) harness arriba con datos copiados, la API intacta; (2) el Admin apunta a `/ai/`;
  (3) se elimina Bedrock/KB/Qdrant de la API. MIENTRAS no se complete la etapa 3, DEBE
  poder volverse a la etapa anterior sin pérdida de datos.

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
- **D-13 (usuario, 2026-10-13, Fase 1):** paridad exacta de contrato bajo `/ai/`; el
  rediseño neutro al proveedor queda para specs posteriores. *Descartado:* rediseñar ya.
- **D-14 (usuario, 2026-10-13, Fase 1):** el agente externo sólo usa `/career/*`; los
  tokens `agent` pierden `POST /bedrock/chat` y la cuenta de servicio del harness es un
  token `agent`. *Descartado:* aceptar tokens `agent` en el chat del harness.

### Decisiones de Fase 2 (usuario, 2026-10-13 — enmiendan la spec tras Gate 1)
- **D-15:** memoria del agente en Postgres del harness con full-text; se migra su
  contenido. `search_knowledge_base` se retira (los datos se consultan por REST).
  *Descartado:* retirar la memoria; conservar Qdrant sólo para memoria.
- **D-16:** no se portan `POST /bedrock/knowledge-base/reindex` ni
  `GET /bedrock/knowledge/search` (excepción a RF-001; el Admin no las usa).
- **D-17:** rol nuevo `service` para la cuenta del harness, con lista explícita de
  rutas; el token `agent` del agente externo sigue sólo en `/career/*`. Enmienda D-09 y
  D-14 (la cuenta de servicio ya no es un token `agent`). *Descartado:* ampliar `agent`;
  aceptar la pérdida de rutas.
- **D-18:** claim `role` en el JWT. *Descartado:* endpoint `GET /auth/session`.
- **D-19:** `audit_logs` se queda en la API con endpoints REST. *Descartado:* moverla.
- **D-26 (usuario, 2026-10-13, Fase 4, bloque B):** excepción a D-13 (paridad exacta).
  `consume_converse_stream` de la API lee `contentBlockIndex` del nivel superior del evento,
  que siempre vale 0; según el modelo de servicio de botocore el índice va dentro de
  `contentBlockStart`, `contentBlockDelta` y `contentBlockStop`, así que varios `toolUse` en
  un mismo mensaje en streaming se mezclan. El harness lo corrige (`_block_index` en
  `providers/bedrock/converse.py`, con el nivel superior como respaldo); con un solo bloque
  el comportamiento es idéntico. *Descartado:* paridad con el bug.
- **Errata 2026-10-13 (T-004):** son 11 tablas `bedrock_*`, no 10 (faltaba `bedrock_conversation_messages`, 578 filas). No cambia ninguna decisión. En `career_ai_db` serán 11 migradas + `bedrock_agent_memory` = 12. T-004 también midió 0 puntos de memoria en Qdrant (los 271 puntos son registros de carrera indexados).
- **D-25 (usuario, 2026-10-13, tras T-002/T-003):** nueva ruta aditiva `GET /files/{id}` en
  la API (metadatos del archivo: `id`, `mime_type`, `original_filename`, tamaño, categoría,
  como los elementos de `GET /files`), dentro de `/files` ya permitido a `service`; la
  usa `store_uploaded_image`. *Descartado:* derivar el mime del `Content-Type` de
  `/files/{id}/raw`. Además se fija `/audit-log` literal en `SERVICE_ALLOWED_PREFIXES`.
- **D-20:** `POST /notifications` aditivo en la API, sólo rol `service`. *Descartado:*
  notificaciones en el harness.
- **D-21:** BD del harness = base `career_ai_db` en `postgres_db`, usuario propio sin
  permisos sobre `career_db`. *Descartado:* contenedor Postgres nuevo.
- **D-22:** la revisión UX (Art. 8) no se limita a una prueba de humo: el usuario no
  confirmó esa reducción, así que aplica la revisión completa de las pantallas afectadas.
- **D-23:** riesgo aceptado: el harness valida solo firma y claim `role` (no consulta
  `is_active`); un usuario desactivado conserva el chat hasta que caduque su access
  token. Los datos siguen pasando por la API, que sí lo rechaza.
- **D-24:** la búsqueda de memoria usa full-text de Postgres con configuración `spanish`,
  configurable por variable de entorno (`MEMORY_FTS_CONFIG`).
- **D-27 (usuario, 2026-10-13, Fase 4, tras el bloque D):** se endurece la validación del
  JWT en API y harness por igual. (1) `exp` obligatorio (`options={"require": ["exp",
  "sub"]}`); hoy todo token emitido ya lo trae. (2) La API emite `"type": "access"` en los
  access tokens; API y harness aceptan como access sólo `type == "access"` o `type`
  ausente (compatibilidad con los emitidos antes del despliegue, como RF-019 con `role`),
  y rechazan con 401 cualquier otro valor. Motivo verificado: el token `state` de LinkedIn
  OAuth (`linkedin_service.build_state_token`, `type = "linkedin_oauth_state"`, mismo
  `SECRET_KEY`) hoy se acepta como bearer en la API porque `decode_access_token` sólo
  excluye `refresh`. *Descartado:* paridad con la validación vigente (a); exigir `type`
  presente ya (cerraría las sesiones vigentes y los tokens de agente sin `type`; se puede
  hacer más adelante cuando caduquen todos).

## 7 · Requisitos no funcionales

- **RNF-001:** ninguna prueba llama a Bedrock reales; Qdrant deja de existir.
- **RNF-002:** backup de `career_db` y snapshot de Qdrant antes de migrar; toda
  operación sobre BD en vivo requiere OK explícito del usuario.
- **RNF-003:** `cjhirashi-career-ai` con tests y cobertura ≥ 80 % por módulo, trazados
  con `@pytest.mark.requisito`.
