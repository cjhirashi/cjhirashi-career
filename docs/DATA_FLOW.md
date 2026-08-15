# Flujo de Datos — MCP Tools Server

_Análisis detallado del flujo de datos en cada operación del servidor._

## Flujo de Generación de CV

Proceso completo desde solicitud del cliente hasta PDF guardado:

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#06B6D4',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#0891B2',
    'secondaryColor': '#10B981',
    'tertiaryColor': '#A855F7',
    'lineColor': '#059669',
    'fontSize': '13px'
  }
}}%%

graph TD
  A["📋 Cliente Prepara Datos<br/>JSON: nombre, email, experiencia, etc."] -->|"JSON String"| B["🔄 Cliente Envía Solicitud<br/>HTTP POST /sse<br/>crear_cv_pdf"]
  B -->|"SSE"| C["📩 FastMCP Recibe<br/>Parámetros:<br/>datos_cv_json, nombre_archivo"]
  C -->|"Parsea"| D["✅ Validación JSON<br/>Convierte string a dict"]
  D -->|"dict datos"| E["🔧 cv_generator.generar_cv"]
  E -->|"Acceso"| F["📄 Carga Plantilla<br/>cv_template.html"]
  F -->|"Template Object"| G["🎨 Jinja2.render<br/>Inserta variables en HTML"]
  G -->|"HTML String"| H["🖨️ WeasyPrint.write_pdf<br/>CSS Paged Media<br/>Renderiza a PDF"]
  H -->|"PDF Bytes"| I["💾 Escribe Archivo<br/>/mcp-outputs/cvs/<br/>nombre_archivo.pdf"]
  I -->|"Éxito"| J["✨ Retorna Mensaje<br/>Éxito: PDF en /path"]
  J -->|"SSE Response"| K["📥 Cliente Recibe<br/>Descarga PDF"]

  style A fill:#A855F7,stroke:#9333EA,color:#fff
  style B fill:#A855F7,stroke:#9333EA,color:#fff
  style C fill:#10B981,stroke:#059669,color:#fff
  style D fill:#10B981,stroke:#059669,color:#fff
  style E fill:#10B981,stroke:#059669,color:#fff
  style F fill:#f0f9fc,stroke:#059669,color:#333
  style G fill:#f0f9fc,stroke:#059669,color:#333
  style H fill:#f0f9fc,stroke:#059669,color:#333
  style I fill:#06B6D4,stroke:#0891B2,color:#fff
  style J fill:#10B981,stroke:#059669,color:#fff
  style K fill:#A855F7,stroke:#9333EA,color:#fff
```

### Puntos Críticos del Flujo

| Paso | Componente | Entrada | Salida | Error Posible |
|------|-----------|---------|--------|---------------|
| 1 | Cliente | Datos CV | JSON string | Validación cliente-side |
| 2 | FastMCP | JSON string | dict Python | JSON inválido |
| 3 | cv_generator | dict | Template | Error de parseo |
| 4 | Jinja2 | Template + datos | HTML string | Variable faltante |
| 5 | WeasyPrint | HTML | PDF bytes | CSS inválido, fuente faltante |
| 6 | File System | PDF bytes | archivo guardado | Permisos, espacio en disco |
| 7 | Cliente | Ruta archivo | Descarga | Red |

---

## Flujo de Generación de Cover Letter

Similar al CV, con plantilla específica:

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

graph TD
  A["👥 Cliente Prepara Datos<br/>nombre, empresa, puesto,<br/>fecha, carta personalizada"] -->|"JSON"| B["📨 Solicitud MCP<br/>crear_cover_letter_pdf"]
  B -->|"Parámetros"| C["🟢 FastMCP Route"]
  C -->|"Llama"| D["🔧 cover_generator.generar_cover"]
  D -->|"Lee"| E["📄 cover_template.html"]
  E -->|"Jinja2"| F["📝 Renderiza Plantilla<br/>Inserta datos de carta"]
  F -->|"HTML+CSS"| G["📄 WeasyPrint Process<br/>Lee CSS desde style_1.css"]
  G -->|"PDF Bytes"| H["💾 Guarda PDF<br/>/mcp-outputs/cover_letters/"]
  H -->|"Success"| I["✅ Retorna Ruta<br/>cover_johndoe_2026.pdf"]
  I -->|"Download"| J["📥 Cliente Descarga"]

  style A fill:#A855F7,stroke:#9333EA,color:#fff
  style B fill:#A855F7,stroke:#9333EA,color:#fff
  style C fill:#10B981,stroke:#059669,color:#fff
  style D fill:#10B981,stroke:#059669,color:#fff
  style E fill:#f0f9fc,stroke:#059669,color:#333
  style F fill:#f0f9fc,stroke:#059669,color:#333
  style G fill:#f0f9fc,stroke:#059669,color:#333
  style H fill:#06B6D4,stroke:#0891B2,color:#fff
  style I fill:#10B981,stroke:#059669,color:#fff
  style J fill:#A855F7,stroke:#9333EA,color:#fff
```

---

## Estructuras de Datos

### JSON de Entrada (CV)

```json
{
  "nombre": "Juan Pérez",
  "email": "juan@ejemplo.com",
  "telefono": "+34 600 123 456",
  "titulo_profesional": "Senior Backend Engineer",
  "resumen": "10 años de experiencia en desarrollo backend...",
  "experiencia": [
    {
      "empresa": "Tech Corp",
      "puesto": "Senior Engineer",
      "fechas": "2020 - 2026",
      "descripcion": "Desarrollo de microservicios..."
    }
  ],
  "educacion": [
    {
      "institucion": "Universidad",
      "titulo": "Licenciatura en Informática",
      "año": "2015"
    }
  ],
  "habilidades": ["Python", "JavaScript", "Docker", "Kubernetes"]
}
```

### JSON de Entrada (Cover Letter)

```json
{
  "nombre": "Juan Pérez",
  "fecha": "2026-08-15",
  "empresa": "Innovate Inc",
  "posicion": "Backend Developer",
  "contacto_empresa": "hr@innovate.com",
  "saludo": "Dear Hiring Manager,",
  "cuerpo": "I am writing to express my interest...",
  "despedida": "Sincerely, Juan Pérez"
}
```

### Estructura Interna Python

```python
# CV Generator
datos_cv = {
    'nombre': 'Juan Pérez',
    'email': 'juan@ejemplo.com',
    # ... más campos
}

# Template render
html = jinja_template.render(**datos_cv)  # Interpola variables

# WeasyPrint
pdf = weasyprint.HTML(
    string=html,
    base_url=templates_dir  # Para resolver CSS relativo
).write_pdf()
```

---

## Transformaciones de Datos

### Cadena de Transformación: JSON → HTML → PDF

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#06B6D4',
    'secondaryColor': '#10B981',
    'tertiaryColor': '#A855F7'
  }
}}%%

graph LR
  JSON["<b>Formato JSON</b><br/>String (cliente)<br/>Data de entrada"] -->|"json.loads()"| DICT["<b>Dict Python</b><br/>Estructura de datos<br/>Variables"]
  DICT -->|"template.render(**dict)"| HTML["<b>HTML String</b><br/>HTML + CSS<br/>Estructura visual"]
  HTML -->|"WeasyPrint.write_pdf()"| PDF["<b>PDF Bytes</b><br/>Documento PDF<br/>Formato final"]
  PDF -->|"File Write"| FILE["<b>Archivo PDF</b><br/>En disco<br/>Descargable"]

  style JSON fill:#A855F7,stroke:#9333EA,color:#fff
  style DICT fill:#10B981,stroke:#059669,color:#fff
  style HTML fill:#f0f9fc,stroke:#059669,color:#333
  style PDF fill:#06B6D4,stroke:#0891B2,color:#fff
  style FILE fill:#06B6D4,stroke:#0891B2,color:#fff
```

### Detalle de Transformación HTML → PDF

WeasyPrint aplica las siguientes transformaciones:

1. **Parseo HTML**: Valida estructura HTML
2. **Resolución de URLs**: Encuentra CSS, imágenes usando `base_url`
3. **Aplicación de CSS**: 
   - Cascada de estilos (inline → style tags → external CSS)
   - Media queries (@media print)
   - Paged media (@page rules)
4. **Renderizado de contenido**:
   - Textos (con fuentes)
   - Imágenes (rasterización)
   - Tablas (layout)
5. **Paginación**:
   - Saltos de página (@page, page-break)
   - Márgenes definidos en CSS
6. **Generación PDF**:
   - Compresión de imágenes
   - Metadatos (título, autor)
   - Compresión de streams
7. **Escritura a disco**: Bytes PDF → archivo

---

## Manejo de Errores

### Posibles Excepciones y Recuperación

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#06B6D4',
    'secondaryColor': '#10B981',
    'tertiaryColor': '#A855F7'
  }
}}%%

graph TD
  START["Solicitud<br/>crear_cv_pdf"] -->|"Try"| JSON_PARSE["json.loads"]
  JSON_PARSE -->|"JSONDecodeError"| ERR1["❌ Error: JSON inválido"]
  JSON_PARSE -->|"OK"| LOAD["Carga plantilla"]
  LOAD -->|"FileNotFoundError"| ERR2["❌ Error: Plantilla no existe"]
  LOAD -->|"OK"| RENDER["Jinja2.render"]
  RENDER -->|"UndefinedError"| ERR3["❌ Error: Variable faltante"]
  RENDER -->|"OK"| WEASY["WeasyPrint.write_pdf"]
  WEASY -->|"WeasyPrintError"| ERR4["❌ Error: CSS inválido"]
  WEASY -->|"OK"| WRITE["File write"]
  WRITE -->|"IOError"| ERR5["❌ Error: Permisos/Espacio"]
  WRITE -->|"OK"| SUCCESS["✅ PDF Guardado"]

  ERR1 -->|"except"| RETURN1["return Error message"]
  ERR2 -->|"except"| RETURN2["return Error message"]
  ERR3 -->|"except"| RETURN3["return Error message"]
  ERR4 -->|"except"| RETURN4["return Error message"]
  ERR5 -->|"except"| RETURN5["return Error message"]
  SUCCESS -->|"return"| SUCCESS_MSG["return Success message"]

  RETURN1 --> CLI["🔴 Cliente recibe error"]
  RETURN2 --> CLI
  RETURN3 --> CLI
  RETURN4 --> CLI
  RETURN5 --> CLI
  SUCCESS_MSG --> LOG["✅ Cliente descarga"]

  style ERR1 fill:#fca5a5,color:#fff
  style ERR2 fill:#fca5a5,color:#fff
  style ERR3 fill:#fca5a5,color:#fff
  style ERR4 fill:#fca5a5,color:#fff
  style ERR5 fill:#fca5a5,color:#fff
  style SUCCESS fill:#10B981,stroke:#059669,color:#fff
  style SUCCESS_MSG fill:#10B981,stroke:#059669,color:#fff
```

### Códigos de Error Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `JSON decode error` | JSON inválido en entrada | Validar JSON antes de enviar |
| `Template not found` | Plantilla no existe | Verificar que cv_template.html existe |
| `UndefinedError` | Variable en plantilla no definida | Agregar variable faltante en JSON |
| `CSS parse error` | CSS inválido en style_1.css | Validar sintaxis CSS |
| `Permission denied` | No puede escribir en `/mcp-outputs/` | Verificar permisos de carpeta |
| `No space left` | Disco lleno | Limpiar archivos antiguos |
| `Image not found` | Referencia a imagen que no existe | Usar rutas relativas correctas |

---

## Optimizaciones de Flujo

### Caché de Plantillas (Propuesto)

```python
# Actual: Carga plantilla en cada solicitud
env = Environment(loader=FileSystemLoader(templates_dir))
template = env.get_template("cv_template.html")

# Propuesto: Caché global
TEMPLATE_CACHE = {}
template = TEMPLATE_CACHE.get("cv_template.html") or env.get_template("cv_template.html")
TEMPLATE_CACHE["cv_template.html"] = template
```

**Beneficio**: Reduce I/O de disco, tiempo de renderizado ~10-20%

### Paralelización (Propuesto)

```python
# Actual: Secuencial
pdf1 = generar_cv(datos1)
pdf2 = generar_cv(datos2)

# Propuesto: Paralelo con ThreadPool
with ThreadPoolExecutor(max_workers=4) as executor:
    pdf1 = executor.submit(generar_cv, datos1)
    pdf2 = executor.submit(generar_cv, datos2)
```

**Beneficio**: Procesar múltiples documentos simultáneamente

---

## Referencias

- [ARCHITECTURE.md](./ARCHITECTURE.md) — Diagramas arquitectónicos
- [NETWORK_TOPOLOGY.md](./NETWORK_TOPOLOGY.md) — Topología de red
- [COLOR_PALETTE.md](../COLOR_PALETTE.md) — Paleta de colores usada

**Actualizado**: 2026-08-15
