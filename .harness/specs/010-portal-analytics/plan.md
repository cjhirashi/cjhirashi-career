---
titulo: "Plan 010 — Analítica profesional del portafolio"
tipo: plan
estado: draft
fecha: 2026-11-04
feature_id: "010"
spec: ./spec.md
---

# Plan 010 — Analítica profesional del portafolio

## 0 · Decisiones de diseño
1. **Crudo inmutable, todo lo demás derivable.** `portal_events` es la fuente; visitas, visitantes y `portal_daily` se pueden reconstruir con `services/portal_rebuild.py`. Esto sostiene RF-022 y el cambio futuro de definiciones.
2. **La visita se calcula en la ingesta** (no en lecturas): una fila de `portal_visits` por visita, actualizada con cada evento (`last_activity_at`, contadores). Evita consultas de sesionización pesadas.
3. **Concurrencia (RF-003):** `pg_advisory_xact_lock(hashtext(site_id || visitor_key))` al inicio de la transacción de ingesta; sin bloqueo global.
4. **Aislamiento:** todas las tablas llevan `user_id` (dueño del portafolio) igual que el resto del dominio, más `site_id`. La API de agentes aplica el mismo aislamiento por `user_id` que `CareerRepository`.
5. **Resúmenes diarios perezosos (RF-036):** no hay planificador. Al leer, para cada día cerrado del rango se compara `portal_daily.computed_at` con `max(portal_visits.updated_at)` del día y se recalcula si está desfasado. `POST /career/portal-metrics/rebuild` fuerza el recálculo.
6. **Geo por cabeceras con respaldo:** `GEO_SOURCE=auto|cf|ipapi`. `auto` usa `cf-ipcountry` y compañía si existen y cae a ipapi.co solo si no hay `cf-ipcountry`. Cuando se verifique que las cabeceras llegan, se fija `cf` y se retira `geo_ip_service`.
7. **Bots:** puntuación aditiva y explicable (`bot_reasons`): UA de rastreador o headless (+80), sin `Accept-Language` (+20), sin `visitorId` de cliente real tras 5 eventos (+10), visita de 1 página con menos de 1 s activo y sin scroll (+15). Umbral 70. Nunca se borra.
8. **Dispositivo:** biblioteca `ua-parser` (Python puro, sin red), nueva dependencia a fijar en `requirements.txt`.

## 1 · Esquema (nombres de columnas definitivos)

IDs prefijados registrados en `services/id_generator.TABLE_PREFIXES`: `portal_sites=psi`, `portal_visitors=pvr`, `portal_visits=pvs`, `portal_goals=pgl`, `portal_funnels=pfn`, `portal_annotations=pan`, `portal_channel_rules=pcr`, `portal_daily=pdy`. `portal_events` conserva `pev`.

### portal_sites
`id`, `user_id`, `name`, `domain` (único), `public_key` (único, 24 car. aleatorios; se envía en el payload), `owner_token_hash` (SHA-256), `allowed_hosts` (JSONB), `timezone` (`America/Mexico_City`), `active`, `created_at`.

### portal_visitors
`id`, `user_id`, `site_id`, `visitor_key` (único con `site_id`), `first_seen`, `last_seen`, `visit_count`, `first_referrer_domain`, `first_channel`, `first_utm_source`, `first_utm_medium`, `first_utm_campaign`, `country`, `is_bot`, `bot_score`, `is_owner`, `legacy` (bool), `created_at`.

### portal_visits
`id`, `user_id`, `site_id`, `visitor_id`, `started_at`, `last_activity_at`, `entry_page`, `exit_page`, `referrer_url`, `referrer_domain`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `click_id_type`, `channel`, `source`, `device_type`, `browser`, `browser_version`, `os`, `os_version`, `screen_size`, `language`, `country`, `region`, `city`, `latitude`, `longitude`, `timezone`, `is_bot`, `bot_score`, `bot_reasons` (JSONB), `is_owner`, `is_new_visitor`, `pageviews`, `events_count`, `active_ms`, `max_scroll_pct`, `is_engaged`, `is_bounce`, `converted`, `application_id` (nullable, sin FK dura), `created_at`, `updated_at`.
Índices: `(site_id, started_at)`, `(visitor_id, last_activity_at DESC)`, `(site_id, channel, started_at)`, `(site_id, country, started_at)`, `(application_id)`.

### portal_events (ampliación; columnas nuevas nullable)
`site_id`, `visitor_id`, `visit_id`, `seq` (orden dentro de la visita), `page_title`, `props` (JSONB, reutiliza `event_metadata` para compatibilidad), `scroll_pct`, `active_ms`, `target_url`. `event_type` admite: `pageview`, `page_leave`, `click`, `download`, `form_submit`, `scroll`, `outbound`, `project_open`, `web_vitals`, `page_duration` (heredado).
Índices nuevos: `(site_id, created_at)`, `(visit_id, seq)`, `(visitor_id, created_at)`.

### portal_goals / portal_funnels / portal_annotations / portal_channel_rules
- goals: `name`, `type` (`event`|`page`|`outbound`|`min_active`|`min_pages`), `match` (JSONB), `is_key_event`.
- funnels: `name`, `steps` (JSONB `[{label,type,match}]`).
- annotations: `day`, `title`, `kind` (`blog_post`|`application`|`deploy`|`other`), `ref`.
- channel_rules: `priority`, `channel`, `conditions` (JSONB), semillas por la migración con reglas estilo GA4 (referrers de buscadores, redes sociales, medio `email`, medio `postulacion`, directo).

### portal_daily
`id`, `user_id`, `site_id`, `day`, `dimension` (`total`, `page`, `entry_page`, `exit_page`, `channel`, `source`, `country`, `device`, `browser`, `os`, `campaign`), `key`, `visitors`, `visits`, `pageviews`, `engaged_visits`, `bounces`, `active_ms_sum`, `conversions`, `computed_at`. Solo tráfico limpio; único `(site_id, day, dimension, key)`.

## 2 · Ingesta v2 (`routes/events.py` + `services/portal_ingest.py`)
Payload nuevo (v1 sigue válido): `siteKey`, `visitorId`, `type`, `page`, `title`, `target`, `targetUrl`, `referrer`, `utm` (objeto), `clickIds`, `scrollPct`, `activeMs`, `screen`, `language`, `ownerToken`, `props`, `vitals`.
Flujo: validar (`siteKey` y `Origin`/`Referer` contra `allowed_hosts`, límite de ritmo en memoria por visitante) → bloqueo consultivo → resolver visitante → resolver o abrir visita → insertar evento con `seq` → actualizar contadores de la visita y banderas (`is_engaged`, `converted`) → commit. Cualquier excepción se registra y devuelve 204.
`POST /events/forget` borra visitante, visitas y eventos de un `visitorId` (RF-012).

## 3 · API de lectura (`routes/portal_analytics.py`, `routes/portal_metrics.py`)
- Fábrica `build_readonly_router(...)` en `career_common.py`: reutiliza `list_for_user`, `count`, `get`, `filters` JSON; sin POST, PUT ni DELETE. Para `portal-sites` el esquema de respuesta omite `public_key` y `owner_token_hash`.
- `portal-goals`, `portal-funnels`, `portal-annotations` usan `build_crud_router` normal (`vectorize=False`).
- `portal_metrics.py` se amplía con los endpoints de RF-033 sobre un `MetricsQuery` común (`site_id`, `since`, `until`, `exclude_bots`, `exclude_owner`, `compare`, `filters`) y un constructor de cláusulas único para que todas las métricas filtren igual.

## 4 · Migración
Revisión nueva sobre `a7c1e9d2f4b8`. Pasos: crear tablas nuevas → ampliar `portal_events` → sembrar el sitio `cjhirashi.com` (clave generada, token del dueño generado e impreso una sola vez) y reglas de canal → reconstruir visitantes y visitas desde `session_id` (`legacy=true`) → crear metas semilla (`cv_download`, `contact_submit`, `outbound_linkedin`, `outbound_github`, `project_open`) → índices. Retroceso: elimina lo nuevo y las columnas añadidas; `portal_events` original queda intacto. Respaldo previo con `pg_dump` de `portal_events` y verificación de conteos, `min/max(created_at)` y suma de `duration_ms` antes y después.

## 5 · Estrategia de pruebas
Pytest sobre Postgres efímero (`TEST_DATABASE_URL`) para sesionización, concurrencia y migración; SQLite solo para unitarias puras. Cobertura obligatoria por requisito, marcada `@pytest.mark.requisito("RF-0NN")`: corte de 30 min, doble evento simultáneo, canal por reglas, vinculación a postulación, bots, dueño, olvido, v1 compatible, solo lectura (405 en escritura), ocultamiento de claves, comparación de periodos, desfase de `portal_daily`, y migración con retroceso. Datos sintéticos de 1 M eventos para RNF-002.

## 6 · Riesgos
| Riesgo | Mitigación |
|---|---|
| Migración sobre producción | Respaldo, ensayo en copia, retroceso probado, ventana corta |
| Cabeceras `cf-ip*` no llegan al origen | `GEO_SOURCE=auto` con respaldo; verificación explícita antes de retirar ipapi.co |
| Cambiar el payload rompe el portafolio en producción | v1 sigue aceptado; el rastreador nuevo se despliega después |
| Datos personales | Sin IP, id aleatorio, respeto a DNT/GPC, aviso, `POST /events/forget` |
| Muestra pequeña engaña | `sample_size` en toda respuesta; el tablero muestra la muestra siempre |

## 7 · Secuencia de entrega
- **Slice 1** (API): tareas A–F del `tasks.md`. Checkpoint de Carlos al final.
- **Slice 2** (rastreador del portafolio): tareas G–H. Se despliega solo tras verificar Slice 1 en producción.
- **Slice 3** (tablero del admin): tareas I–J, tras el checkpoint de los dos primeros.
