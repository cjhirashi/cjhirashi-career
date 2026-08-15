# Banners Dinámicos de Documentación

_Sistema modular de banners personalizados por documento. Cada sección de documentación tiene su propio banner con título, descripción y tipo específicos._

---

## Descripción General

Este directorio contiene banners SVG dinámicos para cada sección de la documentación de **MCP Tools Server**. Cada banner es personalizable manteniendo una estructura visual y estilo consistente.

### Características

- **Gradiente Cyan Consistente**: Color de marca #06B6D4 → #0a5f75
- **Footer Fijo**: Nombre del proyecto "MCP Tools Server" en todos los banners
- **Contenido Personalizable**: Título, descripción y tipo por documento
- **Formato SVG Puro**: Sin dependencias externas, se renderiza en cualquier cliente
- **Responsive**: ViewBox flexible que se adapta a diferentes tamaños

---

## Estructura de un Banner

Cada banner tiene dimensiones **1200x400px** y está dividido en dos zonas:

### 1. Zona Azul Degradada (0-360px)

Contiene tres líneas de texto centradas:

| Línea | Elemento | Tamaño | Peso | Ejemplo |
|-------|----------|--------|------|---------|
| 1 | **Título del Documento** | 72px | Bold | "Getting Started" |
| 2 | **Descripción Breve** | 28px | Light (300) | "Guía rápida para comenzar..." |
| 3 | **Tipo/Categoría** | 40px | Bold | "QUICK START" |

Entre línea 2 y 3 hay un divisor sutil blanco (1px, opacity 0.2).

### 2. Zona Gris (360-400px)

Footer con:
- **Nombre del Proyecto**: "MCP Tools Server" (FIJO en todos)
- **Tamaño**: 16px
- **Color**: Blanco sobre fondo #4A4A4A

---

## Banners Disponibles

### 1. `getting-started.svg`
- **Título**: Getting Started
- **Descripción**: Guía rápida para comenzar con MCP Tools Server
- **Tipo**: QUICK START
- **Uso**: `docs/getting-started/README.md`

### 2. `api-reference.svg`
- **Título**: API Reference
- **Descripción**: Documentación completa de herramientas y endpoints MCP
- **Tipo**: TOOLS & ENDPOINTS
- **Uso**: `docs/api/README.md` o documentación de herramientas

### 3. `troubleshooting.svg`
- **Título**: Troubleshooting
- **Descripción**: Soluciones a problemas comunes y diagnóstico de errores
- **Tipo**: PROBLEM SOLVING
- **Uso**: `docs/troubleshooting/README.md`

### 4. `configuration.svg`
- **Título**: Configuration
- **Descripción**: Setup y configuración paso a paso de MCP Tools Server
- **Tipo**: SETUP & CUSTOMIZATION
- **Uso**: `docs/configuration/README.md`

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
- **Gradiente**: Linear, de arriba a abajo (y1="0%" → y2="100%")
- **Colores**:
  - Inicio: `#06B6D4` (Cyan-600)
  - Fin: `#0a5f75` (Teal-700 personalizado)

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
- ✓ Usar el gradiente cyan consistente (#06B6D4 → #0a5f75)
- ✓ Escribir títulos breves y descriptivos
- ✓ Mantener descripciones en 1 línea si es posible
- ✓ Usar MAYÚSCULAS para el tipo de documento
- ✓ Copiar desde `banner-template.svg` para nuevos banners
- ✓ Probar visualización en GitHub antes de usar

### DON'T ✗

- ✗ Cambiar el nombre del proyecto en el footer
- ✗ Usar colores diferentes al gradiente cyan
- ✗ Agregar logos o imágenes dentro del SVG
- ✗ Hacer títulos demasiado largos (>35 caracteres)
- ✗ Usar fuentes personalizadas (fallback a Arial/Helvetica)
- ✗ Modificar las dimensiones (1200x400)
- ✗ Remover el divisor sutil entre descripción y tipo

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

## Relacionado

- [Documentación Principal](../README.md) — Índice de docs
- [Banner de Proyecto](../../assets/banner.svg) — Banner principal (raíz)
- [CLAUDE.md](../../CLAUDE.md) — Guía para agentes y desarrolladores
- [README Principal](../../README.md) — Información del proyecto

---

**Última actualización**: 2026-08-15  
**Responsable**: Especialista en Documentación Técnica  
**Proyecto**: MCP Tools Server
