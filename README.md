# cjhirashi-career

![Python](https://img.shields.io/badge/python-3.11-3776AB.svg?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)
![React](https://img.shields.io/badge/react-18-61DAFB.svg?logo=react&logoColor=white)
![Estado](https://img.shields.io/badge/estado-en%20producci%C3%B3n-brightgreen.svg)

---

**cjhirashi-career** es la plataforma personal integrada de Carlos Jiménez Hirashi: un portafolio público profesional y un panel de administración privado para gestionar la carrera, ambos sobre una API central y una única fuente de verdad (PostgreSQL).

> Estado a **2026-11-12**: los tres módulos de aplicación (`admin`, `portfolio`, `api`) corren en producción. Los agentes de IA son **externos** y entran por la API con el rol `agent` ([ADR-032](docs/09-DECISIONS/032-agentes-externos-y-bedrock-fuera-de-operacion.md)); el subsistema Bedrock y Qdrant se retiraron el 2026-11-11 ([ADR-033](docs/09-DECISIONS/033-retiro-del-subsistema-bedrock.md)) y el descubrimiento de vacantes el 2026-11-12 ([ADR-034](docs/09-DECISIONS/034-retiro-del-descubrimiento-de-vacantes.md)). El MCP Server (Canal 3) se retiró el 2026-09-04 ([ADR-023](docs/09-DECISIONS/023-retirar-mcp-server.md)).

---

## Servicios

| Módulo | Contenedor (puerto host) | Para qué |
|---|---|---|
| **Portal público** | `cjhirashi-career-portfolio` (8003) | Portafolio: Inicio, Sobre mí, Proyectos, Blog, Contacto, Privacidad |
| **Admin Panel** | `cjhirashi-career-admin` (8002) | Gestión privada de carrera y métricas |
| **Archivos** | `minio_storage` (9000, interno) | Archivos públicos y privados en MinIO |
| **API REST** | `cjhirashi-career-api` (8000, interno) | El portal y el Admin la llaman por `/api/`; la API recibe las rutas sin ese prefijo |

Orquestación: `docker-compose.yml`, con la red Docker externa `net-cjhirashi-career`.

## Arquitectura

- **3 módulos de aplicación**: `cjhirashi-career-admin`, `cjhirashi-career-portfolio` y `cjhirashi-career-api`. La generación de PDF (WeasyPrint) es una capacidad de la API, no un módulo ni un contenedor aparte. Los agentes de IA son externos: se conectan a la API con un token de rol `agent` (solo `/career/*` y la subida de archivos).
- **Infraestructura**: PostgreSQL 15 (`postgres_db`) y MinIO (`minio_storage`).
- **Stack**: React 18 + Vite + TypeScript (admin y portfolio, Node 20), FastAPI + SQLAlchemy 2 + Alembic (API, Python 3.11), WeasyPrint.
- **Datos**: 58 tablas y 56 migraciones Alembic (head `9e5a3b7d2c04`). La API expone 372 operaciones HTTP (241 rutas), de las que 315 cuelgan de `/career`.

## Qué hace cada módulo

**Admin Panel**: panel y métricas de búsqueda; recursos de carrera (identidad, competencias, evidencia, vacantes, aplicaciones, networking, CVs y cartas); archivos; plantillas y estilos de PDF; mensajes de contacto; analítica del portafolio (tablero, metas, embudos, anotaciones); registro de errores; secciones del Admin configurables; y tareas. El panel conserva el área del subsistema de agentes Bedrock (catálogo, instrucciones, herramientas, memoria, auditoría, métricas y chat), fuera de operación ([ADR-032](docs/09-DECISIONS/032-agentes-externos-y-bedrock-fuera-de-operacion.md)).

**Portal público** (9 páginas): Inicio, Sobre mí, Proyectos (y detalle), Blog (y entrada), Contacto (los mensajes llegan al Admin), Privacidad (con borrado de los datos propios del visitante) y 404. Incluye un rastreador de analítica con respeto a DNT/GPC.

**API**: autenticación JWT (el rol `agent` está restringido a `/career/*` y a la subida de archivos nuevos); CRUD de carrera; generación de PDF; archivos en MinIO; endpoints públicos del portal; registro de errores; analítica del portafolio (ingesta, métricas, metas y embudos). Detalle y contrato: [`cjhirashi-career-api/docs/API.md`](cjhirashi-career-api/docs/API.md).

## Specs del arnés

| Spec | Estado | Tema |
|---|---|---|
| 001 a 004, 007 | verified | Sidebar contextual, imágenes y configuración de agentes, herramientas y metodologías (001 a 004 quedaron sin efecto al retirarse el subsistema Bedrock, ADR-033), vacantes por etapa |
| 006 | approved | Tablas y frontends del checklist de carrera |
| 008, 011 | implemented | Descripción de empresa y puesto en vacantes; formulario de contacto al Admin |
| 009 | superseded | Harness de agentes fuera de la API: sin efecto tras el retiro del subsistema Bedrock ([ADR-033](docs/09-DECISIONS/033-retiro-del-subsistema-bedrock.md)) |
| 010 | implemented | Analítica profesional del portafolio |

La fuente de verdad del estado de cada spec es el `estado:` de su `spec.md` en `.harness/specs/`.

## Documentación

| Documento | Contenido |
|---|---|
| [docs/01](docs/01-INTRODUCTION.md) a [docs/12](docs/12-GLOSSARY.md) | Arc42: introducción, objetivos, interesados, estrategia, bloques, ejecución, despliegue, conceptos transversales, ADRs, calidad, riesgos y glosario |
| [docs/09-DECISIONS/](docs/09-DECISIONS/README.md) | Decisiones de arquitectura del producto (ADR-008 a ADR-032) |
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
# MINIO_ROOT_PASSWORD, PUBLIC_PORTAL_USER_ID, PORTAL_SITE_KEY .
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

**Última actualización**: 2026-11-10

## Licencia

Este proyecto se distribuye bajo la [PolyForm Noncommercial License 1.0.0](LICENSE): se puede ver, estudiar y usar con fines no comerciales. **No se permite su uso comercial** sin autorización escrita del autor. Copyright 2026 Carlos Jiménez Hirashi.
