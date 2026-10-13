---
titulo: "Plan — Harness de agentes fuera de la API (cjhirashi-career-ai) y sin indexación"
tipo: plan
feature_id: "009"
estado: approved
fecha: 2026-10-13
---

# Plan 009 — Harness de agentes fuera de la API

Spec: `spec.md` (Gate 1 aprobado, commit c9393a95). Contratos en `contracts/`:

| Archivo | Contenido |
|---|---|
| `contracts/ai-routes.md` | Inventario de las **47** operaciones (39 `/bedrock/*` + 8 `/agent-tasks/*`; no 22) y su disposición (P/P*/S/X) |
| `contracts/auth-jwt-service-account.md` | JWT compartido con claim `role`, rol `service` y su lista de rutas |
| `contracts/harness-db-schema.md` | 11 tablas (+ memoria), secuencias, script de copia, migración DROP de la API |
| `contracts/harness-api-dependencies.md` | 41 tools → endpoint REST (OK/GAP/LOCAL) y cliente `clients/` |
| `contracts/agent-registry.json` | 20 perfiles (id, label, nivel) compartidos API/harness |

Este plan **no implementa** ni toca BD, contenedores, Bedrock o Qdrant reales.

## 0 · Resumen y decisiones de diseño

1. **Patrón (Art. 1–2):** `cjhirashi-career-ai` es un microservicio nuevo del monorepo con
   el mismo patrón en capas que la API: `routes → services → repositories → models`,
   más dos zonas propias: `providers/` (frontera de salida al modelo) y `clients/`
   (frontera de salida a la API). La lógica de negocio va en `services/`; las rutas solo
   validan, autentican y delegan.
2. **El andamiaje actual no se reaprovecha** (está en `.gitignore`, sin código fuente ni
   tests): se reemplaza por una estructura nueva y se retira del `.gitignore` (D-06).
3. **El código se traslada, no se reescribe:** `services/bedrock/*` (~7.8k líneas) se mueve
   al harness reorganizado por capas. Cada acoplamiento a modelos/repositorios de la API se
   sustituye por un cliente REST (`contracts/harness-api-dependencies.md`).
4. **Paridad estricta (D-13):** mismas rutas relativas, cuerpos y respuestas. Externamente
   `/ai/...`; Caddy quita el prefijo (`quitar_prefijo`) y el harness sirve `/bedrock/*` y
   `/agent-tasks/*` sin prefijo.
5. **Corte en 3 etapas reversibles (D-11)** con la API intacta hasta la etapa 3.
6. **Decisiones de Fase 2 (D-15..D-22, ya en la spec):** memoria del agente en Postgres
   del harness con full-text y migración desde Qdrant (`bedrock_agent_memory`;
   `search_knowledge_base` se retira); `reindex` y `knowledge/search` no se portan;
   claim `role` en el JWT (sin `GET /auth/session`); rol `service` con lista explícita de
   rutas para la cuenta del harness (el `agent` externo sigue solo en `/career/*`);
   `audit_logs` se queda en la API con endpoints REST; `GET /files/{id}` aditivo (D-25); `POST /notifications` solo para
   `service`; BD `career_ai_db` en el `postgres_db` existente con usuario propio; revisión
   UX completa (Art. 8).

## 1 · Arquitectura del harness (`cjhirashi-career-ai`) por capas

```
cjhirashi-career-ai/
  Dockerfile, pyproject.toml, alembic.ini, .env.example, README.md
  alembic/versions/0001_initial_harness_schema.py
  scripts/copy_from_career_db.py          # offline, fuera del servicio (RF-007)
  src/
    app.py, config.py, database.py        # FastAPI async, SQLAlchemy async + asyncpg
    middleware/auth.py                    # JWT compartido + claim role (RF-002/019)
    middleware/principal.py               # Principal/ServiceContext (contextvars)
    routes/        bedrock.py agent_profiles.py memory.py tools.py
                   conversations.py audit_log.py agent_tasks.py health.py
    schemas/       (los de la API: bedrock*.py, bedrock_tasks) 
    services/      agent_loop.py chat_service.py profile_catalog.py tools_registry.py
                   delegation.py memory_service.py usage_service.py task_scheduler.py
                   image_service.py prompt.py error_reporting.py id_generator.py
                   web_search.py github_tools.py agent_registry.py
    repositories/  conversation_repo.py task_repo.py settings_repo.py profile_repo.py
                   usage_repo.py custom_tool_repo.py
    models/        los 11 modelos bedrock_* (sin FK a users)
    providers/     base.py  bedrock/{client.py,converse.py,images.py,pricing.py}
    clients/       api_client.py career.py files.py sections.py linkedin.py pdf.py
                   job_discovery.py errors.py
  tests/           unit/ (por capa) contract/ e2e/
```

### Interfaz de proveedor (RF-005)

`providers/base.py` define el `Protocol ModelProvider` con la superficie que hoy usa el
bucle: `converse(request) -> ModelResponse`, `converse_stream(request) -> AsyncIterator[Event]`,
`generate_image(prompt, options) -> ImageResult`, `list_models()`, `estimate_cost(usage)`
y tipos neutros (`ModelRequest`, `ToolSpec`, `ToolCall`, `Usage`). `providers/bedrock/`
implementa el protocolo con boto3 y es **el único módulo que importa `boto3`/`botocore`**.
El bucle (`services/agent_loop.py`) recibe el `ModelProvider` por inyección
(`Depends`/fábrica en `config`), nunca instancia el cliente AWS. Tabla de precios y cache
points (`cachePoint`, ADR-019) viven en el provider Bedrock. Paridad (D-13): los nombres
de ruta, tablas y columnas `bedrock_*` no cambian aunque el servicio sea neutro.

Prueba de frontera: test AST (`tests/unit/test_provider_boundary.py`) que falla si
cualquier archivo de `src/` fuera de `providers/bedrock/` importa `boto3`/`botocore`, o si
`services/`/`routes/` importan `providers.bedrock` (solo la fábrica de `config.py` lo hace).

### Fronteras de salida (implementación concreta)

| Frontera | Implementación | Credencial |
|---|---|---|
| Modelo (Bedrock) | `providers/bedrock/*` | rol/credenciales AWS por entorno |
| API de datos | `clients/*` sobre `httpx.AsyncClient` (`API_BASE_URL`) | JWT del usuario o `AI_SERVICE_TOKEN` (`contracts/auth-jwt-service-account.md` §2) |
| Web / GitHub | `services/web_search.py`, `services/github_tools.py` (LOCAL) | `BRAVE_SEARCH_API_KEY`, `GITHUB_TOKEN` |
| BD propia | `repositories/*` | `AI_DATABASE_URL` (`career_ai_db`) |

El harness **no** tiene ninguna variable ni referencia a `career_db`/Qdrant en `src/`
(test regex, RF-003, ver §8).

## 2 · Fronteras y contratos entre servicios

- **Admin → harness (`/ai/`):** `contracts/ai-routes.md` (47 operaciones, regla de paridad,
  `/health`, `/metrics`, errores). Gate de CI: `tests/contract/test_ai_route_parity.py`
  (ai) y `src/tests/api/aiRoutes.test.ts` (Admin).
- **Autenticación:** `contracts/auth-jwt-service-account.md`.
- **Harness → API:** `contracts/harness-api-dependencies.md`. Cambios aditivos mínimos en la
  API (aprobados: D-18, D-19, D-20): claim `role` en los tokens (RF-019),
  `POST /notifications` solo `service` (RF-020), `GET /files/{id}` (D-25) y `GET /audit-log` +
  `POST /audit-log/{audit_id}/restore` (RF-021). Contrato de cada ruta nueva en
  `contracts/harness-api-dependencies.md`.
- **Catálogo de agentes compartido:** la API conserva `services/agent_registry.py`
  (20 perfiles estáticos: id, label, nivel) porque `admin_sections`, `methodology_scope`
  y `schemas/career_methodologies.py` validan `agent_profile_ids` contra ella (D-10, RF-012,
  hoy importan `services.bedrock.agent_profiles`). Fuente de verdad única:
  `contracts/agent-registry.json`; **un test de contrato en cada servicio** lo compara
  con su registro (si divergen, falla CI en ambos).
- **BD:** `contracts/harness-db-schema.md`.
- **Gates de CI aplicables:** lint + tests con cobertura ≥ 80 % por módulo (Art. 3) para
  `cjhirashi-career-ai`; los tests de contrato anteriores; el job de la API debe seguir verde
  tras cada etapa; test de que `caddy.json` es JSON válido y `bin/caddy-sync --check`
  (solo validar, sin aplicar).

## 3 · Eliminación en la API (etapa 3), archivo por archivo

Todo en `cjhirashi-career-api/`. «Quitar» = borrar el archivo; «Editar» = cambio puntual.
Cada fila va con su test (§8).

| Archivo | Acción | Detalle |
|---|---|---|
| `src/services/bedrock/**` (~7.8k líneas, incl. `agent_profiles`, `profile_catalog`, `profile_tools`, `tools`, `prompt`, `knowledge_base`, `local_memory`, `agent_loop`…) | Quitar | Se han trasladado al harness. |
| `src/services/bedrock_service.py`, `qdrant_service.py` | Quitar | |
| `src/services/task_scheduler.py` | Quitar | Pasa al harness (`services/task_scheduler.py`). Se retira su arranque de `app.py`. |
| `src/routes/bedrock.py`, `src/routes/bedrock_tasks.py` | Quitar | RF-009. |
| `src/schemas/bedrock*.py` | Quitar | |
| `src/models/bedrock_*.py` (11) y sus imports en `models/__init__.py` | Quitar | Tras la migración DROP. |
| `src/app.py` | Editar | Quitar `include_router` de ambas rutas, el arranque/parada del scheduler, el cierre de Qdrant y cualquier métrica Bedrock. |
| `src/middleware/auth.py` | Editar | Quitar el permiso `POST /bedrock/chat` del rol `agent`; el rol `agent` solo pasa en `/career/*`; el resto → 403 (RF-018). Añadir el rol `service` con su lista explícita (`SERVICE_ALLOWED_PREFIXES`) y emitir/leer el claim `role` (`services/auth_service.py`, RF-019). Sin migración: `access_role` es `String(32)` sin CHECK. |
| `src/routes/notifications.py` (nuevo), `src/routes/audit_log.py` (nuevo), `src/services/audit_service.py` | Crear | `POST /notifications` (solo `service`, RF-020); lectura y restauración de `audit_logs` por REST (RF-021). Etapa 1 (aditivos). |
| `src/repositories/career_repository.py` | Editar | Quitar el hook de indexado (`after_write` → KB), `_KB_EXCLUDED_COLUMNS` y la **creación de subtareas `BedrockTask`** en el flujo de escritura (si existe, se mueve a una tarea de harness vía su propia ruta); el repositorio queda sin imports de `bedrock`/`qdrant`. |
| `src/routes/career_common.py` | Editar | Quitar la importación/uso de indexado y de perfiles Bedrock; `build_crud_router` conserva su contrato (el harness lo reutiliza por copia en `routes/agent_tasks.py`). |
| `src/routes/admin_sections.py`, `src/services/admin_sections.py`, `src/services/methodology_scope.py`, `src/services/section_catalog.py`, `src/schemas/career_methodologies.py`, `src/schemas/admin_sections.py` | Editar | Sustituir `from services.bedrock.agent_profiles import …` por `services.agent_registry` (estático, sin Bedrock). Mismo contrato (RF-012). Quitar el reindexado al guardar metodologías. |
| `src/services/error_reporting.py` | Editar | Quitar la referencia a la tabla/uso Bedrock; conserva `POST /system/error-report`. |
| `src/services/id_generator.py` | Editar | Quitar los prefijos `bco/bcm/bct/btk` (solo tras el DROP). |
| `src/routes/pdf_template_styles.py` / `services/pdf_template_styles.py` | Editar | Quitar el acoplamiento a `bedrock` (referencia a tools o perfiles); contrato HTTP intacto. |
| `src/config.py` | Editar | Quitar `QDRANT_*`, `BEDROCK_*`, embeddings. |
| `requirements*.txt` / `pyproject` | Editar | Quitar `qdrant-client`, `boto3` (si no lo usa otro módulo; verificar con grep), dependencias de embeddings. |
| `alembic/versions/<nueva>_drop_bedrock_tables.py` | Crear | `contracts/harness-db-schema.md` §4. |
| `scripts/check_kb_consistency.py` | Quitar | |
| tests: `tests/**/bedrock/**`, `test_methodology_scope` (partes KB), `test_knowledge_base_*`, `test_qdrant_*` | Quitar/Editar | Migran al harness los que prueban lógica de agentes. |
| `docs/` de la API | Editar/Quitar | Ver §11. |

**Orden dentro de la etapa 3** (cada paso deja la suite en verde): (1) ruta `agent` 403 +
claim `role`, rol `service`, `/notifications` y `/audit-log` (aditivos, etapa 1); (2) `agent_registry` + cambiar imports de metodologías/secciones;
(3) quitar el hook de indexado y la creación de subtareas; (4) quitar routers y scheduler;
(5) quitar servicios/modelos/schemas; (6) migración DROP (con guarda) como último paso.

## 4 · Cambios del Admin (`cjhirashi-career-admin/`)

- `src/api/client.ts`: añadir un segundo cliente `aiClient` con `baseURL` `/ai` (mismo
  interceptor de JWT y de refresco que `client`); el primero no cambia.
- `src/api/bedrock.ts` y `src/api/agentTasks.ts`: usan `aiClient`. Las rutas relativas **no
  cambian** (D-13). Quedan: RF-013 sin llamadas a `/api/bedrock` ni `/api/agent-tasks`.
- El chat SSE: el `fetch`/stream de `components/bedrock/*` toma la URL base de `/ai`
  (variable `VITE_AI_BASE_URL`, por defecto `/ai`).
- `vite.config.ts`: proxy de desarrollo `/ai → http://localhost:<puerto ai>`.
- Hooks (`useBedrock*`, `useAgentTasks`) y componentes: sin cambios funcionales (RF-014).
- Tests: `src/tests/api/aiRoutes.test.ts` (nuevo, ver §8); actualizar los tests de API que
  mockean la URL base; `src/tests/api/bedrock*.test.ts` apuntan a `/ai`.
- Memoria: la pantalla conserva su contrato; `reindex`/`knowledge/search` no tienen UI.
  Revisión UX completa de las pantallas afectadas antes del Gate 3 (D-22, Art. 8).

## 5 · Infraestructura

- **`docker-compose.yml`:** servicio `cjhirashi-career-ai` (build `./cjhirashi-career-ai`,
  puerto interno `8010`, `depends_on` BD propia y API, healthcheck `GET /health`, redes
  igual que la API, variables `SECRET_KEY`/`ALGORITHM` **desde el mismo `.env`**,
  `API_BASE_URL`, `AI_DATABASE_URL`, `AI_SERVICE_TOKEN`, claves AWS/Brave/GitHub). BD propia
  (D-21): base `career_ai_db` en el contenedor `postgres_db` existente con usuario propio
  sin permisos sobre `career_db` (script de init idempotente; el contenedor no se crea). Se **elimina** el servicio `qdrant`, su
  volumen y las variables `QDRANT_*` de la API (tras el snapshot).
- **`caddy.json` (solo `servicios`):** en el servicio `admin`, nueva ruta
  `/ai/` → upstream `cjhirashi-career-ai:8010` con `quitar_prefijo: true` y `sse: true`
  (`flush_interval -1`). El bloque `cjhirashi_srv` no se toca (Art. 6). Validar con
  `bin/caddy-sync` en modo comprobación; aplicar solo con OK del usuario.
- **`prometheus.yml`:** job para `cjhirashi-career-ai:8010/metrics`; sin cambios en el job
  de la API salvo retirar métricas Bedrock si las hubiera.
- **`.env.example`:** variables nuevas del harness; retirar `QDRANT_*`.
- **`.gitignore`:** retirar la entrada de `cjhirashi-career-ai`.
- **Snapshot de Qdrant y backup de `career_db`** antes de la etapa 1 y 3 (RNF-002): tarea
  operativa, solo con OK explícito del usuario.

## 6 · BD y migración de datos

Detalle en `contracts/harness-db-schema.md`. Resumen: 11 tablas con los mismos nombres y
tipos más `bedrock_agent_memory` (nueva, FTS; contenido migrado de Qdrant con `scripts/migrate_memory_from_qdrant.py` y reporte de conteos); sin FK a `users`; migración inicial propia; secuencias recreadas y ajustadas con
`setval` tras copiar; script offline idempotente con reporte por tabla (origen, destino,
faltantes, checksum) que termina con error si algún conteo difiere (RF-007); modo
`--verify-only` y dirección inversa para los rollbacks. La migración de la API que elimina
las tablas exige un reporte `ok:true` reciente (guarda `AI_COPY_REPORT`, RF-011); su
`downgrade` recrea la estructura, no los datos. Los conteos reales se registran en la
evidencia de la etapa 1 (no se consultó la BD viva al planificar).

## 7 · Secuencia de corte en 3 etapas y reversibilidad

| Etapa | Qué se despliega | Estado de la API | Verificación | Reversión |
|---|---|---|---|---|
| **1. Harness arriba, datos copiados** | `cjhirashi-career-ai` + `career_ai_db`; cambios aditivos de la API (claim `role`, rol `service`, `/notifications`, `/audit-log`); migración de memoria desde Qdrant; ruta `/ai/` en `caddy.json`; copia de datos (script, `api-to-ai`) | **Intacta**: sigue sirviendo `/bedrock/*`, Qdrant sigue corriendo; el Admin sigue usando la API | Reporte de copia `ok:true`; `/health`; humo con JWT real en `/ai/` | Apagar el servicio y quitar la ruta; la API no cambió → sin pérdida |
| **2. El Admin apunta a `/ai/`** | Admin con `aiClient` | Intacta pero sin tráfico de agentes | Humo UI (chat SSE, tareas, métricas); las escrituras ya van al harness | Volver al Admin anterior. Los datos escritos en el harness en la etapa 2 se devuelven con `copy --direction ai-to-api` **antes** de volver, si se quiere conservarlos |
| **3. Retirar de la API** | API sin Bedrock/KB/Qdrant; `agent` 403 fuera de `/career/*`; migración DROP; compose sin `qdrant` | Limpia | `--verify-only` `ok:true` reciente + backup; suite verde | `alembic downgrade` (recrea estructura) + `copy --direction ai-to-api` o restaurar el backup; el snapshot de Qdrant solo restaura la KB, que no se usa |

Reglas: cada etapa es un despliegue propio con su commit; la etapa 3 no se ejecuta sin
`verify-only` ok y backup; ningún paso opera sobre BD en vivo sin OK del usuario (RNF-002).
La etapa 3 se divide en dos releases: (3a) retirar código y rutas, (3b) migración DROP +
retirada de Qdrant (exige reporte `ok:true` de la migración de memoria y snapshot), para poder revertir el código sin tocar datos.

## 8 · Estrategia de pruebas por zona (tests antes que código)

Orden: para cada tarea, primero el test (rojo), luego el código (verde). Todos con
`@pytest.mark.requisito("RF-0NN")` (RNF-003). Sin Bedrock ni Qdrant reales (RNF-001):
`ModelProvider` falso; `httpx.MockTransport` para la API; BD de test aislada.

| Zona | Pruebas |
|---|---|
| `routes` (ai) | Contrato por ruta con `TestClient`; **paridad** (`test_ai_route_parity`: openapi == tabla P/P*/S, sin X); 401 sin/ con JWT inválido; SSE (eventos `status`/`done`/`error`, ping, cabeceras) |
| `middleware` (ai) | Matriz de `contracts/auth-jwt-service-account.md` §4 |
| `services` (ai) | Bucle de agente con proveedor falso (turnos, tools, delegación, presupuesto diario, historial); scheduler (reloj inyectable, `ServiceContext`, tarea de otro dueño → `failed`); costes; imagen vía provider |
| `repositories`/`models` (ai) | Test de esquema vs `contracts/harness-db-schema.md` §1; secuencias no colisionan tras la copia; migración 0001 arriba/abajo contra BD de test |
| `providers` | Contrato del `Protocol` con un doble; `providers/bedrock` con cliente boto3 simulado (stub); test AST de frontera (solo `providers/bedrock` importa boto3) |
| `clients` | Cada módulo con `MockTransport`; token correcto; `MissingCredentialError`; reintentos solo idempotentes; mapeo de errores; paginación con tope |
| `scripts` | `copy_from_career_db`: idempotencia, ids conservados, sale ≠ 0 si difiere un conteo, `--verify-only` tolera destino mayor, `ai-to-api`, `setval`; BD de prueba, nunca la real |
| Aislamiento (RF-003) | Test regex sobre `src/`: ninguna referencia a `career_db`, `qdrant`, `SOURCE_` |
| API | Auth `agent` 403 fuera de `/career/*` (RF-018); `/bedrock/*` y `/agent-tasks/*` → 404 (RF-009); `career_repository` no emite indexado (RF-010: test con espía que falla si se llama); claim `role` y rol `service` (RF-019/018), `POST /notifications` (RF-020), `/audit-log` (RF-021); contrato de metodologías/secciones sin cambio con `agent_registry` (RF-012); contrato `agent-registry.json`; migración DROP (guarda sin DDL, upgrade, downgrade) |
| Admin | `aiRoutes.test.ts` (cada llamada en `api/bedrock.ts` y `api/agentTasks.ts` usa una ruta de la tabla y la base `/ai`); test que busca `'/api/bedrock'` y `'/api/agent-tasks'` y falla (RF-013); tests de componentes existentes siguen verdes (RF-014) |
| Infra | JSON válido de `caddy.json` y `bin/caddy-sync` en comprobación: `/ai/` con `sse` y sin tocar `cjhirashi_srv`; test que `docker-compose.yml` no contiene `qdrant` (RF-015) |
| E2E | Cadena Admin→(simulada)→harness→API simulada con JWT real firmado con un secreto de prueba |

## 9 · Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | Regresión funcional del bucle al trasladar 7.8k líneas | Mover con tests existentes primero; traslado mecánico; paridad por contrato |
| R2 | Las tools pasan de BD directa a REST: latencia/costes en bucles largos y N+1 (`bulk_update`) | Cliente con paginación tope; medir en etapa 1; `bulk_update` secuencial con límite |
| R3 | La lista del rol `service` puede quedarse corta frente a las tools programadas reales | Inventario en Fase 3; 403 explícito como error de tool; ampliar solo con cambio de spec |
| R4 | Pérdida de memoria del agente (solo en Qdrant). **Residual:** T-004 midió 0 puntos de memoria (`manual_memory`/`agent-notes`); los 271 puntos de Qdrant son registros de carrera indexados (se descartan, D-04) | `migrate_memory_from_qdrant.py` se mantiene por si se crea memoria antes del corte, con reporte de conteos; gate + snapshot antes de borrar el volumen; cambia la relevancia (FTS vs vectorial) |
| R5 | Secuencias desincronizadas tras copiar | `setval` en el script + test |
| R6 | El harness no consulta `is_active`: un usuario desactivado conserva el chat hasta que expire el access token | **Riesgo aceptado por el usuario (D-23).** Mitigación: los datos pasan por la API con el mismo token (que sí rechaza). Tokens antiguos sin `role` = user |
| R7 | Dependencia circular de arranque (harness ↔ API) | `/health` del harness no falla si la API está caída al arrancar |
| R8 | DROP irreversible de datos | Guarda con reporte, backup, `downgrade` estructural, copia inversa |
| R9 | Duplicación de `agent_registry` y `github_service` | Test de contrato en ambos; duplicación documentada |
| R10 | SSE cortado por buffering | `sse: true` en Caddy, `X-Accel-Buffering: no`, ping cada 15 s; prueba de humo |
| R11 | Vulnerabilidad del secreto JWT compartido en dos servicios | Un `.env` único; documentado en `ENVIRONMENT-SECURITY.md` |
| R12 | Endpoints de la API faltantes (GAP) bloquean tools | Inventario en `harness-api-dependencies.md`; tareas separadas; sin OK del usuario no se crean |

## 10 · Implementación por requisito

### Implementación de RF-001
Rutas del harness en `cjhirashi-career-ai/src/routes/{bedrock,agent_profiles,memory,tools,conversations,audit_log,agent_tasks}.py` con los schemas copiados de `cjhirashi-career-api/src/schemas/bedrock*.py`; servicios en `src/services/`. Tabla de rutas y excepciones (X confirmadas por D-16, S por D-15) en `contracts/ai-routes.md`. `reindex` y `knowledge/search` no se portan. Prueba: `tests/contract/test_ai_route_parity.py`.

### Implementación de RF-002
`cjhirashi-career-ai/src/middleware/auth.py` (decodifica con `SECRET_KEY`/`ALGORITHM`, rechaza refresh, `sub` ausente y `role` desconocido; 403 a `agent`/`service`); `src/middleware/principal.py`. Sin llamadas a la API para autenticar. Contrato: `contracts/auth-jwt-service-account.md` §2.

### Implementación de RF-003
`cjhirashi-career-ai/src/clients/{api_client,career,files,sections,linkedin,pdf,job_discovery,errors}.py` sustituyen cada acceso directo de las tools. Sin `SOURCE_*` ni cadena de `career_db` en `src/`. Prueba regex de aislamiento. Mapeo: `contracts/harness-api-dependencies.md`.

### Implementación de RF-004
`cjhirashi-career-ai/src/clients/api_client.py` (toma el `Principal` del contexto; `ServiceContext` explícito en `services/task_scheduler.py`; `MissingCredentialError`); `src/middleware/principal.py`. `AI_SERVICE_TOKEN` en `config.py`. Contrato: `auth-jwt-service-account.md` §2–3.

### Implementación de RF-005
`cjhirashi-career-ai/src/providers/base.py` (`ModelProvider`), `src/providers/bedrock/{client,converse,images,pricing}.py`, fábrica en `src/config.py`; `services/agent_loop.py`, `services/usage_service.py` e `services/image_service.py` dependen solo del protocolo. Prueba AST `tests/unit/test_provider_boundary.py`.

### Implementación de RF-006
`cjhirashi-career-ai/src/models/*` (11 modelos + `bedrock_agent_memory`), `src/repositories/*`, `src/database.py`, `alembic/versions/0001_initial_harness_schema.py`, `src/services/id_generator.py`. Esquema: `contracts/harness-db-schema.md` §1–2.

### Implementación de RF-007
`cjhirashi-career-ai/scripts/copy_from_career_db.py` (upsert idempotente, ids conservados, `setval`, reporte JSON, exit ≠ 0 si un conteo difiere, `--verify-only`, `--direction`). Tests en `cjhirashi-career-ai/tests/unit/scripts/test_copy_from_career_db.py`. Contrato: `harness-db-schema.md` §3.

### Implementación de RF-008
`cjhirashi-career-ai/src/routes/bedrock.py` (`POST /bedrock/chat` con `StreamingResponse` `text/event-stream`, ping 15 s, `X-Accel-Buffering: no`) y `services/chat_service.py`; cliente SSE del Admin en `cjhirashi-career-admin/src/components/bedrock/*` apuntando a `/ai`; `caddy.json` con `sse: true`.

### Implementación de RF-009
Quitar `cjhirashi-career-api/src/routes/bedrock.py`, `routes/bedrock_tasks.py` y sus `include_router` en `src/app.py`. Prueba: `tests/unit/test_bedrock_routes_removed.py` (404).

### Implementación de RF-010
Editar `cjhirashi-career-api/src/repositories/career_repository.py` (hook de indexado, `_KB_EXCLUDED_COLUMNS`, subtareas `BedrockTask`), `src/routes/career_common.py`, `src/config.py`, `src/app.py`; quitar `src/services/bedrock/**`, `bedrock_service.py`, `qdrant_service.py`, `task_scheduler.py`, `scripts/check_kb_consistency.py`; retirar `qdrant-client`/`boto3` de las dependencias. Prueba: espía de indexado + test AST que prohíbe `bedrock|qdrant` en `src/` de la API.

### Implementación de RF-011
`cjhirashi-career-api/alembic/versions/<nueva>_drop_bedrock_tables.py` (guarda `AI_COPY_REPORT`, DROP idempotente, `downgrade` estructural). Prueba `tests/unit/test_drop_bedrock_tables_migration.py`. Contrato: `harness-db-schema.md` §4.

### Implementación de RF-012
Editar `cjhirashi-career-api/src/services/{admin_sections,methodology_scope,section_catalog}.py`, `src/schemas/{career_methodologies,admin_sections}.py`, `src/routes/admin_sections.py`; crear `src/services/agent_registry.py` desde `contracts/agent-registry.json`. Pruebas de contrato existentes (sin cambios) + `tests/unit/test_agent_registry_contract.py`; espejo `cjhirashi-career-ai/tests/contract/test_agent_registry_contract.py`.

### Implementación de RF-013
Editar `cjhirashi-career-admin/src/api/client.ts` (`aiClient`), `src/api/bedrock.ts`, `src/api/agentTasks.ts`, `vite.config.ts`, componentes/hook que fijen la URL del stream. Pruebas: `src/tests/api/aiRoutes.test.ts`, `src/tests/api/noLegacyAgentRoutes.test.ts`.

### Implementación de RF-014
Sin cambios en `components/bedrock/*`, `SidebarRight`, `Agent*`, `AdminSectionsPage`, `TasksPage` más allá de la URL base; las pruebas existentes de esos componentes deben seguir verdes sin modificarse. Revisión UX completa de las pantallas afectadas (Art. 8, D-22): chat lateral, páginas `Agent*`, métricas de coste, `AdminSectionsPage` y `TasksPage`, antes del Gate 3.

### Implementación de RF-015
Editar `docker-compose.yml` (servicio `cjhirashi-career-ai` + BD, retirar `qdrant` y su volumen), `.env.example`, `prometheus.yml`, `.gitignore`. Prueba `tests/infra/test_compose.py` (o script equivalente de CI).

### Implementación de RF-016
Editar `caddy.json` solo en `servicios` (ruta `/ai/` en `admin`, `quitar_prefijo`, `sse`). Prueba: validación de esquema + comprobación de que `cjhirashi_srv` es idéntico al de HEAD.

### Implementación de RF-017
Secuencia y reversibilidad en §7; script `copy_from_career_db.py` (ambas direcciones); migración de la API con guarda; despliegues como commits separados por etapa. Verificación de reversibilidad: prueba de scripts (ida y vuelta) y de migración (upgrade/downgrade).

### Implementación de RF-018
Editar `cjhirashi-career-api/src/middleware/auth.py`: el rol `agent` solo `/career/*` (sin `POST /bedrock/chat`); el rol `service` solo `SERVICE_ALLOWED_PREFIXES` (`/career/*`, `/files`, `/pdf-templates`, `/pdf-template-styles`, `/linkedin`, `/admin/sections`, `/settings/error-reports`, `/notifications`, `/audit-log`); lo demás 403. Prueba: matriz de `auth-jwt-service-account.md` §5 (API).

### Implementación de RF-019
Editar `cjhirashi-career-api/src/services/auth_service.py` (`_create_token` añade `role` derivado de `access_role`; `access_role = "service"` es un valor nuevo de una columna `String(32)` sin CHECK: sin migración Alembic; se amplía la validación en `schemas`), `src/middleware/auth.py` (lee el claim; sin claim = `user`; desconocido = 401) y el middleware del harness (RF-002). Pruebas: `cjhirashi-career-api/tests/unit/test_jwt_role_claim.py`, `cjhirashi-career-ai/tests/unit/middleware/test_auth_role.py`.

### Implementación de RF-020
Crear `cjhirashi-career-api/src/routes/notifications.py` (`POST /notifications`, body `{user_id, title, message, type?}` mapeado al modelo `UserNotification` existente; solo rol `service`, si no 403), con servicio/repositorio en las capas actuales; registrar en `app.py`. El harness lo llama desde `clients/notifications.py` (nuevo) en `services/task_scheduler.py`. El Admin ya muestra las notificaciones (sin cambios). Pruebas: `tests/unit/test_notifications_route.py` (API), `tests/unit/clients/test_notifications.py` (ai).

### Implementación de RF-021
Crear `cjhirashi-career-api/src/routes/audit_log.py` y `src/services/audit_service.py` con `GET /audit-log` y `POST /audit-log/{audit_id}/restore` (lógica movida desde el actual `routes/bedrock.py`; accesibles a usuario y `service`; el usuario solo ve/restaura sus registros). `audit_logs` y su escritura en `career_repository` **se conservan**. El harness los usa desde `clients/audit.py` (nuevo) en `routes/audit_log.py` y en las tools `list_recent_changes`/`restore_deleted_record`. Pruebas: `tests/unit/test_audit_log_routes.py` (API), `tests/unit/clients/test_audit.py` (ai).

### Implementación de RF-022
Harness: modelo `src/models/bedrock_agent_memory.py` (creado con los demás modelos en T-015), `src/repositories/memory_repo.py` (inserción, listado, borrado, `search` con `to_tsvector`/`websearch_to_tsquery`/`ts_rank`), `src/services/memory_service.py` (sustituye `local_memory.py` y `qdrant_service`), `routes/memory.py`; migración `0001` crea la tabla, la columna generada `search_vector` y el índice GIN. Migración de contenido: `cjhirashi-career-ai/scripts/migrate_memory_from_qdrant.py` (solo lectura de Qdrant, idempotente, reporte de conteos, exit ≠ 0 si difiere). Contrato: `contracts/harness-db-schema.md` §1 y §6. Pruebas: `tests/unit/repositories/test_memory_repo.py` (FTS con BD de test), `tests/unit/scripts/test_migrate_memory_from_qdrant.py` (cliente Qdrant simulado, nunca real).

## 11 · Impacto en documentación (Art. 11)

Una fila = una tarea `[doc]`.

| # | Documento | Cambio |
|---|---|---|
| 1 | `docs/09-DECISIONS/029-harness-agentes-fuera-de-api.md` | Nuevo ADR (propuesto) |
| 2 | `docs/09-DECISIONS/README.md` | Fila del ADR-029 |
| 3 | `docs/01-INTRODUCTION.md` | Referencias a Bedrock/Qdrant en la API |
| 4 | `docs/02-CONSTRAINTS.md` | Restricciones de infraestructura (Qdrant) |
| 5 | `docs/03-CONTEXT-SCOPE.md` | Nuevo actor/sistema: harness |
| 6 | `docs/04-SOLUTION-STRATEGY.md` | Estrategia: harness como servicio propio |
| 7 | `docs/05-BUILDING-BLOCKS.md` | Bloques: añadir `cjhirashi-career-ai`, quitar bedrock/qdrant de la API |
| 8 | `docs/06-RUNTIME-VIEW.md` | Flujos de chat y tareas |
| 9 | `docs/07-DEPLOYMENT-VIEW.md` | Servicio `ai`, BD propia, sin `qdrant` |
| 10 | `docs/08-CROSS-CUTTING-CONCEPTS.md` | Autenticación compartida, cuenta de servicio |
| 11 | `docs/10-QUALITY-REQUIREMENTS.md` | Calidad/rendimiento del chat vía REST |
| 12 | `docs/11-RISKS-TECHNICAL-DEBT.md` | Riesgos de §9 |
| 13 | `docs/12-GLOSSARY.md` | Harness, cuenta de servicio, `/ai/` |
| 14 | `docs/BEDROCK-SYSTEM.md` | Reubicar/actualizar |
| 15 | `docs/ENVIRONMENT-SECURITY.md` | Variables nuevas, procedimiento del token de servicio |
| 16 | `docs/IMPLEMENTATION_PLAN.md` | Estado del plan |
| 17 | `docs/ADMIN_PANEL_SETUP.md` | Base `/ai` |
| 18 | `README.md` | Servicios, puertos |
| 19 | `AGENTS.md` | Fila `ai`, puerto 8010, infra sin Qdrant |
| 20 | `.harness/constitution.md` (Art. 2/4/12) | Vía ADR-029 y OK del usuario; no se edita sin él |
| 21 | `cjhirashi-career-api/README.md` y `src/README.md`, `src/models/README.md` | Quitar Bedrock/Qdrant |
| 22 | `cjhirashi-career-api/docs/ARCHITECTURE.md` | Capas sin harness |
| 23 | `cjhirashi-career-api/docs/API.md` | Retirar rutas |
| 24 | `cjhirashi-career-api/docs/DATABASE.md` | Retirar 11 tablas |
| 25 | `cjhirashi-career-api/docs/BEDROCK-HARNESS.md` | Mover al README del harness |
| 26 | `cjhirashi-career-api/docs/sections/` (bedrock, bedrock-tasks, files, linkedin, pdf-*, career-*) | Actualizar o retirar |
| 27 | `cjhirashi-career-api/src/services/bedrock/README.md` | Retirar |
| 28 | `cjhirashi-career-admin/docs/BEDROCK-CHAT.md` | URL base `/ai` |
| 29 | `cjhirashi-career-admin/README.md` | Variable `VITE_AI_BASE_URL` |
| 30 | `cjhirashi-career-ai/README.md` | Nuevo |
| 31 | `docs/DATABASE` / `cjhirashi-career-api/docs/sections/` de notificaciones y auditoría | Nuevos endpoints `POST /notifications`, `/audit-log` |
| 32 | `cjhirashi-career-api/docs/AUTH` (sección de autenticación en `docs/ARCHITECTURE.md`/`API.md`) | Claim `role`, rol `service`, lista de rutas |
| 33 | `cjhirashi-career-ai/docs/MEMORY.md` | Memoria FTS y migración desde Qdrant |
| 34 | `docker-compose.yml`, `caddy.json` (servicios), `prometheus.yml`, `.env.example` | Comentarios y descripciones |

## 12 · Preguntas abiertas

Las Q1–Q8 de la versión anterior quedaron resueltas por el usuario (D-15..D-22 en la spec).
Quedan **supuestos a confirmar en la Fase 3** (no bloquean el Gate 2):

- **P2.** Que la lista de rutas del rol `service` cubra las tools programadas reales
  (`generate_pdf`/render de otros recursos aún por inventariar). Ampliarla requiere cambio
  de spec.
- **P3.** Conteos reales (tablas `bedrock_*`, puntos de memoria en Qdrant) solo se obtienen
  con OK explícito del usuario para operar sobre BD/Qdrant vivos (RNF-002).

Resueltos tras el Gate 2: P1 (`access_role` es `String(32)` sin CHECK: el rol `service` no necesita migración Alembic) y P4 (full-text `spanish`, configurable por env `MEMORY_FTS_CONFIG`, D-24).
