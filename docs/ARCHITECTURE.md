# Arquitectura del Sistema — MCP Tools Server

_Diagramas y descripción de la arquitectura completa del sistema MCP Tools Server._

## Diagrama de Arquitectura General

```mermaid
graph TB
  subgraph client["👤 CLIENTE"]
    UI["🎨 Frontend UI<br/>React + TypeScript"]
  end

  subgraph server["🟢 SERVIDOR MCP"]
    FASTMCP["⚡ FastMCP Server<br/>server.py"]
    CV_GEN["📄 CV Generator<br/>cv_generator.py"]
    COVER_GEN["📧 Cover Generator<br/>cover_generator.py"]
    TEMPLATES["🎯 Plantillas Jinja2<br/>+ CSS Styles"]
  end

  subgraph storage["💾 ALMACENAMIENTO"]
    PDF_OUTPUT["📦 Volumen Persistente<br/>/mcp-outputs/"]
    CV_DIR["📁 CVs/"]
    COVER_DIR["📁 Cover Letters/"]
  end

  subgraph external["🔗 RENDERIZADO"]
    WEASYPRINT["🖨️ WeasyPrint<br/>HTML → PDF"]
    JINJA["🧩 Jinja2<br/>Template Engine"]
  end

  UI -->|HTTP/SSE<br/>:8002| FASTMCP
  FASTMCP -->|crear_cv_pdf| CV_GEN
  FASTMCP -->|crear_cover_letter| COVER_GEN
  CV_GEN -->|load| TEMPLATES
  COVER_GEN -->|load| TEMPLATES
  CV_GEN -->|render| WEASYPRINT
  COVER_GEN -->|render| WEASYPRINT
  WEASYPRINT -->|write| PDF_OUTPUT
  PDF_OUTPUT --> CV_DIR
  PDF_OUTPUT --> COVER_DIR
  CV_GEN -->|use| JINJA
  COVER_GEN -->|use| JINJA

  %% Estilos - Morado (Cliente)
  style UI fill:#A855F7,stroke:#7C1FA1,stroke-width:3px,color:#fff

  %% Estilos - Verde (Servidor - gradiente oscuro)
  style FASTMCP fill:#10B981,stroke:#065F46,stroke-width:3px,color:#fff
  style CV_GEN fill:#059669,stroke:#047857,stroke-width:3px,color:#fff
  style COVER_GEN fill:#0B8A5E,stroke:#065F46,stroke-width:3px,color:#fff
  style TEMPLATES fill:#107569,stroke:#065F46,stroke-width:3px,color:#fff

  %% Estilos - Cyan (Almacenamiento)
  style PDF_OUTPUT fill:#06B6D4,stroke:#0369A1,stroke-width:3px,color:#fff
  style CV_DIR fill:#0891B2,stroke:#0369A1,stroke-width:3px,color:#fff
  style COVER_DIR fill:#0891B2,stroke:#0369A1,stroke-width:3px,color:#fff

  %% Estilos - Gris (Dependencias)
  style WEASYPRINT fill:#9CA3AF,stroke:#4B5563,stroke-width:3px,color:#fff
  style JINJA fill:#9CA3AF,stroke:#4B5563,stroke-width:3px,color:#fff
```

## Descripción de Componentes

### Cliente (Morado - #A855F7)

**Frontend UI**: Aplicación React basada en TypeScript con Tailwind CSS. Proporciona:
- Formulario para ingresar datos del CV
- Formulario para ingresar datos de cover letter
- Visualización y descarga de PDFs generados
- Interfaz responsiva y moderna

**Comunicación**: Envía solicitudes HTTP/SSE al servidor MCP en puerto 8002.

### Servidor MCP (Verde - #10B981)

**FastMCP Server** (`server.py`): Punto de entrada central que expone dos herramientas MCP:
- `crear_cv_pdf(datos_cv_json, nombre_archivo)` → Genera CV en PDF
- `crear_cover_letter_pdf(datos_cover_json, nombre_archivo)` → Genera cover letter en PDF

**CV Generator** (`cv_generator.py`): Lógica de generación de CV:
1. Parsea JSON de entrada
2. Carga plantilla `cv_template.html`
3. Renderiza Jinja2 con datos
4. Aplica estilos CSS (paged media)
5. Convierte a PDF con WeasyPrint
6. Guarda en `/mcp-outputs/cvs/`

**Cover Generator** (`cover_generator.py`): Lógica de generación de cover letter:
1. Parsea JSON de entrada
2. Carga plantilla `cover_template.html`
3. Renderiza Jinja2 con datos
4. Aplica estilos CSS (paged media)
5. Convierte a PDF con WeasyPrint
6. Guarda en `/mcp-outputs/cover_letters/`

**Plantillas y Estilos**: 
- `cv_template.html`: Estructura del CV en HTML/Jinja2
- `cover_template.html`: Estructura de cover letter en HTML/Jinja2
- `css/style_1.css`: Estilos compartidos con media queries para impresión

### Almacenamiento (Cyan - #06B6D4)

**Volumen Persistente**: `/mnt/disco2/cjhirashi-data/mcp-outputs/`
- **CVs**: Contiene todos los PDFs de CV generados
- **Cover Letters**: Contiene todos los PDFs de cover letters generados

Los archivos persisten entre reinicios del contenedor y están accesibles desde el host.

### Dependencias Externas (Gris - #f0f9fc)

**WeasyPrint**: Motor de renderización HTML → PDF
- Soporta CSS paged media (@page, @page:first, márgenes, etc.)
- Resuelve base URLs para cargar CSS e imágenes
- Genera PDFs profesionales con layout exacto

**Jinja2**: Motor de plantillas HTML
- Permite variables, loops, condicionales en plantillas
- Aplica filtros de formato
- Integración directa con Python

---

## Flujo de Datos Completo

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#06B6D4',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#0891B2',
    'secondaryColor': '#10B981',
    'tertiaryColor': '#A855F7',
    'lineColor': '#059669'
  }
}}%%

sequenceDiagram
  participant UI as Frontend (Morado)
  participant MCP as FastMCP (Verde)
  participant GEN as Generator (Verde)
  participant JINJA as Jinja2 (Gris)
  participant WP as WeasyPrint (Gris)
  participant FS as File System (Cyan)

  UI->>MCP: POST /sse crear_cv_pdf(datos_json, archivo)
  activate MCP
  MCP->>GEN: parse_json(datos_json)
  activate GEN
  GEN->>JINJA: template.render(**datos)
  activate JINJA
  JINJA-->>GEN: html_string
  deactivate JINJA
  GEN->>WP: generate_pdf(html_string, base_url)
  activate WP
  WP-->>GEN: pdf_bytes
  deactivate WP
  GEN->>FS: write(archivo, pdf_bytes)
  activate FS
  FS-->>GEN: ok
  deactivate FS
  GEN-->>MCP: "Éxito: PDF en /path/to/archivo"
  deactivate GEN
  MCP-->>UI: SSE response + success
  deactivate MCP
  UI->>FS: GET /mcp-outputs/cvs/archivo
  FS-->>UI: PDF file (descarga)
```

---

## Topología de Red (Docker)

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#06B6D4',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#0891B2',
    'secondaryColor': '#10B981',
    'tertiaryColor': '#A855F7'
  }
}}%%

graph LR
  subgraph host["🖥️ Host Machine"]
    PORT["Port 8002<br/>(HTTP)"]
    MOUNT["Mount Point<br/>/mnt/disco2/cjhirashi-data/<br/>mcp-outputs"]
  end

  subgraph docker["🐳 Docker Container"]
    CONT["Container: mcp_tools_server<br/>Python 3.11 + FastMCP"]
    INTERNAL["Port 8000<br/>(Uvicorn)"]
    VOL["Volume Mount<br/>/app/outputs"]
  end

  PORT -->|"Port Mapping<br/>8002:8000"| INTERNAL
  INTERNAL -->|"Listens on"| CONT
  MOUNT <-->|"Volume Bind"| VOL
  CONT -->|"Writes PDFs"| VOL

  classDef hostStyle fill:#f0f9fc,stroke:#059669,stroke-width:2px,color:#333
  classDef containerStyle fill:#10B981,stroke:#059669,stroke-width:2px,color:#fff
  classDef portStyle fill:#A855F7,stroke:#9333EA,stroke-width:2px,color:#fff
  classDef volumeStyle fill:#06B6D4,stroke:#0891B2,stroke-width:2px,color:#fff

  class host hostStyle
  class CONT,INTERNAL containerStyle
  class PORT portStyle
  class MOUNT,VOL volumeStyle
```

---

## Decisiones de Diseño Clave

### 1. FastMCP como Framework

**Por qué**: 
- Abstracción clara del protocolo MCP
- Decoradores `@mcp.tool()` para exponer funciones como herramientas
- Manejo automático de SSE
- Integración sencilla con Uvicorn

**Alternativas consideradas**:
- Implementar MCP manual (más control, más código)
- Usar servidor genérico (menos específico)

### 2. Jinja2 + WeasyPrint para PDF

**Por qué**:
- Jinja2: Plantillas HTML dinámicas, fácil de mantener
- WeasyPrint: CSS paged media (print media queries), control total sobre layout
- Combinación permite diseños profesionales y reproducibles

**Flujo**:
```
JSON → Jinja2 render → HTML → WeasyPrint → PDF
```

### 3. Volúmenes Persistentes

**Por qué**:
- Los PDFs generados persisten entre reinicios
- Accesibles desde el host para descarga/archivo
- Separación clara entre contenedor y host

**Ubicación**: `/mnt/disco2/cjhirashi-data/mcp-outputs/`

### 4. Separación de Generadores

**Por qué**:
- Cada documento tiene lógica independiente
- Plantillas separadas (cv_template.html, cover_template.html)
- Fácil de mantener y extender
- Posibilidad de agregar nuevos tipos de documentos

### 5. CSS Paged Media

**Por qué**:
- Control preciso de márgenes, saltos de página
- Estilos específicos para primera página (`@page:first`)
- Media queries para impresión (@media print)
- Resultado reproducible y profesional

---

## Escalabilidad y Mejoras Futuras

### Escalabilidad Actual

- **Procesamiento**: Secuencial (una solicitud a la vez por instancia)
- **Múltiples instancias**: Soportadas detrás de load balancer
- **Almacenamiento**: Limitado por espacio en disco host

### Mejoras Propuestas

1. **Cola de trabajos** (Celery + Redis)
   - Procesar PDFs en background
   - Notificar cuando esté listo
   - Mejorar experiencia de usuario

2. **Caché de plantillas compiladas**
   - Cachear Jinja2 templates
   - Reducir tiempo de renderizado

3. **Generación paralela**
   - Procesar múltiples PDFs simultáneamente
   - Thread pool o async/await

4. **Soporte de múltiples plantillas**
   - Parámetro `template_name` en llamadas
   - Biblioteca de diseños

5. **Firma digital y marcas de agua**
   - Agregar seguridad a documentos
   - Personalización adicional

---

## Referencias

- [COLOR_PALETTE.md](../COLOR_PALETTE.md) — Paleta de colores del proyecto
- [CLAUDE.md](../CLAUDE.md) — Guía de desarrollo
- [Guia PDF WeasyPrint y CSS paged media.md](../server/Guia%20PDF%20WeasyPrint%20y%20CSS%20paged%20media.md) — Detalles técnicos de PDF

**Diagrama actualizado**: 2026-08-15
