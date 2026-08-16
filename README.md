# Portafolio-cjhirashi

![Python](https://img.shields.io/badge/python-3.11-3776AB.svg?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)
![React](https://img.shields.io/badge/react-18-61DAFB.svg?logo=react&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-FastMCP-10b981.svg)
![Estado](https://img.shields.io/badge/estado-diseño%20en%20validación-yellow.svg)

---

**Portafolio-cjhirashi** es la plataforma personal integrada de Carlos Jiménez Hirashi. Combina un portafolio público profesional, un panel de administración privado para gestión de carrera, y una interfaz MCP para agentes de IA externos — todo convergiendo en una única fuente de verdad centralizada.

---

## 🎯 Tres Canales de Acceso

### 1️⃣ **Portal Público** (8003)
Sitio de portafolio — About, Proyectos, Blog, Contacto. Visitantes públicos consultan en modo lectura.

### 2️⃣ **Admin Panel** (8002)
Dashboard privado de gestión de carrera para Carlos — identidad profesional, competencias, evidencia, métricas, chat con Bedrock.

### 3️⃣ **MCP Server** (8004)
Interfaz para agentes IA externos (Claude, etc.) — operan el sistema de forma autónoma vía protocolo MCP.

---

## 🏗️ Arquitectura

- **7 módulos independientes**: Portal Público, Admin Panel, MCP Server, API REST, Agent Bedrock, PDF Generator, PostgreSQL
- **Stack**: React 18 + FastAPI + PostgreSQL + FastMCP + AWS Bedrock + WeasyPrint
- **Docker**: 5 contenedores expuestos (Admin 8002, Portal 8003, MCP 8004) + internos (API, PDF, BD)
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

### Levantar el sistema

```bash
cd mcp-server
docker compose up -d
```

### Acceso

- **Portal Público**: http://localhost:8003
- **Admin Panel**: http://localhost:8002 (autenticación requerida)
- **MCP Server**: http://localhost:8004/sse (protocolo MCP)

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
| MCP Server | ✅ Base heredada | Refactor para nuevo alcance |
| API REST | ✅ Base heredada | Evolución para gestión carrera |
| Agent Bedrock | 🟡 En diseño | Asistente IA interno |
| PDF Generator | ✅ Base heredada | Generación CV/Cover Letter |
| PostgreSQL | 🟡 En diseño | Nuevas tablas para carrera/métricas |

---

## 🔗 Conexión Externa

El proyecto está integrado con **cjhirashi-srv** (Caddy + Cloudflare Tunnel) para acceso público:

- Documentación: `/mnt/disco2/cjhirashi-data/proyectos/cjhirashi-srv/servicios-externos/mcp-server.md`
- 3 módulos expuestos: Admin Panel (8002), Portal Público (8003), MCP Server (8004)
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
