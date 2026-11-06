# Estrategia de solución - cjhirashi-career

**ESTRATEGIA DE SOLUCIÓN** (arc42, sección 4)

**Última actualización**: 2026-11-05

---

## Propósito

[02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md) define **qué debe lograrse** y [03-STAKEHOLDERS.md](./03-STAKEHOLDERS.md) **para quién**; este documento explica **el camino elegido**: las decisiones de más alto nivel, por qué se prefirieron y cómo se organizan los contenedores. El detalle vive en [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md) y [06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md); las decisiones formales, en [09-DECISIONS/](./09-DECISIONS/README.md).

## Decisiones de alto nivel

### 1. Dos canales independientes hacia una sola API

**Decisión**: Portal público y Admin Panel son puntos de entrada autónomos; convergen solo en la API REST y la base de datos. (Hubo un tercer canal, el MCP Server, retirado el 2026-09-04: [ADR-023](./09-DECISIONS/023-retirar-mcp-server.md); nunca implementó las herramientas de carrera y no tuvo tráfico. Los agentes externos usan hoy un token de rol `agent` sobre la API.)

**Motivación**: las audiencias (visitante anónimo, administrador autenticado, agente) tienen necesidades de acceso y disponibilidad distintas; compartir un canal acoplaría su disponibilidad.

**Consecuencia**: la API es el único punto de convergencia obligatorio y su disponibilidad es crítica para todos.

### 2. SPA en React para el Admin Panel

**Decisión**: el Admin es una SPA (React 18 + Vite + TypeScript) con CRUD dinámico, métricas y chat con agentes, no un panel renderizado en servidor.

**Motivación**: uso intensivo y frecuente por un único usuario, que alterna entre gestión manual, métricas y chat; exige transiciones fluidas.

**Consecuencia**: el Admin consume la API íntegramente por REST JSON y el estado de sesión y navegación vive en el cliente. El sidebar lo gobierna la sección activa ([ADR-024](./09-DECISIONS/024-sidebar-contextual-por-seccion.md)) y las secciones de tabla comparten plantilla ([ADR-020](./09-DECISIONS/020-admin-section-templates.md)).

### 3. PostgreSQL centralizado, también para observabilidad

**Decisión**: métricas, eventos, auditoría, registro de errores y analítica del portafolio se guardan en tablas de la misma instancia PostgreSQL que los datos de carrera, no en un almacén de series de tiempo aparte.

**Motivación**: el volumen (un administrador, un portafolio personal) no justifica un segundo motor; se gana simplicidad de despliegue, respaldo y coherencia transaccional. La analítica del portafolio (visitas, sesiones, metas, embudos, agregados diarios) usa tablas propias con sesionización y conservación prolongada; el registro de fallas, `error_reports` ([ADR-018](./09-DECISIONS/018-error-reports-registry.md)).

**Consecuencia**: el modelo crece (69 modelos, 53 migraciones Alembic); el particionado queda como trabajo futuro si el volumen lo pide.

### 4. API REST como orquestador único

**Decisión**: la API concentra el CRUD de negocio, los endpoints de gestión, las métricas, los archivos, el PDF y Agent Bedrock; todo dato que necesita un canal pasa por ella.

**Motivación**: evita duplicar la lógica de acceso a datos y garantiza que las reglas de negocio (por ejemplo, qué es publicable) se apliquen igual desde cualquier origen.

**Consecuencia**: la API concentra la carga de todos los canales; es el componente con mayor prioridad de escalabilidad.

### 5. Agent Bedrock como capacidad, no como canal

**Decisión**: Agent Bedrock es una capacidad del Admin Panel (harness local sobre la API de Converse: [ADR-008](./09-DECISIONS/008-bedrock-harness-local.md); jerarquía de tres niveles L1/L2/L3: [ADR-012](./09-DECISIONS/012-bedrock-three-level-agents.md); tareas programadas y subtareas: [ADR-015](./09-DECISIONS/015-scheduled-agent-tasks.md), [ADR-016](./09-DECISIONS/016-task-subtasks-orchestration.md)), sin puerto propio ni exposición a Internet.

**Motivación**: Bedrock asiste al usuario humano dentro de su flujo; convertirlo en canal duplicaría la superficie de autenticación.

**Consecuencia**: opera con el contexto de autorización de quien lo invoca (o, en tareas programadas, con el del usuario propietario de la tarea).

### 6. Harness de agentes fuera de la API y sin indexación (en ejecución)

**Decisión**: el harness completo pasa a `cjhirashi-career-ai` (base propia `career_ai_db`, proveedor de modelos intercambiable, acceso a los datos solo por la API REST). La memoria del agente pasa a Postgres con búsqueda de texto completo; se retiran la base de conocimiento, la indexación en cada escritura y **Qdrant** ([ADR-029](./09-DECISIONS/029-harness-agentes-fuera-de-api.md), spec 009).

**Motivación**: la indexación gastaba embeddings sin consumidor real y el harness acoplaba la API a un proveedor concreto.

**Estado**: la decisión está aprobada pero **no ejecutada**: el corte es en tres etapas reversibles (harness arriba con datos copiados, Admin apuntando a `/ai/`, retirada de la API) y la spec 009 va en la etapa 1. Mientras no se complete la etapa 3, Bedrock, la base de conocimiento y Qdrant siguen dentro de la API y operando.

## Organización en capas

```mermaid
graph TB
    subgraph Capa1["Capa 1 — Canales de entrada (2, independientes)"]
        Portal["Portal público<br/>cjhirashi.com"]
        Admin["Admin Panel<br/>admin.cjhirashi.com"]
    end

    subgraph Capa2["Capa 2 — API (punto de convergencia único)"]
        API["API REST<br/>(Bedrock, PDF WeasyPrint,<br/>archivos, analítica)"]
    end

    subgraph Capa3["Capa 3 — Persistencia"]
        DB["PostgreSQL<br/>carrera · métricas · analítica · auditoría"]
        S3["MinIO<br/>archivos"]
        Q["Qdrant<br/>base de conocimiento<br/>(retiro decidido, ADR-029)"]
    end

    AWS["AWS Bedrock"]

    Portal --> API
    Admin --> API
    API --> DB
    API --> S3
    API --> Q
    API --> AWS
```

| Capa | Módulos | Criterio |
|---|---|---|
| **1. Canales** | Portal público, Admin Panel | Cada uno responde a una audiencia y no depende del otro |
| **2. API** | `cjhirashi-career-api` (incluye Bedrock y PDF) | Concentra las reglas de negocio; solo alcanzable desde fuera por los canales de la capa 1 (`/api/`) |
| **3. Persistencia** | PostgreSQL, MinIO, Qdrant | La API es la única con acceso de lectura/escritura |

`cjhirashi-career-ai` (harness, sin desplegar) se sumará como componente de la capa 2 cuando termine la etapa 1 de la spec 009.

## Alternativas descartadas

| Decisión adoptada | Alternativa | Por qué se descartó |
|---|---|---|
| Dos canales independientes | Un único frontend multipropósito | Acoplaría disponibilidad y autenticación de audiencias opuestas y complicaría el aislamiento de lo publicable |
| PostgreSQL también para observabilidad | Almacén de series de tiempo o eventos dedicado | El volumen no justifica un segundo motor para un solo administrador |
| Bedrock sin exposición propia | Microservicio de agentes público | Superficie de red adicional sin necesidad; el acceso externo se resuelve con el token `agent` |
| MCP Server como tercer canal | Token `agent` sobre la API | El MCP no llegó a implementar herramientas de carrera y no tuvo tráfico (ADR-023) |

## Matriz de comunicación

| Origen | Destino | Protocolo | Autenticación |
|---|---|---|---|
| Visitante | Portal | HTTPS | Ninguna |
| Carlos | Admin Panel | HTTPS | Login (JWT) |
| Portal | API (`/public/*`, contacto, ingesta de analítica) | REST JSON | Ninguna; límites de tasa |
| Admin | API | REST JSON (CRUD, PDF, chat y tareas de Bedrock) | JWT del administrador |
| Agente externo | API (`/career/*`, `POST /bedrock/chat`, `POST /files`) | REST JSON | JWT de rol `agent` |
| API | PostgreSQL | SQL (SQLAlchemy async / asyncpg) | Credenciales de servicio, red Docker interna |
| API | MinIO | S3 | Credenciales de servicio |
| API | Qdrant | HTTP (6333) | Red Docker interna |
| API | AWS Bedrock | HTTPS (boto3) | Credenciales AWS por variable de entorno |

Conexiones deliberadamente ausentes: Portal ↔ Admin, y cualquier acceso a PostgreSQL, MinIO o Qdrant que no sea desde la API.

## Trazabilidad hacia ADR

| Decisión | ADR |
|---|---|
| 1. Dos canales | ADR-014 (módulos) y ADR-023 (retiro del MCP) |
| 2. SPA del Admin | ADR-020, ADR-021, ADR-024, ADR-028 |
| 3. PostgreSQL centralizado | ADR-018 |
| 4. API orquestadora | ADR-011 (descubrimiento de vacantes), ADR-015 y ADR-016 |
| 5. Bedrock como capacidad | ADR-008, ADR-009 (deprecado), ADR-010, ADR-012, ADR-013, ADR-017, ADR-019, ADR-022, ADR-025, ADR-026, ADR-027 |
| 6. Harness fuera de la API | ADR-029 |

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md) · [03-STAKEHOLDERS.md](./03-STAKEHOLDERS.md) · [CLAUDE.md](../CLAUDE.md)
**Contacto**: cjhirashi@gmail.com
