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
- [ ] A1 Registrar prefijos en `services/id_generator.py` (plan §1). Prueba: cada tabla nueva genera ids con su prefijo.
- [ ] A2 Modelos `models/portal_site.py`, `portal_visitor.py`, `portal_visit.py`, `portal_goal.py`, `portal_funnel.py`, `portal_annotation.py`, `portal_channel_rule.py`, `portal_daily.py`; ampliar `models/portal_event.py` con las columnas del plan; exportar en `models/__init__.py`.
- [ ] A3 Migración Alembic sobre `a7c1e9d2f4b8` con tablas, columnas, índices, semillas (sitio, reglas de canal, metas) y `downgrade`. Prueba en Postgres efímero: `upgrade` y `downgrade` limpios (RF-040).
- [ ] A4 Reconstrucción de visitantes y visitas desde los eventos existentes dentro de la migración. Prueba con eventos de ejemplo: conteos de eventos intactos, una visita por `session_id`, eventos sin `session_id` agrupados por hueco de 30 min (RF-040).

### B · Servicios de dominio (puros, sin base de datos donde sea posible)
- [ ] B1 `services/portal_channels.py`: derivar canal desde referrer/UTM con reglas (RF-009). Pruebas por canal y precedencia.
- [ ] B2 `services/portal_bots.py`: `bot_score` y razones (plan §0.7) (RF-007).
- [ ] B3 `services/portal_device.py`: navegador, sistema, dispositivo con `ua-parser`; agregar la dependencia fijada (RF-006).
- [ ] B4 `services/portal_geo.py`: geo desde cabeceras `cf-*` con respaldo según `GEO_SOURCE`; ajustar `config.py` (RF-004).

### C · Ingesta
- [ ] C1 Esquema `schemas/events.py` v2 compatible con v1 (RF-001).
- [ ] C2 `services/portal_ingest.py`: bloqueo consultivo, resolver visitante y visita con corte de 30 min, `seq`, contadores, `is_engaged`, `converted`, vinculación a postulación, dueño (RF-002, 003, 008, 010).
- [ ] C3 `routes/events.py`: usar el servicio, validar `siteKey` y origen, límite de ritmo, 204 ante error (RF-011, 013). Sin persistir IP (RF-005, prueba que ninguna columna ni log la contiene).
- [ ] C4 `POST /events/forget` (RF-012).

### D · Lectura y métricas
- [ ] D1 `build_readonly_router` y registro de `portal-sites`, `portal-visitors`, `portal-visits`, `portal-events`, `portal-daily`; `portal-sites` sin claves (RF-030). Prueba: escritura devuelve 405.
- [ ] D2 CRUD de `portal-goals`, `portal-funnels`, `portal-annotations` con token de agente (RF-031).
- [ ] D3 `MetricsQuery` y constructor de filtros únicos; `overview` conserva su contrato (RF-032). Prueba de contrato contra la respuesta actual.
- [ ] D4 Endpoints `pages`, `channels`, `sources`, `geo`, `devices`, `paths`, `retention`, `realtime`, `goals`, `funnel/{id}` (RF-033).
- [ ] D5 Comparación de periodos y `sample_size` (RF-034, 037).
- [ ] D6 `portal_daily` perezosa y `rebuild` (RF-036, 022).
- [ ] D7 `dictionary` (RF-035).

### E · Conservación
- [ ] E1 `scripts/export_portal_events.py` mensual (RF-021). Prueba con rango sintético.
- [ ] E2 Verificar por prueba que ninguna ruta ni servicio borra datos salvo `forget` (RF-020).

### F · Cierre del slice
- [ ] F1 Documentación: `docs/API.md`, `docs/DATABASE.md`, README de `routes/`, `models/`, `services/`, `schemas/`, y diccionario en la skill `usar-career-api`.
- [ ] F2 Prueba de rendimiento sintética (RNF-001, RNF-002).
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
