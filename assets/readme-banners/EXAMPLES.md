# Ejemplos de Uso — Banners README

_Guía práctica con ejemplos de cómo integrar los banners en los READMEs de cada sección._

## 1. Integración en Server README

### Ubicación
Archivo: `server/README.md`

### Código Markdown Completo

```markdown
![Server README](../../assets/readme-banners/server-readme.svg)

# Server

MCP Tools Server basado en FastMCP que expone herramientas para generar documentos profesionales en PDF.

## 🔧 Tecnologías

- **FastMCP** — Framework para Model Context Protocol
- **WeasyPrint** — Renderizado de PDF desde HTML/CSS
- **Jinja2** — Motor de plantillas para HTML
- **Python 3.11** — Runtime
- **Docker** — Containerización
- **Uvicorn** — Servidor HTTP asincrónico

## 📋 Descripción

El servidor implementa dos herramientas MCP:

- `crear_cv_pdf()` — Genera CVs en PDF a partir de JSON
- `crear_cover_letter_pdf()` — Genera cartas de presentación en PDF

...resto del contenido...
```

### Path de la Imagen

Desde `server/README.md` al banner:
```
../../assets/readme-banners/server-readme.svg
```

**Explicación:**
- `../../` — Sube dos niveles (server → mcp-server)
- `assets/readme-banners/server-readme.svg` — Ruta al banner

---

## 2. Integración en Frontend README

### Ubicación
Archivo: `frontend/README.md`

### Código Markdown Completo

```markdown
![Frontend README](../../assets/readme-banners/frontend-readme.svg)

# Frontend

Interfaz web moderna para interactuar con el MCP Tools Server y descargar documentos generados.

## 🚀 Stack Tecnológico

- **React 18** — Librería UI
- **TypeScript** — Tipado estático
- **Tailwind CSS** — Utilidades de estilo
- **shadcn/ui** — Componentes accesibles
- **Vite** — Build tool ultrarrápido
- **Axios** — Cliente HTTP

## 📖 Características

- Interfaz responsiva y moderna
- Generación de CVs con vista previa en tiempo real
- Descarga de PDFs generados
- Validación de formularios
- Integración SSE con servidor MCP

...resto del contenido...
```

### Path de la Imagen

Desde `frontend/README.md` al banner:
```
../../assets/readme-banners/frontend-readme.svg
```

---

## 3. Integración en Docs README

### Ubicación
Archivo: `docs/README.md`

### Código Markdown Completo

```markdown
![Documentation README](../../assets/readme-banners/docs-readme.svg)

# Documentación

Centro completo de información para desarrolladores y usuarios del proyecto MCP Server.

## 📚 Secciones

- **Getting Started** — Guía de inicio rápido
- **API Reference** — Documentación de herramientas MCP
- **Configuración** — Setup y variables de entorno
- **Troubleshooting** — Solución de problemas comunes
- **Arquitectura** — Diagramas y flujos de datos

## 🎯 Para Nuevos Desarrolladores

1. [Comienza aquí](./getting-started/README.md)
2. Lee la [arquitectura del proyecto](../README.md#-arquitectura)
3. Consulta la [referencia de API](./api/README.md)

...resto del contenido...
```

### Path de la Imagen

Desde `docs/README.md` al banner:
```
../../assets/readme-banners/docs-readme.svg
```

---

## Estructura Actual de READMEs

```
mcp-server/
├── README.md                                    (con banner principal)
├── server/
│   └── README.md                                (con server-readme.svg)
├── frontend/
│   └── README.md                                (con frontend-readme.svg)
├── docs/
│   └── README.md                                (con docs-readme.svg)
└── assets/
    └── readme-banners/
        ├── README.md                            (este sistema)
        ├── EXAMPLES.md                          (este archivo)
        ├── banner-readme-template.svg
        ├── server-readme.svg
        ├── frontend-readme.svg
        └── docs-readme.svg
```

---

## Variaciones de Diseño

### Texto Multilinea en Descripción

Para descripciones más largas, usa dos líneas `<text>`:

```xml
<text x="40" y="160" class="description">Primera línea de descripción</text>
<text x="40" y="195" class="description">Segunda línea de descripción</text>
```

Ajusta los valores de `y`:
- Primera línea: `y="160"`
- Segunda línea: `y="195"` (incremento de 35px)
- Tercera línea (si aplica): `y="230"`

### Footer Multilinea

Para footer con tecnologías complejas:

```xml
<!-- Opción 1: Todo en una línea (recomendado) -->
<text x="40" y="348" class="footer-text">Tech1 • Tech2 • Tech3 • Tech4 • Tech5  |  section/README.md</text>

<!-- Opción 2: Dos líneas (si tecnologías no caben) -->
<text x="40" y="348" class="footer-text">Tech1 • Tech2 • Tech3 • Tech4</text>
<text x="40" y="365" class="footer-text">Tech5 • Tech6  |  section/README.md</text>
```

### Ajustar Línea Decorativa

La línea decorativa bajo la descripción se posiciona en `y="220"`:

```xml
<line x1="40" y1="220" x2="320" y2="220" stroke="white" stroke-width="2" opacity="0.6" />
```

Para ajustar su posición según líneas de descripción:
- Descripción 1 línea: `y1="185"`
- Descripción 2 líneas: `y1="220"`
- Descripción 3 líneas: `y1="255"`

---

## Visualización en GitHub

### Cómo se ve en modo light (GitHub por defecto)

```
┌──────────────────────────────────────────────────────┐
│  [Banner Cyan-Teal con texto blanco]                │
│  Título Grande                                       │
│  Descripción clara                                   │
│  ──────────────                                      │
│  [Footer gris con tecnologías]                      │
└──────────────────────────────────────────────────────┘
```

### Cómo se ven en navegadores

- **Ancho:** Se escala para ocupar el 100% del ancho del contenedor (máximo 1200px)
- **Alto:** Se mantiene la proporción 3:1
- **Fuentes:** Se importan desde Google Fonts (no requiere instalación local)

---

## Checklist de Integración

Al integrar un banner en un README:

- [ ] Imagen referencia correcta (`../../assets/readme-banners/XXX-readme.svg`)
- [ ] Alt text descriptivo (`![Descripción]`)
- [ ] Banner aparece en GitHub sin errores
- [ ] Título en Markdown coincide con el del banner
- [ ] Descripción en README amplía la del banner
- [ ] Ruta en footer del banner es correcta

---

## Troubleshooting

### Banner no se visualiza

**Problema:** El banner aparece como icono quebrado o no carga

**Soluciones:**
1. Verifica que la ruta sea correcta (relativa a la ubicación del README)
2. Asegúrate de que el archivo SVG existe en la ruta especificada
3. Revisa que el nombre del archivo sea exacto (incluyendo mayúsculas/minúsculas)

Ejemplo de ruta correcta desde `server/README.md`:
```markdown
![Server README](../../assets/readme-banners/server-readme.svg)
```

### Texto truncado o cortado

**Problema:** El texto de la descripción se ve cortado

**Solución:** Verifica los valores de `x` y el ancho del contenedor. Deben estar dentro del viewBox (0-1200):

```xml
<!-- Correcto -->
<text x="40" y="160" class="description">Texto aquí</text>

<!-- Incorrecto (fuera del canvas) -->
<text x="1300" y="160" class="description">Texto aquí</text>
```

### Footer no se ve completamente

**Problema:** La ruta del README está cortada en el footer

**Solución:** Usa una línea en lugar de dos. Si el texto es muy largo, considera:

1. Acortar nombres de tecnologías
2. Usar abreviaturas (e.g., "TS" en lugar de "TypeScript")
3. Dividir en dos líneas si es necesario

---

## Automatización (Futuro)

### Script Python para Generar Banners

Idea para automatizar la generación de nuevos banners:

```python
def create_readme_banner(
    title: str,
    description: str,
    type_badge: str,
    technologies: list[str],
    readme_path: str,
    output_file: str
):
    """
    Genera un SVG de banner README personalizado.
    
    Args:
        title: Título del banner (ej: "Server")
        description: Descripción (1-2 líneas)
        type_badge: Tipo (ej: "SERVER", "FRONTEND")
        technologies: Lista de tecnologías (["Tech1", "Tech2"])
        readme_path: Ruta del README (ej: "server/README.md")
        output_file: Archivo SVG de salida
    """
    # Implementación aquí
    pass
```

---

## Referencias

- **Sistema de banners:** `assets/readme-banners/README.md`
- **Plantilla base:** `assets/readme-banners/banner-readme-template.svg`
- **Estándares cjhirashi:** Gradiente Cyan-600 (#06B6D4 → #0a5f75)

---

**Última actualización:** 2026-08-15  
**Tipo:** Documentación de ejemplos e integración  
**Formato:** Markdown + SVG
