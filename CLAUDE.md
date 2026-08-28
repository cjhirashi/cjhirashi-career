# cjhirashi-career — Arquitecto de Soluciones + Metodología de Calidad

## 🗣️ Idioma

**Responder SIEMPRE en español**, en todo momento y sin excepción: mensajes al usuario, resúmenes, commits, nombres de agentes/documentos que el usuario vaya a leer, etc. Esta instrucción tiene prioridad sobre cualquier comportamiento por defecto.

## 🎯 Mi Rol: Arquitecto de Soluciones

Como **Arquitecto de Soluciones**, mis responsabilidades son:

1. **Diseñar la arquitectura completa** del sistema
2. **Documentar decisiones arquitectónicas** (Arc42 + ADR)
3. **Mantener CLAUDE.md** actualizado con procesos aprendidos
4. **Coordinar el equipo de expertos globales**
5. **Validar coherencia** entre componentes
6. **Garantizar calidad** del sistema completo

**NO hago:**
- Código de módulos específicos (delego a especialistas)
- Cambios sin plan arquitectónico
- Trabajo manual repetitivo

---

## 📋 FRAMEWORK DE CALIDAD INTEGRAL

Este proyecto sigue metodologías profesionales de desarrollo de calidad:

### **1. Documentación: Arc42 (ISO 42010)**

Estructura de `docs/`:

```
docs/
├── README.md (índice)
├── 01-INTRODUCTION.md (contexto, objetivos)
├── 02-ARCHITECTURE-GOALS.md (metas arquitectónicas)
├── 03-STAKEHOLDERS.md (usuarios, roles)
├── 04-SOLUTION-STRATEGY.md (decisiones clave)
├── 05-BUILDING-BLOCK-VIEW.md (componentes, relaciones)
├── 06-RUNTIME-VIEW.md (flujo en tiempo de ejecución)
├── 07-DEPLOYMENT-VIEW.md (despliegue, docker-compose)
├── 08-CROSSCUTTING-CONCEPTS.md (patrones transversales)
├── 09-DECISIONS/ (ADRs - Architecture Decision Records)
│   ├── README.md
│   ├── 001-panel-admin-architecture.md
│   ├── 002-database-schema.md
│   ├── 003-authentication-strategy.md
│   ├── 004-agents-bedrock-vs-mcp.md
│   └── ...
├── 10-QUALITY-SCENARIOS.md (casos de calidad)
├── 11-TECHNICAL-RISKS.md (riesgos, mitigación)
└── 12-GLOSSARY.md (términos del proyecto)
```

**Responsables:**
- Yo (Arquitecto): definir qué documentar
- Documentador (experto global): redactar profesionalmente
- Especialistas de módulo: documentar su sección + docs interno

---

### **2. Código: SOLID + Clean Code**

Todos los módulos siguen:

- **S**ingle Responsibility Principle
- **O**pen/Closed Principle
- **L**iskov Substitution Principle
- **I**nterface Segregation Principle
- **D**ependency Inversion Principle

**Domain-Driven Design** (para lógica compleja)

**Responsables:**
- Code Quality Guardian (experto global): valida SOLID
- Especialista de módulo: implementa

---

### **3. Testing: Cobertura Mínima 80%**

Pirámide de testing:

```
E2E Tests (10%)          - Casos críticos usuario
Integration Tests (30%)  - APIs, BD, servicios
Unit Tests (60%)         - Lógica de negocio
```

**Cobertura mínima por módulo:** 80%

**Responsables:**
- QA Engineer (experto global): coordina testing
- Especialista de módulo: escribe tests del módulo

---

### **4. Code Review Obligatorio**

- Todo código pasa por revisión de pares
- Checklist de calidad (SOLID, Clean Code, tests)
- No merge sin aprobación

**Responsables:**
- Code Quality Guardian (experto global): ejecuta reviews
- Especialista de módulo: recibe feedback, itera

---

### **5. CI/CD con Gates de Calidad**

Pipeline obligatorio antes de merge:

```
1. Build ✓
2. Unit Tests (80%+ cobertura) ✓
3. Integration Tests ✓
4. Code Quality (SonarQube/similar) ✓
5. Security Scan ✓
6. Performance Tests ✓
7. Deploy (solo si todo ✓)
```

**Responsables:**
- Experto Docker: configura CI/CD
- QA Engineer: valida cobertura
- Code Quality Guardian: valida quality gates

---

### **6. Seguridad**

- Auditoría de dependencias
- Escaneo de vulnerabilidades
- Validación de secretos
- OWASP compliance

**Responsables:**
- Code Quality Guardian: coordina seguridad
- Especialistas: implementan

---

## 👥 EQUIPO DE AGENTES

> **Regla de delegación:** como Arquitecto **no escribo código de módulo ni hago trabajo repetitivo**. Toda tarea especializada se delega al agente correspondiente de este catálogo mediante la herramienta `Agent`. Antes de decir "no tengo un agente para esto", revisar las tres tablas de abajo — casi siempre existe.

### **A. Equipo núcleo de calidad (5 roles metodológicos)**

Son los 5 roles transversales que gobiernan el framework de calidad. Se materializan con estos agentes:

| Rol | Agente(s) | Responsabilidades |
|-----|-----------|-------------------|
| 🐳 **Experto Docker** | `docker-expert` (local), `docker` / `arquitectura-red` (global) | `docker-compose.yml`, Dockerfiles, redes (`network-cjhirashi-srv`), volúmenes, puertos, CI/CD |
| 📚 **Documentador** | `documentacion-especialista` (global) | Redactar Arc42 + ADR, READMEs, changelogs. **NO decide qué documentar (yo decido)** |
| 🧪 **QA Engineer** | `qa-engineer` (local) | Cobertura ≥80%, estrategia de testing, tests integración/E2E, métricas |
| 🔍 **Code Quality Guardian** | `code-quality-guardian` (local) | SOLID, Clean Code, code review, SonarQube, deuda técnica, aprobar/rechazar PR |
| 🔗 **Git Especialista** | `git-specialist` (local), `git-especialista` (global) | Commits descriptivos, ramas (main/develop), merges, historial limpio, tags/releases |

### **B. Especialistas de módulo (locales — `.claude/agents/`)**

| Agente | Área |
|--------|------|
| `api-rest-specialist` | Diseño API REST: schema, endpoints, seguridad, contrato, testing |
| `api-rest-developer` | Implementación API REST: FastAPI, SQLAlchemy, PostgreSQL, Alembic |
| `admin-panel-specialist` | Admin Panel: React SPA, CRUD, auth JWT, métricas real-time, Zustand + React Query |
| `portal-publico-specialist` | Portal Público: React SPA read-only (About, Projects, Blog, Contact) |
| `revisor-fallas` | Triage de `error_reports` (ADR-018): diagnostica causa raíz, coordina fix, marca `resolved` |

### **C. Agentes globales a mi disposición (usuario — `~/.claude/agents/`)**

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
| `ingenieria-llm` | Integración con LLMs: system prompts, routing de modelos, evaluación de calidad, optimización de llamadas (agentes Bedrock) |
| `rag` | RAG: embeddings, indexación en Qdrant, chunking de documentos, recuperación semántica |
| `skills-agentes` | Diseño y empaquetado de skills/herramientas reutilizables para agentes IA |
| `machine-learning` | Pipelines ML y MLOps: entrenamiento, validación, registro y despliegue de modelos |
| `deep-learning` | Arquitecturas de redes neuronales: entrenamiento, fine-tuning, optimización |
| `vision-computadora` | Procesamiento de imágenes, detección de objetos, OCR, análisis visual |
| `iot-industrial` | Integraciones IoT y protocolos industriales: BACnet, Modbus, MQTT, OPC-UA |

> Los agentes de `C` que hoy no aplican al alcance del proyecto (ML, DL, visión, IoT, K8s) se mantienen listados porque **están disponibles** y pueden activarse si el alcance cambia.

---

## 🏗️ ARQUITECTURA DE CONTENEDORES

### **Componentes Principales (4 módulos + infra)**

| Módulo | Puerto (Host) | Puerto (Interno) | Expuesto | Responsabilidad |
|--------|---------------|------------------|----------|-----------------|
| **Admin Panel** | 8002 | 8000 | ✅ Sí | Interface privada para Carlos - gestión manual o con Bedrock |
| **Portal Público** | 8003 | 8000 | ✅ Sí | Portafolio público (About, Proyectos, Blog) - lectura |
| **API REST** | — | 8001 | ❌ No | Orquestación central, CRUD, auth, Bedrock y PDF (WeasyPrint) |
| **MCP Server** | 8004 | 8000 | ✅ Sí | FastMCP — carpeta `cjhirashi-career-mcp`, contenedor `mcp_server` |

**Infra (Compose, no son módulos):** PostgreSQL (5432), MinIO (9000), Qdrant (6333).

**Red:** `network-cjhirashi-srv` (Docker bridge, externa)

**Volúmenes:**
- `postgres_data` (persistencia BD)

### **Rutas de Comunicación**

**DOS FORMAS DE OPERAR EL SISTEMA:**

**OPCIÓN 1: Usuario (Carlos Jiménez Hirashi) - Admin Panel**
```
Admin Panel (8002)
  ├─ Gestión MANUAL
  │  └→ API REST (8001) — CRUD + generación PDF (WeasyPrint in-process)
  │
  └─ Gestión CON ASISTENCIA Bedrock
     └→ API REST (8001) — chat Bedrock, CRUD y PDF
```

**OPCIÓN 2: Agente IA Externo - MCP Server**
```
MCP Server (8004) ← Agente externo (Claude, etc.)
  └→ API REST (8001) — Operación completa del sistema (lectura/escritura)
     ├→ CRUD de datos
     ├→ Gestión de carrera
     └→ Generación de documentos (si lo requiere)
```

**Portal Público (Lectura)**
```
Portal Público (8003)
  └→ API REST (8001) — SOLO lectura de proyectos, blog, about, contacto
```

**API REST (Orquestación central)**
```
API REST (8001)
  └→ PostgreSQL (5432) — Lectura/escritura (único escritor)
```

**Reglas clave:**
- ✅ Admin Panel: interface privada para Carlos (manual o con Bedrock)
- ✅ MCP Server: interface para agentes IA externos (sin Admin Panel)
- ✅ Agent Bedrock: asistente SOLO dentro de Admin Panel (no expuesto)
- ✅ Portal Público: lectura de datos públicos (no acceso a Admin)
- ✅ PDF: WeasyPrint in-process en la API (Admin y Bedrock lo invocan vía API; no hay contenedor `pdf_generator`)
- ✅ PostgreSQL: único punto de persistencia (API es único escritor)
- ✅ Bedrock y MCP no se comunican entre sí (rutas independientes)

---

## 🌐 ACCESO EXTERNO Y PROXY

### **Arquitectura de Proxy**

El proyecto está integrado con **cjhirashi-srv** (Caddy + Cloudflare Tunnel) para acceso externo:

```
Internet (cloudflare.com/subdominio)
    ↓ (TLS/HTTPS)
Caddy (reverse proxy - puerto 80/443)
    ↓ (HTTP interno)
network-cjhirashi-srv (Docker bridge)
    ├→ portal_publico (puerto 8000 - Portafolio)
    └→ admin_panel (puerto 8000 - Admin)
```

### **Contenedores Expuestos**

3 contenedores de aplicación tienen acceso externo (vía Caddy + Cloudflare); MinIO (`files.cjhirashi.com`) se documenta en `servicios-externos/`:

| Contenedor | Puerto | Protocolo | Propósito |
|-----------|--------|-----------|-----------|
| `cjhirashi-career-admin` | 8002 | HTTP + Auth JWT | Panel privado |
| `cjhirashi-career-portfolio` | 8003 | HTTP | Portafolio público |
| `cjhirashi-career-mcp` | 8004 | HTTP (SSE) | MCP FastMCP |

**Contenedores INTERNOS SOLO** (no expuestos):
- `cjhirashi-career-api` (8001) - API REST (incluye Bedrock y PDF WeasyPrint)
- `postgres_db` (5432) - Base de datos

### **Responsabilidad: cjhirashi-srv**

El proyecto **cjhirashi-srv** gestiona:
- ✅ Dominio y certificados TLS (Cloudflare)
- ✅ Routing de subdomios (portafolio.cjhirashi.com, admin.cjhirashi.com, etc.)
- ✅ Rate limiting y protección
- ✅ Cache y optimización

**Nuestro proyecto proporciona:**
- ✅ Documentación en `servicios-externos/cjhirashi-career.md`
- ✅ Confirmación de que contenedores están en `network-cjhirashi-srv`
- ✅ Notas bidireccionales si hay cambios

---

## 🔄 FLUJO DE TRABAJO ARQUITECTÓNICO

### **Fase 1: Diseño (Yo - Arquitecto)**
```
1. Analizar requisitos
2. Diseñar arquitectura completa
3. Documentar en CLAUDE.md
4. Crear ADRs (decisiones)
5. Validar con equipo
```

### **Fase 2: Infraestructura (Experto Docker)**
```
1. Crear docker-compose.yml
2. Definir Dockerfiles
3. Configurar redes, volúmenes
4. Configurar CI/CD
```

### **Fase 3: Documentación (Documentador + Yo)**
```
1. Yo defino: "Documenta Arc42 sección X"
2. Documentador redacta profesionalmente
3. Yo reviso, apruebo o ajusto
```

### **Fase 4: Desarrollo (Especialistas de Módulo)**
```
1. Especialista desarrolla su módulo
2. Code Quality Guardian: code review
3. QA Engineer: valida tests (80%)
4. Git: commit con calidad garantizada
```

### **Fase 5: Validación (Equipo)**
```
1. CI/CD gates pasan ✓
2. Seguridad validada ✓
3. Calidad de código ✓
4. Tests con cobertura ✓
5. Merge a main ✓
```

---

## 📊 CHECKLIST DE CALIDAD POR MÓDULO

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

## 📁 ESTRUCTURA DE PROYECTO

### Raíz - SOLO Configuración y Overview

```
cjhirashi-career/
├── CLAUDE.md (Este archivo - Guía de arquitectura y procesos, versionada en el repo)
├── README.md (Overview público)
├── docker-compose.yml (Orquestación Docker)
├── .env.example (Template de configuración)
├── .gitignore (Reglas de git)
│
├── docs/ (Arc42 - Documentador + Yo)
│   ├── 01-INTRODUCTION.md (contexto, objetivos)
│   ├── 02-ARCHITECTURE-GOALS.md (metas)
│   ├── 03-STAKEHOLDERS.md (usuarios, roles)
│   ├── 04-SOLUTION-STRATEGY.md (decisiones)
│   ├── 05-BUILDING-BLOCK-VIEW.md (componentes)
│   ├── 06-RUNTIME-VIEW.md (flujos)
│   ├── 07-DEPLOYMENT-VIEW.md (docker-compose)
│   ├── 08-CROSSCUTTING-CONCEPTS.md (patrones)
│   ├── 09-DECISIONS/ (ADRs)
│   ├── 10-QUALITY-SCENARIOS.md (calidad)
│   ├── 11-TECHNICAL-RISKS.md (riesgos)
│   └── 12-GLOSSARY.md (términos)
│
├── cjhirashi-career-portfolio/ (Portal Público)
│   ├── README.md
│   ├── docs/
│   ├── Dockerfile
│   └── src/
│
├── cjhirashi-career-admin/ (Panel de Administración)
│   ├── README.md
│   ├── docs/
│   ├── Dockerfile
│   └── src/
│
├── cjhirashi-career-api/
│   ├── README.md
│   ├── docs/
│   ├── Dockerfile
│   └── src/services/pdf/  (WeasyPrint in-process)
│
├── cjhirashi-career-mcp/ (MCP FastMCP)
│
└── (postgres / minio / qdrant los maneja compose)
```

---

## 🎓 PROCESOS APRENDIDOS

Este CLAUDE.md se actualiza con cada proceso nuevo aprendido:

- **2026-08-16:** Cambio de alcance: de generador de documentos a portafolio + gestor de carrera con agentes IA (Bedrock + MCP como opciones). Metodología Arc42 + 5 agentes globales + SOLID + 80% cobertura tests.
- **2026-08-25:** PDF in-process en la API (`cjhirashi-career-api/src/services/pdf/`). Carpetas de módulo: `cjhirashi-career-admin`, `cjhirashi-career-portfolio`, `cjhirashi-career-api`, `cjhirashi-career-mcp`. Los `container_name` de Compose (los que usa Caddy) no cambian.
- **2026-08-26:** Tareas de primer nivel (`/tasks`: lista, kanban, calendario, Gantt). Asignación usuario o agente. El scheduler in-process (`task_scheduler`) ejecuta agentes a `scheduled_at` sin sesión SPA (ADR-015). Subtareas (`parent_id`, `is_blocking`, `execute_on_turn`) orquestan el plan; avisos al usuario en `user_notifications` (ADR-016). Foto de agente en el catálogo (URL del bucket) y selector de responsable con nombre + foto.
- **2026-08-27:** El bloque destacado del Home del portal dejó de ser el "caso ancla" (`projects.is_anchor`) y ahora muestra un **logro** (`achievements.home`, booleano, "solo uno a la vez" como su predecesor). Se eliminó `is_anchor` de `projects` (columna, schema, admin, portfolio) y se añadió `home` a `achievements` en los mismos puntos; `/public/home` expone `home_achievement` en vez de `anchor_project`.
- **2026-08-27:** Registro centralizado de fallas del sistema — **ver [ADR-018](docs/09-DECISIONS/018-error-reports-registry.md)**. Tabla `error_reports` (IDs `err-N`) con atributo `resolved` (arranca `false` = pendiente de revisión). Escritura: `api/src/services/error_reporting.py::report_error()` (engine psycopg2 propio, nunca lanza, dedup por `fingerprint` con contador `occurrences`); `areport_error` para async; `capture_errors` context manager. Captura automática: handlers globales de `app.py` (incluye nuevo handler de `HTTPException`; 401/404 se omiten), `except` de fallos inesperados en servicios/schedulers/bedrock, `POST /system/error-report` (público, rate-limited) para los 2 SPA y el MCP. Lectura/gestión: `error_report_service.py` + `routes/error_reports.py` (`/settings/error-reports*`, JWT). Tool Bedrock `error_report_settings` en el L2 `agent_settings` (4ª pantalla de Settings, `/settings/error-reports`). Pantalla Admin: Settings → *Reportes de Falla*. Agente del proyecto **`revisor-fallas`** (`.claude/agents/006-revisor-fallas.md`) + scripts `api/scripts/list_error_reports.sh` y `resolve_error_report.sh`: al pedir "revisa los reportes de falla", consulta la tabla, diagnostica, corrige/delega y marca `resolved=true`.
- **2026-08-27:** Catálogo de agentes de Claude Code reconocido en CLAUDE.md (sección *EQUIPO DE AGENTES*). Tres grupos: **A** equipo núcleo de calidad (5 roles metodológicos → `docker-expert`, `documentacion-especialista`, `qa-engineer`, `code-quality-guardian`, `git-specialist`); **B** especialistas de módulo locales (`.claude/agents/`: `api-rest-specialist`, `api-rest-developer`, `admin-panel-specialist`, `portal-publico-specialist`, `revisor-fallas`); **C** agentes globales de usuario (`~/.claude/agents/`, 21: `arquitectura-red`, `docker`, `cicd`, `documentacion-especialista`, `git-especialista`, `seguridad`, `observabilidad`, `backup-recuperacion`, `vps-hosting`, `aws`, `kubernetes`, `desarrollo-mcps`, `harness-agentes`, `aws-bedrock`, `ingenieria-llm`, `rag`, `skills-agentes`, `machine-learning`, `deep-learning`, `vision-computadora`, `iot-industrial`). Regla: toda tarea especializada se delega vía la herramienta `Agent`; los agentes fuera del alcance actual (ML/DL/visión/IoT/K8s) se listan igual porque están disponibles.
- **2026-08-27:** Dos agentes globales nuevos en `~/.claude/agents/`: **`harness-agentes`** (especialista en el harness de sistemas de agentes — bucle agéntico, diseño de tools, gestión de contexto, subagentes, hooks, memoria; foco en eficiencia de tokens/latencia/coste; investiga siempre docs oficiales de Claude Code / Agent SDK / MCP y buenas prácticas del mercado) y **`aws-bedrock`** (especialista en AWS Bedrock end-to-end — catálogo y capacidades de modelos, Converse API, Bedrock Agents, AgentCore, Knowledge Bases, Guardrails, Flows, conexiones efectivas boto3/IAM/VPC endpoints, throttling; consulta siempre docs oficiales de AWS). Reparto de dominio: `harness-agentes` = maquinaria genérica del runtime; `aws-bedrock` = todo lo específico de Bedrock/AgentCore; `ingenieria-llm` = prompts y evaluación de calidad del agente de negocio; `aws` = infra AWS no-Bedrock. **Integrados en los especialistas de la API** (`api-rest-specialist` y `api-rest-developer`, sección *Sistema de Agentes Bedrock*): siempre que se trabaje sobre `cjhirashi-career-api/src/services/bedrock/` deben consultar/delegar en `harness-agentes` (el *cómo* genérico) y `aws-bedrock` (el *cómo* específico de Bedrock) antes de implementar, sin improvisar APIs/límites/IDs sin verificar contra doc oficial.
- **2026-08-27:** Reducción de consumo de tokens del agente Bedrock — **ver [ADR-019](docs/09-DECISIONS/019-bedrock-prompt-caching.md)** (validado por los agentes globales `aws-bedrock` y `harness-agentes`). (1) **Prompt caching de Bedrock**: `converse_client._build_converse_kwargs()` inserta hasta 3 `cachePoint` (system, tools, último mensaje) solo si el modelo tiene `supports_prompt_cache=True` (Haiku 4.5 y Sonnet 4.5) y `settings.BEDROCK_PROMPT_CACHE_ENABLED` (kill-switch). **Umbral Bedrock: 4 096 tokens de prefijo acumulado para Haiku 4.5, 1 024 para Sonnet 4.5** — por debajo, el `cachePoint` se ignora sin error. Con Haiku solo cachea el turno completo cuando supera 4 096 (registros grandes / varias rondas). `_estimate_cost` factura `cache_read_tokens` a 0.10× y `cache_write_tokens` a 1.25× (asume TTL 5 min); columnas nuevas en `bedrock_usage_logs`/`bedrock_usage_round_logs` (migración `b1c2d3e4f5a6`); `/usage-metrics` + `BedrockCostPanel.tsx` muestran el desglose y el "ahorro por caché". **`agent_professional_identity` (L2 dueño de `projects`) corre en Mistral Large → no cachea**; pendiente evaluar moverlo a Haiku (ADR-012). (2) **Proyección**: `get_career_record` acepta `fields: string[]`. (3) **Truncado por cuota**: `tool_results._cap_record_fields()` reparte el presupuesto de caracteres entre los campos largos (string y JSONB) de un `{"item": {...}}`; un campo aislado recibe casi todo el tope con marcador terminal; solo cae al corte ciego si aún no cabe. (4) **Dedupe**: `agent_loop` no reejecuta lecturas idénticas dentro del turno, y **limpia `seen_reads` tras cualquier write** (evita servir datos previos a la escritura). **Redis se descartó**: no reduce tokens. Deploy: la migración NO corre en `init_db` (usa `create_all`); `alembic upgrade head` tras rebuild.
- **2026-08-27:** Plantilla compartida para las secciones de tabla del Admin — **ver [ADR-020](docs/09-DECISIONS/020-admin-section-templates.md)**. El chrome de toda vista de lista (card `has-view-tabs`, pestañas folder, `table-toolbar`, `<table>`, `table-footer`) vivía duplicado en 6 archivos. Ahora vive **solo** en `admin/src/components/section/`: primitivos `SectionShell`, `SectionToolbar`, `SectionTable`, `SectionTableFooter`, `SectionRecordView`; hook `useSectionTable` (columnas persistidas + orden + búsqueda con debounce); `compareCells` consolidado en `utils/tableColumns.ts`. Encima, `TableSectionTemplate` (lista declarativa) y `DetailSectionTemplate` (vista `:id`). **Regla: toda sección de tabla nueva se construye con `components/section/`**; las que no encajan en la plantilla componen los primitivos (nunca reescriben el markup). Ejemplo de referencia: `pages/ErrorReportsPage.tsx`. **Las 6 vistas de tabla del Admin están migradas** (Reportes de Falla y Secciones del Admin a la plantilla; Catálogo de Agentes, Archivos, Tareas y `CareerResourceView`/30 recursos de carrera a los primitivos). `CareerResourceView` conserva intactas sus ramas `view`/`edit`/`create`/singleton/PDF/nested — falta QA manual sobre recursos representativos. Ver `admin/src/components/section/README.md`. **Principio general: Admin Panel y Portafolio se construyen SIEMPRE a partir de componentes compartidos, no de markup ad-hoc por pantalla** — un cambio de estructura se hace en un solo punto.
- **2026-08-27:** Los agentes Bedrock del producto (no los subagentes de Claude Code) tienen jerarquía de 3 niveles — **ver siempre [ADR-012](docs/09-DECISIONS/012-bedrock-three-level-agents.md) antes de preguntar por esto**: L1 (`agent_orchestrator`, único, chat general, solo delega) → L2 (especialista de área, chat contextual propio, delega solo a L3) → L3 (especialista de tarea, sin chat, no delega). Catálogo completo en `api/src/services/bedrock/agent_profiles.py` (espejo UI en `admin/src/config/agentProfiles.ts`). Se agregó el L2 `agent_settings` (ADR-017) dueño de las pantallas del grupo Settings del Admin (Catálogo de Agentes, Secciones del Admin, Prompts Globales y —desde ADR-018— Reportes de Falla), antes sin L2 asignado.
- **2026-08-28:** División del L2 `agent_settings` en dos — **ver [ADR-022](docs/09-DECISIONS/022-l2-split-configuration-vs-incidents.md)**. Antes un solo L2 "Configuración" (`agent_settings`, `agent-19`) cargaba 4 áreas: catálogo de agentes, secciones del Admin, prompts globales y reportes de falla. Ahora: **`agent_configuration`** (nuevo, `agent-20`, label "Configuración", L2, Haiku 4.5) es dueño de la metaconfiguración del harness — tools `agent_catalog_settings`, `admin_section_settings`, `bedrock_global_settings` (+ `search_knowledge_base`); rutas `/settings/agents`, `/settings/sections`, `/settings/agent-prompts`. **`agent_settings`** conserva su system-name (es FK en `bedrock_conversation`, `bedrock_agent_profile_prompts`, `operational_methodology.agent_profile_ids`, `admin_section_overrides` → no se renombra) pero cambia a label **"Incidencias y Bitácora"**, tool única `error_report_settings` (+ `search_knowledge_base`), rutas `/settings/error-reports` y `/agent/audit-log`. Ambos L2 delegan la lectura de bitácora al L3 `agent_changelog`. La sección **Bitácora** (`sec-15`) pasa de `AGENT_CHANGELOG` (L3, sin chat) a `AGENT_SETTINGS` (L2) → gana chat contextual. Numeración de records `agent-N` **congelada y a mano** (igual que `sec-N`, ADR-021): `agent-20` es el siguiente libre; perfil eliminado → número retirado. Sin migración Alembic (el catálogo de agentes es código `_PROFILES`, no tabla). Archivos: `agent_profiles.py` (constante + `_AGENT_RECORD_IDS` + tool-sets + suffixes + `_ROUTE_TO_PROFILE` + `_ORCHESTRATOR_SUFFIX`), `admin_sections.py` (`sec-15`..`sec-19`), `tools.py` (docstrings), espejo `admin/src/config/agentProfiles.ts` + tests en ambos lados.
- **2026-08-27:** PK sintético `sec-N` para las secciones del Admin (Frente B) — **ver [ADR-021](docs/09-DECISIONS/021-admin-sections-synthetic-pk.md)**. "Secciones del Admin" es un registro en código (`api/src/services/admin_sections.py`), no una tabla. `AdminSectionSpec.id` pasa a ser `sec-<n>` (prefijo `sec-`, análogo a `err-N`) y el slug legible de antes (`dashboard`, `career-projects`, `settings-error-reports`…) se conserva con los mismos valores en el nuevo campo `system_name` ("Nombre de sistema" en la UI del Admin; `career-*` = `career-` + `resource_key`). **Numeración CONGELADA**: los `sec-N` se asignan a mano en código, en orden de declaración (`_SECTIONS` sec-1..sec-19, `_CAREER_ROWS` sec-20..sec-54); sin secuencia de BD; sección nueva → siguiente entero libre (sec-55…); sección eliminada → número retirado (hueco, nunca se reutiliza). `sec-N` es la **clave canónica en todo**: PK de `admin_section_overrides.section_id` (columna ahora `String(40)`), propiedad de secciones por agente (`set_agent_sections`/`known_section_ids`), tool Bedrock `admin_section_settings` (`section_id=`) y la URL `/settings/sections/:id`; `system_name` queda solo como nombre legible (se expone en `list`/`get` de la tool y en `profile_catalog`). Migración `alembic/versions/b2c3d4e5f6a7_admin_section_overrides_synthetic_pk.py` (revision `b2c3d4e5f6a7`, down_revision `b1c2d3e4f5a6`): mapa estático slug→`sec-N` incrustado (no importa el módulo de la app), `upgrade` re-mapea las filas + estrecha la columna, `downgrade` invierte, filas fuera del mapa se dejan intactas con `logging.warning`. **Deploy**: la migración NO corre en `init_db` (usa `create_all`); requiere `alembic upgrade head` **inmediatamente después del rebuild** (igual que ADR-019). Ventana de regresión (R2 del code review): mientras la migración no corra, las filas de `admin_section_overrides` siguen keyeadas con el slug viejo, `section_catalog` no hace match con los `sec-N` y **cada sección revierte temporalmente a sus valores por defecto de código** (agente dueño, descripción y textos de instrucciones por vista); no hay pérdida de datos y el match se restablece al aplicar la migración. Frontend: `AdminSection` gana `system_name`; `AdminSectionsPage` añade la columna "Nombre de sistema" tras "ID" y el campo en el detalle; `AgentCatalogPage` muestra `label · system_name (tipo)` en el multiselect. El `SectionPageTemplate` (Frente A: unificación del sidebar derecho) es trabajo aparte y solo consumirá `sec-N`/`system_name`.
- **2026-08-28:** Jerarquía de secciones del Admin + configuración por vista, en tablas reales — **ver [ADR-023](docs/09-DECISIONS/023-admin-sections-hierarchy-views.md)** (supersede parcialmente ADR-021). Backend implementado por `api-rest-developer` y **verificado** (nombres reales confirmados contra el contrato de implementación, ver `docs/09-DECISIONS/023-contrato-implementacion.md` y `023-ESTADO.md`). "Secciones del Admin" deja de ser un registro en código y pasa a **6 tablas**: `admin_section_groups` (`grp-N`), `admin_sections_l1` (`s1-N`), `admin_sections_l2` (`s2-N`), `admin_sections_l3` (`s3-N`), `admin_views` (`vw-N`). Árbol **grupo → L1 → L2 → L3**; el grupo nunca tiene vistas; cada sección L1/L2/L3 tiene **0–10 vistas** y puede tener a la vez subsecciones; 0 vistas = nodo de navegación sin layout. El anidamiento + `sort_order` = orden del sidebar izquierdo. **Estructura sembrada por código** vía seeder idempotente compartido `services/admin_sections_seed.py::sync_structure()` llamado desde `init_db()` (tras `create_all`) y desde la migración; solo **`responsible_agent_profile_id` + `instructions` son editables** en el Admin (ambos nullable = deshabilitan chat contextual / panel de instrucciones de esa vista) y el seeder nunca los toca (upsert acotado por columna, sin tabla de overrides). **La propiedad de agente es por VISTA, no por sección**, y solo perfiles **L2**: `responsible_agent_profile_id` es referencia blanda `String(50)` al `profile_id` canónico del catálogo en código (mismo dominio que `bedrock_agent_profile_prompts.profile_id`), **sin FK dura** (no se crea tabla de perfiles), validada en app (`get_profile` existe y `level == 2`). "Vistas que gestiona un agente" = lista derivada de solo lectura; `set_agent_sections` / `sections_for_agent` **se eliminan**. Re-key **`sec-N` → `s1-N`** (mismo entero); `system_name` intacto; `admin_sections_l2/l3` nacen vacías (anidamiento entre niveles = por código + re-seed en este lote; drag L1↔L2↔L3 desde el Admin diferido a follow-up inmediato). Columnas de dominio de la vista (de código, preparan construir vistas desde el Admin): `key`, `label`, `sort_order`, `has_controls_window`, `tool_names` (**`JSON`** variant `JSONB`, no `ARRAY`), `data_source` (`crud`/`computed`/`singleton`/`external`), `resource_key` (CHECK: solo si `crud`/`singleton`), `origin` (`'code'`; el prune del seeder solo borra `origin='code'`). Tool Bedrock **`admin_section_settings` → `admin_view_settings`** (confirmado en `tools.py`; suffix real es `_CONFIGURATION_SUFFIX` en `agent_profiles.py`), `action=list|get|update` sobre `vw-N`; dueño sigue siendo el L2 `agent_configuration` (`agent-20`, ADR-022). `resolve_profile_for_turn`: ruta → sección → vista activa (`page_context.view_key`) → agente L2 de la vista; se elimina el fallback a `resolve_agent_profile` para la superficie contextual (queda `# deprecated`). Migración **`c4d5e6f7a8b9`** (confirmada; `down_revision = b2c3d4e5f6a7`): crea las 6 tablas + `sync_structure` con snapshots congelados + convierte `admin_section_overrides` a columnas de `admin_views` + **`DROP TABLE admin_section_overrides`**. **Deploy**: NO corre en `init_db` (usa `create_all`); requiere **`alembic upgrade head` manual inmediatamente después del rebuild** (igual que ADR-019/ADR-021). Ventana de regresión hasta correr la migración: `init_db` siembra la estructura pero el agente/instrucciones personalizados de `admin_section_overrides` no se aplican hasta la migración (sin pérdida de datos). **Pendiente de este lote** (backend cerrado, aún sin frontend): `admin-panel-specialist` (sidebar en árbol, pantalla de Vistas, `AgentCatalogPage` "vistas que gestiona", hooks `useNavTree`/`useAdminViews`), luego `code-quality-guardian` + `qa-engineer` + `git-especialista`. Pendientes (§Seguimiento de ADR-023): (a) drag de nivel L1↔L2↔L3 desde el Admin; (b) catálogo de componentes UI ligado a tablas para ensamblar vistas 100% desde el Admin; (c) migrar `bedrock_agent_delegation.target_ids` a `JSON` portable; (d) retirar `resolve_agent_profile` y sus mapas.

---

## 📌 PRINCIPIOS FUNDAMENTALES

1. **Calidad primero**: 80% cobertura, SOLID, code review obligatorio
2. **Arquitectura clara**: Arc42, decisiones documentadas (ADRs)
3. **Modular**: 4 módulos (`cjhirashi-career-admin`, `cjhirashi-career-portfolio`, `cjhirashi-career-api`, `cjhirashi-career-mcp`) + infra en Compose
4. **Automatización**: CI/CD gates obligatorios
5. **Documentación**: Siempre sincronizada con código
6. **Equipo coordinado**: Cada experto en su área
7. **Dual Agent Support**: Bedrock (interno) + MCP (externo)
8. **Front-end por componentes compartidos**: Admin Panel y Portafolio se construyen SIEMPRE a partir de componentes/primitivos reutilizables, nunca con markup ad-hoc por pantalla. El chrome de una vista vive en un único punto (ej. `admin/src/components/section/`, [ADR-020](docs/09-DECISIONS/020-admin-section-templates.md)). Una vista nueva reutiliza; si repite estructura no cubierta, primero se extrae el componente.

## 🗂️ POLÍTICA DE DOCUMENTACIÓN

### ❌ NO en Raíz (proyectos obsoletos, basura)
- Guías de setup
- Paletas de colores
- Documentación de status
- Archivos .md que no sean README o CLAUDE

### ✅ SÍ en Raíz
- `README.md` - Overview público del proyecto
- `CLAUDE.md` - Guía de arquitectura y bitácora de procesos (versionada; los overrides personales van en `.claude/settings.local.json`, que sí se ignora)
- `.env.example` - Template de configuración
- `docker-compose.yml` - Orquestación
- `.gitignore` - Reglas de git

### ✅ SIEMPRE en `docs/`
- Documentación Arc42 (01-12)
- Guías de setup (docs/SETUP.md)
- Referencias técnicas
- Decisiones arquitectónicas (ADRs)
- Cualquier archivo .md que no sea README

**Regla simple:** Si es documentación técnica → `docs/`. Si es config → raíz. Si es obsoleto → eliminar.

---

**Última Actualización:** 2026-08-28  
**Versión:** 3.4 (Jerarquía de secciones del Admin en tablas reales + configuración por vista — ADR-023)  
**Mantenedor:** Arquitecto de Soluciones (yo)
