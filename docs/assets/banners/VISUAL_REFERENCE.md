# Referencia Visual - Sistema de Banners Dinámicos

_Guía visual completa mostrando el diseño, dimensiones y ejemplos de cada banner._

---

## Estructura de Banner

```
DIMENSIONES: 1200px × 400px
PROPORCIÓN: 3:1 (ancho:alto)
FORMATO: SVG (escalable, sin pérdida)

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                ┃
┃  ╔══════════════════════════════════════════╗  ┃
┃  ║         ZONA DEGRADADA (360px)           ║  ┃
┃  ║    Gradiente: #06B6D4 → #0a5f75         ║  ┃
┃  ║                                          ║  ┃
┃  ║              Getting Started              ║  ┃ ← Título (72px, bold)
┃  ║                                          ║  ┃
┃  ║     Guía rápida para comenzar...         ║  ┃ ← Descripción (28px, light)
┃  ║                                          ║  ┃
┃  ║  ──────────────────────────────────────  ║  ┃ ← Divisor (1px, opacity 0.2)
┃  ║                                          ║  ┃
┃  ║              QUICK START                  ║  ┃ ← Tipo (40px, bold)
┃  ║                                          ║  ┃
┃  ╚══════════════════════════════════════════╝  ┃
┃                                                ┃
┃  ┌──────────────────────────────────────────┐  ┃
┃  │  ZONA FOOTER (40px)                      │  ┃
┃  │  Fondo: #4A4A4A                          │  ┃
┃  │                                          │  ┃
┃  │      MCP Tools Server (16px, white)      │  ┃
┃  │                                          │  ┃
┃  └──────────────────────────────────────────┘  ┃
┃                                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

TOTAL: 400px de alto
```

---

## Composición Visual por Elemento

### 1. Zona Degradada (0-360px)

```
ALTURA: 360 píxeles
ANCHURA: 1200 píxeles (completa)
GRADIENTE: Lineal, de arriba a abajo

Inicio (#06B6D4 - Cyan-600):
  ┌──────────────────────────────────────────────┐
  │████████████████████████████████████████████│  ← Y=0 (100% opaco)
  │████████████████████████████████████████████│
  │████████████████████████████████████████████│

Medio (transición):
  │████████████████████████████████████████████│  ← Y=180
  │████████████████████████████████████████████│
  │████████████████████████████████████████████│

Fin (#0a5f75 - Teal-700+):
  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  ← Y=360 (100% opaco)
  └──────────────────────────────────────────────┘
```

**Código Gradiente**:
```xml
<linearGradient id="gradient-cyan-[ID]" 
                 x1="0%" y1="0%" 
                 x2="0%" y2="100%">
  <stop offset="0%" style="stop-color:#06B6D4;stop-opacity:1" />
  <stop offset="100%" style="stop-color:#0a5f75;stop-opacity:1" />
</linearGradient>
```

---

### 2. Posicionamiento de Texto

```
VISTA FRONTAL CON COORDENADAS:

Y=0px  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
       ┃                                  ┃
Y=50px ┃        [ZONA VACÍA]              ┃
       ┃                                  ┃
Y=130px┃      Getting Started             ┃ ← Título (font-size: 72px)
       ┃      (text-anchor: middle)        ┃    (y es la base del texto)
       ┃                                  ┃
Y=190px┃   Guía rápida para comenzar      ┃ ← Descripción (font-size: 28px)
       ┃   (fill-opacity: 0.9)             ┃    (más ligera visualmente)
       ┃                                  ┃
Y=230px┃ ───────────────────────────── ┃ ← Divisor (stroke-width: 1px)
       ┃ (stroke-opacity: 0.2)             ┃
       ┃                                  ┃
Y=290px┃      QUICK START                 ┃ ← Tipo (font-size: 40px)
       ┃      (text-anchor: middle)        ┃
       ┃                                  ┃
Y=360px┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
       ┃ ZONA FOOTER (#4A4A4A)            ┃
       ┃                                  ┃
Y=385px┃  MCP Tools Server (16px)         ┃ ← Footer fijo en todos
       ┃                                  ┃
Y=400px┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

NOTA: X=600 en todos los elementos (centrado horizontal)
      1200px / 2 = 600px
```

---

## Ejemplos de Banners Completados

### Ejemplo 1: Getting Started

```
ARCHIVO: getting-started.svg

┌────────────────────────────────────────────────┐
│                                                │
│                                                │
│              Getting Started                   │
│                                                │
│     Guía rápida para comenzar con              │
│        MCP Tools Server                        │
│                                                │
│  ──────────────────────────────────────────    │
│                                                │
│              QUICK START                       │
│                                                │
├────────────────────────────────────────────────┤
│          MCP Tools Server                      │
└────────────────────────────────────────────────┘

COMPONENTES:
  Título: "Getting Started" (18 caracteres)
  Descripción: "Guía rápida para comenzar..." (46 caracteres)
  Tipo: "QUICK START" (11 caracteres)
  Footer: "MCP Tools Server" (FIJO)
  Gradiente ID: gradient-cyan-gs
```

### Ejemplo 2: API Reference

```
ARCHIVO: api-reference.svg

┌────────────────────────────────────────────────┐
│                                                │
│                                                │
│             API Reference                      │
│                                                │
│   Documentación completa de herramientas       │
│      y endpoints MCP                           │
│                                                │
│  ──────────────────────────────────────────    │
│                                                │
│            TOOLS & ENDPOINTS                   │
│                                                │
├────────────────────────────────────────────────┤
│          MCP Tools Server                      │
└────────────────────────────────────────────────┘

COMPONENTES:
  Título: "API Reference" (13 caracteres)
  Descripción: "Documentación completa de..." (54 caracteres)
  Tipo: "TOOLS & ENDPOINTS" (17 caracteres)
  Footer: "MCP Tools Server" (FIJO)
  Gradiente ID: gradient-cyan-api
```

### Ejemplo 3: Troubleshooting

```
ARCHIVO: troubleshooting.svg

┌────────────────────────────────────────────────┐
│                                                │
│                                                │
│            Troubleshooting                     │
│                                                │
│    Soluciones a problemas comunes y            │
│       diagnóstico de errores                   │
│                                                │
│  ──────────────────────────────────────────    │
│                                                │
│            PROBLEM SOLVING                     │
│                                                │
├────────────────────────────────────────────────┤
│          MCP Tools Server                      │
└────────────────────────────────────────────────┘

COMPONENTES:
  Título: "Troubleshooting" (15 caracteres)
  Descripción: "Soluciones a problemas comunes..." (55 caracteres)
  Tipo: "PROBLEM SOLVING" (15 caracteres)
  Footer: "MCP Tools Server" (FIJO)
  Gradiente ID: gradient-cyan-ts
```

### Ejemplo 4: Configuration

```
ARCHIVO: configuration.svg

┌────────────────────────────────────────────────┐
│                                                │
│                                                │
│             Configuration                      │
│                                                │
│    Setup y configuración paso a paso de        │
│       MCP Tools Server                         │
│                                                │
│  ──────────────────────────────────────────    │
│                                                │
│         SETUP & CUSTOMIZATION                  │
│                                                │
├────────────────────────────────────────────────┤
│          MCP Tools Server                      │
└────────────────────────────────────────────────┘

COMPONENTES:
  Título: "Configuration" (13 caracteres)
  Descripción: "Setup y configuración paso a paso..." (37 caracteres)
  Tipo: "SETUP & CUSTOMIZATION" (21 caracteres)
  Footer: "MCP Tools Server" (FIJO)
  Gradiente ID: gradient-cyan-config
```

---

## Comparación de Estilos de Texto

### Tamaño de Fuente Comparativo

```
TÍTULO (72px)
█████████████████████████████████████████████████
█████████████████████████████████████████████████
██ Getting Started ██
█████████████████████████████████████████████████
█████████████████████████████████████████████████

TIPO (40px)
████████████████████████████
████████████████████████████
██ QUICK START ██
████████████████████████████
████████████████████████████

DESCRIPCIÓN (28px)
████████████████████
████████████████████
██ Guía rápida ██
████████████████████
████████████████████

FOOTER (16px)
████████████
████████████
██ MCP Tools Server ██
████████████
████████████
```

---

## Paleta de Colores Exacta

### Gradiente Principal (Degradado Cyan → Teal)

```
INICIO: #06B6D4 (Cyan-600)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ RGB(6, 182, 212)                       ┃
┃ HSL(189°, 96%, 43%)                    ┃
┃ Tailwind: cyan-600                     ┃
┃ Uso: Inicio del gradiente (parte sup) ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

TRANSICIÓN: Lineal vertical
┌──────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ ← Inicio
│ ░░░░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░  │
│ ░░░░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░  │
│ ░░░░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░  │
│ ░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░  │
│ ░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░  │ ← Fin
└──────────────────────────────────────────┘

FIN: #0a5f75 (Teal-700+ personalizado)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ RGB(10, 95, 117)                       ┃
┃ HSL(194°, 84%, 25%)                    ┃
┃ Tailwind: Similar a teal-700 modificad ┃
┃ Uso: Fin del gradiente (parte inferior)┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Footer Gris

```
#4A4A4A (Gris Neutro)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ RGB(74, 74, 74)                        ┃
┃ HSL(0°, 0%, 29%)                       ┃
┃ Similar a: gray-600 en Tailwind         ┃
┃ Uso: Fondo del pie de página           ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Propiedades:                            ┃
┃ - Neutral, ni muy claro ni muy oscuro ┃
┃ - Contrasta bien con texto blanco      ┃
┃ - Profesional y limpio                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Texto y Acentos

```
BLANCO (Principal)
#FFFFFF (RGB 255, 255, 255)
- Todos los títulos, tipos y footer
- Máximo contraste sobre degradado cyan
- Totalmente opaco (opacity: 1)

BLANCO CON OPACITY (Descripción)
#FFFFFF con opacity: 0.9
- Descripción (28px light)
- Más suave visualmente
- Sigue siendo legible

BLANCO MÁS SUTIL (Divisor)
#FFFFFF con opacity: 0.2
- Línea divisor solo ornamental
- Casi invisible pero presente
- Agrega profundidad visual
```

---

## Comparación: Antes vs Después de Integración

### ANTES (Sin Banners)

```markdown
# Getting Started

Welcome to MCP Tools Server...

## Prerequisites
- Docker...
```

### DESPUÉS (Con Banners)

```markdown
![Getting Started](../assets/banners/getting-started.svg)

# Getting Started

Welcome to MCP Tools Server...

## Prerequisites
- Docker...
```

**Mejora Visual**:
- ✓ Identidad visual clara desde el inicio
- ✓ Navegación más intuitiva
- ✓ Diferenciación clara entre secciones
- ✓ Profesionalismo aumentado

---

## Guía de Prueba Visual

### 1. Verificar en Navegador Local

```bash
# Abre el archivo SVG directamente
firefox docs/assets/banners/getting-started.svg

# O en VS Code
# Instala extensión "SVG Preview"
# Click derecho → Open Preview
```

### 2. Verificar en GitHub

Cuando hagas push:
1. Abre el PR o rama en GitHub
2. Navega a `docs/assets/banners/getting-started.svg`
3. Verifica que se renderiza con:
   - Gradiente cyan → teal visible
   - Texto blanco legible
   - Footer gris en la parte inferior
   - Sin errores de SVG

### 3. Verificar en Markdown Preview

Crea un archivo test:
```markdown
![Test Banner](assets/banners/getting-started.svg)
```

En VS Code:
- `Ctrl+K V` (Windows/Linux)
- `Cmd+K V` (Mac)

---

## Especificaciones de Diseño Resumidas

### Dimensiones
| Elemento | Valor |
|----------|-------|
| Ancho | 1200px |
| Alto Total | 400px |
| Zona Gradiente | 360px |
| Zona Footer | 40px |

### Tipografía
| Elemento | Tamaño | Peso | Opacity |
|----------|--------|------|---------|
| Título | 72px | Bold (700) | 1.0 |
| Descripción | 28px | Light (300) | 0.9 |
| Tipo | 40px | Bold (700) | 1.0 |
| Footer | 16px | Regular (400) | 1.0 |

### Colores
| Zona | Color | Hex | RGB |
|------|-------|-----|-----|
| Gradiente Inicio | Cyan-600 | #06B6D4 | 6,182,212 |
| Gradiente Fin | Teal-700+ | #0a5f75 | 10,95,117 |
| Footer | Gris | #4A4A4A | 74,74,74 |
| Texto | Blanco | #FFFFFF | 255,255,255 |

---

## Resumen Visual Completo

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          BANNER DINÁMICO - MCP SERVER           ┃
┃                    1200 × 400px                 ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                ┃
┃  ┌──────────────────────────────────────────┐ ┃
┃  │       ZONA DEGRADADA (360px)             │ ┃
┃  │   Gradiente #06B6D4 → #0a5f75            │ ┃
┃  │                                          │ ┃
┃  │           [TÍTULO 72px BOLD]             │ ┃
┃  │                                          │ ┃
┃  │      [DESCRIPCIÓN 28px LIGHT]            │ ┃
┃  │                                          │ ┃
┃  │   ────────────────────────────────────   │ ┃
┃  │                                          │ ┃
┃  │          [TIPO 40px BOLD]                │ ┃
┃  │                                          │ ┃
┃  └──────────────────────────────────────────┘ ┃
┃                                                ┃
┃  ┌──────────────────────────────────────────┐ ┃
┃  │    ZONA FOOTER (40px) #4A4A4A            │ ┃
┃  │                                          │ ┃
┃  │    MCP Tools Server (16px REGULAR)       │ ┃
┃  │                                          │ ┃
┃  └──────────────────────────────────────────┘ ┃
┃                                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

CARACTERÍSTICAS:
✓ Totalmente responsive (SVG escala automáticamente)
✓ Sin dependencias externas (SVG puro)
✓ Performance optimizado (<2KB por archivo)
✓ Gradiente suave y profesional
✓ Tipografía clara y legible
✓ Espaciado balanceado
✓ Color de marca consistente
✓ Footer fijo en todos los banners
```

---

**Última actualización**: 2026-08-15  
**Proyecto**: MCP Tools Server  
**Sistema**: Banners Dinámicos v1.0
