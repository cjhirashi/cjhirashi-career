# Especificaciones Técnicas de Banners Dinámicos

_Referencia completa de dimensiones, colores, tipografía y estructura SVG del sistema de banners._

---

## Dimensiones Globales

| Propiedad | Valor | Notas |
|-----------|-------|-------|
| **Ancho (Width)** | 1200px | Estándar web, optimizado para desktops |
| **Alto (Height)** | 400px | Altura suficiente para todos los elementos |
| **Proporción (Aspect Ratio)** | 3:1 (1200:400) | Estándar de banners web |
| **ViewBox** | `0 0 1200 400` | Scaling automático en responsive |
| **SVG Namespace** | `http://www.w3.org/2000/svg` | Requerido para renderizado correcto |

---

## Estructura de Zonas

### Zona Degradada (Azul/Cyan)

```
┌─────────────────────────────────────────┐
│         ZONA DEGRADADA (360px)          │
│  Gradiente: #06B6D4 → #0a5f75           │
│                                         │
│            Título (72px)                │
│         Descripción (28px)              │
│       ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─          │
│          Tipo (40px)                    │
│                                         │
└─────────────────────────────────────────┘
```

**Altura**: 0px - 360px  
**Color**: Gradiente lineal de arriba a abajo

### Zona Footer (Gris)

```
┌─────────────────────────────────────────┐
│    ZONA FOOTER (40px) #4A4A4A           │
│   MCP Tools Server (16px, blanco)       │
└─────────────────────────────────────────┘
```

**Altura**: 360px - 400px  
**Color**: Sólido #4A4A4A

---

## Definición de Gradiente

### XML SVG

```xml
<defs>
  <linearGradient id="gradient-cyan-[ID]" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" style="stop-color:#06B6D4;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#0a5f75;stop-opacity:1" />
  </linearGradient>
</defs>
```

### Parámetros de Gradiente

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| **ID** | `gradient-cyan-[nombre]` | Único por banner (ej: gradient-cyan-gs) |
| **x1, y1** | `0%, 0%` | Punto de inicio (superior izquierda) |
| **x2, y2** | `0%, 100%` | Punto final (inferior izquierda) |
| **Direction** | Vertical (arriba→abajo) | Linear gradient de superior a inferior |
| **Color Inicio** | `#06B6D4` (Cyan-600) | Tailwind color palette |
| **Color Fin** | `#0a5f75` (Teal-700+) | Variante personalizada |
| **Opacity** | `1` (100%) | Gradiente opaco, sin transparencia |

### Paleta de Colores

| Nombre | Código Hex | RGB | Uso |
|--------|-----------|-----|-----|
| **Cyan (Inicio)** | `#06B6D4` | rgb(6, 182, 212) | Inicio de gradiente |
| **Teal (Fin)** | `#0a5f75` | rgb(10, 95, 117) | Fin de gradiente |
| **Footer Gray** | `#4A4A4A` | rgb(74, 74, 74) | Fondo del pie de página |
| **Blanco (Texto)** | `#FFFFFF` | rgb(255, 255, 255) | Texto principal |
| **Blanco Translúcido** | `#FFFFFF, opacity=0.9` | Opcional | Descripción (light) |
| **Blanco Divisor** | `#FFFFFF, opacity=0.2` | Opcional | Línea divisor sutil |

---

## Tipografía

### Familia de Fuentes

```xml
font-family="Arial, Helvetica, sans-serif"
```

| Font | Fallback 1 | Fallback 2 | Notas |
|------|-----------|-----------|-------|
| Arial | Helvetica | sans-serif | Stack seguro, sin fuentes externas |

**Razón**: Arial está disponible en 99%+ de sistemas. Helvetica es alternativa en Mac. Sans-serif como último recurso.

### Pesos de Fuente

| Elemento | Weight | Código CSS | Apariencia |
|----------|--------|-----------|-----------|
| **Título** | Bold (700) | `font-weight="bold"` | Nítido, llamativo |
| **Descripción** | Light (300) | `font-weight="300"` | Elegante, secundario |
| **Tipo** | Bold (700) | `font-weight="bold"` | Destaca, categoría |
| **Footer** | Regular (400) | `font-weight="400"` | Neutral, informativo |

---

## Elementos de Texto

### 1. Título (Línea 1)

```xml
<text x="600" y="130" 
      font-family="Arial, Helvetica, sans-serif" 
      font-size="72" 
      font-weight="bold" 
      fill="white" 
      text-anchor="middle">
  Getting Started
</text>
```

| Propiedad | Valor | Propósito |
|-----------|-------|----------|
| **x** | 600 | Centrado horizontal (ancho / 2) |
| **y** | 130 | Posición vertical desde arriba |
| **font-size** | 72px | Tamaño grande, muy visible |
| **font-weight** | bold | Destacado |
| **fill** | white | Color blanco nítido |
| **text-anchor** | middle | Alineación centrada |
| **Opacity** | 1 (default) | Totalmente opaco |

**Características**:
- Máximo ~35 caracteres para no truncar
- Se renderiza completamente en 360px de altura disponible
- Mejor contraste sobre el gradiente

### 2. Descripción (Línea 2)

```xml
<text x="600" y="190" 
      font-family="Arial, Helvetica, sans-serif" 
      font-size="28" 
      font-weight="300" 
      fill="white" 
      fill-opacity="0.9" 
      text-anchor="middle">
  Guía rápida para comenzar
</text>
```

| Propiedad | Valor | Propósito |
|-----------|-------|----------|
| **x** | 600 | Centrado horizontal |
| **y** | 190 | Debajo del título |
| **font-size** | 28px | Secundario, legible |
| **font-weight** | 300 | Light, elegante |
| **fill** | white | Color base blanco |
| **fill-opacity** | 0.9 | 90% opacidad (ligeramente translúcido) |
| **text-anchor** | middle | Centrado |

**Características**:
- Máximo ~70 caracteres
- Opacity al 90% la hace visualmente "más ligera" que el título
- Separación visual clara

### 3. Divisor (Línea Sutil)

```xml
<line x1="24" y1="230" 
      x2="1176" y2="230" 
      stroke="white" 
      stroke-width="1" 
      stroke-opacity="0.2" 
      stroke-linecap="round" />
```

| Propiedad | Valor | Propósito |
|-----------|-------|----------|
| **x1, x2** | 24 - 1176 | Línea horizontal de lado a lado (98% ancho) |
| **y1, y2** | 230 | Posición vertical fija |
| **stroke** | white | Color blanco |
| **stroke-width** | 1px | Línea muy fina |
| **stroke-opacity** | 0.2 | Muy sutil (20% opacidad) |
| **stroke-linecap** | round | Extremos redondeados |

**Características**:
- Separa visualmente descripción de tipo
- No invasiva (opacity baja)
- Margen: 24px desde los lados (evita bordes)

### 4. Tipo/Categoría (Línea 3)

```xml
<text x="600" y="290" 
      font-family="Arial, Helvetica, sans-serif" 
      font-size="40" 
      font-weight="bold" 
      fill="white" 
      text-anchor="middle">
  QUICK START
</text>
```

| Propiedad | Valor | Propósito |
|-----------|-------|----------|
| **x** | 600 | Centrado |
| **y** | 290 | Cerca del footer, bien visible |
| **font-size** | 40px | Intermedio, destaca |
| **font-weight** | bold | Proyecta importancia |
| **fill** | white | Contraste total |
| **text-anchor** | middle | Centrado |
| **Opacity** | 1 (default) | Totalmente opaco |

**Características**:
- SIEMPRE en MAYÚSCULAS
- Máximo ~30 caracteres
- Muy visible

### 5. Footer (Nombre del Proyecto)

```xml
<text x="600" y="385" 
      font-family="Arial, Helvetica, sans-serif" 
      font-size="16" 
      font-weight="400" 
      fill="white" 
      text-anchor="middle">
  MCP Tools Server
</text>
```

| Propiedad | Valor | Propósito |
|-----------|-------|----------|
| **x** | 600 | Centrado |
| **y** | 385 | Casi al borde inferior (385/400) |
| **font-size** | 16px | Pequeño, informativo |
| **font-weight** | 400 (regular) | Neutral |
| **fill** | white | Contrasta con fondo gris |
| **text-anchor** | middle | Centrado |

**Características**:
- **FIJO en todos los banners**: "MCP Tools Server"
- Se renderiza sobre fondo gris #4A4A4A
- No cambiar entre documentos

---

## Posiciones de Elementos (Eje Y)

```
0px  ┌──────────────────────────────────┐
     │ INICIO DE ZONA DEGRADADA         │
     │                                  │
130px│         TÍTULO (72px)            │ ← Principal
     │                                  │
190px│      DESCRIPCIÓN (28px)          │ ← Secundario
     │                                  │
230px│ ─────────────────────────────── │ ← Divisor
     │                                  │
290px│       TIPO (40px)                │ ← Categoría
     │                                  │
360px├──────────────────────────────────┤
     │ ZONA FOOTER (gris #4A4A4A)       │
     │                                  │
385px│   MCP Tools Server (16px)        │ ← Footer (fijo)
     │                                  │
400px└──────────────────────────────────┘
```

**Notas sobre posiciones**:
- Y=0 es el borde superior
- Y=360 es el límite entre gradiente y footer
- Y=400 es el borde inferior
- Las posiciones están optimizadas considerando la altura de los caracteres (baseline)

---

## Rectángulos Base

### Rectángulo de Gradiente

```xml
<rect width="1200" height="360" fill="url(#gradient-cyan-[ID])" />
```

| Propiedad | Valor |
|-----------|-------|
| width | 1200px |
| height | 360px |
| fill | reference al gradiente |
| x (implicit) | 0 |
| y (implicit) | 0 |

### Rectángulo de Footer

```xml
<rect y="360" width="1200" height="40" fill="#4A4A4A" />
```

| Propiedad | Valor |
|-----------|-------|
| x (implicit) | 0 |
| y | 360px |
| width | 1200px |
| height | 40px |
| fill | #4A4A4A (gris) |

---

## Validación de Estructura

### Checklist de SVG Válido

```xml
<?xml version="1.0"?>                                    ✓ Opcional pero recomendado
<svg xmlns="http://www.w3.org/2000/svg"                 ✓ Namespace requerido
     viewBox="0 0 1200 400"                             ✓ Siempre este tamaño
     width="1200"                                        ✓ Pixel-perfect
     height="400">                                       ✓ Pixel-perfect
  <defs>                                                ✓ Gradientes aquí
    <linearGradient id="gradient-cyan-...">             ✓ ID único
      <stop ... />                                      ✓ Dos stops
      <stop ... />
    </linearGradient>
  </defs>
  
  <rect width="1200" height="360" fill="url(...)" />   ✓ Zona gradiente
  <rect y="360" ... fill="#4A4A4A" />                  ✓ Zona footer
  
  <text ... >TÍTULO</text>                              ✓ Y=130
  <text ... >Descripción</text>                         ✓ Y=190
  <line ... y1="230" y2="230" ... />                    ✓ Divisor
  <text ... >TIPO</text>                                ✓ Y=290
  
  <text ... >MCP Tools Server</text>                     ✓ Y=385 (footer)
</svg>                                                  ✓ Cierre
```

---

## Aplicación a Casos de Uso

### Case 1: Banner de "Getting Started"

```xml
<!-- gradient-cyan-gs (ID único para GS) -->
<!-- Título: "Getting Started" (18 caracteres) ✓ < 35 -->
<!-- Descripción: "Guía rápida para comenzar con MCP Tools Server" (46 chars) ✓ < 70 -->
<!-- Tipo: "QUICK START" (11 caracteres) ✓ < 30 -->
```

### Case 2: Banner de "API Reference"

```xml
<!-- gradient-cyan-api (ID único para API) -->
<!-- Título: "API Reference" (13 caracteres) ✓ < 35 -->
<!-- Descripción: "Documentación completa de herramientas y endpoints MCP" (54 chars) ✓ < 70 -->
<!-- Tipo: "TOOLS & ENDPOINTS" (17 caracteres) ✓ < 30 -->
```

### Case 3: Banner de "Troubleshooting"

```xml
<!-- gradient-cyan-ts (ID único para TS) -->
<!-- Título: "Troubleshooting" (15 caracteres) ✓ < 35 -->
<!-- Descripción: "Soluciones a problemas comunes y diagnóstico de errores" (55 chars) ✓ < 70 -->
<!-- Tipo: "PROBLEM SOLVING" (15 caracteres) ✓ < 30 -->
```

---

## Optimizaciones Técnicas

### Renderizado en Navegadores

- **SVG Nativo**: Soportado en 99%+ de navegadores modernos
- **Escalado**: ViewBox permite escalar sin pixelado
- **Performance**: Archivo pequeño (<2KB), carga instantánea
- **Sin JavaScript**: SVG estático, no requiere interacción

### Renderizado en GitHub

- **Markdown Renderer**: GitHub renderiza SVG inline correctamente
- **Tamaño en Preview**: Se adapta al ancho de la columna
- **Fallback**: Si SVG falla, muestra alt text

### Renderizado en Diferentes Plataformas

| Plataforma | Compatibilidad | Notas |
|-----------|----------------|-------|
| GitHub | 100% | Renderiza perfecto |
| GitLab | 100% | Renderiza perfecto |
| Gitea | 100% | Renderiza perfecto |
| Navegadores | 99%+ | Desktop y mobile |
| Markdown Viewers | 95%+ | La mayoría lo soportan |

---

## Guía de Debugging

### Problema: Gradiente No Aparece

**Causa**: ID de gradiente no coincide o no está referenciado

**Verificar**:
```xml
<!-- En <defs> -->
<linearGradient id="gradient-cyan-gs">
  ...
</linearGradient>

<!-- En <rect> -->
<rect fill="url(#gradient-cyan-gs)" />  ← IDs deben coincidir
```

### Problema: Texto Se Superpone

**Causa**: Valores Y demasiado cercanos

**Verificar**:
```
Título (Y=130) vs Descripción (Y=190) = 60px de separación ✓
Descripción (Y=190) vs Divisor (Y=230) = 40px de separación ✓
Divisor (Y=230) vs Tipo (Y=290) = 60px de separación ✓
```

### Problema: Footer Cortado

**Causa**: Y del texto demasiado bajo (>390)

**Verificar**:
```xml
<!-- Y del footer debe estar entre 380-390 -->
<text y="385">MCP Tools Server</text>  ← Correcto
<text y="395">MCP Tools Server</text>  ← Demasiado bajo!
```

---

## Referencias Útiles

- [MDN: SVG Text](https://developer.mozilla.org/en-US/docs/Web/SVG/Element/text)
- [MDN: linearGradient](https://developer.mozilla.org/en-US/docs/Web/SVG/Element/linearGradient)
- [SVG Spec](https://www.w3.org/TR/SVG2/)
- [Tailwind Colors](https://tailwindcss.com/docs/customizing-colors)

---

**Última actualización**: 2026-08-15  
**Proyecto**: MCP Tools Server  
**Autor**: Especialista en Documentación Técnica
