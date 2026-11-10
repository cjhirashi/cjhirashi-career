# Conceptos transversales - cjhirashi-career

**CONCEPTOS TRANSVERSALES** (arc42, sección 8)

**Última actualización**: 2026-11-10
**Resumen**: autenticación, persistencia, errores, registro y auditoría, seguridad, pruebas, documentación, convenciones, métricas y analítica. Aplican a todos los módulos.

---

## Autenticación y autorización

| Acceso | Mecanismo | Alcance |
|---|---|---|
| Portal público | Sin autenticación; CORS restringido y límites de tasa | Solo lectura de lo publicable (`/public/*`); escribe contacto y analítica |
| Admin Panel | JWT HS256 emitido por `POST /auth/login` (acceso 7 días, refresco 30), contraseñas con bcrypt (12 rondas) | Acceso completo del único administrador a sus datos |
| Agent Bedrock | Sin credencial propia: opera con el usuario que lo invoca (o el propietario de la tarea programada) | El mismo alcance que ese usuario, siempre acotado a su `user_id` |
| Agente externo | JWT de un usuario con `access_role = agent` | Solo `/career/*`, `POST /bedrock/chat` y `POST /files` (subida); lo demás responde 403 (`middleware/auth.py`) |

- **Aislamiento por usuario**: todo endpoint de carrera filtra por el `user_id` del token. El portal público lee con el usuario dueño del portafolio (`PUBLIC_PORTAL_USER_ID`).
- **Sin RBAC multiusuario**: hay un administrador y cuentas de agente acotadas.
- **Punto de mayor sensibilidad**: el token `agent` puede escribir datos de carrera sin supervisión en tiempo real; sus escrituras vía Bedrock quedan en `audit_logs`.

## Persistencia

- **PostgreSQL** es la única fuente de verdad de carrera; la API la usa con SQLAlchemy 2 async (asyncpg).
- **Esquema**: Alembic es la fuente de verdad para despliegues (`alembic upgrade head`); 53 migraciones. Detalle y dominios: [`cjhirashi-career-api/docs/DATABASE.md`](../cjhirashi-career-api/docs/DATABASE.md).
- **IDs prefijados** por recurso (p. ej. `comp-12`) y secciones del Admin con PK sintético `sec-N` ([ADR-021](./09-DECISIONS/021-admin-sections-synthetic-pk.md)).
- **Archivos** en MinIO (bucket único), con metadatos y visibilidad en `file_uploads`.
- **Base vectorial** (Qdrant): índice derivado, reconstruible desde PostgreSQL; el retiro está decidido ([ADR-029](./09-DECISIONS/029-harness-agentes-fuera-de-api.md)).
- **Respaldo** de PostgreSQL antes de cualquier migración con datos.

## Manejo de errores

- La API responde `{"detail": …}` (formato estándar de FastAPI); los 422 de validación llevan además la lista de errores. La norma del arnés (Constitución Art. 6) pide Problem Details (RFC 9457) para contratos nuevos.
- Los manejadores globales (`app.py`) registran cada fallo relevante en `error_reports` con huella para deduplicar (ADR-018): se omiten 401 y 404 por ruido, y todos los 5xx se registran. El Admin los gestiona en `/settings/error-reports`, y el cliente también puede reportar (`POST /system/error-report`).
- Los fallos del indexado en Qdrant nunca fallan la escritura (best-effort); en cambio el registro de auditoría del agente sí falla en voz alta.

## Registro y auditoría

- **Logs**: `logging` a stdout (INFO; DEBUG si `DEBUG=true`).
- **`audit_logs`**: toda escritura del agente con el estado completo antes y después, usuario, recurso, IP y motivo («Agent Bedrock»). Las ediciones manuales del Admin no se auditan.
- **Uso de agentes**: `bedrock_usage_logs` y `bedrock_usage_round_logs` (costos y rondas), con presupuesto diario (`BEDROCK_DAILY_BUDGET_USD`).

## Seguridad

- **Transporte**: el tráfico interno viaja por `net-cjhirashi-career`.
- **Superficie**: solo Portal, Admin y archivos públicos están expuestos; API, PostgreSQL y Qdrant, no.
- **Límites de tasa** (ventana deslizante) en el formulario de contacto (3 por hora por IP y por correo) y en la ingesta de analítica; clasificación de bots (umbral 70).
- **Privacidad del visitante**: id seudónimo, respeto a DNT/GPC y borrado propio en `/privacy`.
- **Secretos** en `.env` (nunca versionado): `SECRET_KEY` de 32+ caracteres, credenciales de AWS y MinIO. Política y variables: [ENVIRONMENT-SECURITY.md](./ENVIRONMENT-SECURITY.md).
- **Archivos**: la subida por agentes es la única operación de `/files` permitida a su rol; listar, cambiar visibilidad, descargar y borrar son del administrador.
- Línea base **OWASP** en todo lo expuesto.

## Pruebas

Cobertura mínima del **80 %** por módulo; en la API la impone `pytest.ini` (`--cov-fail-under=80`).

| Módulo | Herramienta | Ubicación |
|---|---|---|
| API | pytest (867 pruebas en 93 archivos: unitarias e integración), marcador `@pytest.mark.requisito("RF-NNN")` | `cjhirashi-career-api/tests/` |
| Admin y Portal | Vitest + React Testing Library, `describe("RF-NNN: …")` | `src/tests/` y junto al código |
| `cjhirashi-career-ai` | pytest; las pruebas con Postgres real usan una base desechable (`TEST_DATABASE_URL`) | `cjhirashi-career-ai/tests/` |
| CI | GitHub Actions: pruebas del subsistema Bedrock de la API (Python 3.11) y build del Admin (Node 20) | `.github/workflows/ci.yml` |

La compuerta del arnés (`.harness/gate/check.sh`) comprueba el estado del repo antes de cada sesión.

## Documentación

- Arc42 (`docs/01` a `docs/12`) describe el producto; los ADR (`docs/09-DECISIONS/`) registran las decisiones; cada servicio documenta su superficie en su README y en `cjhirashi-career-api/docs/`.
- **Regla 🔴: todo cambio actualiza su documentación en el mismo commit** o declara `Docs actualizadas: ninguna — <motivo>` (Constitución Art. 11; el gate lo exige).
- `.harness/` (método, constitución, specs, memoria) describe cómo se trabaja y **no** se mezcla con `docs/`.

## Convenciones de código

- Código y comentarios en inglés; specs, ADR y documentación en español.
- Arquitectura por capas: `routes → services → repositories → models`; en el frontend, `components/pages → hooks → api → stores`. La lógica de negocio vive en `services/`.
- Commits en Conventional Commits con sufijo `(RF-NNN)`; IDs `RF-`/`RNF-`/`T-` estables por feature.
- Frontend: tema claro/oscuro con tokens semánticos y contraste AA ([ADR-028](./09-DECISIONS/028-contraste-tokens-semanticos-admin.md)).

## Métricas y analítica

- **Analítica del portafolio**: el rastreador del portal envía eventos a `POST /events/track`; la API sesioniza, filtra bots, resuelve canal, dispositivo y geografía y consolida agregados diarios (`portal_daily`). Se consulta en `/career/portal-metrics/*`. Flujo: [06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md).
- **Agentes**: uso, costo y tareas en las pantallas `/agent/metrics`, `/agent/tasks` y `/agent/audit-log`.
- **Errores**: `/settings/error-reports`.

## Tiempo real

No hay canal WebSocket. El chat de agentes responde por streaming HTTP (`POST /bedrock/chat`), y la vista casi en vivo del tablero consulta periódicamente `GET /career/portal-metrics/realtime`.

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md) · [06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md) · [ENVIRONMENT-SECURITY.md](./ENVIRONMENT-SECURITY.md)
**Contacto**: cjhirashi@gmail.com
