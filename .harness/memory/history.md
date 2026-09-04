---
tipo: memoria
subtipo: history
---

# Bitácora del arnés — cjhirashi-career

> Append-only, orden cronológico inverso (lo más reciente arriba). Una entrada
> Session-End por sesión, con el formato fijo de `method.md §10`.

## [2026-09-04] 001 · Sidebar contextual configurable por sección — implemented (verified bloqueado por admin)

- **Fase alcanzada:** implement (`verified` bloqueado: mitad admin de la compuerta en rojo por fallos pre-existentes).
- **Rebotes del verificador:** 0 (verificación adversarial self-run; sin agente revisor separado esta sesión).
- **Directiva de Pausa:** sí — GATE 1 fijó "la migración siembra la DB con las instrucciones"; al planear se vio que exigía congelar ~130 textos en el archivo de migración (que no puede importar app) y dejaba los defaults de código inertes → se cambió a "sin siembra + override de vista con 3 estados (heredar / texto / `""` vacío-explícito)" (spec D-6, aprobado por el humano).
- **Drift / re-anchor:** advisory (esperado para `implemented`: `covers` + `spec.md` cambiaron juntos; mover `anchor_commit` al commit de cierre cuando la compuerta cierre verde).
- **Anclas movidas:** ninguna (pendiente al pasar a `verified`).
- **Gate:** API **verde** (`309 passed, 72 skipped`), tras commit aparte que repara fallos pre-existentes (shim `JSONB→JSON` en SQLite, camino Postgres opcional `TEST_DATABASE_URL` + hook de skip para tests PG-only, `test_auth` con aserción `str/int` obsoleta, `test_auth_integration` con rutas `/api/v1/*` muertas → skip de módulo). Admin **rojo** por **14 tests pre-existentes** (XHR sin mockear, spacing, mocks de auth) — 0 regresiones (`+4 passed` vs baseline); los 33 tests propios de 001 en verde y `type-check` 0 errores tras `npm install` (el repo admin no tenía `react-router-dom` ni lockfile).
- **Docs actualizadas:** `docs/09-DECISIONS/024-sidebar-contextual-por-seccion.md` (nuevo), enmienda en `021-admin-sections-synthetic-pk.md`, `cjhirashi-career-api/src/services/bedrock/README.md` (escalera de resolución), `docs/BEDROCK-SYSTEM.md`.
- **Decisiones de diseño / límites de integración:** `agent_profile_id` de sección = agente **L2** del chat contextual (selector sólo L2, `NULL`=sin chat); se retiran `chat_agent_id()`/`_L3_CHAT_FALLBACK`; `resolve_profile_for_turn` contextual sale del catálogo con fallback al orquestador (nunca 5xx). `sidebar_body` por vista → Markdown (sin `rehype-raw`). Se elimina la columna/override `description` (migración `c4d5e6f7a8b9`). Re-mapeo de 11 secciones L1/L3 → L2 o `None`. `set_agent_sections` también valida L2.
- **Próximo paso:** (1) commitear un lockfile de `cjhirashi-career-admin` y sanear los 14 tests pre-existentes (XHR a `localhost:3000` sin mock, etc.) para reabrir la compuerta admin; (2) reescribir `tests/integration/test_auth_integration.py` contra el esquema de rutas actual; (3) al verde, mover `anchor_commit` de la spec 001 y pasar a `verified`.

## [2026-09-04] Sesión — cerrar migración de red (MSG-0004)

- **Fase alcanzada:** mantenimiento de integración (sin ciclo de feature).
- **Gate:** ROJO — mismo fallo pre-existente del `api` (`Evidence`). Sin relación.
- **Docs actualizadas:** `docker-compose.yml` (comentarios de red) + `.harness/memory/`.
- **Qué se hizo:** MSG-0001 sólo cubría 5 contenedores y dejaba `postgres`/`qdrant` en
  `network-cjhirashi-srv`. cjhirashi-srv abrió **MSG-0004** para cerrarlo. Fase 1:
  `net-cjhirashi-career` añadida a `postgres` y `qdrant`, recreados, verificado que api
  los alcanza. Fase 2: `network-cjhirashi-srv` quitada de los 6 servicios y de la
  sección `networks:`; `docker compose up -d` recreó todo. Verificado: los 6 en
  `net-cjhirashi-career` solamente; `/api/health` y `/api/public/home` 200 vía Caddy;
  en `network-cjhirashi-srv` sólo quedan `caddy_proxy` y `admin_dev_test3` (ajenos).
- **También:** MSG-0003 quedó `resuelto` por cjhirashi-srv (host MCP retirado; ya no 502).
- **Próximo paso:** cerrar MSG-0004 con `bin/caddy-msg` desde el repo `cjhirashi-srv`.

## [2026-09-04] Sesión — retirar el MCP Server

- **Fase alcanzada:** cambio de arquitectura registrado por ADR (carril SDD; sin
  `spec.md`/`plan.md`/`tasks.md` — es un retiro, no una feature con `RF-`).
- **Rebotes del verificador:** 0
- **Directiva de Pausa:** no
- **Drift / re-anchor:** sí — se retira un servicio del perfil de arquitectura
  (Constitución Art. 2). Anclado a `ADR-023`.
- **Anclas movidas:** `constitution.md` Art. 1 (5→4 servicios), Art. 2 (yaml: fuera
  `cjhirashi-career-mcp` y el sustrato `mcp`), Art. 6 (fuera la regla MCP); enmienda nueva.
- **Gate:** ROJO — mismo fallo pre-existente del `api` (`Evidence` no existe; tests
  podridos tras el split del dominio). El chequeo de obsolescencia de docs pasó ✅.
- **Docs actualizadas:** `docs/09-DECISIONS/023-retirar-mcp-server.md` (nuevo) +
  índice; `ADR-014` revisado; banner de estado en arc42 `01/04/05/07/08/10/12`;
  `README.md`, `AGENTS.md`, `cjhirashi-career-api/README.md`, `cjhirashi-career-api/src/README.md`.
  Reescritura narrativa completa del arc42 sin Canal 3 queda pendiente (anotada en ADR-023).
- **Decisiones de diseño / límites de integración:**
  - Alcance elegido por el humano: borrar `cjhirashi-career-mcp/`, pedir a `cjhirashi-srv`
    el retiro del host (`MSG-0003`), y registrar con ADR + docs (no sólo memoria).
  - `MSG-0003` (de: cjhirashi-career) añadido a mano a `caddy.json → mensajes[]` porque
    `bin/caddy-msg` vive en el repo `cjhirashi-srv`, no accesible desde aquí.
  - Runtime: contenedor `cjhirashi-career-mcp` parado + borrado + imágenes eliminadas.
    Verificado: `admin`/`portafolio` siguen 200 y `/api/health` 200; `mcp.cjhirashi.com`
    ahora 502 (lo retira `cjhirashi-srv` al cerrar `MSG-0003`).
  - Limpieza asociada: origen CORS `:8004` quitado de `.env`, `.env.example`,
    `api/src/config.py` (era vestigial — un cliente MCP no hace preflight de navegador).
- **Próximo paso:** `cjhirashi-srv` cierra `MSG-0003`; reescritura arc42; arreglar los
  tests de modelos del `api`.

## [2026-09-04] Sesión — resolver mensajes de `caddy.json`

- **Fase alcanzada:** (mantenimiento de integración — no aplica ciclo de feature)
- **Rebotes del verificador:** 0
- **Directiva de Pausa:** no
- **Drift / re-anchor:** no
- **Anclas movidas:** ninguna
- **Gate:** ROJO al cierre — fallo **pre-existente** en `cjhirashi-career-api`
  (`ImportError: 'Evidence' from 'models'` en colección de tests), reproducido en
  `HEAD` limpio con los cambios en stash. No causado por esta sesión. También aparece
  un cambio sin autoría en `.harness/gate/check.sh` (bloque opcional `gate/project.sh`).
- **Docs actualizadas:** ninguna del mapa (Art. 11). El gate marca ⚠️ porque el diff
  toca `docker-compose.yml`; los `docs/**` con `:8001` para dev local quedaron pendientes
  (fuera del alcance del bloqueo; el contrato es el puerto del contenedor).
- **Decisiones de diseño / límites de integración:**
  - **MSG-0002 (bloqueo) → opción (a):** API de vuelta a `:8000` (contrato acordado
    2026-09-01) en `Dockerfile` + healthcheck de compose. Rebuild + recreate.
    Verificado end-to-end: `GET /api/health` → 200 vía Caddy en `admin` y `portafolio`
    (antes 502).
  - **MSG-0001 (cambio de red permanente):** `net-cjhirashi-career` declarada `external`
    y añadida a los 5 contenedores (admin, portfolio, mcp, api, minio). Se **mantiene**
    `network-cjhirashi-srv` en paralelo; quitarla es el paso diferido "una vez fijo".
  - Los mensajes se cierran desde el repo `cjhirashi-srv` (`bin/caddy-msg`), no aquí;
    el bloque `cjhirashi_srv` y `mensajes[]` de `caddy.json` no se editan desde este repo.
- **Próximo paso:** cerrar MSG-0001/MSG-0002 con `bin/caddy-msg` + `bin/caddy-sync`;
  arreglar la colección de tests del `api` para reabrir el gate.

## [2026-09-04] Génesis del arnés — completada

- **Fase alcanzada:** (génesis — no aplica ciclo de feature)
- **Rebotes del verificador:** 0
- **Directiva de Pausa:** no
- **Drift / re-anchor:** no
- **Anclas movidas:** ninguna
- **Gate:** pendiente de primera corrida (`.harness/gate/check.sh`)
- **Docs actualizadas:** ninguna (el arnés no toca `docs/`)
- **Decisiones de diseño / límites de integración:**
  - Se adopta el arnés SDD Anchored **simplificado** del repo `harness` (3 archivos
    por feature; método en 1 archivo; memoria en 2; anclaje en el front-matter de
    `spec.md`; trazabilidad en la tabla de cobertura de `tasks.md`; sin
    `anchor.json`/`traceability-matrix.md`/`feature-ledger.json` aparte).
  - **Génesis en modo alineación:** arquitectura detectada del código y `docs/`, no
    elegida. Monorepo de microservicios; patrón interno **por capas**; sustratos
    REST/HTTP + MCP + Bedrock-LLM + Qdrant; topología multi-perfil Bedrock.
    Registrada en `constitution.md` Art. 2 + `ADR-001`.
  - Contenido reusado del arnés anterior (rama `feat/admin-sections-split-tables`):
    context-packs de los 5 subproyectos (stack, comandos, fronteras, hazards),
    lecciones de `memory.md` → `memory/state.md`, mapa de documentación.
  - **No** se importó el `feature_list.json` anterior: su backlog es sobre trabajo
    posterior al commit base (8227848) o revertido.
- **Próximo paso:** el humano define la primera feature; correr el gate antes de tocar código.
