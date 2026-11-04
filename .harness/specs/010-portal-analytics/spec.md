---
titulo: "Analítica profesional del portafolio público (cjhirashi.com), consultable por API"
tipo: spec
estado: draft
fecha: 2026-11-04
feature_id: "010"
anchor_mode: advisory
anchor_commit: null
covers:
  - .harness/specs/010-portal-analytics/**
  - cjhirashi-career-api/src/models/portal_*.py
  - cjhirashi-career-api/src/schemas/portal_*.py
  - cjhirashi-career-api/src/routes/events.py
  - cjhirashi-career-api/src/routes/portal_*.py
  - cjhirashi-career-api/src/services/portal_*.py
  - cjhirashi-career-api/alembic/versions/*portal_analytics*.py
  - cjhirashi-career-api/tests/unit/test_portal_*.py
  - cjhirashi-career-api/docs/**
  - cjhirashi-career-portfolio/src/hooks/useTracking.ts
  - cjhirashi-career-portfolio/src/api/tracking.ts
  - cjhirashi-career-admin/src/pages/PortalMetrics*.tsx
---

# Analítica profesional del portafolio público

## 1 · Contexto

Hoy `portal_events` es una tabla plana (110 eventos desde 2026-10-24) y `GET /career/portal-metrics/overview` es un resumen fijo de 30 días. Una «visita» es una pestaña de navegador, no se guarda el origen del visitante, ni dispositivo, ni calidad (bots, visitas del propio dueño), el promedio de duración está contaminado por pestañas olvidadas y los agentes no pueden consultar eventos ni filtrar. Carlos pidió un sistema de métricas profesional, con conservación prolongada, que los agentes consulten por API para plantear estrategia.

Referencias estudiadas (2026-11-04): esquemas de Umami y Plausible, modelo de Matomo (crudo vs. archivo), métricas de Plausible y GA4, grupo de canales de GA4, cabeceras de ubicación de Cloudflare. Fuente en la wiki de AIRA.

## 2 · Alcance

### En alcance
- Modelo de datos en cuatro capas con `site_id` (multi-sitio): sitios, visitantes seudónimos, visitas, eventos inmutables, y tablas de configuración y resumen.
- Ingesta pública v2 compatible con el payload actual.
- API de lectura para agentes con filtros, comparación de periodos, definiciones de métricas y recursos paginados.
- Rastreador del portafolio (slice 2) y tablero del admin (slice 3).
- Conservación del crudo sin fecha de borrado y exportación mensual de respaldo.

### Fuera de alcance
- Repetición de sesiones (replay), mapas de calor, pruebas A/B, ingresos/ecommerce.
- Identificar personas (nombre, correo) o guardar IP.
- Medir otros sitios en esta entrega: el modelo lo admite (`site_id`), no se despliega para ellos.
- Alertas automáticas (se evalúan después de tener datos).

## 3 · Modelo de datos (resumen; detalle en plan.md)

| Tabla | Rol |
|---|---|
| `portal_sites` | Un sitio medido: dominio, clave pública de ingesta, hash del token del dueño, zona horaria. |
| `portal_visitors` | Visitante seudónimo (id aleatorio del navegador): primer y último contacto, nº de visitas, primer origen, `is_bot`, `is_owner`. |
| `portal_visits` | Visita real (corte a 30 min de inactividad): entrada/salida, referrer, UTM, canal, dispositivo, geografía, vistas, tiempo activo, comprometida, rebote, conversión, postulación vinculada. |
| `portal_events` | Registro inmutable (se conserva y se amplía): `site_id`, `visitor_id`, `visit_id`, `seq`, `props` JSONB. |
| `portal_goals`, `portal_funnels` | Definiciones de metas y embudos. |
| `portal_annotations` | Hitos sobre la gráfica (post publicado, postulación enviada, despliegue). |
| `portal_channel_rules` | Reglas editables para derivar el canal; el referrer crudo siempre se conserva. |
| `portal_daily` | Resumen diario por dimensión; derivado y recalculable. |

## 4 · Definiciones de métricas (contrato único, también expuesto por API)

- **Visitante:** `visitor_key` distinto en el periodo. **Visita:** secuencia de eventos del mismo visitante con huecos < 30 min.
- **Visita comprometida:** tiempo activo > 10 s, o 2+ vistas de página, o un evento clave (meta marcada `is_key_event`). **Rebote:** visita no comprometida.
- **Tiempo activo:** solo con la pestaña visible; por página se topa en 30 min. Se reporta mediana y p90, nunca promedio crudo.
- **Conversión (meta):** visitantes únicos que cumplen la meta / visitantes únicos.
- **Profundidad de scroll:** máximo porcentaje alcanzado en la página.
- **Canal:** `Direct`, `Organic Search`, `Organic Social`, `Email`, `Referral`, `Paid`, `Application` (UTM de postulación), `Unknown`; reglas en `portal_channel_rules`.
- **Tráfico limpio:** `is_bot = false` y `is_owner = false`. Es el predeterminado de toda consulta; ambos filtros se pueden desactivar.
- Toda respuesta agregada incluye `sample_size` (visitas y visitantes que la sustentan).

## 5 · Criterios de aceptación (EARS)

### Ingesta
- **RF-001** Cuando llega `POST /events/track` con el payload v1 (sin `siteKey`, `visitorId`), el sistema debe aceptarlo, asignarlo al sitio predeterminado y responder 204.
- **RF-002** Cuando llega un evento con `visitorId`, el sistema debe resolver o crear el visitante y asignar el evento a la visita vigente del visitante si su último evento es de hace menos de 30 min, o abrir una visita nueva.
- **RF-003** Cuando llegan dos eventos simultáneos del mismo visitante, el sistema no debe crear dos visitas.
- **RF-004** El sistema debe derivar de las cabeceras de Cloudflare (`cf-ipcountry`, `cf-ipcity`, `cf-region`, `cf-iplatitude`, `cf-iplongitude`, `cf-timezone`) la ubicación; si faltan, debe usar el servicio externo actual como respaldo mientras la configuración `GEO_SOURCE` sea `auto`.
- **RF-005** El sistema no debe persistir la IP del visitante en ninguna tabla ni registro.
- **RF-006** El sistema debe derivar navegador, sistema, tipo de dispositivo e idioma del `User-Agent` y `Accept-Language`, y guardar el `User-Agent` crudo solo en el evento.
- **RF-007** El sistema debe calcular `bot_score` (0–100) y razones; con puntuación ≥ 70, marcar `is_bot` en la visita y el visitante sin descartar el evento.
- **RF-008** Cuando el evento trae `ownerToken` válido para el sitio, el sistema debe marcar al visitante como `is_owner`.
- **RF-009** El sistema debe derivar el canal de cada visita al abrirla con `portal_channel_rules` y guardar referrer crudo, dominio, UTM e identificadores de clic.
- **RF-010** Cuando `utm_campaign` coincide con el identificador de una postulación, el sistema debe vincular la visita a esa postulación.
- **RF-011** Si ocurre cualquier error interno al procesar un evento, el sistema debe registrarlo y responder 204 al visitante.
- **RF-012** Cuando un visitante llama `POST /events/forget` con su `visitorId`, el sistema debe eliminar su visitante, visitas y eventos.
- **RF-013** El sistema debe rechazar eventos con `siteKey` desconocida o dominio de origen no permitido y limitar el ritmo por visitante.

### Conservación
- **RF-020** El sistema no debe borrar eventos, visitas ni visitantes automáticamente.
- **RF-021** El sistema debe exportar cada mes los eventos del mes anterior a `/mnt/disco2/cjhirashi-data/backups/portal-analytics/AAAA-MM.jsonl.gz`.
- **RF-022** Cuando se reglasifican canales o cambian definiciones, el sistema debe poder recalcular `portal_visits` y `portal_daily` desde `portal_events` sin perder datos.

### API para agentes (rutas bajo `/career/`)
- **RF-030** Los recursos `portal-sites`, `portal-visitors`, `portal-visits`, `portal-events` y `portal-daily` deben ser de solo lectura (list, count, get, filtros, orden y paginación) y accesibles con token de agente. `portal-sites` no debe exponer claves ni hashes.
- **RF-031** Los recursos `portal-goals`, `portal-funnels` y `portal-annotations` deben admitir lectura y escritura con token de agente.
- **RF-032** `GET /career/portal-metrics/overview` debe conservar su respuesta actual (campos existentes) y aceptar `site_id`, `since`, `until`, `exclude_bots`, `exclude_owner`, `compare`.
- **RF-033** Debe existir `GET /career/portal-metrics/{pages,channels,sources,geo,devices,paths,retention,realtime,goals}` y `funnel/{id}`, todos con los mismos parámetros comunes y filtros JSON (`page`, `channel`, `country`, `device`, `campaign`, `application_id`).
- **RF-034** Con `compare=previous|year|weekday`, la respuesta debe traer el periodo comparado y el delta por métrica.
- **RF-035** `GET /career/portal-metrics/dictionary` debe devolver las definiciones de la sección 4.
- **RF-036** Los agregados deben leerse de `portal_daily` para días cerrados y del crudo para el día en curso; si `portal_daily` está desactualizada respecto de las visitas, el sistema debe recalcularla antes de responder.
- **RF-037** Toda respuesta agregada debe incluir `sample_size`.

### Migración
- **RF-040** La migración debe conservar los 110 eventos existentes, reconstruir visitantes (`legacy-<session_id>`) y visitas a partir de `session_id`, y tener retroceso probado.
- **RF-041** Antes de aplicarla en producción, el sistema debe haberse respaldado y la migración ensayada en una copia con conteos y sumas idénticos antes y después.

### Rastreador del portafolio (slice 2)
- **RF-050** El rastreador debe crear un `visitorId` aleatorio en `localStorage`, salvo que el navegador envíe Do Not Track o Global Privacy Control, caso en que usa solo un id de pestaña.
- **RF-051** Debe medir tiempo activo (pestaña visible y con interacción reciente), máxima profundidad de scroll, enlaces salientes, descarga de CV, envío de formulario, apertura de proyecto y Web Vitals (LCP, INP, CLS).
- **RF-052** Debe capturar `document.referrer`, UTM e identificadores de clic de la primera página de la visita.
- **RF-053** El portafolio debe mostrar un aviso de privacidad visible y enlazado desde el pie, con la forma de borrar los propios datos.
- **RF-054** Cuando el dueño abre `/?owner=<token>`, el rastreador debe guardar el token localmente y enviarlo en adelante.

### Tablero del admin (slice 3)
- **RF-060** El tablero debe mostrar KPIs (visitantes, visitas, vistas, páginas por visita, rebote, duración mediana) con delta contra el periodo comparado, minigráfica y «visitantes ahora».
- **RF-061** Debe mostrar la gráfica principal con periodo incompleto punteado y anotaciones.
- **RF-062** Debe incluir paneles con pestañas de fuentes, páginas, ubicación y dispositivos; metas y embudo; recorridos y retención; y calidad de datos (porcentaje de bots, tamaño de muestra).
- **RF-063** Debe ofrecer selector de rango con comparación, filtros combinables y los controles «excluir bots» y «excluir mis visitas» activos por defecto.

## 6 · Requisitos no funcionales
- **RNF-001** La ingesta responde en menos de 150 ms p95 sin llamadas externas en la ruta crítica cuando la geografía llega por cabeceras.
- **RNF-002** Las consultas del tablero responden en menos de 500 ms con 1 millón de eventos (verificado con datos sintéticos).
- **RNF-003** Las pruebas no usan red ni servicios externos.
- **RNF-004** Documentación del API, de la base de datos y de cada ruta nueva en el mismo commit.

## 7 · Decisiones de Carlos (2026-11-04)
1. Visitante persistente seudónimo en `localStorage`, sin IP, con aviso de privacidad.
2. Cloudflare lo configura AIRA desde el navegador: activado «Add visitor location headers» (2026-11-04).
3. Modelo con `site_id` para medir otros sitios después.
4. Conservación prolongada del crudo.
5. Modelos de ejecución: diseño y revisión con Sonnet (AIRA); implementación con Haiku, en serie.

## 8 · Preguntas abiertas
- Mecanismo del respaldo mensual (RF-021): `crontab` del host o automatización de AIRA; se decide inspeccionando lo que ya respalda `/mnt/disco2/cjhirashi-data/backups`.
- Que las cabeceras `cf-ip*` lleguen al origen a través del túnel y Caddy está sin verificar (RF-004); el respaldo de ipapi.co cubre el caso.
