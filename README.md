# cjhirashi-career

![Python](https://img.shields.io/badge/python-3.11-3776AB.svg?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)
![React](https://img.shields.io/badge/react-18-61DAFB.svg?logo=react&logoColor=white)
![Estado](https://img.shields.io/badge/estado-diseño%20en%20validación-yellow.svg)

---

**cjhirashi-career** es la plataforma personal integrada de Carlos Jiménez Hirashi. Combina un portafolio público profesional y un panel de administración privado para gestión de carrera — todo convergiendo en una única fuente de verdad centralizada.

> El **MCP Server** (Canal 3) se retiró el 2026-09-04 — ver [ADR-023](docs/09-DECISIONS/023-retirar-mcp-server.md). El arc42 todavía lo describe como diseño previo.

---

## 🎯 Dos Canales de Acceso

### 1️⃣ **Portal Público** (8003)
Sitio de portafolio — About, Proyectos, Blog, Contacto. Visitantes públicos consultan en modo lectura.

### 2️⃣ **Admin Panel** (8002)
Dashboard privado de gestión de carrera para Carlos — identidad profesional, competencias, evidencia, métricas, chat con Bedrock.

---

## 🏗️ Arquitectura

- **3 módulos**: `cjhirashi-career-admin`, `cjhirashi-career-portfolio`, `cjhirashi-career-api` (Bedrock y PDF son capacidades de la API; Postgres/MinIO/Qdrant son infraestructura)
- **Stack**: React 18 + FastAPI + PostgreSQL + AWS Bedrock + WeasyPrint
- **Docker**: 2 contenedores de app expuestos (Admin 8002, Portal 8003) + internos (API con PDF WeasyPrint, Qdrant, Postgres, MinIO)
- **Métricas**: Tracking de visitantes, actividad del agente, auditoría centralizada
- **Real-time**: WebSocket/SSE para dashboards vivos

---

## 📚 Documentación

**Documentación arquitectónica completa** (Arc42 ISO 42010):

| Sección | Propósito |
|---------|-----------|
| **[01-INTRODUCTION.md](docs/01-INTRODUCTION.md)** | Visión y contexto del sistema |
| **[02-ARCHITECTURE-GOALS.md](docs/02-ARCHITECTURE-GOALS.md)** | Objetivos y restricciones arquitectónicas |
| **[03-STAKEHOLDERS.md](docs/03-STAKEHOLDERS.md)** | Usuarios, roles y expectativas |
| **[04-SOLUTION-STRATEGY.md](docs/04-SOLUTION-STRATEGY.md)** | Decisiones de alto nivel |
| **[05-BUILDING-BLOCK-VIEW.md](docs/05-BUILDING-BLOCK-VIEW.md)** | Componentes y estructura (Admin Panel SPA detallado) |
| **[06-RUNTIME-VIEW.md](docs/06-RUNTIME-VIEW.md)** | Flujos de datos en tiempo de ejecución |
| **[07-DEPLOYMENT-VIEW.md](docs/07-DEPLOYMENT-VIEW.md)** | Docker, puertos, configuración |
| **[08-CROSSCUTTING-CONCEPTS.md](docs/08-CROSSCUTTING-CONCEPTS.md)** | Patrones transversales (métricas, tracking, auth) |
| **[09-DECISIONS/README.md](docs/09-DECISIONS/README.md)** | Architecture Decision Records (ADRs) |
| **[10-QUALITY-SCENARIOS.md](docs/10-QUALITY-SCENARIOS.md)** | Escenarios de calidad verificables |
| **[11-TECHNICAL-RISKS.md](docs/11-TECHNICAL-RISKS.md)** | Riesgos técnicos y mitigación |
| **[12-GLOSSARY.md](docs/12-GLOSSARY.md)** | Glosario de términos |

---

## 🚀 Inicio Rápido

### Requisitos
- Docker y Docker Compose
- Acceso a red `network-cjhirashi-srv`

### Configurar Variables de Entorno

**IMPORTANTE**: Las variables de entorno se configuran en `.env.local` (NO versionado en git)

```bash
# Copiar plantilla de configuración
cp .env.example .env.local

# Editar valores en .env.local (cambiar contraseñas, claves, etc.)
nano .env.local  # o tu editor favorito

# Variables críticas a actualizar:
# - POSTGRES_PASSWORD (contraseña segura)
# - SECRET_KEY (mínimo 32 caracteres aleatorios)
# - CORS_ORIGINS (hosts permitidos - comma-separated sin espacios)
# - BEDROCK_REGION / BEDROCK_MODEL_ID (si usas AWS Bedrock)
```

### Levantar el sistema

```bash
# Docker Compose carga automáticamente .env.local
docker compose up -d

# O especificar explícitamente (opcional)
docker compose --env-file .env.local up -d
```

### Verificar que está en línea

```bash
docker compose ps
docker compose logs -f cjhirashi-career-api
```

### Acceso

- **Portal Público**: http://localhost:8003
- **Admin Panel**: http://localhost:8002 (credenciales: ver setup inicial)
- **API REST**: interna (Swagger en `http://localhost:8000/docs` solo si se publica el puerto en depuración)

---

## 🏛️ Guía de Desarrollo

**Ver [CLAUDE.md](CLAUDE.md)** para:
- Rol del Arquitecto de Soluciones
- Framework de calidad (Arc42 + SOLID + TDD 80%)
- 5 agentes globales (Docker Expert, Documentador, QA Engineer, Code Quality Guardian, Git Specialist)
- Workflow arquitectónico (Diseño → Infraestructura → Documentación → Desarrollo → Validación)
- Estructura del proyecto

---

## 📊 Estado Actual

**Fase**: Diseño arquitectónico validado ✅

**Status por componente**:

| Componente | Estado | Notas |
|-----------|--------|-------|
| Portal Público | 🟡 En diseño | Réplica mejorada de cjhirashi.com |
| Admin Panel SPA | 🟡 En diseño | Dashboard dinámico con métricas |
| MCP Server | ❌ Retirado 2026-09-04 | Ver [ADR-023](docs/09-DECISIONS/023-retirar-mcp-server.md) |
| API REST | ✅ Base heredada | Evolución para gestión carrera |
| Agent Bedrock | ✅ En la API | Asistente IA interno (sin contenedor propio) |
| PDF (WeasyPrint) | ✅ En la API | CV / plantillas HTML; no es un módulo ni un contenedor |
| PostgreSQL | 🟡 En diseño | Nuevas tablas para carrera/métricas |

---

## 🔗 Conexión Externa

El proyecto está integrado con **cjhirashi-srv** (Caddy + Cloudflare Tunnel) para acceso público:

- Documentación: `servicios-externos/cjhirashi-career.md`
- 2 módulos de app expuestos: Admin Panel (8002), Portal Público (8003)
- Proxy: Caddy reverse proxy + Cloudflare Tunnel
- Dominio: Configurado en cjhirashi-srv

---

## 📋 Checklist de Calidad

Antes de que un módulo sea "listo":

```
☐ Código escrito (SOLID + Clean Code)
☐ Unit tests: 80%+ cobertura
☐ Integration tests: flujos críticos
☐ Code review: aprobado
☐ Security scan: sin vulnerabilidades
☐ Performance: aceptable
☐ Documentación: Arc42 + ADR
☐ README: claro y profesional
☐ CI/CD gates: pasan todos
☐ Integración: funciona con otros módulos
```

---

## 🤝 Contribuir

Ver [CLAUDE.md](CLAUDE.md) para workflows, roles y procesos de calidad.

```bash
# Crear rama de feature
git checkout -b feature/mi-cambio

# Commit con Conventional Commits
git commit -m "feat: descripción del cambio"

# Push
git push origin feature/mi-cambio
```

---

## 📧 Contacto

- **Propietario**: Carlos Jiménez Hirashi
- **Email**: cjhirashi@gmail.com
- **Issues**: Reportar en repositorio

---

**Última actualización**: 2026-08-16  
**Versión**: 3.0 (Portafolio + Gestor Carrera + Agentes IA)  
**Documentación**: Arc42 completo (12 secciones)
