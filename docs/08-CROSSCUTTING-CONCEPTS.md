# Conceptos Transversales - cjhirashi-career

**CONCEPTOS TRANSVERSALES**

[![Document Type](https://img.shields.io/badge/type-architecture-blue)]()
[![Audience](https://img.shields.io/badge/audiencia-arquitectos%20%7C%20developers-informational)]()
[![Estado](https://img.shields.io/badge/estado-diseño%20en%20validación-yellow)]()

---

**Última actualización**: 2026-08-16
**Resumen rápido**: 9 conceptos transversales al diseño objetivo — autenticación, persistencia, errores, logging/auditoría, seguridad, testing, documentación, convenciones de código, sistema de métricas — más dos anexos operativos (tiempo real, tracking del Portal Público)

---

## 📋 Tabla de Contenidos

- [Cómo Leer Este Documento](#-cómo-leer-este-documento)
- [Autenticación y Autorización](#-autenticación-y-autorización)
- [Persistencia](#-persistencia)
- [Manejo de Errores](#-manejo-de-errores)
- [Logging y Auditoría](#-logging-y-auditoría)
- [Seguridad](#-seguridad)
- [Testing](#-testing)
- [Documentación](#-documentación)
- [Convenciones de Código](#-convenciones-de-código)
- [Sistema de Métricas](#-sistema-de-métricas)
- [Tiempo Real](#-tiempo-real)
- [Tracking en Portal Público](#-tracking-en-portal-público)

---

## 📖 Cómo Leer Este Documento

Este documento es la sección 8 de la documentación Arc42 y describe **patrones que cruzan varios módulos** — decisiones que no pertenecen a un solo componente sino que los tres canales y sus servicios de apoyo deben respetar por igual. No repite el detalle de endpoints ([05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md)) ni de flujos ([06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md)) ni de infraestructura ([07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md)); enlaza a ellos donde corresponde.

El marco de calidad que rige estos conceptos está definido en `CLAUDE.md` (framework de calidad integral: Arc42, SOLID, testing 80%, code review, CI/CD, seguridad). Este documento describe el **diseño objetivo** de cómo ese marco se aplica al alcance de cjhirashi-career — no es un inventario de lo ya implementado, dado que el sistema está en fase de diseño (ver estado en todos los documentos Arc42 previos).

## 🔐 Autenticación y Autorización

**Mecanismo por canal**, coherente con [01-INTRODUCTION.md — Modelo de Seguridad](./01-INTRODUCTION.md#-modelo-de-seguridad):

| Canal | Mecanismo | Alcance de autorización |
|---|---|---|
| Portal Público | Sin autenticación de usuario; controles de red (CORS, límites de tasa) | Ninguno — solo lectura de contenido publicable |
| Admin Panel | JWT (`HS256`), emitido por `POST /api/v1/auth/login` y validado en cada endpoint protegido | Acceso completo del único usuario administrador sobre sus propios datos de carrera |
| Agent Bedrock | Ninguno propio — hereda el JWT de la sesión del Admin Panel que lo invoca | Idéntico al de la sesión que lo invocó; nunca un alcance distinto |
| MCP Server | Mecanismo propio e independiente del JWT del Admin Panel (token estático, API key rotable u OAuth — pendiente de definir) | Lectura/escritura plena sobre la API REST, de forma autónoma y sin depender de una sesión humana activa |

**Aislamiento por usuario**: todo endpoint de gestión de carrera filtra por `user_id` (ver [05-BUILDING-BLOCK-VIEW.md — Base de Datos Detallada](./05-BUILDING-BLOCK-VIEW.md#-base-de-datos-detallada)) — aun con un único usuario administrador, el modelo de datos y las consultas mantienen esta separación para sostener el objetivo técnico de "aislamiento de datos por usuario" de [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md#-objetivos-técnicos).

**Sin RBAC**: no se contempla un modelo multiusuario ni roles diferenciados en este alcance — restricción explícita documentada en [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md#-restricciones).

**Punto de mayor riesgo**: la autorización del MCP Server, al operar sin supervisión humana en tiempo real, es el punto de mayor sensibilidad del sistema — permanece como pregunta de validación abierta en [01-INTRODUCTION.md](./01-INTRODUCTION.md#-preguntas-de-validación-abiertas) y debe resolverse antes de formalizar el ADR correspondiente (ver `docs/09-DECISIONS/`).

## 🗄️ Persistencia

**Motor único**: PostgreSQL, accedido exclusivamente por la API REST vía SQLAlchemy 2.0 async + `asyncpg` (ver [05-BUILDING-BLOCK-VIEW.md — Nivel 2 PostgreSQL](./05-BUILDING-BLOCK-VIEW.md#-nivel-2--descomposición-de-postgresql)).

**Transacciones**: cada solicitud HTTP a la API REST es su propia unidad transaccional — commit automático al finalizar sin errores, rollback automático ante excepción. Las operaciones que además deben escribir en `audit_logs` (toda mutación) lo hacen dentro de la misma transacción que la escritura de negocio, garantizando que nunca exista un cambio de datos sin su entrada de auditoría correspondiente.

**Migraciones**: el esquema de las doce tablas descritas en [05-BUILDING-BLOCK-VIEW.md — Base de Datos Detallada](./05-BUILDING-BLOCK-VIEW.md#-base-de-datos-detallada) debe versionarse con una herramienta de migraciones (Alembic, dado que ya es el ecosistema natural de SQLAlchemy) desde el inicio del desarrollo — a diferencia del proyecto heredado, que no contaba con esta capa, este alcance nuevo lo incorpora como requisito de diseño para evitar deriva entre el ORM y el esquema físico.

**Backups**: sin réplicas ni backups automatizados definidos aún — pendiente de diseño, coherente con [07-DEPLOYMENT-VIEW.md — Ambiente de Producción](./07-DEPLOYMENT-VIEW.md#-ambiente-de-producción). Dado que el sistema centraliza datos de carrera profesional sensibles (ver dominio de datos en `05-BUILDING-BLOCK-VIEW.md`), una estrategia mínima de backup periódico debe definirse antes de considerar el sistema listo para producción, siguiendo el checklist de calidad de `CLAUDE.md`.

## ⚠️ Manejo de Errores

**Códigos HTTP estándar** en toda la superficie de la API REST, consistentes entre los tres canales que la consumen:

| Código | Uso |
|---|---|
| `400 Bad Request` | Validación de negocio fallida (por ejemplo, datos duplicados) |
| `401 Unauthorized` | Token ausente, inválido o expirado |
| `404 Not Found` | Recurso inexistente o que no pertenece al usuario autenticado (nunca `403`, para no confirmar la existencia del recurso a quien no está autorizado) |
| `422 Unprocessable Entity` | Validación de schema Pydantic fallida |
| `500 Internal Server Error` | Excepción no controlada, capturada por un manejador global |

**Logging de error**: todo error `500` se loguea con traza completa (`exc_info`) en el manejador global — es el único nivel de severidad que siempre debe capturar la traza íntegra, sin importar el canal de origen.

**Propagación hacia el MCP Server**: al ser un canal distinto del navegador, el MCP Server debe mapear los códigos HTTP de la API REST hacia el formato de error del protocolo MCP (JSON-RPC) de forma explícita — este mapeo es parte del diseño objetivo del MCP Server y debe definirse junto con su mecanismo de autenticación (ver [01-INTRODUCTION.md — Preguntas de Validación Abiertas](./01-INTRODUCTION.md#-preguntas-de-validación-abiertas)).

## 📝 Logging y Auditoría

**Niveles de logging** (aplicación, no auditoría de negocio): `INFO` para el ciclo de vida normal de solicitudes, `WARNING` para condiciones recuperables (por ejemplo, degradación de la conexión de tiempo real), `ERROR` para excepciones no controladas con traza completa. Salida a `stdout`, capturable por `docker logs` de cada contenedor — sin agregación centralizada definida en este alcance.

**Auditoría de negocio (`audit_logs`)**: distinta del logging de aplicación — es un registro de negocio inmutable, no un log técnico. Cada mutación sobre una entidad de carrera profesional, sin importar el canal de origen, genera una entrada con:

| Campo | Propósito |
|---|---|
| `actor_type` / `actor_id` | Quién o qué originó el cambio (`admin`, `bedrock`, `mcp_agent`, `system`) |
| `channel` | Canal de origen: `admin_panel`, `bedrock`, `mcp_server` |
| `action` | Tipo de operación (`create`, `update`, `delete`) |
| `entity_type` / `entity_id` | Qué entidad fue afectada |
| `before_data` / `after_data` | Estado anterior y posterior, en formato `JSONB` |
| `occurred_at` | Momento exacto del cambio |

**Formato**: JSON estructurado, no texto libre — a diferencia del patrón heredado del MCP Server anterior (que devolvía errores como texto libre en el protocolo), este alcance nuevo exige que toda entrada de auditoría sea consultable y filtrable programáticamente desde la sección Logs & Auditoría del Admin Panel (ver [05-BUILDING-BLOCK-VIEW.md — Admin Panel Detallado](./05-BUILDING-BLOCK-VIEW.md#-admin-panel-detallado)).

**Retención**: 90 días por defecto, configurable — igual que la retención definida para el [Sistema de Métricas](#-sistema-de-métricas), dado que ambos dominios (auditoría y observabilidad) comparten el mismo motor de PostgreSQL y el mismo criterio de expiración de datos operativos no permanentes.

## 🛡️ Seguridad

| Control | Alcance objetivo |
|---|---|
| CORS | Restringido a los orígenes conocidos de Portal Público y Admin Panel; el MCP Server, al servir a clientes de agentes de IA (no navegadores), se protege con autenticación por token en cada llamada, no con CORS |
| Validación de entrada | Todo payload de los tres canales se valida contra schemas Pydantic antes de llegar a la capa de Services |
| Hashing de contraseñas | `bcrypt` (vía `passlib` o equivalente), nunca contraseña en texto plano persistida ni transmitida |
| Rate limiting | Obligatorio en los tres canales expuestos a Internet (Portal Público, Admin Panel, MCP Server), con especial atención al endpoint de login y al endpoint de tracking (`/api/v1/events/track`), ambos accesibles sin autenticación |
| Rotación de `SECRET_KEY` y credenciales de AWS Bedrock | Gestionadas fuera de texto plano versionado — vía variables de entorno inyectadas en despliegue o un gestor de secretos (ver [07-DEPLOYMENT-VIEW.md — Ambiente de Producción](./07-DEPLOYMENT-VIEW.md#-ambiente-de-producción)) |
| TLS/HTTPS | Terminación delegada a Caddy, infraestructura externa al proyecto (ver [07-DEPLOYMENT-VIEW.md — Caddy y Cloudflare Tunnel](./07-DEPLOYMENT-VIEW.md#-caddy-y-cloudflare-tunnel)) |
| Escaneo de dependencias/vulnerabilidades | Parte del gate de CI/CD obligatorio definido en `CLAUDE.md` — responsabilidad del Experto Docker en coordinación con Code Quality Guardian |
| Cumplimiento OWASP | Exigido en los tres canales expuestos a Internet, restricción explícita en [02-ARCHITECTURE-GOALS.md — Restricciones](./02-ARCHITECTURE-GOALS.md#-restricciones) |
| Credenciales de AWS Bedrock | Superficie de seguridad adicional fuera de la red del proyecto — requiere un rol IAM acotado exclusivamente al servicio de Bedrock, con alcance mínimo necesario |

## 🧪 Testing

`CLAUDE.md` exige una pirámide de testing con **cobertura mínima del 80%** por módulo:

```
E2E Tests (10%)          — Casos críticos de usuario (login, CRUD completo, flujo Bedrock, flujo MCP)
Integration Tests (30%)  — Endpoints de la API REST, canal de tiempo real, integración con AWS Bedrock
Unit Tests (60%)         — Servicios de dominio, validadores, utilidades de formateo
```

**Aplicación por módulo**:

| Módulo | Enfoque de testing objetivo |
|---|---|
| API REST | Unit tests por servicio de dominio (incluye `services/pdf/`); integration tests contra una base de datos de prueba para cada grupo de endpoints |
| Admin Panel | Unit tests de componentes y hooks (React Testing Library); integration tests del flujo CRUD y del canal de tiempo real con mocks de WebSocket/SSE |
| Portal Público | Unit tests de renderizado; E2E de navegación básica |
| MCP Server | Unit tests por herramienta MCP; integration tests que verifiquen la llamada saliente hacia la API REST |

**Gate obligatorio**: ningún módulo se considera "listo" (checklist de `CLAUDE.md`) sin 80% de cobertura, validado por el QA Engineer antes de cualquier merge a `main`.

## 📚 Documentación

- **Arc42**: esta serie de documentos (`docs/01-*` a `docs/12-*`) sigue la estructura definida en `CLAUDE.md`, con responsabilidad editorial del Arquitecto de Soluciones y redacción del Documentador.
- **ADRs**: `docs/09-DECISIONS/` es donde se formalizan las decisiones arquitectónicas de este alcance como Architecture Decision Records — inmutables una vez aceptados; una decisión que cambia genera un ADR nuevo que deprecia al anterior, nunca una edición del original.
- **READMEs modulares**: cada módulo de aplicación (Portal Público, Admin Panel, API REST, MCP Server) mantiene su propio `README.md` con quick start — complementan, no duplican, la vista Arc42.
- **Diagramas**: todo diagrama de arquitectura de este proyecto usa Mermaid (versionable en Git) con la paleta de colores semántica estándar — ver [protocolo de paleta de colores](../COLOR_PALETTE.md).

## 🧱 Convenciones de Código

`CLAUDE.md` exige SOLID + Clean Code y Domain-Driven Design para lógica compleja. Aplicación al diseño objetivo de este alcance:

- **Separación de capas en la API REST**: `Controllers → Services → Repository → Models` (ver [05-BUILDING-BLOCK-VIEW.md — Nivel 2: API REST](./05-BUILDING-BLOCK-VIEW.md#-nivel-2--descomposición-de-la-api-rest)), con los siete servicios de dominio como unidad de responsabilidad única (*Single Responsibility*).
- **Naming**: consistente en español para entidades y conceptos del dominio de negocio (`competencias`, `evidencia`, `vacantes`) e inglés para infraestructura y framework (`get_current_user`, `AuditService`, `EntityDataTable`) — mismo patrón ya usado en el proyecto heredado.
- **Linters y formateadores**: obligatorios desde el inicio del desarrollo — `ruff`/`black` en Python (API REST, MCP Server), `eslint`/`prettier` en TypeScript (Portal Público, Admin Panel) — como parte del gate de CI/CD.
- **Code review**: obligatorio antes de cualquier merge a `main`, ejecutado por Code Quality Guardian contra un checklist de SOLID, Clean Code y cobertura de tests.

## 📡 Sistema de Métricas

Ver el flujo completo en [06-RUNTIME-VIEW.md — Métricas en Tiempo Real](./06-RUNTIME-VIEW.md#-métricas-en-tiempo-real). Resumen transversal:

| Aspecto | Detalle |
|---|---|
| **Qué se mide** | Solicitudes del MCP Agent (volumen, latencia, herramienta invocada, resultado), visitas del Portal Público (procedencia, dispositivo, geolocalización aproximada), interacciones del Portal (`pageview`, `click`, `download`, `time_on_page`) |
| **Dónde se almacena** | `mcp_agent_metrics`, `portal_visits`, `portal_interactions` — tres tablas del dominio de observabilidad en PostgreSQL (ver [05-BUILDING-BLOCK-VIEW.md — Base de Datos Detallada](./05-BUILDING-BLOCK-VIEW.md#-base-de-datos-detallada)) |
| **Cómo se consume** | Admin Panel: carga inicial vía `GET /api/v1/metrics/mcp` y `GET /api/v1/metrics/portal`, actualizaciones en vivo vía el canal WebSocket/SSE `/api/v1/metrics/stream` |
| **Quién lo escribe** | La API REST, nunca los módulos de origen directamente sobre PostgreSQL — el MCP Server y el Portal Público solo hablan con la API REST, coherente con la regla de "único escritor" (ver [01-INTRODUCTION.md — Diagrama del Sistema](./01-INTRODUCTION.md#-diagrama-del-sistema)) |
| **Retención** | 90 días por defecto, configurable — pasado ese umbral, los registros agregados (totales por día) pueden conservarse en una tabla de resumen si se decide en el futuro, pero el detalle fila-a-fila expira |

**Por qué existe este sistema**: es la única forma en que Carlos Jiménez Hirashi puede confiar en que los agentes externos (el canal de mayor autonomía) están operando correctamente, sin tener que revisar manualmente cada operación — objetivo técnico priorizado en [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md#-objetivos-técnicos).

## ⚡ Tiempo Real

| Aspecto | Detalle |
|---|---|
| **Protocolo** | WebSocket o SSE (Server-Sent Events) — la elección concreta entre ambos queda a discreción de la implementación de la API REST, dado que el contrato observable desde el Admin Panel es el mismo: un flujo de eventos JSON |
| **Formato de mensaje** | JSON sobre el canal elegido, con al menos `{tipo_evento, payload, timestamp}` por mensaje |
| **Quién consume** | Únicamente el Admin Panel (sección Métricas Dashboard) — ni el Portal Público ni el MCP Server consumen este canal |
| **Latencia objetivo** | < 500 ms desde que un evento se persiste en PostgreSQL hasta que aparece en el dashboard (ver [06-RUNTIME-VIEW.md — Latencias Esperadas](./06-RUNTIME-VIEW.md#latencias-esperadas-objetivo)) |
| **Reconexión** | El cliente del Admin Panel debe implementar reconexión automática con backoff ante caída de la conexión, mostrando el estado mediante `RealtimeIndicator` (ver [05-BUILDING-BLOCK-VIEW.md — Admin Panel Detallado](./05-BUILDING-BLOCK-VIEW.md#-admin-panel-detallado)) |

## 🌐 Tracking en Portal Público

| Aspecto | Detalle |
|---|---|
| **Script de tracking** | JavaScript minimal embebido en el Portal Público, sin dependencia de librerías de analítica de terceros — coherente con que el sistema es la única fuente de verdad de sus propias métricas |
| **Eventos capturados** | `pageview` (al cargar cada sección), `click` (en elementos relevantes, por ejemplo enlaces de proyectos o descarga de CV), `download` (descarga de documentos generados), `time_on_page` (tiempo de permanencia, enviado al abandonar la página o cambiar de sección) |
| **Envío** | `POST /api/v1/events/track`, sin autenticación (canal público), de forma asíncrona y no bloqueante para la experiencia del visitante |
| **Procesamiento** | `EventTrackingService` normaliza el evento y lo persiste en `portal_visits` (si es el primer evento de una sesión) o `portal_interactions` (para eventos subsecuentes de la misma visita) — ver el flujo completo en [06-RUNTIME-VIEW.md — Métricas en Tiempo Real](./06-RUNTIME-VIEW.md#flujo-eventos-del-portal-público) |
| **Privacidad** | La geolocalización se resuelve de forma aproximada (país/ciudad, no coordenadas exactas) y la IP no se almacena en texto plano sino como valor derivado (`ip_hash`) — decisión de diseño para minimizar datos personales identificables sobre visitantes anónimos |

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md) · [06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md) · [07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md) · [CLAUDE.md](../CLAUDE.md)
**Contacto**: Carlos Jiménez Hirashi (cjhirashi@gmail.com)
