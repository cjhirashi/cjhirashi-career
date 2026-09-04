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
- `specs/` **vacío**. No hay features en curso.
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

- **[2026-09-04] Gate en ROJO por fallo pre-existente en `cjhirashi-career-api`**
  (no causado por el fix de caddy): `ImportError: cannot import name 'Evidence'
  from 'models'` al colectar `tests/unit/test_models.py` y `test_models_extended.py`.
  Reproducido en `HEAD` limpio (a52ff41) con los cambios en stash. **Confirmado
  2026-09-04:** NO existe modelo `Evidence` — el dominio se dividió en `Achievement`,
  `StarStory`, `Project`, `WorkHistory`, etc. Los dos tests están podridos tras ese
  refactor; hay que reescribirlos contra el set de modelos actual (no es one-liner).
  Bloquea marcar `verified` cualquier cosa que toque `api/` hasta arreglarlo.
- **[2026-09-04] `.harness/gate/check.sh` con cambio sin autoría en el working tree**
  (mtime durante la sesión): añade un bloque opcional que hace `source` de
  `gate/project.sh` si existe (no existe → no-op). No lo tocamos; confirmar con el humano.

## Próximo paso concreto

- (Contrato `caddy.json` limpio: MSG-0001/0002/0003/0004 todos `resuelto`.)
- Reescritura narrativa del arc42 sin el Canal 3 (ADR-023 lo deja anotado).
- Reescribir `api/tests/unit/test_models.py` y `test_models_extended.py` contra los
  modelos actuales (ya no hay `Evidence`) para reabrir el gate.
- El humano define la primera feature. Para arrancarla: aplicar la rúbrica
  (`method.md §2`); si entra al carril SDD, Fase 1 = elicitación interactiva.
- Antes de tocar nada: correr `.harness/gate/check.sh`.
