# Paleta de Colores Armónica — MCP Tools Server

_Guía de referencia para colores, gradientes y su uso en documentación visual._

## Paleta Primaria

Tres familias de colores que forman una armonía complementaria profesional:

### Tonalidades Cyan (Azul Cian)

Color primario: fresco, confiable, tecnológico.

| Nivel | Código Hex | RGB | Uso |
|-------|-----------|-----|-----|
| **Claro (600)** | `#06B6D4` | rgb(6, 182, 212) | Gradientes superiores, elementos primarios |
| **Medio (700)** | `#0891B2` | rgb(8, 145, 178) | Gradientes intermedios, bordes |
| **Oscuro (800)** | `#0E7490` | rgb(14, 116, 144) | Gradientes inferiores, backgrounds |

**Uso:**
- Banners de documentación principal (Getting Started, Configuration)
- Banner raíz del proyecto
- Componentes de "inicio" y "guía"

### Tonalidades Verde (Verde Esmeralda)

Color secundario: crecimiento, éxito, estabilidad.

| Nivel | Código Hex | RGB | Uso |
|-------|-----------|-----|-----|
| **Claro (600)** | `#10B981` | rgb(16, 185, 129) | Gradientes superiores, elementos positivos |
| **Medio (700)** | `#059669` | rgb(5, 150, 105) | Gradientes intermedios, líneas decorativas |
| **Oscuro (800)** | `#047857` | rgb(4, 120, 87) | Gradientes inferiores, backgrounds |

**Uso:**
- Banner del servidor (Server README)
- Diagramas de componentes exitosos
- Elementos de confirmación/éxito

### Tonalidades Morado (Púrpura)

Color terciario: innovación, creatividad, distinción.

| Nivel | Código Hex | RGB | Uso |
|-------|-----------|-----|-----|
| **Claro (600)** | `#A855F7` | rgb(168, 85, 247) | Gradientes superiores, elementos innovadores |
| **Medio (700)** | `#9333EA` | rgb(147, 51, 234) | Gradientes intermedios, transiciones |
| **Oscuro (800)** | `#7E22CE` | rgb(126, 34, 206) | Gradientes inferiores, backgrounds |

**Uso:**
- Banner del frontend (Frontend README)
- Diagramas de interfaz/usuario
- Elementos de interacción

---

## Asignación de Colores por Sección

### Documentación (docs/)

| Sección | Color | Gradiente | Archivo Banner |
|---------|-------|-----------|-----------------|
| Getting Started | Cyan | #06B6D4 → #0891B2 | `docs/assets/banners/getting-started.svg` |
| API Reference | Verde | #10B981 → #059669 | `docs/assets/banners/api-reference.svg` |
| Troubleshooting | Morado | #A855F7 → #9333EA | `docs/assets/banners/troubleshooting.svg` |
| Configuration | Cyan (oscuro) | #06B6D4 → #0E7490 | `docs/assets/banners/configuration.svg` |

### READMEs (assets/readme-banners/)

| Sección | Color | Gradiente | Archivo Banner |
|---------|-------|-----------|-----------------|
| Server | Verde | #10B981 → #059669 | `assets/readme-banners/server-readme.svg` |
| Frontend | Morado | #A855F7 → #9333EA | `assets/readme-banners/frontend-readme.svg` |
| Docs | Cyan | #06B6D4 → #0891B2 | `assets/readme-banners/docs-readme.svg` |

### Banner Raíz

| Sección | Color | Gradiente | Archivo Banner |
|---------|-------|-----------|-----------------|
| MCP Tools Server | Verde | #10B981 → #059669 | `assets/banner.svg` |

---

## Uso en Diagramas Mermaid

### Configuración de Tema

```
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#06B6D4',      // Cyan claro
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#0891B2', // Cyan medio
    'secondaryColor': '#10B981',     // Verde claro
    'tertiaryColor': '#A855F7',      // Morado claro
    'lineColor': '#059669',          // Verde medio
    'backgroundColor': '#f0f9fc',
    'fontSize': '14px',
    'fontFamily': 'Inter, sans-serif'
  }
}}%%
```

### Aplicación en Diagramas

- **Cyan**: Componentes de documentación, entrada, flujos iniciales
- **Verde**: Servidores, componentes activos, procesos exitosos
- **Morado**: Interfaces, clientes, componentes de usuario

---

## Paleta de Elementos Visuales

### Formas Decorativas (Banners SVG)

Cada banner incluye elementos visuales sutiles para mayor sofisticación:

- **Círculos decorativos**: Opacidad 0.1-0.15, color primario del banner
- **Rectángulos decorativos**: Opacidad 0.15-0.2, posicionados en bordes
- **Líneas divisoras**: Opacidad 0.4, color primario del banner
- **Gradientes de fondo**: Vertical, de color primario a variante oscura

**Ejemplo de composición:**
```
Degradado principal (vertical)
  ↓
Formas decorativas (círculos, rectángulos con opacidad baja)
  ↓
Línea divisor sutil
  ↓
Contenido textual (título, descripción, badge)
  ↓
Footer con información
```

---

## Tokens de Color

### CSS Variables (Para uso futuro en docs/CSS)

```css
/* Cyan */
:root {
  --color-cyan-600: #06B6D4;
  --color-cyan-700: #0891B2;
  --color-cyan-800: #0E7490;
  
  /* Verde */
  --color-green-600: #10B981;
  --color-green-700: #059669;
  --color-green-800: #047857;
  
  /* Morado */
  --color-purple-600: #A855F7;
  --color-purple-700: #9333EA;
  --color-purple-800: #7E22CE;
}
```

---

## Armonía y Coherencia

### Regla de Contraste

Todos los colores tienen contraste suficiente (4.5:1 o mayor) con texto blanco en fondos:
- Texto blanco sobre gradientes Cyan/Verde/Morado: ✓ Accesible (WCAG AA)
- Texto oscuro sobre fondos claros: ✓ Accesible

### Coherencia Visual

1. **Gradientes verticales**: Siempre de claro (600) a oscuro (800 u otro nivel)
2. **Opacidad de decoraciones**: 0.1-0.2 para no competir con contenido
3. **Líneas divisoras**: Usando color primario con opacidad 0.4
4. **Footer**: Gris neutro (#4A4A4A) o variante del color principal

### Escala de Valores

| Elemento | Opacidad |
|----------|----------|
| Decoraciones sutiles (círculos, rectángulos) | 0.10 - 0.15 |
| Líneas decorativas | 0.20 - 0.30 |
| Líneas divisoras | 0.40 - 0.50 |
| Fondos secundarios | 0.60 - 0.80 |
| Texto primario | 1.0 |

---

## Casos de Uso

### Documentación Técnica

- **Getting Started**: Cyan → accesibilidad y confianza
- **API Reference**: Verde → componentes activos, referencia técnica
- **Troubleshooting**: Morado → distinción, resolución de problemas
- **Configuration**: Cyan oscuro → configuración profunda

### Componentes del Sistema

**Diagramas Mermaid:**
- **Cyan**: Documentación, entrada de datos, clientes
- **Verde**: Servidores, procesamiento, componentes activos
- **Morado**: Interfaces, usuarios, interacción

**Ejemplo - Flujo de datos:**
```
Cliente (Morado) → API (Verde) → Database (Cyan)
```

---

## Referencias

- **Paleta basada en**: Tailwind CSS color system
- **Armonía**: Complementaria (colores que trabajan juntos visualmente)
- **Accesibilidad**: WCAG 2.1 AA (contraste mínimo 4.5:1)
- **Profesionalismo**: Estándar de tech/SaaS moderno

**Actualizado**: 2026-08-15  
**Mantenedor**: Especialista en Documentación Técnica
