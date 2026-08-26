# cjhirashi-career — Agentes Locales

Esta carpeta contiene la **definición de estructura de agentes** del proyecto cjhirashi-career.

## 📋 Estructura de Archivos

### Agentes Globales (001-005)

Expertos que coordinan trabajo específico en **todas las fases**:

| ID | Nombre | Tipo | Responsabilidad |
|----|--------|------|-----------------|
| 001 | Docker Expert | Local | Infraestructura: docker-compose, Dockerfiles, redes, volúmenes |
| — | **Documentador** | **Global Claude** | **Documentación: Arc42, ADRs, READMEs profesionales** |
| 003 | QA Engineer | Local | Testing: estrategia, cobertura (80%), validación de calidad |
| 004 | Code Quality Guardian | Local | Code review: SOLID, Clean Code, seguridad, SonarQube |
| 005 | Git Specialist | Local | Control de versiones: commits, ramas, merges, releases |

**Nota:** El Documentador es el agente global de Claude (`documentacion-especialista`), no local.

### Especialistas de Módulo — Fase 1 (101-105)

Desarrolladores responsables de **módulos específicos**:

| ID | Nombre | Módulo | Responsabilidad |
|----|--------|--------|-----------------|
| 101 | API REST Specialist | API REST | Diseño: schema, endpoints, seguridad, testing strategy (incluye PDF WeasyPrint) |
| 102 | API REST Developer | API REST | Implementación: FastAPI, SQLAlchemy, PostgreSQL, PDF in-process |
| 103 | Admin Panel Specialist | Admin Panel | Implementación: React SPA, CRUD, autenticación, métricas |
| 104 | Portal Público Specialist | Portal Público | Implementación: React SPA read-only, Home (entry point), About, Projects, Blog, Contact |

## 🎯 Cómo Usar

### Invocación de Agentes Globales

```
Arquitecto → [Invoca agente global] → Experto → Entrega
```

**Ejemplo:**
```
"Docker Expert, diseña docker-compose.yml para 3 módulos + infra:
 - Admin Panel (8002)
 - Portal Público (8003)
 - API REST (8001 internal; Bedrock + PDF WeasyPrint)
 - PostgreSQL, MinIO, Qdrant
 MCP no va en Compose hasta que exista mcp/.
 
 Usa network-cjhirashi-srv y volúmenes en /mnt/disco1/..."
```

### Invocación de Especialistas de Módulo

**Flujo típico:**
```
1. Especialista DISEÑO define especificación
2. Especialista DEVELOPER implementa
3. QA Engineer valida tests (80%)
4. Code Quality Guardian aprueba código
5. Git Specialist coordina merge
6. Merge a develop ✓
```

**Ejemplo Fase 1:**
```
# Semana 1: API REST Specialist (Diseño)
Arquitecto → API REST Specialist → Especificación técnica ✓

# Semanas 2-3: API REST Developer (Implementación)
API REST Specialist → API REST Developer → API funcional ✓

# Semanas 3-4: Admin Panel Specialist
API REST Developer → Admin Panel Specialist → Admin Panel ✓

# Semanas 4-5: Portal Público Specialist
API REST Developer → Portal Público Specialist → Portal ✓

# Semanas 3-4: Admin Panel Specialist
API REST Developer → Admin Panel Specialist → Admin Panel (PDF vía API) ✓
```

## 📌 Responsabilidades Claras

### Arquitecto (Yo)
- ✅ Decidir QUÉ documentar
- ✅ Decidir arquitectura (decisiones)
- ✅ Supervisar calidad general
- ✅ Coordinar agentes
- ✅ Mantener CLAUDE.md actualizado
- ❌ NO: Redactar documentos
- ❌ NO: Escribir código
- ❌ NO: Hacer code review

### Especialistas de Módulo
- ✅ Implementar su módulo
- ✅ Escribir tests (80%)
- ✅ Documentar su código (docstrings)
- ✅ Participar en code review
- ❌ NO: Decidir arquitectura
- ❌ NO: Redactar documentación técnica (Arc42)
- ❌ NO: Code review de otros módulos

### Agentes Globales
- ✅ Ejecutar su especialidad
- ✅ Consultoría a especialistas de módulo
- ✅ Validación de calidad/seguridad
- ❌ NO: Implementar módulos
- ❌ NO: Tomar decisiones arquitectónicas

## 🔄 Flujo de Coordinación

```
┌─────────────────────────────────────────────────────────┐
│ ARQUITECTO                                              │
│ - Diseño arquitectónico                                 │
│ - Decisiones (ADRs)                                     │
│ - Supervisión general                                   │
└────────────────┬────────────────────────────────────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
┌────▼──────┐   │    ┌──────▼─────┐
│ Docker    │   │    │ Documentador│
│ Expert    │   │    │ (Redacta)   │
└───────────┘   │    └─────────────┘
                │
     ┌──────────┼──────────┐
     │          │          │
┌────▼──┐  ┌───▼────┐  ┌──▼──────┐
│  QA   │  │ Quality │  │   Git   │
│Engine │  │Guardian │  │Specialist
└───────┘  └────────┘  └─────────┘
                │
     ┌──────────┼──────────┐
     │          │          │
 ┌───▼─────┐ ┌─▼────┐ ┌───▼──────┐
 │ API REST│ │Admin │ │ Portal   │
 │Developer│ │Panel │ │Público   │
 └─────────┘ └──────┘ └──────────┘
```

## 📊 Timeline de Fases

### Fase 1 (MVP - 8 semanas)
- **Semana 1:** API REST Specialist diseña
- **Semanas 2-3:** API REST Developer implementa
- **Semanas 3-4:** Admin Panel Specialist
- **Semanas 4-5:** Portal Público Specialist
- **Semanas 5-8:** Integración, testing, bugfixes

### Fase 2 (MCP - 3 semanas)
- MCP Server Specialist diseña e implementa
- Integración con API REST (ya funcional)

### Fase 3 (Bedrock - 3 semanas)
- Bedrock Agent Specialist diseña e implementa
- Integración con Admin Panel

## 🎓 Aprendizajes Registrados

Cada vez que se ejecuta un agente o se descubre un patrón nuevo, se registra en CLAUDE.md (Arquitecto) o memory/ (memoria persistente).

## 📝 Cómo Crear Nuevo Agente

1. Crear archivo en `.claude/agents/`
2. Formato: `[ID]-[nombre-kebab-case].md`
3. Incluir frontmatter YAML:
   ```markdown
   ---
   name: agent-name
   description: One-line description
   type: [global-expert|module-specialist]
   phase: [1|2|3]
   tools: [list of tools]
   ---
   ```
4. Secciones obligatorias:
   - Role
   - Responsibilities
   - Definition of Done
   - Invocation Guide
   - Implementation Checklist

5. Agregar referencia en README.md (este archivo)

## 🔗 Referencias

- **CLAUDE.md** — Guía principal del proyecto (local, no versionado)
- **docs/** — Documentación técnica (Arc42, ADRs)
- **memory/** — Memoria persistente del proyecto
- **docker-compose.yml** — Orquestación Docker
- **.env.example** — Template de configuración

---

**Última Actualización:** 2026-08-16  
**Versión de Agentes:** 1.0  
**Responsable:** Arquitecto de Soluciones (Yo)