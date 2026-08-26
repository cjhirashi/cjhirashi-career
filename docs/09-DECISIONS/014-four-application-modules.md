# ADR-014: Cuatro módulos de aplicación

## Estado

Aceptado — 2026-08-25

## Contexto

El diseño previo trataba como “módulos” siete unidades de distinto tipo: Admin Panel, Portal Público, MCP Server, API REST, Agent Bedrock, PDF Generator y PostgreSQL. Eso mezclaba **canales de producto**, **capacidades internas** e **infraestructura**, y hacía más difícil coordinar especialistas y leer el árbol del repo.

El alcance de cjhirashi-career se opera por tres canales (humano, público, agente externo) más un orquestador. Bedrock ya vive in-process en la API. PostgreSQL, MinIO y Qdrant no son código de negocio. El PDF es un renderer interno de la API (WeasyPrint).

## Decisión

El proyecto tiene **exactamente cuatro módulos de aplicación**:

| Módulo | Carpeta | Puerto host | Rol |
|--------|---------|-------------|-----|
| **Admin Panel** | `cjhirashi-career-admin/` | 8002 | Canal privado de Carlos (CRUD + chat Bedrock) |
| **Portal Público** | `cjhirashi-career-portfolio/` | 8003 | Canal de lectura pública |
| **API REST** | `cjhirashi-career-api/` | 8001 (interno) | Orquestador único; único escritor de PostgreSQL |
| **MCP Server** | `cjhirashi-career-mcp/` | 8004 | Canal MCP (contenedor `cjhirashi-career-mcp`) |

**No son módulos:**

- **Agent Bedrock** — capacidad de la API, usada desde el Admin Panel; sin contenedor propio.
- **PDF** — capacidad de la API (`cjhirashi-career-api/src/services/pdf/`, WeasyPrint in-process). No hay carpeta ni contenedor propios.
- **PostgreSQL, MinIO, Qdrant** — infraestructura en Compose.
- **`frontend/`** — se eliminó (SPA del generador de documentos). No era el servidor MCP.

### Por Qué

- Un módulo = unidad de código con especialista, tests (80%) y README, no cada contenedor Docker.
- Los tres canales más la API cubren todo el producto; el resto es apoyo o infra.
- Evita que Bedrock o Postgres se traten como “módulos a implementar” en paralelo al Admin o al Portal.

## Consecuencias

### Positivas

- Árbol y equipo alineados: 101/102 API, 103 Admin, 104 Portal, 105 MCP.
- Compose puede tener más *servicios* que módulos (Postgres, MinIO, Qdrant).

### Negativas

- Se eliminó `frontend/` (SPA del generador de documentos). El MCP vive en `cjhirashi-career-mcp/` (antes `server/`).
- El contenedor `pdf_generator` se fusionó en la API (WeasyPrint in-process, ADR-014 seguimiento 2026-08-25).

## Alternativas consideradas

### Siete módulos (una unidad por contenedor o capacidad)

- Contra: Bedrock y Postgres no se desarrollan como el Admin; infla el mapa mental.

### Dejar PDF Generator como contenedor aparte

- Contra: un hop HTTP extra y un servicio más que solo usaba la API.
- Se rechazó: WeasyPrint corre in-process en la API (pool de procesos para aislar crashes nativos).

## Implicaciones

- [x] Fusionar PDF Generator en la API (WeasyPrint in-process).
- [x] Eliminar `frontend/` (SPA del generador de documentos; no era el MCP).
- [x] Renombrar carpetas: `admin` → `cjhirashi-career-admin`, `portal` → `cjhirashi-career-portfolio`, `api` → `cjhirashi-career-api`, `server` → `cjhirashi-career-mcp`.

## Seguimiento

Depreca la lectura de “7 módulos” en CLAUDE.md, README y Arc42 a partir de 2026-08-25.

---

**Creado por**: Arquitecto de Soluciones
**Aprobado por**: Carlos Jiménez Hirashi
**Fecha de creación**: 2026-08-25
**Última revisión**: 2026-08-25
**Estado de vigencia**: Vigente
