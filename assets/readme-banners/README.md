# Sistema de Banners para READMEs

_Sistema dinámico de banners SVG personalizados para cada sección del proyecto MCP Server._

## Descripción

Este sistema proporciona banners visuales consistentes y reutilizables para los READMEs de cada sección del proyecto:

- **server/** — MCP server implementation
- **frontend/** — Web UI para interactuar con el servidor
- **docs/** — Documentación completa

Cada banner está diseñado con:
- Gradiente profesional (Cyan → Teal)
- Título y descripción personalizados
- Tipo de sección (badge)
- Footer con tecnologías y ruta del README
- Dimensiones estándar: **1200×400px**

## Estructura

```
assets/readme-banners/
├── README.md                        # Este archivo
├── EXAMPLES.md                      # Ejemplos de uso e integración
├── banner-readme-template.svg       # Plantilla base (reutilizable)
├── server-readme.svg                # Banner para server/
├── frontend-readme.svg              # Banner para frontend/
└── docs-readme.svg                  # Banner para docs/
```

## Banners Disponibles

### 1. Server Banner
**Archivo:** `server-readme.svg`

```
Título:      Server
Descripción: MCP server implementation with FastMCP and WeasyPrint PDF generation
Tipo:        SERVER
Tecnologías: FastMCP • WeasyPrint • Jinja2 • Python • Docker
Ruta:        server/README.md
```

### 2. Frontend Banner
**Archivo:** `frontend-readme.svg`

```
Título:      Frontend
Descripción: Web UI for interacting with MCP server and downloading generated documents
Tipo:        FRONTEND
Tecnologías: React • TypeScript • Tailwind CSS • shadcn/ui
Ruta:        frontend/README.md
```

### 3. Documentation Banner
**Archivo:** `docs-readme.svg`

```
Título:      Documentation
Descripción: Complete guides, API reference, and troubleshooting for all components
Tipo:        DOCS
Tecnologías: Markdown • Mermaid • HTML • CSS • Guides
Ruta:        docs/README.md
```

## Uso en Markdown

### Integración en README de Server

```markdown
![Server README](../../assets/readme-banners/server-readme.svg)

# Server

Contenido del README aquí...
```

### Integración en README de Frontend

```markdown
![Frontend README](../../assets/readme-banners/frontend-readme.svg)

# Frontend

Contenido del README aquí...
```

### Integración en README de Docs

```markdown
![Documentation README](../../assets/readme-banners/docs-readme.svg)

# Documentation

Contenido del README aquí...
```

## Especificaciones Técnicas

### Dimensiones
- **Ancho:** 1200px
- **Alto:** 400px
- **Proporción:** 3:1 (estándar para banners)

### Colores

| Elemento | Color | Valor Hex |
|----------|-------|-----------|
| Gradiente Superior | Cyan | #06B6D4 |
| Gradiente Inferior | Teal | #0a5f75 |
| Footer | Gris | #4A4A4A |
| Texto | Blanco | #FFFFFF |
| Línea Divisor | Blanco (20% opacity) | rgba(255,255,255,0.2) |

### Tipografía

| Elemento | Fuente | Tamaño | Peso |
|----------|--------|--------|------|
| Título | Inter | 72px | 700 (Bold) |
| Descripción | Inter | 28px | 300 (Light) |
| Tipo (Badge) | Inter | 40px | 700 (Bold) |
| Footer | Inter | 12px | 400 (Regular) |

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│                                                    SERVER   │
│  Título                                                     │
│  Descripción primera línea                                 │
│  Descripción segunda línea                                 │
│  ─────────────                                             │
├─────────────────────────────────────────────────────────────┤
│  Tecnología • Stack • List  |  section/README.md           │
└─────────────────────────────────────────────────────────────┘
```

- **Margen superior:** 40px
- **Margen izquierdo:** 40px
- **Margen derecho:** 40px
- **Altura footer:** 80px
- **Línea divisor:** 98% del ancho total

## Personalización

### Crear un Nuevo Banner

Si necesitas crear un banner para una nueva sección, usa `banner-readme-template.svg` como punto de partida:

1. Abre `banner-readme-template.svg` en un editor de texto
2. Personaliza los siguientes elementos:
   - Reemplaza `Section Title` con el nombre de tu sección
   - Actualiza la descripción
   - Cambia el valor de `TYPE` en el badge
   - Actualiza la lista de tecnologías en el footer
   - Modifica la ruta del README

3. Guarda como `seccion-readme.svg`

### Ejemplo de Personalización

```xml
<!-- Título -->
<text x="40" y="100" class="title">Tu Sección</text>

<!-- Descripción -->
<text x="40" y="160" class="description">Tu descripción aquí</text>
<text x="40" y="195" class="description">Segunda línea si es necesaria</text>

<!-- Tipo -->
<text x="1150" y="60" text-anchor="end" class="type-badge" opacity="0.3">TIPO</text>

<!-- Footer -->
<text x="40" y="348" class="footer-text">Tech1 • Tech2 • Tech3  |  seccion/README.md</text>
```

## Visualización en GitHub

Los banners SVG se renderizan automáticamente en GitHub cuando se incluyen en Markdown:

```markdown
![Descripción](path/to/banner.svg)
```

- Los SVG se muestran en tamaño completo por defecto
- Se renderiza en modo claro (light mode) automáticamente
- Compatible con dark mode a través de CSS personalizado (si es necesario)

## Mantenimiento

### Actualizar Tecnologías

Si cambian las dependencias de una sección:

1. Edita el banner SVG correspondiente
2. Actualiza la sección de tecnologías en el footer
3. Mantén separadores con " • " entre tecnologías
4. Usa separador " | " entre tecnologías y ruta del README

### Agregar Nuevas Secciones

Cuando se agreguen nuevas carpetas al proyecto:

1. Crea un nuevo SVG basado en `banner-readme-template.svg`
2. Documenta el banner en `EXAMPLES.md`
3. Integra el banner en el README de la nueva sección
4. Actualiza este archivo con la nueva entrada

## Ejemplos de Uso

Ver archivo `EXAMPLES.md` para:
- Ejemplos de integración en cada README
- Capturas de pantalla de cómo se ven los banners
- Variaciones de diseño (si aplica)
- Troubleshooting visual

## Notas

- **Formato SVG:** Todos los banners están en SVG puro (sin importar imágenes externas)
- **Fuentes:** Se usan Google Fonts (Inter) cargadas desde CDN
- **Responsividad:** Los banners son de tamaño fijo (1200×400px) — no son responsive
- **Versionado:** Los cambios de diseño deben incrementar el número de versión en los nombres de archivos si se necesita compatibilidad hacia atrás

## Referencias

- **Ubicación:** `/mnt/disco2/cjhirashi-data/proyectos/mcp-server/assets/readme-banners/`
- **Servidor README:** `../../server/README.md`
- **Frontend README:** `../../frontend/README.md`
- **Docs README:** `../../docs/README.md`

---

**Última actualización:** 2026-08-15  
**Diseño:** Sistema de banners dinámicos para documentación técnica  
**Estándar:** Ecosystem cjhirashi — Banners con gradiente Cyan-600
