---
titulo: "Tasks — Analítica profesional del portafolio"
tipo: tasks
estado: draft
fecha: 2026-11-04
feature_id: "010"
spec: ./spec.md
plan: ./plan.md
---

# Tareas (atómicas, TDD: prueba antes que código)

Marcar `[x]` solo con salida de terminal pegada. Rutas relativas a `cjhirashi-career-api/` salvo que se indique. Pytest con `@pytest.mark.requisito("RF-0NN")`. Sin red ni servicios externos en pruebas. **[REQUIERE OK]** = toca producción; lo ejecuta AIRA, nunca el implementador.
Ejecutor: Haiku implementa por bloque; AIRA revisa cada bloque (Converge) y ejecuta lo marcado REQUIERE OK.

## Slice 1 · API

### A · Modelos y migración
- [x] A1 Registrar prefijos en `services/id_generator.py` (plan §1). Prueba: cada tabla nueva genera ids con su prefijo.
- [x] A2 Modelos `models/portal_site.py`, `portal_visitor.py`, `portal_visit.py`, `portal_goal.py`, `portal_funnel.py`, `portal_annotation.py`, `portal_channel_rule.py`, `portal_daily.py`; ampliar `models/portal_event.py` con las columnas del plan; exportar en `models/__init__.py`.
- [x] A3 Migración Alembic sobre `a7c1e9d2f4b8` con tablas, columnas, índices, semillas (sitio, reglas de canal, metas) y `downgrade`. Prueba en Postgres efímero: `upgrade` y `downgrade` limpios (RF-040).
- [x] A4 Reconstrucción de visitantes y visitas desde los eventos existentes dentro de la migración. Prueba con eventos de ejemplo: conteos de eventos intactos, una visita por `session_id`, eventos sin `session_id` agrupados por hueco de 30 min (RF-040).

### B · Servicios de dominio (puros, sin base de datos donde sea posible)
- [x] B1 `services/portal_channels.py`: derivar canal desde referrer/UTM con reglas (RF-009). Pruebas por canal y precedencia.
- [x] B2 `services/portal_bots.py`: `bot_score` y razones (plan §0.7) (RF-007).
- [x] B3 `services/portal_device.py`: navegador, sistema, dispositivo con `ua-parser`; agregar la dependencia fijada (RF-006).
- [x] B4 `services/portal_geo.py`: geo desde cabeceras `cf-*` con respaldo según `GEO_SOURCE`; ajustar `config.py` (RF-004).

### C · Ingesta
- [x] C1 Esquema `schemas/events.py` v2 compatible con v1 (RF-001).
- [x] C2 `services/portal_ingest.py`: bloqueo consultivo, resolver visitante y visita con corte de 30 min, `seq`, contadores, `is_engaged`, `converted`, vinculación a postulación, dueño (RF-002, 003, 008, 010).
- [x] C3 `routes/events.py`: usar el servicio, validar `siteKey` y origen, límite de ritmo, 204 ante error (RF-011, 013). Sin persistir IP (RF-005, prueba que ninguna columna ni log la contiene).
- [x] C4 `POST /events/forget` (RF-012).

### D · Lectura y métricas
- [x] D1 `build_readonly_router` y registro de `portal-sites`, `portal-visitors`, `portal-visits`, `portal-events`, `portal-daily`; `portal-sites` sin claves (RF-030). Prueba: escritura devuelve 405.
- [x] D2 CRUD de `portal-goals`, `portal-funnels`, `portal-annotations` con token de agente (RF-031).
- [x] D3 `MetricsQuery` y constructor de filtros únicos; `overview` conserva su contrato (RF-032). Prueba de contrato contra la respuesta actual.
- [x] D4 Endpoints `pages`, `channels`, `sources`, `geo`, `devices`, `paths`, `retention`, `realtime`, `goals`, `funnel/{id}` (RF-033).
- [x] D5 Comparación de periodos y `sample_size` (RF-034, 037).
- [x] D6 `portal_daily` perezosa y `rebuild` (RF-036, 022).
- [x] D7 `dictionary` (RF-035).

### E · Conservación
- [x] E1 `scripts/export_portal_events.py` mensual (RF-021). Prueba con rango sintético.
- [x] E2 Verificar por prueba que ninguna ruta ni servicio borra datos salvo `forget` (RF-020).

### F · Cierre del slice
- [x] F1 (la skill usar-career-api es del sistema y no la puedo editar: el diccionario se sirve en /career/portal-metrics/dictionary; pedir a main que la actualice) Documentación: `docs/API.md`, `docs/DATABASE.md`, README de `routes/`, `models/`, `services/`, `schemas/`, y diccionario en la skill `usar-career-api`.
- [x] F2 Prueba de rendimiento sintética (RNF-001, RNF-002). RNF-002 se acotó a ventanas de 30 días por decisión de Carlos (2026-11-04); ver evidencia.
- [ ] F3 **[REQUIERE OK]** Respaldo, ensayo en copia, aplicar migración en producción, desplegar API, verificar `overview`, verificar cabeceras `cf-ip*` con una petición real y fijar `GEO_SOURCE`.
- [ ] F4 Respaldo mensual programado (RF-021). **[REQUIERE OK]**
- [ ] F5 Push y checkpoint de Carlos.

## Slice 2 · Rastreador del portafolio
- [ ] G1 `useTracking.ts`: visitor id, DNT/GPC, tiempo activo, scroll, salientes, descargas, formulario, proyecto, Web Vitals, referrer/UTM (RF-050 a 052, 054). Vitest por requisito.
- [ ] G2 Aviso de privacidad y borrado propio (RF-053).
- [ ] H1 Despliegue del portafolio y verificación en Chromium real. **[REQUIERE OK]**

## Slice 3 · Tablero del admin
- [ ] I1 Hooks y tipos de los endpoints nuevos.
- [ ] I2 Página de métricas según RF-060 a 063, con verificación visual contra capturas reales a 1280 y 390 px.
- [ ] J1 Despliegue del admin y verificación. **[REQUIERE OK]**

## Evidencia (AIRA, 2026-11-04)
- Bloque A: pytest `test_portal_analytics_models.py`, `test_portal_analytics_migration.py`, `test_portal_events.py` en verde (29). La prueba de migración es estructural; la ejecución real se verificó sobre una copia restaurada de producción (pg_dump a Postgres desechable): `upgrade` siembra sitio, 11 reglas y 5 metas, reconstruye 60 visitantes y 65 visitas desde los 110 eventos (110 con `visit_id`, 73 vistas de página, `created_at` y suma de `duration_ms` intactos), `downgrade` devuelve `portal_events` a sus 16 columnas y 110 filas, y un segundo `upgrade` repite el resultado.
- Correcciones de AIRA a la entrega de Haiku: dueño del sitio tomado de `PUBLIC_PORTAL_USER_ID` (Haiku usaba el primer usuario), JSONB con `CAST` (Haiku usaba `sa.json.dumps`, inexistente), sin `conn.commit()` dentro de Alembic, reglas de canal completas (faltaban referrers sociales y de búsqueda), reconstrucción A4 (no entregada).
- Bloque B: 55 pruebas en verde (`test_portal_channels/bots/device/geo.py`) ejecutadas por AIRA; `ua-parser[regex]==1.0.2` fijado. Corrección de AIRA: `cf-ipcountry` en minúsculas ("xx") ya se trata como desconocido. Haiku reportó 76 pruebas sumando regresiones y pegó una salida con erratas; la cifra verificada es 55 nuevas.
- Bloque C1-C2: 52 pruebas en verde (24 de ingesta con Postgres real, 36 de esquema v2 y goal_matches). Haiku entregó el servicio con las pruebas de base de datos sin ejecutar y varias comprobando el defecto («con reglas vacías el canal debe ser Unknown»). Correcciones de AIRA: carga de reglas de canal desde `portal_channel_rules`, vinculación a `applications`, `visit_count` por visita (Haiku lo sumaba por evento), cabecera `User-Agent` como respaldo, marca de dueño sobre la visita vigente, sitio predeterminado con varios sitios; prueba de concurrencia real con 5 ingestas simultáneas, verificada por mutación (sin el bloqueo consultivo falla con violación de unicidad).
- Bloque C3-C4 (escrito por AIRA, sin subagente: pegamento con peso en seguridad): `routes/events.py` v2 con validación de Origin (403), límite de ritmo por visitante e IP (429), 204 ante error interno y `POST /events/forget` autoservicio (204 siempre, no permite sondear ids). 14 pruebas en verde con Postgres real, incluida la comprobación de que ninguna columna de ninguna tabla `portal_*` contiene la IP.
- Bloque D3-D7 (escrito por AIRA: SQL de métricas, donde se concentra el riesgo): motor `services/portal_metrics.py` con constructor único de filtros, KPIs con definiciones GA4, desgloses, páginas, recorridos, retención semanal, metas, embudo en orden, tendencia con `portal_daily` perezosa y comparación de periodos; `overview` conserva sus campos históricos. 21 pruebas con Postgres real y expectativas calculadas a mano (excluye bots y dueño, mediana/p90, orden del embudo, retención). Contra la copia de producción: con bots y dueño suma las 73 vistas históricas; en tráfico limpio, 63 (10 son de bots).
- Bloque D1-D2 (subagente Haiku detenido a mitad; AIRA completó): las pruebas que dejó Haiku usaban `TestClient` síncrono sobre una sesión asíncrona y fallaban con «attached to a different loop». AIRA reescribió `tests/unit/test_portal_analytics_routes.py` con el patrón de `test_portal_metrics_routes.py` (18 pruebas) y corrigió tres defectos de la ruta: rango de fechas en columnas `Date` (`portal-daily`) comparado como datetime, `sort_by` aceptaba atributos que no son columnas (ahora 400) y bloque de rango duplicado en `list`/`count` (ahora `_time_range`). La validación de funnel (mínimo 2 pasos) estaba en `__init__`, que FastAPI no ejecuta al validar el cuerpo: pasó a `Field(min_length=2)`. Resultado: `test_portal_analytics_routes.py` 18/18 en verde; regresión `test_portal_metrics_routes`, `test_portal_events_route`, `test_portal_metrics_engine`, `test_portal_ingest` 56/56 en verde.
- F2 (AIRA, parcial, RNF-002 **no** cumplido): `scratch/perf_bench.py` contra `perf` (1 M eventos, 300 k visitas, 150 k visitantes), mediana de 3 corridas, sin carga concurrente. Antes: los índices compuestos de la migración no existían en `perf` (se creó con `create_all`; los modelos no declaran índices). Creados a mano en `perf` (no en producción) y medidos. Corrección: `retention` acotaba la actividad por visitante sin ventana de fechas (escaneo de 300 k visitas); ahora se acota a la ventana más `weeks`+2 semanas; 90 d bajó de 664 a 199 ms; pruebas `test_portal_metrics_engine` + `test_portal_metrics_routes` 23/23 en verde.
  - 90 d (ms): sample_size 145, kpis 256, breakdown canal 240, país 193, **pages 829**, paths 353, retention 199, trend día 102, trend semana 186. Todo bajo 500 ms salvo `pages`.
  - 365 d (ms): sample_size 429, kpis 742, canal 651, país 581, **pages 2026**, paths 1135, retention 1394, trend día 449, trend semana 615, ensure_daily_fresh caliente 453; rebuild_daily frío 26 484. Más de la mitad fuera de meta.
  - Causa: `pages` lee el total de eventos (seq scan de 1 M) porque la ventana de 90 d cubre el 25 % de las visitas, y repite el subconjunto de visitas en 4 consultas; `retention` 365 d y `kpis` 365 d procesan ~300 k visitas en una sola pasada (agregación y percentiles), no son problema de índices.
  - Decisión de Carlos (2026-11-04): declarar los índices en los modelos (hecho: `PortalVisit` y `PortalEvent` ahora declaran los mismos 8 índices compuestos de la migración, así `create_all` y Alembic coinciden); intentar `pages` en una sola consulta; bajar la meta de RNF-002 a 30 días.
  - `pages` en una sola consulta **descartado por medición** (90 d, mediana): original 829 ms, con CTE 1014 ms, con función de ventana 957 ms (EXPLAIN en SQL); un plan por bucle anidado e índice tarda 569 ms contra 313 ms del hash. Se revirtió a la versión original. El coste de `pages` es leer los ~235 mil eventos de la ventana, no la forma de la consulta.
  - **30 d (ms), cumple RNF-002:** ensure_daily_fresh 34, sample_size 42, kpis 66, canal 56, país 52, pages 371, paths 162, retention 85, trend día 43, trend semana 57, realtime 20. Todas bajo 500.
  - 90 d: todas bajo 500 salvo `pages` (729 a 829). 365 d: ver medidas arriba; sin meta.
  - **RNF-001 cumplido:** `scratch/perf_ingest.py`, 600 peticiones a `POST /events/track` en proceso contra `perf` (1 M eventos, índices compuestos), límites de ritmo desactivados: p50 11.7 ms, p95 20.1 ms, p99 24.6 ms, máx 254 ms (arranque en frío); 600 eventos persistidos (verificado por conteo SQL). No incluye red ni Caddy. Una primera corrida dio 11 ms p95 pero era falsa: las secuencias de ids de `perf` no estaban avanzadas, todas las inserciones fallaron y la ruta devolvió 204 (RF-011). Corregido con `setval`.
  - Pruebas tras los cambios: `test_portal_metrics_engine` + `test_portal_metrics_routes` 23/23; `test_portal_analytics_models` + `test_portal_analytics_migration` en verde.
- Bloque E y RF-022 (AIRA): `scripts/export_portal_events.sh` (eventos, visitas y visitantes del mes a JSONL comprimido; probado contra la copia: 105 eventos de octubre, igual al conteo SQL, mes inválido rechazado) y `rebuild_visits` (reclasifica canal y recalcula contadores desde el crudo; `POST /rebuild?include_visits=true`). Prueba de que solo `/events/forget` borra datos crudos. **Corrección de especificación:** `/mnt/disco1/openclaw-backup` es un archivo gzip de 791 MB, no una carpeta; el destino del respaldo pasa a `/mnt/disco2/cjhirashi-data/backups/portal-analytics/` (junto a los volcados de BD existentes, en otro disco que el Postgres). Crear esa carpeta y programar el respaldo requiere autorización de Carlos (F4).
