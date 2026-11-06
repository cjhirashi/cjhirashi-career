# cjhirashi-career

![Python](https://img.shields.io/badge/python-3.11-3776AB.svg?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)
![React](https://img.shields.io/badge/react-18-61DAFB.svg?logo=react&logoColor=white)
![Estado](https://img.shields.io/badge/estado-en%20producci%C3%B3n-brightgreen.svg)

---

**cjhirashi-career** es la plataforma personal integrada de Carlos Jiménez Hirashi: un portafolio público profesional y un panel de administración privado para gestionar la carrera, ambos sobre una API central y una única fuente de verdad (PostgreSQL).

> Estado a **2026-11-05**: los tres módulos de aplicación (`admin`, `portfolio`, `api`) corren en producción. El harness de agentes se está separando de la API en `cjhirashi-career-ai` (spec 009, en curso; **aún no desplegado**). El MCP Server (Canal 3) se retiró el 2026-09-04 ([ADR-023](docs/09-DECISIONS/023-retirar-mcp-server.md)).

---

## Servicios

| Módulo | Contenedor (puerto host) | Para qué |
|---|---|---|
| **Portal público** | `cjhirashi-career-portfolio` (8003) | Portafolio: Inicio, Sobre mí, Proyectos, Blog, Contacto, Privacidad |
| **Admin Panel** | `cjhirashi-career-admin` (8002) | Gestión privada de carrera, agentes y métricas |
| **Archivos** | `minio_storage` (9000, interno) | Archivos públicos y privados en MinIO |
| **API REST** | `cjhirashi-career-api` (8000, interno) | El portal y el Admin la llaman por `/api/`; la API recibe las rutas sin ese prefijo |

Orquestación: `docker-compose.yml`, con la red Docker externa `net-cjhirashi-career`.

## Arquitectura

- **3 módulos de aplicación**: `cjhirashi-career-admin`, `cjhirashi-career-portfolio` y `cjhirashi-career-api`. Bedrock (agentes) y PDF (WeasyPrint) son capacidades de la API, no módulos ni contenedores aparte.
- **`cjhirashi-career-ai`** (en construcción, spec 009): harness de agentes con base de datos propia (`career_ai_db`) que sacará de la API los agentes, la base de conocimiento y su indexación. No está en `docker-compose.yml` todavía.
- **Infraestructura**: PostgreSQL 15 (`postgres_db`), MinIO (`minio_storage`) y Qdrant (`qdrant`, base de conocimiento vectorial de Agent Bedrock). El retiro de Qdrant está **decidido** ([ADR-029](docs/09-DECISIONS/029-harness-agentes-fuera-de-api.md)) pero se ejecuta en la etapa 3 de la spec 009: hoy sigue en uso por la API.
- **Stack**: React 18 + Vite + TypeScript (admin y portfolio, Node 20), FastAPI + SQLAlchemy 2 + Alembic (API, Python 3.11), AWS Bedrock, WeasyPrint.
- **Datos**: 69 modelos SQLAlchemy y 51 migraciones Alembic (head `4439c6915701`). La API expone 419 operaciones HTTP (282 rutas), de las que 319 cuelgan de `/career`.

## Qué hace cada módulo

**Admin Panel** (24 pantallas): panel y métricas de búsqueda; recursos de carrera (identidad, competencias, evidencia, vacantes, aplicaciones, networking, CVs y cartas); descubrimiento de vacantes; archivos; plantillas y estilos de PDF; mensajes de contacto; analítica del portafolio (tablero, metas, embudos, anotaciones); registro de errores; secciones del Admin configurables; y el área de agentes (catálogo, instrucciones, herramientas, memoria, tareas, auditoría, métricas, chat).

**Portal público** (9 páginas): Inicio, Sobre mí, Proyectos (y detalle), Blog (y entrada), Contacto (los mensajes llegan al Admin), Privacidad (con borrado de los datos propios del visitante) y 404. Incluye un rastreador de analítica con respeto a DNT/GPC.

**API**: autenticación JWT (el rol `agent` está restringido: `/career/*`, el chat de Bedrock y la subida de archivos); CRUD de carrera; descubrimiento de vacantes (Adzuna, Greenhouse, Lever, LinkedIn, Remotive y otros); Agent Bedrock y tareas programadas de agentes; generación de PDF; archivos en MinIO; endpoints públicos del portal; registro de errores; analítica del portafolio (ingesta, métricas, metas y embudos). Detalle y contrato: [`cjhirashi-career-api/docs/API.md`](cjhirashi-career-api/docs/API.md).

## Specs del arnés

| Spec | Estado | Tema |
|---|---|---|
| 001 a 004, 007 | verified | Sidebar contextual, imágenes del agente Visual, configuración de agentes, herramientas y metodologías, vacantes por etapa |
| 005 | draft | Metodologías: esquema mínimo y vínculo con secciones |
| 006 | approved | Tablas y frontends del checklist de carrera |
| 008, 011 | implemented | Descripción de empresa y puesto en vacantes; formulario de contacto al Admin |
| 009 | approved (en ejecución) | Harness de agentes fuera de la API y sin indexación |
| 010 | draft en el archivo; desplegada | Analítica profesional del portafolio |

La fuente de verdad del estado de cada spec es el `estado:` de su `spec.md` en `.harness/specs/`.

## Documentación

| Documento | Contenido |
|---|---|
| [docs/01](docs/01-INTRODUCTION.md) a [docs/12](docs/12-GLOSSARY.md) | Arc42: introducción, objetivos, interesados, estrategia, bloques, ejecución, despliegue, conceptos transversales, ADRs, calidad, riesgos y glosario |
| [docs/09-DECISIONS/](docs/09-DECISIONS/README.md) | Decisiones de arquitectura del producto (ADR-008 a ADR-029) |
| [docs/BEDROCK-SYSTEM.md](docs/BEDROCK-SYSTEM.md) | Subsistema de agentes |
| [docs/ENVIRONMENT-SECURITY.md](docs/ENVIRONMENT-SECURITY.md) | Variables de entorno, secretos y políticas |
| [docs/ADMIN_PANEL_SETUP.md](docs/ADMIN_PANEL_SETUP.md) | Arranque y configuración del panel |
| [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | Hoja de ruta |
| `cjhirashi-career-*/README.md` | Setup y superficie de cada servicio |

El arnés de trabajo (método, constitución, specs, memoria) vive en [`.harness/`](.harness/); el mapa del repo para agentes, en [AGENTS.md](AGENTS.md).

## Inicio rápido

Requisitos: Docker y Docker Compose, y la red Docker externa `net-cjhirashi-career` (créala con `docker network create net-cjhirashi-career` si no existe).

```bash
cp .env.example .env       # el compose lee `.env`; nunca se versiona
# Cambia al menos: POSTGRES_PASSWORD, SECRET_KEY (32+ caracteres aleatorios), CORS_ORIGINS,
# MINIO_ROOT_PASSWORD, PUBLIC_PORTAL_USER_ID, PORTAL_SITE_KEY y las credenciales de AWS Bedrock.
docker compose up -d --build
docker compose ps
docker compose logs -f api
```

- **Portal público**: http://localhost:8003
- **Admin Panel**: http://localhost:8002 (credenciales del usuario inicial)
- **API**: interna; Swagger en `/docs` solo si publicas el puerto 8000 para depurar

Pruebas por servicio: ver [AGENTS.md](AGENTS.md) (sección «Comandos por subproyecto»).

## Contribuir

El flujo de trabajo, los gates y las reglas del repo están en [CLAUDE.md](CLAUDE.md) y [`.harness/method.md`](.harness/method.md). Resumen:

- Commits en Conventional Commits con sufijo `(RF-NNN)` cuando aplica.
- **Todo cambio actualiza su documentación en el mismo commit** (Constitución, Art. 11); el gate bloquea si no.
- Cobertura mínima de pruebas: 80 %.

## Contacto

- **Propietario**: Carlos Jiménez Hirashi, cjhirashi@gmail.com

---

**Última actualización**: 2026-11-05
