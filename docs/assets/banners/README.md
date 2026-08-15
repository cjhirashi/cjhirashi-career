# Banners Dinámicos de Documentación

_Sistema modular de banners personalizados por documento con paleta armónica de colores. Cada sección de documentación tiene su propio banner con título, descripción, tipo y color distintivo._

---

## Descripción General

Este directorio contiene banners SVG dinámicos para cada sección de la documentación de **MCP Tools Server**. Cada banner es personalizable manteniendo una estructura visual consistente con una paleta armónica de colores.

### Características

- **Paleta Armónica**: Tres familias de colores (Cyan, Verde, Morado) coordinadas entre sí
- **Colores Distintivos**: Cada sección tiene su color primario para identificación rápida
- **Elementos Visuales Mejorados**: Formas decorativas sutiles, líneas divisoras, badges con opacidad
- **Footer Fijo**: Nombre del proyecto "MCP Tools Server" en todos los banners
- **Contenido Personalizable**: Título, descripción y tipo por documento
- **Formato SVG Puro**: Sin dependencias externas, se renderiza en cualquier cliente
- **Responsive**: ViewBox flexible que se adapta a diferentes tamaños

---

## Estructura de un Banner

Cada banner tiene dimensiones **1200x400px** y está dividido en zonas:

### 1. Zona de Gradiente Colorido (0-360px)

**Fondo**: Gradiente lineal vertical con paleta armónica según sección:
- Inicio (superior): Color primario (600) — más claro
- Fin (inferior): Color secundario (700) — más oscuro

| Sección | Color Primario | Color Secundario | Ejemplo |
|---------|---|---|---|
| **Getting Started** | Cyan-600 #06B6D4 | Cyan-700 #0891B2 | Inicio rápido |
| **API Reference** | Verde-600 #10B981 | Verde-700 #059669 | Herramientas activas |
| **Troubleshooting** | Morado-600 #A855F7 | Morado-700 #9333EA | Resolución creativa |
| **Configuration** | Cyan-600 #06B6D4 | Cyan-800 #0E7490 | Setup profundo |

**Elementos decorativos** (opacidad baja 0.10-0.15):
- Círculos sutiles en esquinas (radio 40-80px)
- Rectángulos verticales en bordes
- Línea divisor inferior en color primario (opacity 0.4)

**Contenido textual** (alineación izquierda):

| Elemento | Tamaño | Peso | Posición X | Posición Y |
|----------|--------|------|-----------|-----------|
| **Título del Documento** | 72px | Bold | 60 | 120 |
| **Descripción Breve** (Línea 1) | 28px | Light (300) | 60 | 195 |
| **Descripción Breve** (Línea 2) | 28px | Light (300) | 60 | 235 |
| **Línea decorativa** | 2px stroke | N/A | 60-320 | 260 |
| **Badge "tipo"** (esquina superior derecha) | 40px | Bold | 1140 | 70 |

### 2. Zona Gris (360-400px)

Footer con:
- **Nombre del Proyecto**: "MCP Tools Server" (FIJO en todos)
- **Tamaño**: 14px
- **Color**: Blanco sobre fondo #4A4A4A
- **Información**: Categorías y ruta del documento
  - Ejemplo: "Instalación • Configuración • Primeros Pasos  |  docs/getting-started/"

---

## Banners Disponibles

### 1. `getting-started.svg` — CYAN (Confianza, Inicio)

| Atributo | Valor |
|----------|-------|
| **Título** | Getting Started |
| **Descripción** | Comienza en minutos con una guía paso a paso para configurar tu entorno |
| **Color Primario** | Cyan-600 (#06B6D4) → Cyan-700 (#0891B2) |
| **Badge** | START |
| **Tipo** | QUICK START |
| **Uso** | `docs/getting-started/README.md` |
| **Propósito** | Guía de inicio rápido para nuevos usuarios |

### 2. `api-reference.svg` — VERDE (Actividad, Herramientas)

| Atributo | Valor |
|----------|-------|
| **Título** | API Reference |
| **Descripción** | Documentación completa de herramientas y endpoints MCP disponibles |
| **Color Primario** | Verde-600 (#10B981) → Verde-700 (#059669) |
| **Badge** | API |
| **Tipo** | TOOLS & ENDPOINTS |
| **Uso** | `docs/api/README.md` o documentación de herramientas |
| **Propósito** | Referencia técnica de componentes activos |

### 3. `troubleshooting.svg` — MORADO (Resolución, Distincción)

| Atributo | Valor |
|----------|-------|
| **Título** | Troubleshooting |
| **Descripción** | Soluciones a problemas comunes y diagnóstico de errores |
| **Color Primario** | Morado-600 (#A855F7) → Morado-700 (#9333EA) |
| **Badge** | DEBUG |
| **Tipo** | PROBLEM SOLVING |
| **Uso** | `docs/troubleshooting/README.md` |
| **Propósito** | Solución de problemas y FAQ |

### 4. `configuration.svg` — CYAN OSCURO (Setup Profundo)

| Atributo | Valor |
|----------|-------|
| **Título** | Configuration |
| **Descripción** | Setup y configuración paso a paso de MCP Tools Server |
| **Color Primario** | Cyan-600 (#06B6D4) → Cyan-800 (#0E7490) |
| **Badge** | SETUP |
| **Tipo** | SETUP & CUSTOMIZATION |
| **Uso** | `docs/configuration/README.md` |
| **Propósito** | Configuración detallada y personalización |

---

## Cómo Integrar Banners en Documentación

Cada README de sección DEBE incluir el banner correspondiente al inicio:

```markdown
![Getting Started](../assets/banners/getting-started.svg)

# Getting Started

Contenido del documento...
```

**Estructura de carpetas ejemplo:**

```
docs/
├── README.md                              # Banner principal
├── assets/
│   ├── banner-docs.svg                   # Banner de índice (si existe)
│   └── banners/
│       ├── getting-started.svg
│       ├── api-reference.svg
│       ├── troubleshooting.svg
│       ├── configuration.svg
│       ├── banner-template.svg
│       └── README.md                     # Este archivo
├── getting-started/
│   └── README.md                         # ![Getting Started](../assets/banners/getting-started.svg)
├── api/
│   └── README.md                         # ![API Reference](../assets/banners/api-reference.svg)
├── troubleshooting/
│   └── README.md                         # ![Troubleshooting](../assets/banners/troubleshooting.svg)
└── configuration/
    └── README.md                         # ![Configuration](../assets/banners/configuration.svg)
```

---

## Crear un Nuevo Banner

### Método 1: Usando el Template

1. **Copiar** `banner-template.svg` a un nuevo archivo:
   ```bash
   cp banner-template.svg mi-documento.svg
   ```

2. **Editar** el archivo SVG con valores específicos:
   ```xml
   <!-- Cambiar la línea 1 (Título) -->
   <text x="600" y="130" ... >
     Mi Título Personalizado
   </text>

   <!-- Cambiar la línea 2 (Descripción) -->
   <text x="600" y="190" ... >
     Descripción breve y clara del documento
   </text>

   <!-- Cambiar la línea 3 (Tipo) -->
   <text x="600" y="290" ... >
     TIPO DE DOCUMENTO
   </text>

   <!-- El footer NO se cambia - "MCP Tools Server" es fijo -->
   ```

3. **Cambiar ID del gradiente** para evitar conflictos (opcional pero recomendado):
   ```xml
   <linearGradient id="gradient-cyan-nombre">
     <!-- IDs únicos previenen conflictos si múltiples banners se cargan en la misma página -->
   </linearGradient>
   ```

### Método 2: Editar Directamente

Si usas un editor SVG visual:

1. Abre cualquier banner existente (ej: `getting-started.svg`)
2. Edita en tu editor (Figma, Inkscape, VS Code + extensión SVG)
3. Guarda con nuevo nombre
4. Verifica que el footer siga siendo "MCP Tools Server"

---

## Pautas de Contenido

### Títulos (Línea 1)

- **Máximo 30-35 caracteres** para legibilidad
- **Debe ser descriptivo**: reflejar la sección del documento
- **Ejemplos válidos**:
  - "Getting Started" (19 chars)
  - "API Reference" (13 chars)
  - "Troubleshooting" (15 chars)
  - "Configuration" (13 chars)
  - "Docker Deployment" (17 chars)

### Descripciones (Línea 2)

- **Máximo 60-70 caracteres** para que quepa en una línea
- **Breve y clara**: explica de qué trata la sección
- **Ejemplos válidos**:
  - "Guía rápida para comenzar con MCP Tools Server" (46 chars)
  - "Documentación completa de herramientas y endpoints MCP" (54 chars)
  - "Soluciones a problemas comunes y diagnóstico de errores" (55 chars)

### Tipo/Categoría (Línea 3)

- **SIEMPRE en MAYÚSCULAS** para destacar
- **Máximo 25-30 caracteres**
- **Palabras clave del contexto**:
  - Secciones de inicio: "QUICK START", "GETTING STARTED"
  - Referencias: "API REFERENCE", "TOOLS & ENDPOINTS", "DOCUMENTATION"
  - Troubleshooting: "PROBLEM SOLVING", "TROUBLESHOOTING"
  - Setup: "SETUP & CUSTOMIZATION", "CONFIGURATION"
  - Deployment: "DEPLOYMENT", "PRODUCTION"

---

## Validación Visual

Antes de usar un nuevo banner, verifica:

- [ ] **Titulo legible**: No truncado, color blanco nítido
- [ ] **Descripción visible**: Ajustada en 1-2 líneas máximo
- [ ] **Tipo prominente**: Stands out, mayúsculas claras
- [ ] **Divisor sutil**: Línea blanca fina visible pero no invasiva
- [ ] **Footer correcto**: "MCP Tools Server" en gris
- [ ] **Gradiente limpio**: Transición suave cyan → teal
- [ ] **No hay desbordamiento**: Todo el contenido dentro del viewBox

### Herramientas para Validar

1. **GitHub**: Sube a rama y visualiza en PR (GitHub renderiza SVG nativamente)
2. **Mermaid Live**: https://mermaid.live (no ideal pero funciona para SVG inline)
3. **Online SVG Viewer**: https://www.svgviewer.dev
4. **Navegador local**: Abre el archivo SVG directamente en Firefox/Chrome
5. **Markdown Preview**: VS Code extension "Markdown Preview Enhanced"

---

## Especificaciones Técnicas

### Dimensiones Globales
- **Ancho**: 1200px
- **Alto**: 400px
- **Proporción**: 3:1 (estándar de banners web)
- **ViewBox**: `0 0 1200 400` (responsive)

### Zona Degradada
- **Alto**: 360px
- **Gradiente**: Linear, vertical de arriba a abajo (y1="0%" → y2="100%")
- **Colores** (por sección):
  
  | Sección | Inicio (600) | Fin (700/800) |
  |---------|-------------|-------------|
  | Getting Started | `#06B6D4` (Cyan) | `#0891B2` (Cyan) |
  | API Reference | `#10B981` (Verde) | `#059669` (Verde) |
  | Troubleshooting | `#A855F7` (Morado) | `#9333EA` (Morado) |
  | Configuration | `#06B6D4` (Cyan) | `#0E7490` (Cyan oscuro) |

- **Elementos decorativos**:
  - Círculos blancos (opacity 0.10-0.12)
  - Rectángulos blancos (opacity 0.12-0.15)
  - Línea divisor en color primario (opacity 0.4)

### Zona Footer
- **Alto**: 40px (y="360" a y="400")
- **Fondo**: `#4A4A4A` (Gris neutro)
- **Contenido**: Nombre del proyecto fijo

### Tipografía
- **Font**: Arial, Helvetica, sans-serif
- **Antialiasing**: Por defecto (browser lo maneja)
- **Colores**: Blanco (#FFFFFF) o con opacity para variaciones

### Posiciones de Texto (Y-axis)

| Elemento | Y | Font-Size | Font-Weight |
|----------|---|-----------|-------------|
| Título | 130 | 72px | Bold (700) |
| Descripción | 190 | 28px | Light (300) |
| Divisor | 230 | N/A | N/A |
| Tipo | 290 | 40px | Bold (700) |
| Footer | 385 | 16px | Regular (400) |

**Nota**: Los valores Y están optimizados para centrado visual considerando la altura de los caracteres.

---

## Buenas Prácticas

### DO ✓

- ✓ Mantener el footer "MCP Tools Server" en todos los banners
- ✓ Usar los colores correctos según sección (ver tabla en "Banners Disponibles")
- ✓ Aplicar gradientes con opacidad consistente (0.10-0.15 para decoraciones)
- ✓ Incluir línea divisor en color primario (opacity 0.4)
- ✓ Escribir títulos breves y descriptivos (máximo 30-35 caracteres)
- ✓ Mantener descripciones en 1-2 líneas máximo
- ✓ Usar MAYÚSCULAS para el tipo de documento
- ✓ Agregar badge de tipo en esquina superior derecha
- ✓ Copiar desde `banner-template.svg` para nuevos banners
- ✓ Probar visualización en GitHub antes de usar
- ✓ Verificar que elementos decorativos no compitan con el texto

### DON'T ✗

- ✗ Cambiar el nombre del proyecto en el footer
- ✗ Usar colores fuera de la paleta armónica (Cyan, Verde, Morado)
- ✗ Mezclar colores de secciones diferentes en un mismo banner
- ✗ Remover elementos decorativos (círculos, líneas, badges)
- ✗ Agregar logos o imágenes dentro del SVG
- ✗ Hacer títulos demasiado largos (>35 caracteres)
- ✗ Usar fuentes personalizadas (fallback a Arial/Helvetica/Inter)
- ✗ Modificar las dimensiones (1200x400)
- ✗ Cambiar la opacidad de elementos decorativos (usar 0.10-0.15)
- ✗ Usar opacidad demasiado alta en decoraciones (compite con contenido)

---

## Ejemplos de Uso en Markdown

### En README de sección

```markdown
![Getting Started](../assets/banners/getting-started.svg)

# Getting Started

Esta guía te ayudará a instalar y configurar MCP Tools Server en 5 minutos.

## Requisitos Previos

- Docker y Docker Compose instalados
- ...
```

### Con ruta relativa desde subsección

```markdown
![API Reference](../../assets/banners/api-reference.svg)

# API Reference

Documentación completa de todas las herramientas MCP disponibles...
```

### En documentación anidada profunda

```markdown
![Configuration](../../../assets/banners/configuration.svg)

# Configuration

Guía detallada de variables de entorno, opciones de Docker...
```

---

## Mantenimiento

### Agregar Nueva Sección

Cuando agregues una nueva sección de documentación:

1. Identifica el nombre y descripción de la sección
2. Copia `banner-template.svg` → `nombre-seccion.svg`
3. Edita título, descripción y tipo
4. Prueba en navegador y en GitHub
5. Referencia en el README de la sección: `![Título](../assets/banners/nombre-seccion.svg)`

### Actualizar Descripción Existente

Si el contenido de una sección cambia significativamente:

1. Edita el banner SVG correspondiente
2. Actualiza la descripción (línea 2) si cambia el propósito
3. Actualiza el tipo (línea 3) si la categoría cambia
4. Mantén título consistente (generalmente no cambia)

### Resolver Conflictos de Nombres

Si dos banners tienen `id` de gradiente igual:

```xml
<!-- ANTES: Conflicto -->
<linearGradient id="gradient-cyan">
<linearGradient id="gradient-cyan">  <!-- Duplicado! -->

<!-- DESPUÉS: IDs únicos -->
<linearGradient id="gradient-cyan-gs">      <!-- getting-started.svg -->
<linearGradient id="gradient-cyan-api">     <!-- api-reference.svg -->
```

---

## Archivo de Banners Disponibles

```
docs/assets/banners/
├── README.md                    # Este archivo
├── banner-template.svg          # Plantilla base para crear nuevos
├── getting-started.svg          # Guía de inicio rápido
├── api-reference.svg            # Referencia de herramientas
├── troubleshooting.svg          # Solución de problemas
└── configuration.svg            # Setup y configuración
```

---

## Referencia de Paleta de Colores

Para más detalles sobre la paleta armónica, tokens de color y uso en diagramas Mermaid:

- [COLOR_PALETTE.md](../../COLOR_PALETTE.md) — Paleta completa (Cyan, Verde, Morado)
- Código Hex, RGB, armonía y principios de accesibilidad

## Diagramas de Arquitectura

Consulta los diagramas Mermaid que usan la misma paleta de colores:

- [ARCHITECTURE.md](../ARCHITECTURE.md) — Componentes del sistema con colores
- [DATA_FLOW.md](../DATA_FLOW.md) — Flujo de datos con paleta
- [NETWORK_TOPOLOGY.md](../NETWORK_TOPOLOGY.md) — Topología de red

## Relacionado

- [Documentación Principal](../README.md) — Índice de docs
- [Banners de README](../../assets/readme-banners/README.md) — Banners principales
- [Banner de Proyecto](../../assets/banner.svg) — Banner principal (raíz)
- [CLAUDE.md](../../CLAUDE.md) — Guía para agentes y desarrolladores
- [README Principal](../../README.md) — Información del proyecto

---

**Última actualización**: 2026-08-15  
**Responsable**: Especialista en Documentación Técnica  
**Proyecto**: MCP Tools Server  
**Versión**: 2.0 (Paleta Armónica)
