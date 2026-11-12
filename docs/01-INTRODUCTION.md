# Introducción y contexto - cjhirashi-career

**INTRODUCCIÓN ARQUITECTÓNICA** (arc42, sección 1)

**Última actualización**: 2026-11-10
**Resumen**: dos canales de entrada (Portal público y Admin Panel) hacia una API central con una sola base de datos. Stack: React 18 · FastAPI · PostgreSQL · MinIO · WeasyPrint. Estado: en producción.

> El MCP Server (antes «Canal 3») se retiró el 2026-09-04: [ADR-023](./09-DECISIONS/023-retirar-mcp-server.md). Los agentes de IA son externos y acceden con tokens de rol `agent` a la API REST; el subsistema de agentes interno (Bedrock) se retiró el 2026-11-11 ([ADR-033](./09-DECISIONS/033-retiro-del-subsistema-bedrock.md)).

---

## Visión general

**cjhirashi-career** es la plataforma personal integrada de Carlos Jiménez Hirashi. Combina un portafolio público y una herramienta privada de gestión de carrera sobre una única fuente de verdad: la curación de la carrera (hecha a mano en el Admin Panel o por un agente externo con token `agent`) alimenta el contenido que el portal publica.

| Canal | Contenedor | Audiencia | Acceso |
|---|---|---|---|
| **Portal público** | `cjhirashi-career-portfolio` (puerto host 8003) | Reclutadores, colegas, público | Solo lectura, sin autenticación; formulario de contacto y analítica con límites de tasa |
| **Admin Panel** | `cjhirashi-career-admin` (8002) | Carlos, único usuario administrador | Login con JWT |
| **Archivos públicos** | `minio_storage` | Cualquiera, por enlace | Lectura de los archivos marcados públicos |

El portal y el Admin llaman a la API por `/api/`; la API recibe las rutas sin ese prefijo. La API (`cjhirashi-career-api:8000`) no publica puerto al host.

Los **agentes de IA** no son un canal propio: son clientes externos de la API REST con un rol `agent` acotado a `/career/*` y a la subida de archivos.

## Componentes

| # | Componente | Contenedor | Rol |
|---|---|---|---|
| 1 | Portal público | `cjhirashi-career-portfolio` | SPA React: Inicio, Sobre mí, Proyectos, Blog, Contacto, Privacidad; rastreador de analítica |
| 2 | Admin Panel | `cjhirashi-career-admin` | SPA React: carrera, vacantes, archivos, PDF, métricas, mensajes de contacto, agentes |
| 3 | API REST | `cjhirashi-career-api` | FastAPI: autenticación, CRUD de carrera, PDF (WeasyPrint), archivos, analítica; dueña del esquema |
| 4 | PostgreSQL | `postgres_db` | Persistencia de todo el negocio (69 modelos, 53 migraciones Alembic) |
| 5 | MinIO | `minio_storage` | Archivos (bucket único; los públicos se sirven como archivos públicos) |

Detalle de bloques: [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md). Despliegue: [07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md).

## Flujos principales

1. **Gestión manual**: Admin → API → PostgreSQL.
2. **Con un agente externo**: agente → API (`/career/*`, con token de rol `agent`) → PostgreSQL; pasa por las mismas validaciones que el Admin.
3. **Portal público**: Portal → API (`/public/*`, sin autenticación) → PostgreSQL; el contenido publicable sale de la misma base que cura el Admin.
4. **Analítica del portafolio**: el rastreador del portal envía eventos a la API (ingesta con sesionización y filtro de bots); el Admin los consulta en su tablero y un agente con token puede consultar las métricas.
5. **Contacto**: el formulario del portal crea un mensaje en la API, con aviso en la campana del Admin.

Secuencias detalladas: [06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md).

## Stack tecnológico

| Capa | Tecnología | Versión |
|---|---|---|
| Portal y Admin | React + TypeScript + Vite, Tailwind, React Query, Zustand, React Router; Recharts en el Admin | React 18, Vite 5, TypeScript 5, Node 20 |
| API | FastAPI + SQLAlchemy (async, asyncpg) + Alembic + Pydantic | FastAPI 0.104, SQLAlchemy 2.0, Python 3.11 (imagen) |
| Autenticación | PyJWT (HS256, acceso 7 días, refresco 30) + bcrypt | PyJWT 2.8 |
| PDF | WeasyPrint + plantillas HTML | WeasyPrint 69 |
| Archivos | MinIO (cliente `minio`) | — |
| Base de datos | PostgreSQL | 15 (alpine) |
| Orquestación | Docker Compose | red externa `net-cjhirashi-career` |

## Principios de diseño

- **Dos canales, una sola API.** Portal y Admin no se invocan entre sí; convergen en la API.
- **Fuente única de verdad.** No hay copia paralela del contenido público: todo pasa por PostgreSQL vía la API, y se distingue por su condición de publicable.
- **La API es la única que escribe en la base de carrera.** Ningún frontend mantiene estado de negocio propio.
- **Los agentes de IA son clientes externos de la API**, sin puerto propio ni exposición adicional.
- **Acceso restringido por diseño.** Solo Portal, Admin y archivos son alcanzables desde fuera; API y PostgreSQL, solo dentro de la red Docker.
- **Capas.** `routes → services → repositories → models` en Python; la lógica de negocio vive en `services/`.

## Modelo de seguridad

- **Autenticación**: JWT HS256 emitido por la API; contraseñas con bcrypt (12 rondas). Un único usuario administrador; no hay RBAC multiusuario.
- **Rol `agent`**: token dedicado para agentes. Solo alcanza `/career/*` y `POST /files` (subida); no puede listar, cambiar visibilidad, descargar ni borrar archivos. El resto responde 403.
- **Portal público**: sin login; CORS restringido a los orígenes conocidos, límite de tasa en el formulario de contacto (3 por hora por IP y por correo) y en la ingesta de analítica; el visitante puede borrar sus datos en `/privacy`.
- **Archivos**: la subida acepta `is_public` (por defecto `true`); solo los públicos se sirven como archivos públicos. Listar, cambiar la visibilidad, descargar y borrar son exclusivos del administrador.
- **Transporte**: el tráfico interno viaja por la red Docker.

## Preguntas abiertas

2. **Autorización de agentes**: el token `agent` puede escribir datos de carrera sin supervisión en tiempo real; no hay confirmación humana por operación.
3. **Caché del portal**: el portal lee de la API en cada visita; no hay capa de caché ni paso de publicación explícito.

Las decisiones ya tomadas están en [09-DECISIONS/](./09-DECISIONS/README.md).

---

**Relacionado**: [README.md](../README.md) · [CLAUDE.md](../CLAUDE.md) · **Contacto**: cjhirashi@gmail.com
