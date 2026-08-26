# Glosario de Términos - cjhirashi-career

**GLOSARIO DEL PROYECTO**

[![Document Type](https://img.shields.io/badge/type-architecture-blue)]()
[![Audience](https://img.shields.io/badge/audiencia-arquitectos%20%7C%20developers%20%7C%20stakeholders-informational)]()
[![Estado](https://img.shields.io/badge/estado-diseño%20en%20validación-yellow)]()

---

**Última actualización**: 2026-08-16
**Resumen rápido**: 37 términos definidos, orden alfabético · cubre los tres canales, Agent Bedrock, el sistema de métricas y los conceptos transversales del nuevo alcance · cada entrada enlaza a la sección Arc42 donde se detalla en profundidad

---

## 📋 Tabla de Contenidos

- [Cómo Leer Este Documento](#-cómo-leer-este-documento)
- [Glosario (A–W)](#-glosario-aw)

---

## 📖 Cómo Leer Este Documento

Este documento es la sección 12, la última de la documentación Arc42, y existe para eliminar ambigüedad: cada término técnico o de dominio usado en `docs/01-*` a `docs/11-*` tiene aquí una definición única y su referencia a dónde se detalla. Si un término se usa en más de un documento con el mismo significado, esta es la fuente de verdad de esa definición — evita que cada sección Arc42 tenga que redefinirlo.

Este glosario reemplaza por completo la versión anterior del documento, redactada para el alcance previo de generador de documentos. Todos los términos aquí corresponden al alcance de portafolio profesional (Portal Público, Admin Panel, MCP Server, API REST con Bedrock y PDF, PostgreSQL) descrito desde [01-INTRODUCTION.md](./01-INTRODUCTION.md).

## 📚 Glosario (A–W)

### Admin Panel

Canal 2 del sistema: SPA privada de un único usuario (Carlos Jiménez Hirashi), autenticada, que combina gestión CRUD de carrera profesional, panel de métricas, chat con Agent Bedrock, configuración y auditoría. Es uno de los dos canales de escritura del sistema, independiente del MCP Server. Ver [01-INTRODUCTION — Componente 2️⃣](./01-INTRODUCTION.md#2️⃣-admin-panel).

### Agent Bedrock

Asistente de IA gestionado sobre AWS Bedrock, embebido en la API REST. El chat vive en el Admin Panel (sesión JWT). El scheduler de tareas (`task_scheduler`) también puede invocarlo sin SPA, con el `user_id` dueño de la fila, cuando una tarea asignada a un agente vence. Ver [01-INTRODUCTION — Componente 4️⃣](./01-INTRODUCTION.md#4️⃣-agent-bedrock-asistente-interno-del-admin-panel) y [ADR-015](./09-DECISIONS/015-scheduled-agent-tasks.md).

### Aislamiento de Usuario (*User Isolation*)

Garantía de que las consultas y mutaciones de carrera profesional de un usuario nunca exponen ni modifican datos de otro usuario. Hoy se implementa exclusivamente filtrando cada consulta de la capa de Services por `user_id`; Row-Level Security (RLS) a nivel de PostgreSQL es una mitigación adicional propuesta, no implementada. Ver [08-CROSSCUTTING-CONCEPTS — Autenticación y Autorización](./08-CROSSCUTTING-CONCEPTS.md#-autenticación-y-autorización) y el riesgo R5 en [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md#-riesgos-del-nuevo-alcance).

### API REST

Punto central de CRUD y orquestación del sistema — la única puerta de entrada a PostgreSQL y el único lugar donde convergen los tres canales (Portal Público, Admin Panel, MCP Server). Se organiza en cuatro capas: Controllers, Services, Repository y Models. Ver [01-INTRODUCTION — Componente 3️⃣](./01-INTRODUCTION.md#3️⃣-api-rest) y [05-BUILDING-BLOCK-VIEW — API REST Detallada](./05-BUILDING-BLOCK-VIEW.md#-api-rest-detallada).

### Arc42

Plantilla de documentación de arquitectura de software (ISO 42010) usada como estructura de `docs/` en este proyecto — doce secciones numeradas, de la introducción y el contexto (sección 1) al glosario (sección 12, este documento). Definida como estándar del proyecto en `CLAUDE.md`.

### Audit Log (`audit_logs`)

Tabla del dominio de auditoría en PostgreSQL: registro inmutable de cada mutación sobre una entidad de carrera profesional, con el canal de origen (`admin_panel`, `bedrock`, `mcp_server`), la acción, la entidad afectada y el estado antes/después en formato JSONB. Distinto del *logging* técnico de aplicación. Ver [08-CROSSCUTTING-CONCEPTS — Logging y Auditoría](./08-CROSSCUTTING-CONCEPTS.md#-logging-y-auditoría).

### Autenticación y Autorización

Conjunto de mecanismos, distintos por canal, que determinan quién puede acceder al sistema y qué puede hacer: sin autenticación para el Portal Público, JWT completo para el Admin Panel, herencia del JWT de sesión para Agent Bedrock, y un mecanismo propio (pendiente de definir) para el MCP Server. Ver [08-CROSSCUTTING-CONCEPTS — Autenticación y Autorización](./08-CROSSCUTTING-CONCEPTS.md#-autenticación-y-autorización).

### Canal (de entrada)

Cualquiera de los tres puntos de entrada completamente independientes del sistema — Portal Público, Admin Panel, MCP Server —, cada uno con su propia audiencia, mecanismo de autenticación y disponibilidad, que convergen únicamente en la API REST. Ver [01-INTRODUCTION — Visión General del Sistema](./01-INTRODUCTION.md#-visión-general-del-sistema).

### CORS (*Cross-Origin Resource Sharing*)

Mecanismo del navegador que restringe qué orígenes (dominios) pueden hacer peticiones a la API REST. Protege al Portal Público y al Admin Panel; el MCP Server, al no ser consumido por un navegador, se protege por autenticación de token en cada llamada en lugar de CORS. Ver [08-CROSSCUTTING-CONCEPTS — Seguridad](./08-CROSSCUTTING-CONCEPTS.md#-seguridad).

### Dashboard de Métricas (*Metrics Dashboard*)

Sección del Admin Panel que visualiza, casi en tiempo real, el uso del MCP Agent, el tráfico del Portal Público y un resumen de auditoría reciente — combina carga inicial vía REST con actualizaciones en vivo vía el canal de tiempo real. Ver [05-BUILDING-BLOCK-VIEW — Admin Panel Detallado](./05-BUILDING-BLOCK-VIEW.md#-admin-panel-detallado).

### Docker Compose

Herramienta de orquestación que define y arranca los seis contenedores del sistema (Agent Bedrock queda fuera por ser un servicio gestionado sin contenedor propio) a partir de `docker-compose.yml`. Ver [07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md).

### Entidad de Carrera Profesional

Cualquiera de las categorías de datos que Carlos Jiménez Hirashi gestiona en el Admin Panel: identidad profesional, competencias, evidencia (proyectos, cargos, logros, casos STAR), estrategias de búsqueda, vacantes, contactos de networking y entrevistas — cada una con su propia tabla en el dominio de gestión de carrera de PostgreSQL. Ver [05-BUILDING-BLOCK-VIEW — Tablas de Gestión de Carrera](./05-BUILDING-BLOCK-VIEW.md#tablas-de-gestión-de-carrera).

### Evento de Tracking (*Event Tracking*)

Registro de una interacción de un visitante anónimo con el Portal Público (`pageview`, `click`, `download`, `time_on_page`), enviado sin autenticación vía `POST /api/v1/events/track` y persistido en `portal_visits`/`portal_interactions`. Ver [08-CROSSCUTTING-CONCEPTS — Tracking en Portal Público](./08-CROSSCUTTING-CONCEPTS.md#-tracking-en-portal-público).

### FastAPI

*Framework* Python usado para construir la API REST — provee validación automática vía Pydantic, documentación interactiva (Swagger) y soporte async nativo. Ver [01-INTRODUCTION — Stack Tecnológico](./01-INTRODUCTION.md#-stack-tecnológico).

### FastMCP

*Framework* Python usado para implementar el MCP Server — expone funciones Python como herramientas invocables vía el protocolo MCP por un agente de IA externo. Ver [04-SOLUTION-STRATEGY — Decisión 6](./04-SOLUTION-STRATEGY.md#6-mcp-server-expuesto-para-agentes-externos).

### Geolocalización (en métricas de tráfico)

Ubicación aproximada (país/ciudad, no coordenadas exactas) de un visitante del Portal Público, derivada al procesar un evento de tracking y almacenada en `portal_visits` — decisión de diseño deliberada para minimizar datos personales identificables sobre visitantes anónimos. Ver [08-CROSSCUTTING-CONCEPTS — Tracking en Portal Público](./08-CROSSCUTTING-CONCEPTS.md#-tracking-en-portal-público).

### Health Check

Mecanismo que Docker ejecuta periódicamente para determinar si un contenedor está sano, condicionando reinicios automáticos (`restart: unless-stopped`) y dependencias de arranque (`depends_on: condition: service_healthy`). Ver [07-DEPLOYMENT-VIEW — Health Checks](./07-DEPLOYMENT-VIEW.md#-health-checks).

### Identidad Profesional

Entidad de carrera que reúne nombre, titular, resumen, contacto y enlaces de Carlos Jiménez Hirashi — la información base que el Portal Público consulta para la sección "About". Ver [05-BUILDING-BLOCK-VIEW — Tablas de Gestión de Carrera](./05-BUILDING-BLOCK-VIEW.md#tablas-de-gestión-de-carrera).

### JWT (*JSON Web Token*)

Mecanismo de autenticación *stateless* del Admin Panel — firmado con `HS256`, emitido por `POST /api/v1/auth/login`, con expiración objetivo menor a 24 horas (aún no confirmada; el valor heredado del alcance anterior es 7 días). Agent Bedrock hereda el JWT de la sesión que lo invoca; el MCP Server usa un mecanismo propio, independiente del JWT del Admin Panel. Ver [08-CROSSCUTTING-CONCEPTS — Autenticación y Autorización](./08-CROSSCUTTING-CONCEPTS.md#-autenticación-y-autorización) y el escenario S2 en [10-QUALITY-SCENARIOS.md](./10-QUALITY-SCENARIOS.md#-seguridad).

### MCP (*Model Context Protocol*)

Protocolo abierto que permite a un agente de IA externo descubrir e invocar herramientas expuestas por un servidor, de forma estandarizada. Es el contrato de interfaz sobre el que opera el Canal 3 del sistema. Ver [02-ARCHITECTURE-GOALS — Restricciones](./02-ARCHITECTURE-GOALS.md#-restricciones).

### MCP Server

Canal 3 del sistema: interfaz completa y autónoma del protocolo MCP que permite a un agente de IA externo operar el sistema de gestión de carrera sin pasar por el Admin Panel en ningún momento. Es el segundo canal de escritura, independiente del Admin Panel. Ver [01-INTRODUCTION — Componente 5️⃣](./01-INTRODUCTION.md#5️⃣-mcp-server-canal-independiente-para-agentes-de-ia-externos).

### Métrica / Métricas del Sistema

Dato cuantitativo de observabilidad almacenado en el dominio correspondiente de PostgreSQL: `mcp_agent_metrics` (uso del MCP Agent), `portal_visits`/`portal_interactions` (tráfico del Portal Público). Escritas exclusivamente por la API REST, nunca directamente por los módulos de origen. Ver [08-CROSSCUTTING-CONCEPTS — Sistema de Métricas](./08-CROSSCUTTING-CONCEPTS.md#-sistema-de-métricas).

### Módulo / Componente

Unidad mínima de despliegue del sistema — un contenedor Docker independiente. Los **módulos de aplicación** son cuatro: Portal Público, Admin Panel, API REST y MCP Server. PostgreSQL, MinIO y Qdrant son infra. Bedrock y PDF son capacidades de la API. Ver [ADR-014](./09-DECISIONS/014-four-application-modules.md).

### `network-cjhirashi-srv`

Red Docker tipo *bridge*, **externa** al proyecto — preexiste en el host compartido `cjhirashi-srv` y este proyecto la consume sin administrarla. Todos los módulos contenedorizados se conectan exclusivamente a ella. Ver [07-DEPLOYMENT-VIEW — Red Docker](./07-DEPLOYMENT-VIEW.md#-red-docker).

### OWASP

*Open Web Application Security Project* — organización de referencia cuyo "Top 10" de riesgos de seguridad web es la línea base de cumplimiento exigida en los tres canales expuestos a Internet (Portal Público, Admin Panel, MCP Server). Ver [02-ARCHITECTURE-GOALS — Restricciones](./02-ARCHITECTURE-GOALS.md#-restricciones) y el escenario S4 en [10-QUALITY-SCENARIOS.md](./10-QUALITY-SCENARIOS.md#-seguridad).

### PDF (WeasyPrint)

Capacidad de la API REST (`api/src/services/pdf/`): transforma plantillas HTML o Markdown de CV en PDF. El Admin Panel y Bedrock lo invocan por endpoints JWT de la API; no hay contenedor ni carpeta propios. Ver [01-INTRODUCTION — API REST](./01-INTRODUCTION.md#3️⃣-api-rest).

### Portal Público

Canal 1 del sistema: sitio web de solo lectura, sin autenticación, donde cualquier visitante conoce el perfil profesional de Carlos Jiménez Hirashi (About, Proyectos, Blog, Contacto). Su único destino de salida es la API REST, en modo lectura. Ver [01-INTRODUCTION — Componente 1️⃣](./01-INTRODUCTION.md#1️⃣-portal-público).

### PostgreSQL

Motor de base de datos relacional, único mecanismo de persistencia del sistema — alcanzable exclusivamente por la API REST. Centraliza tres dominios: gestión de carrera, observabilidad y auditoría. Ver [05-BUILDING-BLOCK-VIEW — Nivel 2: PostgreSQL](./05-BUILDING-BLOCK-VIEW.md#-nivel-2--descomposición-de-postgresql).

### React SPA (*Single Page Application*)

Patrón de aplicación de una sola página, sin recargas de navegador entre secciones, usado tanto por el Portal Público como por el Admin Panel — con estado de sesión y navegación viviendo enteramente en el cliente. Ver [04-SOLUTION-STRATEGY — Decisión 2](./04-SOLUTION-STRATEGY.md#2-spa-en-react-para-el-admin-panel).

### Row-Level Security (RLS)

Mecanismo de PostgreSQL para restringir, a nivel de fila y dentro de la propia base de datos, qué registros son visibles o modificables según el usuario de la conexión. Propuesto (no implementado) como capa adicional de mitigación al riesgo de fuga de datos entre usuarios — el aislamiento actual depende únicamente del filtro por `user_id` en la capa de aplicación. Ver el riesgo R5 en [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md#-riesgos-del-nuevo-alcance).

### Secreto (variable de entorno)

Credencial sensible (`SECRET_KEY`, contraseña de PostgreSQL, credenciales de AWS Bedrock) que debe resolverse vía variables de entorno inyectadas en despliegue o un gestor de secretos, nunca versionada en texto plano. El código heredado del repositorio hoy viola esta regla (`docker-compose.yml`), riesgo registrado como R12 en [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md#-riesgos-adicionales-del-código-heredado).

### Server-Sent Events (SSE)

Protocolo de transporte unidireccional (servidor → cliente) sobre HTTP, una de las dos opciones (junto con WebSocket) para implementar el canal de tiempo real (`/api/v1/metrics/stream`) que consume el Metrics Dashboard del Admin Panel. Ver [08-CROSSCUTTING-CONCEPTS — Tiempo Real](./08-CROSSCUTTING-CONCEPTS.md#-tiempo-real).

### SOLID Principles

Los cinco principios de diseño orientado a objetos (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion) que `CLAUDE.md` exige en todo módulo de código, validados por el Code Quality Guardian antes de cualquier merge. Ver [02-ARCHITECTURE-GOALS — Convenciones de Equipo](./02-ARCHITECTURE-GOALS.md#-convenciones-de-equipo).

### Stakeholder

Persona o rol con interés o responsabilidad sobre el sistema — de negocio (Carlos Jiménez Hirashi, visitantes anónimos, agentes de IA externos), de equipo (los 5 agentes globales y especialistas de módulo definidos en `CLAUDE.md`) o de infraestructura (administrador de `cjhirashi-srv`, DevOps). Ver [03-STAKEHOLDERS.md](./03-STAKEHOLDERS.md).

### Tarea programada

Fila de `bedrock_tasks` asignada a un agente (`assignee_type=agent`) con `scheduled_at`. El `task_scheduler` de la API la ejecuta a esa hora sin que el Admin esté abierto. Ver [ADR-015](./09-DECISIONS/015-scheduled-agent-tasks.md).

### Tiempo Real (*Real-time*)

Capacidad del Admin Panel de recibir actualizaciones del Metrics Dashboard sin refrescar la página ni hacer *polling* manual, con una latencia objetivo menor a 500 ms desde que el evento se persiste en PostgreSQL. Implementado vía WebSocket o SSE, consumido únicamente por el Admin Panel. Ver [08-CROSSCUTTING-CONCEPTS — Tiempo Real](./08-CROSSCUTTING-CONCEPTS.md#-tiempo-real).

### Time to Interactive (TTI)

Métrica de rendimiento *front-end*: tiempo desde que una página empieza a cargar hasta que es completamente interactiva para el usuario. Es la medida concreta del escenario de rendimiento P1 del Admin Panel (objetivo: menor a 2 segundos en el percentil 95). Ver [10-QUALITY-SCENARIOS — Rendimiento](./10-QUALITY-SCENARIOS.md#-rendimiento).

### WebSocket

Protocolo de comunicación bidireccional y persistente sobre TCP, la segunda de las dos opciones (junto con SSE) consideradas para implementar el canal de tiempo real de métricas del Admin Panel — la elección concreta entre ambas queda a discreción de la implementación de la API REST. Ver [08-CROSSCUTTING-CONCEPTS — Tiempo Real](./08-CROSSCUTTING-CONCEPTS.md#-tiempo-real).

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md) · [06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md) · [08-CROSSCUTTING-CONCEPTS.md](./08-CROSSCUTTING-CONCEPTS.md) · [10-QUALITY-SCENARIOS.md](./10-QUALITY-SCENARIOS.md) · [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md) · [CLAUDE.md](../CLAUDE.md)
**Contacto**: Carlos Jiménez Hirashi (cjhirashi@gmail.com)
