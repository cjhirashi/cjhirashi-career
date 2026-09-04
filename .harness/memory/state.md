---
tipo: memoria
subtipo: state
actualizado: 2026-09-04
---

# Estado del arnés — cjhirashi-career

## ⚠️ Correcciones del usuario (leer SIEMPRE — no borrar)

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
- **[2026-09-04] Feature `001-sidebar-contextual-por-seccion` — `verified`**
  (rama `001-sidebar-contextual-por-seccion`, commits `ffac40a` reparación gate api ·
  `6d948f7` feature · `4ec56f8` saneo tests admin/portfolio; `anchor_commit` = `6d948f7`).
  `agent_profile_id` de una sección del Admin = agente **L2** del chat contextual del
  sidebar derecho (selector sólo L2, `NULL` = sin chat); se retiran
  `chat_agent_id()`/`_L3_CHAT_FALLBACK`; `resolve_profile_for_turn` contextual sale del
  catálogo con fallback al orquestador. `sidebar_body` por vista → Markdown. Se elimina
  la columna/override `description` (migración `c4d5e6f7a8b9` — **no** corre en
  `init_db`; `alembic upgrade head` tras rebuild). Sidebar derecho condicional (sin
  chat ni instrucciones → ni panel ni botón). ADR-024. **Pendiente:** merge del PR +
  `alembic upgrade head` en el deploy.
- **[2026-09-04] Mensajes de `caddy.json` resueltos en código** (pendiente de cerrarlos
  con `bin/caddy-msg` desde el repo `cjhirashi-srv`):
  - **MSG-0002 (bloqueo):** el API volvió a `:8001` tras el restore. Corregido a `:8000`
    en `cjhirashi-career-api/Dockerfile` (EXPOSE/HEALTHCHECK/CMD) y en el healthcheck
    del `docker-compose.yml`. Rebuild + recreate hechos. Verificado: `GET /health` 200
    vía Caddy en `admin.cjhirashi.com/api/` y `portafolio.cjhirashi.com/api/`.
  - **MSG-0001 (cambio de red):** `net-cjhirashi-career` declarada `external` y añadida a
    los 5 contenedores (admin, portfolio, mcp, api, minio). Cerrado por el humano.
  - **MSG-0004 (cierre de la migración de red) — hecho 2026-09-04:** `net-cjhirashi-career`
    añadida a `postgres` y `qdrant`; luego `network-cjhirashi-srv` **quitada de los 6**
    (admin, portfolio, api, minio, postgres, qdrant) y de la sección `networks:` del
    `docker-compose.yml`. Recreados en 2 fases (verificación entre medias, como pedía el
    mensaje). Verificado: los 6 en `net-cjhirashi-career` **solamente**; api resuelve
    postgres/qdrant/minio por esa red; `admin`/`portafolio` 200, `/api/health` 200,
    `/api/public/home` 200. En `network-cjhirashi-srv` sólo quedan `caddy_proxy` (de
    cjhirashi-srv) y `admin_dev_test3` (ajeno). **MSG-0004 cerrado (`resuelto`)** por
    cjhirashi-srv el 2026-09-04 (verificaron su lado; cierra también el paso 3 de MSG-0001).
    Los 4 mensajes de `caddy.json` quedan `resuelto`. Re-verificado runtime tras su ajuste:
    los 6 sólo en `net-cjhirashi-career`, schedulers del `api` consultando Postgres OK,
    `mcp.cjhirashi.com` ya sin respuesta (host retirado).
- Repo en la rama `recover/pre-section-tables` (commit base 8227848). El backlog del
  arnés anterior **no** se importó: era sobre trabajo posterior a este commit o
  revertido. Las features nuevas las prioriza el humano.
- **[2026-09-04] MCP Server retirado** — `ADR-023`. Decisión del humano: borrar carpeta
  + pedir retiro del host + ADR/docs. Hecho en código: `git rm -r cjhirashi-career-mcp/`;
  fuera de `docker-compose.yml` y `caddy.json → servicios`; contenedor `cjhirashi-career-mcp`
  parado, borrado y sus imágenes eliminadas; CORS sin `:8004` (`.env`, `.env.example`,
  `api/src/config.py`); `AGENTS.md`/`README`/`constitution.md` (Art. 1/2/6 + enmienda)
  actualizados; `ADR-014` revisado; banner de estado en arc42 01/04/05/07/08/10/12.
  **MSG-0003 cerrado (`resuelto`)** por cjhirashi-srv: retiró `hosts.mcp`, regeneró la
  conf de Caddy sin la ruta a `cjhirashi-career-mcp` y sacó el host de DNS_RECORDS
  (la baja del registro A en Cloudflare la hace el operador a mano). `mcp.cjhirashi.com`
  ya no da 502. **Pendiente:** reescritura narrativa completa del arc42 sin el Canal 3
  (tarea de doc aparte, anotada en ADR-023).

## Decisiones tomadas (esta sesión)

- Adoptar el arnés SDD Anchored **simplificado** (repo `harness`). `ADR-001`.
- Patrón interno detectado: **por capas** (no hexagonal).
- **Retirar el MCP Server** del alcance activo (`ADR-023`): coste de mantener > valor;
  nunca implementó tools de carrera, PDF ya está in-process en la API, sin tráfico.

## Obstáculos y resolución

- **[2026-09-04] Compuerta `api` reparada** (fallos pre-existentes, no de la feature
  001). Los tests `Evidence`/`JobStrategy` ya se habían retirado (commit ff72127);
  quedaban: (a) `33 errors` por `JSONB` sin compilar en el SQLite de los fixtures;
  (b) `test_auth::test_extract_user_id_from_token` con aserción `str` vs `int`
  obsoleta; (c) `tests/integration/test_auth_integration.py` contra rutas `/api/v1/*`
  muertas (404). **Resuelto en commit aparte:** shim `@compiles(JSONB,"sqlite")` en
  `tests/conftest.py`; camino a Postgres desechable vía `TEST_DATABASE_URL`
  (+ `pytest_collection_modifyitems` que salta los tests con fixtures PG-only:
  `test_db`/`db_session`/`test_user`/…); aserción de `test_auth` corregida a `str`;
  `pytest.mark.skip` de módulo en `test_auth_integration.py`. Resultado:
  `309 passed, 72 skipped, 0 failed, 0 errors`. Existe la BD `career_db_test` en el
  contenedor `postgres_db` para el camino `TEST_DATABASE_URL` (aislada de dev).
- **[2026-09-04] Compuerta `admin`/`portfolio` saneada** (commit `4ec56f8`). El repo
  `cjhirashi-career-admin` **no versiona lockfile** (`.gitignore` lo excluye) y
  `node_modules` no traía `react-router-dom`; `npm install` lo dejó ejecutable. Los
  **14 tests pre-existentes** en rojo eran todos desalineación con el código actual
  (IDs prefijados vs numéricos, `scrollIntoView` sin stub en jsdom, `tokenExpiresAt`
  no fijado, auto-mock de axios, forma de error axios `response.data.detail`, `mb-8`
  movido de `<h1>` a contenedor, breadcrumb por CSS, nombre accesible de opción de
  `ThemedSelect`) — corregidos. `cjhirashi-career-admin` `435 passed`;
  `cjhirashi-career-portfolio` `309 passed` (`cache:false` en su `vitest.config.ts`
  para esquivar un `node_modules/.vite/vitest` con otro dueño).
- **[2026-09-04] `--full` — `cjhirashi-career-ai` sale con código 5** ("no tests"): es
  un directorio **git-ignored** (scaffold sin suite). `check.sh --full` lo lee como
  fallo; el gate por defecto no lo corre. No se toca `check.sh`.
- **[2026-09-04] `.harness/gate/check.sh` con cambio sin autoría en el working tree**
  (bloque opcional `source gate/project.sh`). No lo tocamos; confirmar con el humano.
  (Sigue sin commitear, junto con `AGENTS.md` y `.claude/`.)

## Próximo paso concreto

- **Deploy de 001:** `alembic upgrade head` en `cjhirashi-career-api` tras el rebuild
  (migración `c4d5e6f7a8b9` retira `admin_section_overrides.description`; no corre en
  `init_db`).
- Merge del PR de la rama `001-sidebar-contextual-por-seccion`.
- Aparte de 001: reescribir `cjhirashi-career-api/tests/integration/test_auth_integration.py`
  contra el esquema de rutas actual (hoy `pytest.mark.skip`); `cjhirashi-career-ai`
  sigue sin suite de tests.
- Reescritura narrativa del arc42 sin el Canal 3 (ADR-023 lo deja anotado).
- Antes de tocar nada: correr `.harness/gate/check.sh`.
