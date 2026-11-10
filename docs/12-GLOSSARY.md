# Glosario - cjhirashi-career

> **Estado (2026-11-10, [ADR-032](09-DECISIONS/032-agentes-externos-y-bedrock-fuera-de-operacion.md)):** los agentes de IA son externos y entran por la API con el rol `agent`; el subsistema de agentes con AWS Bedrock está fuera de operación. Donde este documento describe agentes internos, léase como referencia de diseño.

**GLOSARIO DEL PROYECTO** (arc42, sección 12)

**Última actualización**: 2026-11-05

Términos en orden alfabético. Los del MCP Server (retirado el 2026-09-04, [ADR-023](./09-DECISIONS/023-retirar-mcp-server.md)) ya no forman parte del sistema.

---

**Admin Panel** — SPA privada (puerto host 8002) donde Carlos gestiona su carrera, los agentes y la analítica. Un solo usuario administrador.

**ADR (Architecture Decision Record)** — Registro corto e inmutable de una decisión de arquitectura del producto, en `docs/09-DECISIONS/`. Las decisiones del arnés van en `.harness/decisions/`.

**Agent Bedrock** — Asistente de IA sobre AWS Bedrock que opera con el alcance del usuario que lo invoca. No es un canal. Hoy vive en la API; pasará a `cjhirashi-career-ai` (ADR-029).

**Agente externo** — Cliente de IA que usa un token de un usuario con `access_role = agent`. Solo alcanza `/career/*`, `POST /bedrock/chat` y `POST /files`.

**Aislamiento por usuario** — Todo endpoint de carrera filtra por el `user_id` del token.

**API REST** — `cjhirashi-career-api` (FastAPI). Único componente con acceso a PostgreSQL, MinIO y Qdrant; dueña del esquema. No se publica: se alcanza por `/api/` de los hosts del Admin y del Portal.

**Arc42** — Plantilla de documentación de arquitectura (12 secciones, `docs/01` a `docs/12`).

**Arnés (`.harness/`)** — Método, constitución, specs y memoria con los que se trabaja el repo (SDD Anchored). No es documentación de producto.

**Audit log (`audit_logs`)** — Registro de cada escritura del agente con el estado completo antes y después.

**Base de conocimiento (KB)** — Índice vectorial en Qdrant de los registros de carrera y las metodologías, para la búsqueda semántica del agente. Se retira con ADR-029.

**Canal (de entrada)** — Punto de acceso autónomo al sistema: hoy son dos, Portal y Admin.

**Compuerta (gate)** — `.harness/gate/check.sh`: verificación previa a cada sesión; exige, entre otras cosas, la documentación al día.

**CORS** — Restricción de orígenes del navegador; la API admite solo los de `CORS_ORIGINS`.

**Descubrimiento de vacantes** — Búsqueda por adaptadores (Adzuna/Indeed, Greenhouse, Lever, LinkedIn por URL oficial, Remotive, RemoteOK, GetOnBoard) que devuelve una vista previa con referencias `L1, L2…`; solo se guarda en `vacancies` lo que se autoriza (ADR-011).

**Docker Compose** — Orquestación de los 6 contenedores del sistema (`docker-compose.yml`).

**Embudo (analítica)** — Secuencia de pasos configurable cuya conversión mide el tablero.

**Entidad de carrera** — Recurso gestionado bajo `/career/{recurso}`: identidad, competencias, evidencia, vacantes, aplicaciones, contactos, CVs, etc.

**Evento de analítica** — Registro enviado por el rastreador del portal a `POST /events/track` (visita, tiempo activo, scroll, salientes, Web Vitals).

**Gate (de spec)** — Punto de aprobación del usuario en el flujo SDD (Gate 1 al aprobar el spec, Gate 2 el plan…).

**Harness (de agentes)** — El bucle que conversa con el modelo, ejecuta herramientas y gestiona memoria, perfiles y tareas. Hoy en la API (`services/bedrock/`); destino: `cjhirashi-career-ai`.

**Health check** — Prueba que Docker ejecuta para decidir si un contenedor está sano (`GET /health` en la API).

**JWT** — Token firmado (HS256) que la API emite al iniciar sesión: acceso de 7 días y refresco de 30.

**Mensaje de contacto** — Mensaje enviado desde el formulario del portal (`POST /public/contact-message`); llega al Admin con aviso en la campana.

**Metodología operativa** — Documento de instrucciones que guía a los agentes; se asigna a perfiles de agente y a secciones del Admin.

**`net-cjhirashi-career`** — Red Docker externa y dedicada del proyecto, declarada `external: true` en `docker-compose.yml`.

**Notificación in-app** — Aviso en la campana del Admin (turnos de tareas, mensajes de contacto).

**OWASP** — Línea base de seguridad exigida a todo lo expuesto a Internet.

**PDF (WeasyPrint)** — Render de CVs y cartas desde plantillas HTML, dentro de la API.

**Perfil de agente** — Configuración de un agente (nivel L1 orquestador, L2 por área o L3 por tarea, prompts, herramientas, metodologías, modelo). Se gestiona en el catálogo de agentes del Admin.

**Portal público** — SPA pública (`cjhirashi.com`, puerto host 8003): solo lectura, contacto y analítica.

**PostgreSQL** — Base de datos única de negocio (`career_db` en `postgres_db`).

**Qdrant** — Base vectorial (`qdrant`) de la KB de Agent Bedrock. Retiro decidido (ADR-029), pendiente de la etapa 3 de la spec 009.

**Rol `agent`** — Valor de `access_role` de las cuentas de agente; ver *Agente externo*.

**Secreto** — Variable de entorno sensible (`SECRET_KEY`, credenciales de AWS y MinIO); vive en `.env`, nunca versionado.

**Sección (del Admin)** — Entrada de navegación configurable (`admin_sections_l1/l2/l3`) con PK sintético `sec-N` (ADR-021); gobierna el sidebar contextual (ADR-024).

**Spec** — Especificación viva de una feature en `.harness/specs/NNN-slug/` (`spec.md`, `plan.md`, `tasks.md`) con su `estado` (`draft`, `approved`, `implemented`, `verified`).

**Streaming** — Respuesta HTTP progresiva del chat de agentes (`POST /bedrock/chat`); no hay WebSocket.

**Subtarea / plan orquestado** — Tarea padre con hijas que se ejecutan por turno; las bloqueantes siguen el `sort_order` (ADR-016).

**Tarea programada** — Tarea de agente con `scheduled_at` que ejecuta el scheduler in-process de la API aunque el Admin esté cerrado (ADR-015).

**TTI (Time to Interactive)** — Tiempo hasta que la SPA responde a la interacción.

**Vacante** — Oferta guardada en `vacancies`, con etapa del proceso y estado calculado.

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md) · [09-DECISIONS/README.md](./09-DECISIONS/README.md)
**Contacto**: cjhirashi@gmail.com
