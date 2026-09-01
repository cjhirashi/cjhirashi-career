# Equipo de Agentes — cjhirashi-career

⚠️ **NOTA DE OBSOLESCENCIA (2026-09-01):** Este documento mantiene valor histórico y como referencia de dominios/proveedores externos (agentes globales de C), pero el sistema de agentes locales (Tabla B) pasó a un harness minimalista: los roles se simplificaron a **Líder** (`agents/leader.md`), **Implementador** (`agents/implementer.md`) y **Revisor** (`agents/reviewer.md`). Los especialistas de módulo antiguos (`.claude/agents/`) han sido retirados. Consultar [`AGENTS.md`](../AGENTS.md) para el nuevo sistema de gobernanza.

---

Catálogo de a quién delegar cada tipo de tarea. Referenciado desde [`CLAUDE.md`](../CLAUDE.md) — **no se repite ahí** para no cargar este catálogo en cada turno de trabajo; se consulta solo cuando hay que decidir a quién delegar.

> **Regla de delegación (HISTÓRICA):** el Arquitecto de Soluciones (rol definido en `CLAUDE.md`) **no escribe código de módulo ni hace trabajo repetitivo**. Hoy la delegación usa los 3 roles genéricos de `agents/`, no los especialistas viejos de la Tabla B abajo.

## A. Equipo núcleo de calidad (5 roles metodológicos)

Son los 5 roles transversales que gobiernan el framework de calidad (ver [METODOLOGIA-CALIDAD.md](METODOLOGIA-CALIDAD.md)). Se materializan con estos agentes:

| Rol | Agente(s) | Responsabilidades |
|-----|-----------|-------------------|
| 🐳 **Experto Docker** | `docker-expert` (local), `docker` / `arquitectura-red` (global) | `docker-compose.yml`, Dockerfiles, redes (`network-cjhirashi-srv`), volúmenes, puertos, CI/CD |
| 📚 **Documentador** | `documentacion-especialista` (global) | Redactar Arc42 + ADR, READMEs, changelogs. **NO decide qué documentar (lo decide el Arquitecto)** |
| 🧪 **QA Engineer** | `qa-engineer` (local) | Cobertura ≥80%, estrategia de testing, tests integración/E2E, métricas |
| 🔍 **Code Quality Guardian** | `code-quality-guardian` (local) | SOLID, Clean Code, code review, SonarQube, deuda técnica, aprobar/rechazar PR |
| 🔗 **Git Especialista** | `git-specialist` (local), `git-especialista` (global) | Commits descriptivos, ramas (main/develop), merges, historial limpio, tags/releases |

## B. Especialistas de módulo (locales — `.claude/agents/`)

| Agente | Área |
|--------|------|
| `api-rest-specialist` | Diseño API REST: schema, endpoints, seguridad, contrato, testing |
| `admin-panel-specialist` | Admin Panel: React SPA, CRUD, auth JWT, métricas real-time, Zustand + React Query |
| `portal-publico-specialist` | Portal Público: React SPA read-only (About, Projects, Blog, Contact) |
| `revisor-fallas` | Triage de `error_reports` (ADR-018): diagnostica causa raíz, coordina fix, marca `resolved` |

## C. Agentes globales a disposición (usuario — `~/.claude/agents/`)

Disponibles en **todos** los proyectos de Charlie. Delegar a estos cuando la tarea caiga en su dominio:

| Agente | Cuándo delegarle |
|--------|------------------|
| `arquitectura-red` | Estructura de proyectos Docker, conectividad inter-servicio, redes compartidas y volúmenes |
| `docker` | Docker/Compose: imágenes, contenedores, redes, volúmenes, optimización de builds multi-proyecto |
| `cicd` | Pipelines CI/CD con GitHub Actions: tests, builds reproducibles, quality gates, despliegues |
| `documentacion-especialista` | READMEs, guías de arquitectura, referencias de API, changelogs, docs de procesos |
| `git-especialista` | Ramas, commits, merges, resolución de conflictos, flujos Git |
| `seguridad` | Auditoría de dependencias, análisis de vulnerabilidades, revisión de auth y control de acceso |
| `observabilidad` | Logging estructurado, métricas, health checks, alertas |
| `backup-recuperacion` | Estrategias de backup, DR, continuidad operativa |
| `vps-hosting` | Despliegue en VPS: Ubuntu, Cloudflare Tunnel, servicios del sistema, dominio |
| `aws` | Recursos e infraestructura AWS: EC2, S3, RDS, IAM, VPC (Bedrock vive aquí) |
| `kubernetes` | Orquestación K8s: manifests, deployments, services, ingress, clusters |
| `desarrollo-mcps` | Servidores MCP: tools, resources y prompts expuestos a agentes IA (módulo `cjhirashi-career-mcp`) |
| `harness-agentes` | Harness de sistemas de agentes: bucle agéntico, diseño de tools, gestión de contexto, subagentes, hooks, memoria y **eficiencia** (tokens/latencia/coste). Investiga docs oficiales (Claude Code, Agent SDK, MCP) y buenas prácticas |
| `aws-bedrock` | AWS Bedrock end-to-end: catálogo y capacidades de modelos, Converse API, Bedrock Agents, **AgentCore**, Knowledge Bases, Guardrails, Flows, conexiones efectivas (boto3/IAM/VPC endpoints) y throttling. Siempre consulta docs oficiales de AWS |
| `modelado-datos-api` | Estructura de las tablas de una API — clasificación de modelos en **Sistema / Operativa / Integración** para que la arquitectura de datos sea reutilizable al replicar la API en otro proyecto; organización de carpetas `models`/`schemas`, plan de migración de imports, convenciones de PK/auditoría, documentación del esquema con diagramas. **Solo diseña en `docs/`, nunca toca código** |
| `implementador-modelos-api` | Ejecuta en código el plan que diseña `modelado-datos-api`: modelos SQLAlchemy, esquemas Pydantic, migraciones Alembic (rename, no recreación) y los endpoints/servicios/imports afectados. No decide clasificación ni columnas de dominio nuevas |
| `ingenieria-llm` | Integración con LLMs: system prompts, routing de modelos, evaluación de calidad, optimización de llamadas (agentes Bedrock) |
| `rag` | RAG: embeddings, indexación en Qdrant, chunking de documentos, recuperación semántica |
| `skills-agentes` | Diseño y empaquetado de skills/herramientas reutilizables para agentes IA |
| `machine-learning` | Pipelines ML y MLOps: entrenamiento, validación, registro y despliegue de modelos |
| `deep-learning` | Arquitecturas de redes neuronales: entrenamiento, fine-tuning, optimización |
| `vision-computadora` | Procesamiento de imágenes, detección de objetos, OCR, análisis visual |
| `iot-industrial` | Integraciones IoT y protocolos industriales: BACnet, Modbus, MQTT, OPC-UA |

> Los agentes de `C` que hoy no aplican al alcance del proyecto (ML, DL, visión, IoT, K8s) se mantienen listados porque **están disponibles** y pueden activarse si el alcance cambia.
