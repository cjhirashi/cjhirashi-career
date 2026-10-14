---
tipo: memoria
subtipo: state
actualizado: 2026-10-14
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
- **[2026-10-13] 007** `verified` (usuario), desplegada (`c7e1a4d92b60`) y en `origin/main`.
- **[2026-10-13] 008** (4 textos descriptivos de vacante) implementada, revisor APPROVED,
  DESPLEGADA: `career_db` → `d8f2b5a13c97` (backup `…/backups/career_db_pre_008_20261013_170216.dump`);
  api+admin recreados; CRUD en vivo OK. Exclusión KB transitoria → la retira 009. Gate 4 OK + push.
- **[2026-10-14] 009** (harness → `cjhirashi-career-ai`, sin KB/Qdrant): Gate 1 y Gate 2 OK,
  **Fase 4**. Bloques 0, A–E hechos (T-001..T-071, revisor aprobado), punta `a191ae15`,
  en `origin/main`. Decisiones de Fase 4 del usuario: D-26, D-27 (JWT: `exp` obligatorio,
  `type` access/ausente), D-28 (metodologías con paridad exacta vía tools de lectura de
  carrera; el filtro `applies_to_caller` lo aplica el ejecutor en el bloque F).

## Decisiones tomadas (esta sesión)

- Adoptar el arnés SDD Anchored **simplificado** (repo `harness`). `ADR-001`.
- Patrón interno detectado: **por capas** (no hexagonal).
- **Retirar el MCP Server** del alcance activo (`ADR-023`): coste de mantener > valor;
  nunca implementó tools de carrera, PDF ya está in-process en la API, sin tráfico.

## Próximo paso concreto

- **009:** Bloque F — empezar por T-080 (`tests/unit/repositories/test_memory_repo.py`).
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
- **002** (`verified`, 2026-09-04), **003** (`verified` 2026-09-06; reabierta bloques F y J,
  re-cerrada 2026-09-07) y **004** (`verified`, 2026-09-08, ADR-027, migración
  `b3d4e5f6a7c8`): detalle completo en `history.md` y en sus `.harness/specs/`.
  Falsa alarma 002: el 403 de `files.cjhirashi.com` era Cloudflare bloqueando el
  User-Agent de `urllib` (error 1010), no un bug.
- **[2026-09-08] Acción pendiente del OPERADOR:** re-ligar las metodologías a sus
  secciones desde `/settings/sections/:id`. La migración quitó los vínculos a agentes L2;
  las que estaban asignadas a un L2 quedaron **compartidas** hasta que se re-liguen.
- **[2026-09-08] 004 D-11 (Directiva de Pausa):** `search_knowledge_base` es baseline de
  TODA sección; las funcionales operativas de config declaran su meta-tool
  (`agent_catalog_settings`/`admin_section_settings`/`bedrock_global_settings`); métricas
  y visores quedan sólo con baseline (monitoreo, correcto). **Backlog:** `agent-memory`
  (sec-12) y `agent-tools`/MCP (sec-14) son operativas sin tool dedicada.
- **Operativa nueva:** tras cualquier migración que toque ids o `user_id`, correr
  `POST /bedrock/knowledge-base/reindex` y `scripts/check_kb_consistency.py` (ADR-026 §Reapertura).
- Antes de tocar nada: correr `.harness/gate/check.sh`.
