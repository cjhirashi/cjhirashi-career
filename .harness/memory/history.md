---
tipo: memoria
subtipo: history
---

# Bitácora del arnés — cjhirashi-career

> Append-only, orden cronológico inverso (lo más reciente arriba). Una entrada
> Session-End por sesión, con el formato fijo de `method.md §10`.

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
