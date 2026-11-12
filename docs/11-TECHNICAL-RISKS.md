# Riesgos técnicos y mitigación - cjhirashi-career

**RIESGOS TÉCNICOS** (arc42, sección 11)

**Última actualización**: 2026-11-05
**Resumen**: 15 riesgos vigentes y 2 cerrados. Los de mayor prioridad: registro público abierto (R15), respaldo de PostgreSQL (R8), ejecución de la spec 009 sin perder la memoria de los agentes (R11) y expiración de los tokens (R7).

---

## Cómo leer este documento

Registra **qué puede salir mal** y cómo se mitiga hoy; no repite el detalle de los capítulos 1 a 8. **Probabilidad**: Baja/Media/Alta de que el riesgo cause un incidente con el sistema en producción. **Impacto**: Bajo/Medio/Alto/Crítico (el crítico es el daño irreversible a datos personales o credenciales).

## Riesgos vigentes

| # | Riesgo | Prob. | Impacto | Mitigación actual / pendiente |
|---|---|:---:|:---:|---|
| R1 | La complejidad del Admin (24 pantallas, formularios genéricos, chat, tareas) crece sin control y se acopla | Media | Alta | Capas del frontend, plantilla compartida de secciones (ADR-020), revisión del experto UX/UI y compuerta del arnés. Pendiente: vigilar el tamaño de las páginas más grandes |
| R2 | El volumen de analítica (`portal_events`) supera lo razonable en la instancia única | Media | Media | Agregados diarios (`portal_daily`), consultas medidas con 1 M de eventos (spec 010) y exportación mensual por cron. Pendiente: política de purga o archivado |
| R3 | Una escritura del agente falla a mitad de una operación | Media | Media | Toda escritura del agente deja `audit_logs` con el estado completo antes y después; si el registro falla, la herramienta falla (no escribe sin rastro) |
| R4 | Los agentes (token `agent`) escriben datos malformados | Media | Media | Validación Pydantic en el CRUD, aislamiento por `user_id` |
| R5 | Fuga de datos entre usuarios | Baja | Crítico | Aislamiento a nivel de aplicación (filtro por `user_id`) y un solo administrador. Pendiente: evaluar Row-Level Security antes de cualquier uso multiusuario |
| R6 | Un token JWT comprometido permite suplantar a Carlos | Baja | Crítico | HS256 con `SECRET_KEY` de 32+ caracteres. Pendiente: expiración más corta que los 7 días actuales y rotación de la clave |
| R7 | Tokens de larga vida y sin revocación del lado del servidor (`logout` no invalida; la tabla `refresh_tokens` no se usa), también los de rol `agent` | Media | Alta | Rol `agent` acotado a `/career/*` y subida de archivos. Pendiente: revocación con `refresh_tokens` o expiración menor |
| R8 | Corrupción o pérdida de PostgreSQL sin respaldo reciente | Baja | Crítico | Solo `pg_dump` manual antes de migraciones con datos y exportación mensual de eventos del portal. **Pendiente (prioridad alta)**: respaldo automático diario y fuera del disco de datos |
| R9 | Una dependencia (React, FastAPI, SQLAlchemy, WeasyPrint…) introduce un CVE | Alta | Media | Versiones fijadas en `requirements.txt`. Pendiente: escaneo automático de dependencias en CI (hoy el CI solo corre pruebas) |
| R11 | La spec 009 (harness fuera de la API) pierde memoria del agente o rompe el chat durante el corte | Media | Alta | Corte en tres etapas reversibles; migración de memoria con reporte de conteos y `--verify-only`; `pg_dump` previo (ADR-029). Estado: 62 de 163 tareas, sin etapas aplicadas |
| R13 | El scheduler de tareas corre in-process: con varias réplicas de la API duplicaría ejecuciones | Baja | Media | Hoy hay una sola instancia y un solo worker; antes de escalar hay que sacarlo (el harness lo hará, ADR-029) |
| R15 | **Registro público abierto**: `POST /auth/register` es alcanzable desde Internet sin autenticación y permite crear cuentas `user` con acceso al CRUD propio, y a la subida de archivos | Media | Alta | Sin mitigación: decidir si se desactiva, se protege con invitación o se limita (ver [SECURITY.md](../cjhirashi-career-api/docs/SECURITY.md), deuda 1). Detectado el 2026-11-05 |
| R14 | Ruido y crecimiento de `error_reports` (errores repetitivos, escaneo de bots) | Media | Baja | Deduplicación por huella, se omiten 401 y 404, purga de resueltos (`POST /settings/error-reports/purge-resolved`) |

## Riesgos cerrados

| # | Riesgo | Cierre |
|---|---|---|
| C1 | Secretos en texto plano versionados en `docker-compose.yml` | Cerrado: el compose usa `${VARIABLE}` y `.env` no se versiona |
| C2 | Brecha entre el diseño arc42 y el código real | Cerrado el 2026-11-05 con la revisión completa de la documentación; la regla «todo cambio actualiza su doc en el mismo commit» (Constitución Art. 11) con gate evita que reaparezca |

## Matriz de priorización

| | Prob. Baja | Prob. Media | Prob. Alta |
|---|---|---|---|
| **Impacto Crítico** | R5, R6, R8 | — | — |
| **Impacto Alto** | — | R1, R7, R11, R15 | — |
| **Impacto Medio** | — | R2, R3, R4, R13 | R9 |
| **Impacto Bajo** | — | R10, R12, R14 | — |

## Orden de atención recomendado

1. **R15 — Registro público abierto**: cerrarlo o protegerlo; es la única puerta de entrada sin control a un sistema pensado para un solo administrador.
2. **R8 — Respaldo automático de PostgreSQL**: el único riesgo crítico sin mitigación automatizada.
3. **R6 y R7 — Expiración y revocación de tokens**: acortar la vida del acceso y definir cómo se revoca un token `agent`.
4. **R11 — Ejecución segura de la spec 009**: no aplicar etapas sin el reporte `ok: true` de la migración de memoria ni los respaldos.
5. **R9 — Escaneo de dependencias en CI**.
6. **R5 — Evaluar Row-Level Security** antes de cualquier escenario multiusuario.
7. Resto (R1 a R4, R10, R12 a R14): según el uso real.

---

**Relacionado**: [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md) · [07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md) · [08-CROSSCUTTING-CONCEPTS.md](./08-CROSSCUTTING-CONCEPTS.md) · [09-DECISIONS/README.md](./09-DECISIONS/README.md) · [10-QUALITY-SCENARIOS.md](./10-QUALITY-SCENARIOS.md)
**Contacto**: cjhirashi@gmail.com
