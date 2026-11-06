# Escenarios de calidad - cjhirashi-career

**ESCENARIOS DE CALIDAD** (arc42, sección 10)

**Última actualización**: 2026-11-05
**Resumen**: 6 atributos de calidad, 24 escenarios con estímulo, medida, estado y evidencia. El sistema está en producción: el estado refleja lo medido o verificado, y lo que no se ha medido se dice como tal.

---

## Cómo leer este documento

Cada escenario tiene **Estímulo**, **Medida**, **Estado** (✅ cumple · ⚠️ parcial · ❌ pendiente) y **Evidencia**. Un estado ❌ «no medido» no significa que falle: significa que no hay medición. El marco de referencia es la Constitución del arnés (`.harness/constitution.md`).

## Rendimiento

| # | Escenario | Medida | Estado | Evidencia |
|---|---|---|---|---|
| P1 | Carga del Admin: la SPA es interactiva | TTI < 2 s en P95 | ❌ no medido | Sin medición de TTI en producción |
| P2 | Tablero de analítica casi en vivo | `GET /career/portal-metrics/realtime` cada 20 s; el evento aparece en la siguiente consulta | ✅ por diseño | `usePortalAnalytics.ts` (`refetchInterval: 20_000`) |
| P3 | Latencia de la API en CRUD y lectura | P95 < 200 ms | ❌ no medido | No hay medición global; solo la de analítica (P4 y P5) |
| P4 | Ingesta de analítica (`POST /events/track`) | P95 < 150 ms sin llamadas externas | ✅ cumple | Spec 010 RNF-001: con 1 M de eventos, p50 11,7 ms, p95 20,1 ms, p99 24,6 ms (`.harness/specs/010-portal-analytics/tasks.md`) |
| P5 | Consultas del tablero de analítica | < 500 ms para ventanas de hasta 30 días con 1 M de eventos | ⚠️ parcial | Spec 010 RNF-002, verificado con datos sintéticos y acotado a 30 días por decisión de Carlos; 90 y 365 días sin meta |

## Disponibilidad

| # | Escenario | Medida | Estado | Evidencia |
|---|---|---|---|---|
| D1 | Disponibilidad del sistema | 99,5 % | ❌ no medido | No hay monitoreo de uptime externo ni SLA definido |
| D2 | Recuperación ante incidente (RTO) | < 1 h | ❌ pendiente | Sin runbook ni ensayo; los contenedores tienen `restart: unless-stopped` |
| D3 | Pérdida máxima de datos (RPO) | < 5 min | ❌ pendiente | No hay respaldo automático de PostgreSQL; se hace `pg_dump` manual antes de migraciones con datos y una exportación mensual de eventos del portal (cron, día 1) |
| D4 | Detección de contenedor caído | Healthcheck y reinicio automático | ✅ cumple | `docker-compose.yml`: healthcheck en admin, portfolio, api, postgres y minio (Qdrant sin healthcheck); `docker compose ps` los muestra `healthy` |

## Mantenibilidad

| # | Escenario | Medida | Estado | Evidencia |
|---|---|---|---|---|
| M1 | Cobertura de pruebas | ≥ 80 % por módulo | ⚠️ parcial | La API lo impone en `pytest.ini` (`--cov-fail-under=80`) y tiene 93 archivos de prueba; el último `coverage.json` del repo es de 2026-08-17 (78,4 %) y está obsoleto. Admin y Portal usan Vitest sin umbral automático |
| M2 | Documentación al día | Arc42 y READMEs reflejan el sistema | ✅ cumple (revisado 2026-11-05) | Toda la documentación se revisó contra el código; desde entonces rige la regla «todo cambio actualiza su doc en el mismo commit», con gate (Constitución Art. 11) |
| M3 | Deuda técnica registrada y priorizada | Registro con prioridad | ✅ cumple | [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md) |
| M4 | Separación de responsabilidades | `routes → services → repositories → models` | ✅ cumple | Estructura de `cjhirashi-career-api/src/`; la lógica de negocio vive en `services/` |

## Seguridad

| # | Escenario | Medida | Estado | Evidencia |
|---|---|---|---|---|
| S1 | Aislamiento entre usuarios | Toda consulta filtra por `user_id` | ✅ cumple | Repositorios y rutas de carrera acotados al `user_id` del token; el portal lee con `PUBLIC_PORTAL_USER_ID` |
| S2 | Expiración de sesión | Token de acceso con vida corta | ⚠️ parcial | Acceso 7 días y refresco 30 (`config.py`); no hay objetivo formal menor |
| S3 | Restricción de orígenes (CORS) | Un conjunto de orígenes por entorno | ✅ cumple | `CORS_ORIGINS` por variable de entorno; la plantilla trae solo localhost |
| S4 | OWASP Top 10 | Sin vulnerabilidades conocidas sin mitigar | ❌ pendiente | Sin auditoría formal |
| S5 | Gestión de secretos | Nada versionado en texto plano | ✅ cumple | `.env` fuera de git; `docker-compose.yml` solo usa `${VARIABLE}` |
| S6 | Acceso de agentes acotado | El rol `agent` no alcanza rutas fuera de su lista | ✅ cumple | `middleware/auth.py` responde 403 fuera de `/career/*`, `POST /bedrock/chat` y `POST /files` |

## Escalabilidad

| # | Escenario | Medida | Estado | Evidencia |
|---|---|---|---|---|
| E1 | Escalado horizontal de la API | Réplicas sin coordinación adicional | ⚠️ no probado | La API es *stateless* respecto al negocio, pero el scheduler de tareas corre in-process (un `uvicorn` con 1 worker): varias réplicas lo duplicarían |
| E2 | Réplica de lectura de PostgreSQL | Primaria/réplica | ❌ pendiente | No priorizado (un solo usuario administrador) |
| E3 | Volumen de datos de analítica | Crecimiento acotado | ⚠️ parcial | Conservación prolongada con agregados diarios (`portal_daily`) y exportación mensual; sin política de purga automática |

## Usabilidad

| # | Escenario | Medida | Estado | Evidencia |
|---|---|---|---|---|
| U1 | Tareas frecuentes del Admin | ≤ 5 clics desde la sección | ❌ no medido | Sin medición formal |
| U2 | Tablero de analítica accionable | Cada gráfico responde una pregunta operativa | ✅ cumple | `/metrics`: KPIs con comparación, tendencia, páginas, recorridos, retención, metas y embudos; validado con Carlos en la spec 010 |

## Resumen de estado

| Atributo | ✅ | ⚠️ | ❌ | Total |
|---|:---:|:---:|:---:|:---:|
| Rendimiento | 2 | 1 | 2 | 5 |
| Disponibilidad | 1 | 0 | 3 | 4 |
| Mantenibilidad | 3 | 1 | 0 | 4 |
| Seguridad | 4 | 1 | 1 | 6 |
| Escalabilidad | 0 | 2 | 1 | 3 |
| Usabilidad | 1 | 0 | 1 | 2 |
| **Total** | **11** | **5** | **8** | **24** |

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md) · [07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md) · [08-CROSSCUTTING-CONCEPTS.md](./08-CROSSCUTTING-CONCEPTS.md) · [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md)
**Contacto**: cjhirashi@gmail.com
