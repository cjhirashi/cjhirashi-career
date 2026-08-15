# Configuración Personalizada de Agentes — MCP Tools Server

Este archivo documenta las instrucciones personalizadas para agentes especializados cuando trabajan en este proyecto.

---

## 📚 Agente: documentacion-tecnica

### Instrucciones Personalizadas

Cuando trabajes en documentación para el proyecto **MCP Tools Server**, aplica los siguientes estándares:

#### 1. Banners SVG

**Para README.md del proyecto raíz:**
- Archivo: `assets/banner.svg`
- Si NO existe, **CREAR** con:
  - Fondo: **Gradiente lineal cyan-600** (de arriba a abajo)
  - Colores: `#06B6D4` (cyan-600) → `#0891B2` (cyan-700)
  - Tamaño: 1200x400px (proporción 3:1)
  - Incluir: Logo/icono MCP, título "MCP Tools Server", descripción breve
  - Estilo: Moderno, limpio, profesional
  - Formato: SVG puro (no imágenes externas)

**Para documentación de aplicación (docs/):**
- Archivo: `docs/assets/banner-docs.svg`
- Si NO existe, **CREAR** con:
  - Fondo: **Gradiente lineal cyan-600** (de arriba a abajo)
  - Colores: `#06B6D4` (cyan-600) → `#0891B2` (cyan-700)
  - Tamaño: 1200x400px
  - Incluir: Logo/icono de documentación, título "MCP Tools Server — Documentación"
  - Estilo: Coherente con banner.svg pero con variante para docs
  - Formato: SVG puro

#### 2. Integración en README

**README.md (proyecto raíz):**
```markdown
![MCP Tools Server](assets/banner.svg)

# MCP Tools Server
```

**docs/README.md (documentación):**
```markdown
![MCP Tools Server — Documentación](assets/banner-docs.svg)

# Documentación — MCP Tools Server
```

#### 3. Estructura de Documentación Modular

El proyecto usa estructura multi-README:

```
mcp-server/
├── README.md                          # Inicio rápido + overview
├── CLAUDE.md                          # Guía para desarrolladores
├── mcp_tools_server.md               # Guía operacional
├── Guia PDF WeasyPrint y CSS paged media.md  # Técnica
│
└── docs/                             # Documentación de usuario/aplicación
    ├── README.md                     # Índice de documentación
    ├── assets/
    │   └── banner-docs.svg          # Banner para docs (crear si no existe)
    ├── getting-started/
    │   └── README.md                # Guía de inicio
    ├── api/
    │   └── README.md                # Referencia API
    ├── templates/
    │   └── README.md                # Guía de templates
    └── troubleshooting/
        └── README.md                # Solución de problemas
```

#### 4. Estándar por Sección

Cada subsección (`docs/getting-started/`, `docs/api/`, etc.) debe tener su propio `README.md` que:

- Comience con **un párrafo descriptivo** (qué cubre esta sección)
- Incluya **tabla de contenidos** si es > 3 secciones
- Tenga **ejemplos prácticos** con código JSON
- Termine con **Enlaces relacionados** a otras secciones
- Use **emoji** para mejor legibilidad (🚀 para inicio, 🔧 para config, etc.)

**Estructura estándar de sección:**
```markdown
# [Título Sección]

_Descripción de qué cubre esta sección: 1-2 frases._

## 📋 Contenido

- [Tema 1](#tema-1)
- [Tema 2](#tema-2)

## 🚀 Tema 1

[Contenido...]

## 🔧 Tema 2

[Contenido...]

---

## 📚 Relacionado

- [Otra Sección](../otra-seccion/)
- [CLAUDE.md](../../CLAUDE.md) — Para desarrolladores
```

#### 5. Checklist para Documentación

Cuando trabajes en documentación, asegúrate de:

- [ ] Banner SVG existe y usa gradiente cyan-600 (crear si falta)
- [ ] README raíz tiene el banner integrado
- [ ] Cada subsección en `docs/` tiene su README.md
- [ ] Banner-docs.svg existe en `docs/assets/` (crear si falta)
- [ ] No hay duplicación entre READMEs (cada uno tiene su propósito)
- [ ] Ejemplos JSON están formateados y funcionan
- [ ] Enlaces internos usan rutas relativas
- [ ] Checklist de Troubleshooting está actualizado
- [ ] Referencias a CLAUDE.md y mcp_tools_server.md son correctas

---

## 🐳 Agente: docker

### Instrucciones Personalizadas

- Dockerfile debe usar **Python 3.11** (Debian Bookworm)
- Volumen persistente: `/mnt/disco2/cjhirashi-data/mcp-outputs/`
- Red: `network-cjhirashi-srv` (existente, no crear)
- Puerto interno: 8000 (FastMCP SSE)
- Puerto expuesto: 8002 (host)

---

## 🔗 Agente: arquitectura-red

### Instrucciones Personalizadas

- Red existente: `network-cjhirashi-srv` (external: true)
- Volumen persistente en disco secundario (/mnt/disco2/)
- DNS por nombre de contenedor (`mcp_tools_server`)
- Validar que no hay conflicto de puertos (8002 es dedicado a este proyecto)

---

## 🛠️ Agente: desarrollo-mcps

### Instrucciones Personalizadas

- Transporte: **SSE** (no websockets)
- Herramientas principales: `crear_cv_pdf`, `crear_cover_letter_pdf`
- Parámetros de entrada: siempre strings JSON (no objetos directos)
- Respuesta: string con ruta de archivo o error
- Validación: parsear JSON antes de pasar a generadores

---

## 📋 Notas

- Este archivo es la **fuente de verdad** para instrucciones personalizadas
- Actualizar cuando cambien estándares del proyecto
- Los agentes deben leerlo antes de empezar trabajo en documentación
- Coherencia: CLAUDE.md (devs), mcp_tools_server.md (ops), docs/ (usuarios)

**Última actualización:** 2026-08-15
