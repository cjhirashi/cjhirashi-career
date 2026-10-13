---
tipo: memoria
subtipo: state
actualizado: 2026-09-04
---

# Estado del arnés — cjhirashi-career

## ⚠️ Correcciones del usuario (leer SIEMPRE — no borrar)

### [2026-09-10] Toda feature de frontend pasa por el especialista `experto-ux-ui`
- **Qué pasó:** el usuario quiere que los frontends (`admin`, `portfolio`) estén
  siempre bien diseñados, profesionales y con buena UX — no dependiente del criterio
  del `implementador` de turno.
- **Corrección:** especialista `experto-ux-ui` añadido (`ADR-003`). Interviene en
  Fase 1/2 (flujos, estados por vista, componentes a reutilizar, `RF-` de UX) y en
  Fase 4 (revisa la UI contra estándar: contraste WCAG AA, consistencia, accesibilidad,
  responsive, microcopy) antes de que cierre el `revisor`. Constitución Art. 8.
- **Cómo aplicar:** ante una feature que toque interfaz, delega en `experto-ux-ui`;
  la spec no está lista para el Gate 1 sin su sección de UX. No escribe código de
  producción — diseña y revisa.

### [2026-09-04] El arnés no estaba forzando la Fase 1 al pedir "corrige esta falla"
- **Qué pasó:** el usuario reportó que, al pedir corregir fallas, el flujo saltaba
  directo a "arreglar/rediseñar" sin pasar por Specify. Evidencia en este mismo
  archivo: los bugs de sesión/MinIO/imágenes y el retiro del MCP Server se resolvieron
  como "Obstáculos y resolución" con commits directos, sin `spec.md`/`plan.md`/`tasks.md`.
  Causa raíz (`ADR-002`): (1) faltaba `.claude/settings.json` — sin hook `Stop`, el gate
  solo corría si el agente decidía correrlo; (2) `CLAUDE.md` perdió las "reglas duras"
  explícitas que el arnés viejo sí tenía; (3) el código heredado no tiene `spec.md`
  BASELINE (Génesis en alineación nunca sembró uno) — nada que anclar, nada que avise.
- **Corrección:** añadido el hook `Stop` (`.claude/settings.json`), reglas duras en
  `CLAUDE.md`, y dos ramas nuevas en la rúbrica de `method.md §2` (rediseña una decisión
  existente → SDD; área sin ancla + toca negocio/contrato → SDD). Desempate: en duda, SDD.
- **Cómo aplicar:** ante "arregla X"/"corrige X", clasifica con la rúbrica ANTES de
  tocar nada, en voz alta. "Área sin spec.md" no es luz verde — es la señal de que hace
  falta un spec mínimo, no de que se puede saltar Fase 1.

### [2026-09-02] No mezclar documentos del arnés con documentos del proyecto
- **Qué pasó:** se metieron manuales del arnés dentro de `docs/`.
- **Corrección:** `docs/` = producto (arc42, ADRs, diseño). `.harness/` = cómo
  operamos. Al crear un archivo, preguntar cuál de los dos es.
- **Cómo aplicar:** nada del arnés en `docs/`; nada de producto en `.harness/`.

### [2026-09-02] El implementador (sobre todo con modelos flojos) fabrica evidencia
- **Qué pasó:** entregas con "salida esperada y obtenida" en vez de salida ejecutada
  (IDs inventados, resumen de gate falso, conteos de pytest inventados), y tareas
  marcadas hechas con un test en rojo.
- **Corrección:** la evidencia DEBE ser salida de terminal **pegada**, nunca
  "esperada". El verificador re-ejecuta él mismo — no confía en el reporte.
- **Cómo aplicar:** al lanzar al implementador, pásale la evidencia real ya
  capturada; prohíbe explícitamente "salida esperada". Una tarea sin salida real
  se queda `[ ]`.

### [2026-09-02] "FASE X 100%" editando estado no es verificar
- **Qué pasó:** reportes marcaban fases completas actualizando un JSON de estado sin
  arrancar el servicio. `cjhirashi-career-ai` nunca había arrancado pese a estar
  "completo".
- **Cómo aplicar:** `verified` exige arranque real (uvicorn / compose → `GET /health`)
  o endpoint que responde con JWT real. Constitución Art. 3.

### [2026-09-02] La dev DB de Postgres no trackea Alembic del todo
- **Qué pasó:** hay cambios aplicados por `ALTER TABLE` directo.
- **Cómo aplicar:** no asumir que `alembic upgrade head` = estado real del schema.
  Verificar contra la DB. Constitución Art. 4.

## Estado del backlog

- **Génesis en modo alineación completada** (2026-09-04): arquitectura detectada y
  registrada en `constitution.md` Art. 2 + `ADR-001`.
- **[2026-09-04] Feature `001-sidebar-contextual-por-seccion` — `verified` + DESPLEGADA**
  a `main` (`ea94840` la punta; commits `ffac40a` gate api · `6d948f7` feature ·
  `4ec56f8` tests admin/portfolio · `cba8f98d` .claude+gate · `ea94840` migración
  idempotente; `anchor_commit` = `6d948f7`). `main` == `origin/main`. Stack recreado
  (`docker compose build/up` api+admin); `career_db.admin_section_overrides` sin la
  columna `description` (`alembic_version` = `c4d5e6f7a8b9`). Verificado en vivo por
  Caddy: `admin.cjhirashi.com/api/health` 200, `/admin/sections` con el shape nuevo.
  `agent_profile_id` de una sección del Admin = agente **L2** del chat contextual del
  sidebar derecho (selector sólo L2, `NULL` = sin chat); se retiran
  `chat_agent_id()`/`_L3_CHAT_FALLBACK`; `resolve_profile_for_turn` contextual sale del
  catálogo con fallback al orquestador. `sidebar_body` por vista → Markdown. Se elimina
  la columna/override `description` (migración `c4d5e6f7a8b9` — **no** corre en
  `init_db`; `alembic upgrade head` tras rebuild). Sidebar derecho condicional (sin
  chat ni instrucciones → ni panel ni botón). ADR-024. **Pendiente:** merge del PR +
  `alembic upgrade head` en el deploy.
- **[2026-09-04] Mensajes de `caddy.json` — los 4 cerrados (`resuelto`):** MSG-0001..0004
  (API en `:8000`; los 6 contenedores sólo en `net-cjhirashi-career`; host mcp retirado).
- Repo en la rama `recover/pre-section-tables` (commit base 8227848). El backlog del
  arnés anterior **no** se importó: era sobre trabajo posterior a este commit o
  revertido. Las features nuevas las prioriza el humano.
- **[2026-09-04] MCP Server retirado** — `ADR-023` (carpeta, compose, CORS, docs y host
  `mcp.cjhirashi.com` retirados; MSG-0003 cerrado). **Pendiente:** reescritura narrativa
  del arc42 sin el Canal 3.
- **[2026-10-13] Feature `007-vacantes-etapa-y-estado` — `implemented` + DESPLEGADA**
  (sin push; commits f871832f…3c5907f9 + cierre; `anchor_commit` = `3c5907f9`).
  `career_db` migrada a `c7e1a4d92b60` (backup
  `/mnt/disco2/cjhirashi-data/backups/career_db_pre_007_20261013_005618.dump`); api+admin
  recreados; KB reindexada. Gate 4 aprobado y push hecho (2026-10-13).

## Decisiones tomadas (esta sesión)

- Adoptar el arnés SDD Anchored **simplificado** (repo `harness`). `ADR-001`.
- Patrón interno detectado: **por capas** (no hexagonal).
- **Retirar el MCP Server** del alcance activo (`ADR-023`): coste de mantener > valor;
  nunca implementó tools de carrera, PDF ya está in-process en la API, sin tráfico.

## Próximo paso concreto

- **007:** Gate 4 aprobado por el usuario y subido a `origin/main` (2026-10-13).
- **[2026-09-04] Hazard CERRADO (no hubo pérdida de datos):** las tablas `admin_sections_l1/l2/l3`
  + `admin_views` de `career_db` son leftovers físicos de `origin/develop` (nunca
  fusionada a `main`, ADR-023 abandonada); el código de `main` no las referencia.
  Decisión del humano: dejarlas tal cual, sólo documentar. Si se retoma la jerarquía
  L1/L2/L3, esa migración debe cambiar de revision ID (no `c4d5e6f7a8b9`) y usar
  `IF [NOT] EXISTS`. **Regla general de migraciones: id nuevo garantizado único** —
  el 2026-09-08 la de 004 chocó con `a1b2c3d4e5f6` ya usado.
- **Cuidado al desplegar:** `docker compose up -d` puede recrear `api` con un
  `DATABASE_URL` obsoleto — usar `up -d --force-recreate --no-deps api` y verificar
  `docker inspect ... .Config.Env`.
- **[2026-10-13] Deuda (decisión del usuario, 007 D-14):** el handler global de
  `RequestValidationError` (`cjhirashi-career-api/src/app.py:144-162`) no emite RFC 9457
  (Constitución) y además da **500** si un validador lanza `ValueError` (`ctx.error` no
  serializable; arreglo de raíz: `jsonable_encoder(exc.errors())`). Afectados probables:
  `schemas/bedrock_task.py`, `career_methodologies.py`, `user.py`. Feature SDD aparte.
- **[2026-10-13] Deuda (decisión del usuario, 007 D-16):** `npm run lint` del Admin falla
  en todo el repo (228 problemas en HEAD 42b79f26): la regla
  `@typescript-eslint/explicit-function-return-types` no existe en el plugin instalado
  (config rota) + `formatCellValue` sin usar en `CareerResourceView.tsx:54`. Arreglo de
  configuración ESLint: tarea aparte.
- **[2026-10-13] Deuda (revisión UX 007, §8.1):** `formatDate` del Admin usa locale
  `en-US` en una UI en español (global, preexistente).
- Deuda: `test_auth_integration.py` (hoy `skip`) contra el esquema de rutas actual;
  `cjhirashi-career-ai` sin suite; reescritura narrativa del arc42 sin el Canal 3 (ADR-023).
- **[2026-09-04] Feature `002-generacion-imagenes-agente-visual` — CERRADA
  (`verified`).** Commits `a3c322a6` (ADR-002 arnés) · `dc9aab10` (feature, 12
  `RF-`) · `e78904bd` (anchor + verified). Gate `--full`: 24 ok · 0 warn · 0 error.
  Detalle completo en el Session-End de `history.md` y en
  `.harness/specs/002-generacion-imagenes-agente-visual/`.
  **Falsa alarma corregida:** el "403 en `files.cjhirashi.com`" reportado durante
  el cierre **no era un bug** — era Cloudflare bloqueando el User-Agent por
  defecto de `urllib` de Python (`error code: 1010`, "browser signature banned").
  Confirmado con `curl` y con un User-Agent de navegador real: ambos `200`. Las
  imágenes generadas sí cargan para cualquier cliente normal (frontend, curl,
  navegador). No se abre mensaje en `caddy.json` — no había nada que reportar.
- **[2026-09-06] Feature `003` (frentes 1–3) — `verified`.** Override de herramientas por
  agente (`bedrock_agent_profile_tools`, `GET/PUT /bedrock/agent-profiles/{id}/tools`) +
  catálogo de tools read-only (`GET /bedrock/tools/catalog`) + editor. Commit `c855a19d`.
  Migración `f7a8b9c0d1e2` aplicada. Detalle en `history.md`.
- **[2026-09-07] Feature `003` — REABIERTA (Bloque F) y re-cerrada `verified`.** El Bloque F
  ("adopción de metodologías") se había cerrado en falso con tests mockeados: en vivo el
  agente seguía sin reconocer metodologías. **Causa raíz:** índice Qdrant `career_knowledge`
  stale por una migración de IDs (enteros→`usr-2`/`opm-33`) nunca re-indexada — `_point_id`
  deriva de `resource_key:record_id` → dos generaciones acumuladas; `search` filtra
  `user_id` exacto y solo veía la minoría re-escrita (usr-2: 7 de 23 metodologías; +252
  huérfanos). **Fix (RF-010..015):** `services/bedrock/knowledge_base.py::reindex_knowledge_base`
  (idempotente, rebuild real), `POST /bedrock/knowledge-base/reindex` (operador, síncrono),
  `qdrant_service.purge_orphans` + `prune_stale_points` + borrado del gemelo heredado en
  `upsert_point`, `RESOURCE_VECTORIZE` vía `register_resource`, `set_agent_methodologies`
  fuerza reindex, `scripts/check_kb_consistency.py`. API `394 passed`. **Verificado en vivo**
  (contenedor reconstruido): reindex HTTP 200 → 265 career_record + 24 methodology, 0
  huérfanos; `check_kb_consistency.py` EXIT 0 (todo cuadra); `search_knowledge_base
  type=methodology` devuelve por perfil solo lo asignado + compartido, y ahora sí lo devuelve.
- **[2026-09-07] Feature `003` — Bloque J (lectura selectiva de metodologías) `verified`.**
  Con el índice sano, el agente recibía la metodología **truncada** (opm-61 = 15,6k > tope
  tool-results 8k). Modelo correcto: "lee sólo la metodología que ocupa este trabajo,
  entera". Fix (RF-016/017/018): `search_knowledge_base type=methodology` devuelve
  **extractos** (`record_id`, `title`, `section`, `excerpt`≤800, `read_full`) — el payload
  Qdrant de metodologías ahora lleva `title`/`section`; `get_career_record` sobre
  `operational-methodologies` usa `BEDROCK_MAX_METHODOLOGY_RESULT_CHARS = 24000` (vs global
  8000) → la metodología entra entera; el system prompt guía "buscar→leer, una por
  trabajo". API `403 passed`. **Verificado en vivo:** search devuelve extractos sin `text`;
  `get_career_record opm-61` → 15.611 chars sin truncar. 18 RF, cobertura completa.
- **[2026-09-08] Feature `004` — herramientas y metodologías por sección (L2) — `verified`.**
  ADR-027 (revisa parcialmente ADR-026, **sólo L2**). L2: herramientas **derivadas** de
  sus secciones (`admin_sections.tools_for_section`), metodologías **ligadas**
  (`operational_methodologies.section_ids`, `PUT /bedrock/sections/{id}/methodologies`);
  set del L2 = unión de todas sus secciones, resuelto 1×/turno en `agent_loop`
  (`profile_tools.resolve_effective_tools`). L1/L3 sin cambio (asignación directa).
  `PUT /agent-profiles/{L2}/tools|methodologies` → **409**. `scope` en el catálogo de
  tools; `admin_section_settings action=update` gana `views`. `applies_to_caller`
  reemplaza a `applies_to_agent`. Migración **`b3d4e5f6a7c8`** (id previo `a1b2c3d4e5f6`
  colisionaba) — aplicada en `career_db`: `section_ids` + limpieza de ids L2. API `441
  passed`, admin `437 passed`. Verificado en vivo (api+admin redeployados). Detalle en
  `.harness/specs/004-...` y `history.md`.
- **[2026-09-08] Acción pendiente del OPERADOR:** re-ligar las metodologías a sus
  secciones desde `/settings/sections/:id`. La migración quitó los vínculos a agentes L2;
  las que estaban asignadas a un L2 quedaron **compartidas** hasta que se re-liguen.
- **[2026-09-08] Pendiente de git:** **5 commits de 004** sin `git push`
  (`02110918` feature · `603b98b3`+`448d2c2b` anchor/state · `92ec40ed` fix baseline de
  tools por sección (Directiva de Pausa) · commit de anchor→`92ec40ed`). 003 ya en
  `origin/main` (`07cae9ff`). Código de 003 y 004 (incl. el fix) YA desplegado; migración
  `b3d4e5f6a7c8` aplicada en `career_db` prod.
- **[2026-09-08] 004 D-11 (Directiva de Pausa):** `search_knowledge_base` es baseline de
  TODA sección; las funcionales operativas de config declaran su meta-tool
  (`agent_catalog_settings`/`admin_section_settings`/`bedrock_global_settings`); métricas
  y visores quedan sólo con baseline (monitoreo, correcto). **Backlog:** `agent-memory`
  (sec-12) y `agent-tools`/MCP (sec-14) son operativas sin tool dedicada.
- **Operativa nueva:** tras cualquier migración que toque ids o `user_id`, correr
  `POST /bedrock/knowledge-base/reindex` y `scripts/check_kb_consistency.py` (ADR-026 §Reapertura).
- Antes de tocar nada: correr `.harness/gate/check.sh`.
