# Analítica del portafolio — `portal-analytics`

Sistema de métricas del sitio público (`cjhirashi.com`), consultable por API para que los agentes
planteen estrategia con datos. Especificación: `.harness/specs/010-portal-analytics/`.

## Capas de datos

```mermaid
flowchart LR
    Web[Portafolio<br/>rastreador] -->|POST /events/track| Ingest[portal_ingest]
    Ingest --> Ev[(portal_events<br/>crudo inmutable)]
    Ingest --> Vis[(portal_visits)]
    Ingest --> Vr[(portal_visitors)]
    Ev -. reconstruye .-> Vis
    Vis --> Daily[(portal_daily<br/>derivado)]
    Vis --> API[/career/portal-metrics/*]
    Ev --> API
    Daily --> API
    Cfg[(portal_goals<br/>portal_funnels<br/>portal_annotations<br/>portal_channel_rules<br/>portal_sites)] --> Ingest
    Cfg --> API
```

| Tabla | Prefijo | Qué guarda |
|-------|---------|------------|
| `portal_sites` | `psi` | Sitio medido: dominio, `public_key` de ingesta, hash del token del dueño, `allowed_hosts`, zona horaria |
| `portal_visitors` | `pvr` | Visitante seudónimo (`visitor_key`, id aleatorio del navegador, sin IP): primer y último contacto, nº de visitas, primer origen, `is_bot`, `is_owner`, `legacy` |
| `portal_visits` | `pvs` | Visita (corte a 30 min): entrada/salida, referrer, UTM, canal, dispositivo, geografía, vistas, tiempo activo, `is_engaged`, `is_bounce`, `converted`, `application_id` |
| `portal_events` | `pev` | Registro inmutable de cada evento, con `visit_id`, `seq` y `props` |
| `portal_goals` / `portal_funnels` | `pgl` / `pfn` | Metas y embudos (definiciones) |
| `portal_annotations` | `pan` | Hitos sobre la gráfica (post, postulación, despliegue) |
| `portal_channel_rules` | `pcr` | Reglas editables que derivan el canal; el referrer crudo siempre se conserva |
| `portal_daily` | `pdy` | Resumen diario por dimensión; derivado y recalculable |

El crudo **nunca se borra** salvo el olvido autoservicio (`POST /events/forget`). Bots y visitas propias se
marcan, no se eliminan. `portal_visits` y `portal_daily` se pueden reconstruir desde `portal_events`.

## Ingesta pública

`POST /events/track` (sin autenticación). Acepta el payload v1 (`type`, `page`, `sessionId`, …) y el v2:
`siteKey`, `visitorId`, `title`, `targetUrl`, `referrer`, `utm`, `clickIds`, `scrollPct`, `activeMs`, `screen`,
`ownerToken`, `props`, `vitals`. Reglas:

- **Visita:** un evento se une a la visita vigente del visitante si su último evento es de hace menos de 30 min;
  los avisos pasivos (`page_duration`, `page_leave`, `scroll`, `web_vitals`) se unen hasta 24 h después.
  Un bloqueo consultivo por visitante evita visitas duplicadas con eventos simultáneos.
- **Origen:** `Origin`/`Referer` debe ser un host de `allowed_hosts` (403 si no); `siteKey` desconocida → 403;
  más de 120 eventos/min por visitante o 600 por IP → 429. Cualquier error interno responde 204.
- **Geografía:** cabeceras de Cloudflare (`cf-ipcountry`, `cf-ipcity`, `cf-region`, `cf-iplatitude`, `cf-iplongitude`,
  `cf-timezone`; requiere «Add visitor location headers»). Con `GEO_SOURCE=auto` (predeterminado) cae a ipapi.co
  si no hay `cf-ipcountry`; `cf` solo cabeceras; `ipapi` solo el servicio externo.
- **Privacidad:** la IP no se guarda en ninguna tabla ni registro; el `User-Agent` crudo vive solo en el evento.
  `POST /events/forget` `{siteKey, visitorId}` borra visitante, visitas y eventos de quien lo pide (204 siempre).
- **Dueño:** un `ownerToken` válido marca visitante y visita como `is_owner`.
- **Postulaciones:** si `utm_campaign` es igual al id de una postulación (`apl-…`), la visita se vincula a ella.

## API de lectura (rutas bajo `/career/`, también con token de agente)

Recursos de **solo lectura** (list, count, get; `skip`, `limit`≤200, `sort_by`, `sort_dir`, `since`, `until`,
`site_id`, `filters` JSON): `portal-sites` (sin claves ni hashes), `portal-visitors`, `portal-visits`,
`portal-events`, `portal-daily`. Orden predeterminado: su columna de tiempo, descendente.
Recursos con **lectura y escritura**: `portal-goals`, `portal-funnels`, `portal-annotations`.

### `/career/portal-metrics/*`

Parámetros comunes: `site_id`, `since`, `until` (o `days`, 30 por omisión), `exclude_bots` y `exclude_owner`
(ambos `true`), `filters` (JSON con claves de `/dictionary`).

| Ruta | Devuelve |
|------|----------|
| `GET /overview` | Resumen histórico (campos antiguos conservados) más `kpis`, `sample_size`, mediana y p90, `compare` |
| `GET /kpis` | Visitantes, visitas, vistas, páginas por visita, rebote, compromiso, mediana y p90 de tiempo activo, conversión, nuevos y recurrentes; `compare=previous\|year\|weekday` añade periodo comparado y deltas |
| `GET /trend` | Serie por `day\|week\|month`, anotaciones y `incomplete_from`; el día usa `portal_daily` para días cerrados |
| `GET /channels` `/sources` `/campaigns` `/geo` `/devices` `/breakdown` | Desglose por una dimensión |
| `GET /pages` | Vistas, visitantes, entradas, salidas, tasa de salida, tiempo mediano y scroll por página |
| `GET /paths` | Transiciones más frecuentes entre páginas |
| `GET /retention` | Cohortes semanales de visitantes nuevos |
| `GET /realtime` | Visitantes de los últimos minutos |
| `GET /goals` · `GET /funnel/{id}` | Conversión por meta; pasos de embudo en orden |
| `GET /dictionary` | Definiciones de métricas y filtros |
| `POST /rebuild` | Recalcula `portal_daily` (y con `include_visits=true`, las visitas) desde el crudo |

Toda respuesta agregada trae `sample_size`. Con muestras pequeñas, no concluir de porcentajes.

## Definiciones

Visita comprometida: más de 10 s de tiempo activo, o 2+ vistas, o un evento clave. Rebote: visita no comprometida.
Tiempo activo: pestaña visible, tope de 30 min por página, siempre en mediana/p90. Canales: Direct, Organic Search,
Organic Social, Email, Referral, Paid, Application, Unknown. Tráfico limpio: sin bots ni visitas del dueño.
El texto vigente sale de `GET /career/portal-metrics/dictionary`.

## Operación

- **Respaldo mensual:** `scripts/export_portal_events.sh [AAAA-MM]` exporta eventos, visitas y visitantes del mes
  a `AAAA-MM[.visits|.visitors].jsonl.gz` en `$OUT_DIR` (por defecto `/mnt/disco2/cjhirashi-data/backups/portal-analytics`).
- **Reclasificar canales:** editar `portal_channel_rules` y `POST /career/portal-metrics/rebuild?include_visits=true&since=…&until=…`.
- **Migración:** `b8d2f4a6c1e9_portal_analytics` crea las tablas, siembra el sitio, 11 reglas de canal y 5 metas, y reconstruye
  visitantes y visitas legados desde los eventos v1 (`legacy=true`). Imprime una sola vez `OWNER_TOKEN`, `PORTAL_SITE_ID` y
  `PORTAL_PUBLIC_KEY`.
