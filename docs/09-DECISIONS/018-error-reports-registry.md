# ADR-018: Registro centralizado de fallas del sistema (`error_reports`)

## Estado

Aceptado — 2026-08-27

## Contexto

Hasta ahora, cuando algo fallaba en el sistema —una excepción no controlada en la API, un
`try/except` que hacía `logger.error(...)` y seguía, un tick del scheduler in-process que
reventaba, un error del loop de Bedrock, un fallo de red en un SPA— el rastro quedaba
únicamente en los logs de contenedor (`stdout`). No había forma de responder preguntas
básicas de operación: *¿qué se ha roto?*, *¿cuántas veces?*, *¿ya lo arreglamos?*. Revisar
fallas implicaba `docker logs` + `grep` sobre varios contenedores, sin estado de "pendiente /
resuelto" ni deduplicación.

Se necesitaba: (1) una tabla que registre cada falla con su mensaje, su origen y su
fecha/hora, con un atributo que arranque "inactivo" (pendiente de revisión) y pase a "activo"
(resuelto) cuando el problema se corrige; (2) captura automática desde **todo** el sistema;
(3) un agente que revise esos reportes cuando se le pida; (4) una pantalla en el Admin para
ver pendientes y resueltos.

## Decisión

### 1. Tabla `error_reports` (PostgreSQL, IDs `err-N`)

Columnas relevantes: `message`, `source` (dónde: `api:POST /...`, `service:<módulo>.<func>`,
`scheduler:*`, `bedrock:*`, `mcp:*`, `admin:*`, `portfolio:*`), `error_type`, `stack_trace`,
`context` (JSONB), `severity` (`warning|error|critical`), **`resolved`** (booleano, arranca
`false` = pendiente), `resolution_notes`, `resolved_at`, `resolved_by`, y para agrupar
repeticiones: `fingerprint`, `occurrences`, `first_seen_at`, `last_seen_at`.

**Deduplicación por huella**: `fingerprint = sha256(source | error_type | mensaje
normalizado)` (el mensaje se normaliza colapsando dígitos, UUIDs y hex). Si ya existe una fila
**pendiente** con esa huella, se incrementa `occurrences` y se actualiza `last_seen_at` en vez
de crear otra fila. Esto evita que un error en bucle genere miles de registros. Al resolver un
reporte, una nueva ocurrencia de la misma huella crea una fila nueva (el problema reapareció).

### 2. Camino de escritura — `services/error_reporting.py`

`report_error(message, source, *, error_type, exc, context, severity)` es el punto único.
Propiedades de diseño:

- **Nunca lanza.** Un fallo al registrar la falla se traga con `logger.error`.
- **Nunca reentra** (guard con `contextvars`) — corta el bucle "error al registrar el error".
- **Engine síncrono propio (psycopg2), `NullPool`.** Independiente del event loop async de la
  app y de la sesión de la request que falló (que puede estar en rollback). Desde código async
  se usa `areport_error` (threadpool). `capture_errors(source, reraise=...)` es el context
  manager para envolver bloques (schedulers).

### 3. Captura automática

| Punto | Mecanismo |
|-------|-----------|
| Excepciones no controladas de la API | `@app.exception_handler(Exception)` → `areport_error(severity="critical")` |
| `HTTPException` | Nuevo `@app.exception_handler(StarletteHTTPException)`: 5xx → `error`; 4xx → `warning` (constante `REPORT_CLIENT_ERRORS`); 401 y 404 se omiten como ruido de fondo |
| Errores de validación | handler de `RequestValidationError` → `warning` |
| `except` que hacían `logger.error/exception` de un fallo **inesperado** o lo tragaban | se añadió `report_error(...)` junto al log, en el punto de origen (converse, image/embeddings de Bedrock, PDF, auth token, GitHub/LinkedIn API, indexado Qdrant, schedulers, loop de tools) |
| Scheduler in-process y LinkedIn scheduler | `capture_errors(..., reraise=False)` a nivel tick + `report_error` por tarea |
| Bedrock: fallo al ejecutar una tool | `report_error(source="bedrock:tool.<nombre>")` en `agent_loop` |
| MCP server | `error_reporting.py` propio → `POST /system/error-report` (no tiene BD) |
| SPA Admin y Portfolio | interceptor de axios (5xx / error de red), `window.onerror`, `unhandledrejection`, y `ErrorBoundary` (Admin) → `POST /system/error-report` |

**Regla del barrido de `except`**: sólo se instrumentan los que representan un fallo
*inesperado*. Los `except` de control de flujo esperado (`NoResultFound` → 404, validación →
400, adaptadores de `job_discovery` que prueban la siguiente fuente, feature-detection) **no**
se tocan. Los `except ...: raise HTTPException(5xx)` no se instrumentan en el punto: ya los
cubre el handler global. Migración de los `except` restantes: incremental.

### 4. Endpoints — `routes/error_reports.py`

- `POST /system/error-report` — **público**, rate-limit por IP (token bucket en memoria) +
  límite de tamaño de cuerpo. Ingesta desde los SPA y el MCP. Sin auth por diseño: el
  Portfolio es anónimo y el MCP no tiene credenciales de usuario.
- `GET /settings/error-reports` (lista con filtros `resolved`, `severity`, `source`, `q`,
  paginada), `GET .../summary`, `GET .../{id}`, `PATCH .../{id}` (`resolved` + notas →
  resolver / reabrir), `DELETE .../{id}`, `POST .../purge-resolved` — todos **JWT** (Carlos).

El camino de lectura/gestión vive en `services/error_report_service.py`, reusado por la ruta
REST **y** por la tool de Bedrock (sin lógica duplicada).

### 5. Tool de Bedrock `error_report_settings` (coherente con ADR-017)

Nueva tool del L2 `agent_settings` (`list|get|resolve|reopen|summary`). El grupo Settings del
Admin gana una 4ª pantalla (`/settings/error-reports`) con chat contextual propio —
`_ROUTE_TO_PROFILE` la mapea a `agent_settings`, igual que las otras tres.

### 6. Pantalla en el Admin — Settings → *Reportes de Falla*

Sección `settings-error-reports` (`SECTION_TABLE`, `group="Settings"`, `sort_order=93`).
Tabla con filtros (estado, severidad, búsqueda) + detalle con `stack_trace`, `context`,
ocurrencias y acciones **"Marcar como resuelto"** (con nota) / **"Reabrir"**. Badge de
pendientes en el sidebar.

### 7. Agente `revisor-fallas` (`.claude/agents/006-revisor-fallas.md`)

Agente global del proyecto. Cuando se le pide *"revisa los reportes de falla"*: consulta
`error_reports` (vía `psql` o los scripts `cjhirashi-career-api/scripts/list_error_reports.sh`
y `resolve_error_report.sh`), prioriza por severidad y ocurrencias, ubica el código por el
`source`, diagnostica la causa raíz, aplica o delega el fix, verifica, y marca el reporte como
resuelto con nota. No cierra un reporte sin haber corregido el problema.

## Consecuencias

### Positivas

- Una sola tabla responde "¿qué está roto y qué falta por arreglar?".
- Deduplicación por huella: un error en bucle es una fila con `occurrences`, no ruido.
- El agente `revisor-fallas` da un flujo repetible de triage → fix → cierre.
- Captura desde todas las capas, incluida la parte cliente de los dos SPA.

### Costos / riesgos

- **Superficie nueva sin auth**: `POST /system/error-report`. Mitigación: rate-limit por IP,
  límite de tamaño de cuerpo, normalización obligatoria, `source` con prefijo de capa.
- **Ruido / crecimiento de tabla**: mitigado con dedup por `fingerprint`, `severity`,
  omisión de 401/404, la constante `REPORT_CLIENT_ERRORS` y `POST .../purge-resolved`.
- **I/O síncrono en el camino de error**: `report_error` abre su propia conexión psycopg2;
  en handlers async se envuelve en `areport_error` (threadpool) para no bloquear el loop.
- El barrido de `except` es amplio (~40 archivos); se hizo con la regla "sólo fallos
  inesperados". Revisión recomendada por `code-quality-guardian` antes del merge.

### Alternativas rechazadas

- **Sólo logs + agregador externo (Loki/Sentry)**: no hay stack de observabilidad desplegado
  y añade infraestructura; el objetivo aquí es un flujo simple dentro del propio producto.
- **Escribir la falla en la misma sesión de BD de la request**: esa sesión puede estar en
  rollback tras el error; de ahí el engine síncrono propio.
- **Una fila por ocurrencia siempre**: la tabla crece sin control ante errores repetitivos.
- **Reescribir cada `except` del código para pasar por el helper en esta entrega**: se acotó
  a los `except` que representan fallos inesperados; el resto ya queda cubierto por el handler
  global y se migra incrementalmente.

## Referencias

- API: `src/models/error_report.py`, `src/services/error_reporting.py`,
  `src/services/error_report_service.py`, `src/routes/error_reports.py`,
  `src/schemas/error_reports.py`, `src/app.py` (handlers),
  `alembic/versions/a9b8c7d6e5f4_error_reports.py`
- Bedrock: `src/services/bedrock/tools.py` (`error_report_settings`),
  `src/services/bedrock/agent_profiles.py` (`AGENT_SETTINGS`, `_ROUTE_TO_PROFILE`)
- Admin: `src/pages/ErrorReportsPage.tsx`, `src/api/errorReports.ts`,
  `src/hooks/useErrorReports.ts`, `src/services/admin_sections.py` (`settings-error-reports`)
- SPA (cliente): `cjhirashi-career-admin/src/utils/reportClientError.ts`,
  `cjhirashi-career-portfolio/src/utils/reportClientError.ts`
- MCP: `cjhirashi-career-mcp/error_reporting.py`
- Agente: `.claude/agents/006-revisor-fallas.md`,
  `cjhirashi-career-api/scripts/list_error_reports.sh`, `resolve_error_report.sh`
- [ADR-012](./012-bedrock-three-level-agents.md) · [ADR-017](./017-l2-agent-settings.md)

---

**Creado por**: Arquitecto de Soluciones
**Fecha de creación**: 2026-08-27
**Estado de vigencia**: Vigente
