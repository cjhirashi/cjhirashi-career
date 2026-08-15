# Flujo de Datos — MCP Tools Server

_Análisis detallado del flujo de datos en cada operación del servidor._

## Flujo de Generación de CV

Proceso completo desde solicitud del cliente hasta PDF guardado:

```mermaid
graph TD
  A["📋 Cliente Prepara Datos<br/>JSON: nombre, email, experiencia"] -->|"JSON String"| B["🔄 Cliente Envía Solicitud<br/>HTTP POST /sse<br/>crear_cv_pdf"]
  B -->|"SSE"| C["📩 FastMCP Recibe<br/>Parámetros"]
  C -->|"Parsea"| D["✅ Validación JSON<br/>string → dict"]
  D -->|"dict datos"| E["🔧 cv_generator.generar_cv<br/>Procesa datos"]
  E -->|"Acceso"| F["📄 Carga Plantilla<br/>cv_template.html"]
  F -->|"Template"| G["🎨 Jinja2.render<br/>Variables en HTML"]
  G -->|"HTML"| H["🖨️ WeasyPrint.write_pdf<br/>CSS → PDF"]
  H -->|"PDF Bytes"| I["💾 Escribe Archivo<br/>/mcp-outputs/cvs/"]
  I -->|"Éxito"| J["✨ Retorna Mensaje<br/>Éxito"]
  J -->|"SSE Response"| K["📥 Cliente Recibe<br/>Descarga PDF"]

  %% MORADO (Cliente/Entrada)
  style A fill:#A855F7,stroke:#9333EA,stroke-width:3px,color:#fff
  style B fill:#9333EA,stroke:#7C1FA1,stroke-width:3px,color:#fff
  
  %% VERDE CLARO (FastMCP)
  style C fill:#10B981,stroke:#059669,stroke-width:3px,color:#fff
  style D fill:#0FB981,stroke:#059669,stroke-width:3px,color:#fff
  
  %% VERDE OSCURO (Procesamiento)
  style E fill:#059669,stroke:#047857,stroke-width:3px,color:#fff
  
  %% CYAN CLARO (Plantillas)
  style F fill:#06D9FF,stroke:#0891B2,stroke-width:3px,color:#000
  style G fill:#06B6D4,stroke:#0891B2,stroke-width:3px,color:#fff
  
  %% CYAN OSCURO (PDF)
  style H fill:#0891B2,stroke:#0369A1,stroke-width:3px,color:#fff
  style I fill:#0369A1,stroke:#024960,stroke-width:3px,color:#fff
  
  %% VERDE (Respuesta)
  style J fill:#10B981,stroke:#059669,stroke-width:3px,color:#fff
  style K fill:#A855F7,stroke:#9333EA,stroke-width:3px,color:#fff
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
graph TD
  A["👥 Cliente Prepara Datos<br/>nombre, empresa, puesto"] -->|"JSON"| B["📨 Solicitud MCP<br/>crear_cover_letter_pdf"]
  B -->|"Parámetros"| C["🟢 FastMCP Route<br/>Recibe solicitud"]
  C -->|"Llama"| D["🔧 cover_generator<br/>Procesa datos"]
  D -->|"Lee"| E["📄 cover_template.html<br/>Carga plantilla"]
  E -->|"Jinja2"| F["📝 Renderiza Plantilla<br/>Variables en HTML"]
  F -->|"HTML+CSS"| G["🖨️ WeasyPrint<br/>CSS → PDF"]
  G -->|"PDF Bytes"| H["💾 Guarda PDF<br/>/mcp-outputs/cover_letters/"]
  H -->|"Success"| I["✅ Retorna Ruta<br/>cover_johndoe.pdf"]
  I -->|"Download"| J["📥 Cliente Descarga"]

  %% MORADO (Cliente/Entrada)
  style A fill:#A855F7,stroke:#9333EA,stroke-width:3px,color:#fff
  style B fill:#9333EA,stroke:#7C1FA1,stroke-width:3px,color:#fff
  
  %% VERDE (FastMCP/Procesamiento)
  style C fill:#10B981,stroke:#059669,stroke-width:3px,color:#fff
  style D fill:#059669,stroke:#047857,stroke-width:3px,color:#fff
  
  %% CYAN (Plantillas)
  style E fill:#06D9FF,stroke:#0891B2,stroke-width:3px,color:#000
  style F fill:#06B6D4,stroke:#0891B2,stroke-width:3px,color:#fff
  
  %% CYAN OSCURO (PDF)
  style G fill:#0891B2,stroke:#0369A1,stroke-width:3px,color:#fff
  style H fill:#0369A1,stroke:#024960,stroke-width:3px,color:#fff
  
  %% VERDE (Respuesta)
  style I fill:#10B981,stroke:#059669,stroke-width:3px,color:#fff
  style J fill:#A855F7,stroke:#9333EA,stroke-width:3px,color:#fff
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
graph LR
  JSON["<b>JSON</b><br/>String<br/>Cliente"] -->|"json.loads()"| DICT["<b>Dict</b><br/>Datos<br/>Variables"]
  DICT -->|"template.render"| HTML["<b>HTML</b><br/>HTML+CSS<br/>Visual"]
  HTML -->|"WeasyPrint"| PDF["<b>PDF</b><br/>Bytes<br/>Renderizado"]
  PDF -->|"File Write"| FILE["<b>Archivo</b><br/>En disco<br/>Persistente"]

  %% Progresión Morado → Verde → Cyan
  style JSON fill:#A855F7,stroke:#9333EA,stroke-width:2px,color:#fff
  style DICT fill:#10B981,stroke:#059669,stroke-width:2px,color:#fff
  style HTML fill:#06B6D4,stroke:#0891B2,stroke-width:2px,color:#fff
  style PDF fill:#0891B2,stroke:#0369A1,stroke-width:2px,color:#fff
  style FILE fill:#047857,stroke:#065F46,stroke-width:2px,color:#fff
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
graph TD
  START["Solicitud<br/>crear_cv_pdf"] -->|"Try"| JSON_PARSE["json.loads"]
  JSON_PARSE -->|"JSONDecodeError"| ERR1["❌ JSON inválido"]
  JSON_PARSE -->|"OK"| LOAD["Carga plantilla"]
  LOAD -->|"FileNotFoundError"| ERR2["❌ Plantilla no existe"]
  LOAD -->|"OK"| RENDER["Jinja2.render"]
  RENDER -->|"UndefinedError"| ERR3["❌ Variable faltante"]
  RENDER -->|"OK"| WEASY["WeasyPrint.write_pdf"]
  WEASY -->|"WeasyPrintError"| ERR4["❌ CSS inválido"]
  WEASY -->|"OK"| WRITE["File write"]
  WRITE -->|"IOError"| ERR5["❌ Permisos/Espacio"]
  WRITE -->|"OK"| SUCCESS["✅ PDF Guardado"]

  ERR1 -->|"except"| RETURN1["return Error"]
  ERR2 -->|"except"| RETURN2["return Error"]
  ERR3 -->|"except"| RETURN3["return Error"]
  ERR4 -->|"except"| RETURN4["return Error"]
  ERR5 -->|"except"| RETURN5["return Error"]
  SUCCESS -->|"return"| SUCCESS_MSG["return Success"]

  RETURN1 --> CLI["🔴 Error al cliente"]
  RETURN2 --> CLI
  RETURN3 --> CLI
  RETURN4 --> CLI
  RETURN5 --> CLI
  SUCCESS_MSG --> LOG["✅ Cliente descarga"]

  %% Entrada - Morado
  style START fill:#A855F7,stroke:#9333EA,stroke-width:3px,color:#fff
  
  %% Procesamiento - Verde
  style JSON_PARSE fill:#10B981,stroke:#059669,stroke-width:3px,color:#fff
  style LOAD fill:#0FB981,stroke:#059669,stroke-width:3px,color:#fff
  style RENDER fill:#059669,stroke:#047857,stroke-width:3px,color:#fff
  style WEASY fill:#047857,stroke:#065F46,stroke-width:3px,color:#fff
  style WRITE fill:#10B981,stroke:#059669,stroke-width:3px,color:#fff
  style SUCCESS fill:#047857,stroke:#065F46,stroke-width:3px,color:#fff
  
  %% Errores - Rojo
  style ERR1 fill:#EF4444,stroke:#DC2626,stroke-width:3px,color:#fff
  style ERR2 fill:#EF4444,stroke:#DC2626,stroke-width:3px,color:#fff
  style ERR3 fill:#EF4444,stroke:#DC2626,stroke-width:3px,color:#fff
  style ERR4 fill:#EF4444,stroke:#DC2626,stroke-width:3px,color:#fff
  style ERR5 fill:#EF4444,stroke:#DC2626,stroke-width:3px,color:#fff
  
  %% Recuperación - Naranja
  style RETURN1 fill:#D97706,stroke:#B45309,stroke-width:2px,color:#fff
  style RETURN2 fill:#D97706,stroke:#B45309,stroke-width:2px,color:#fff
  style RETURN3 fill:#D97706,stroke:#B45309,stroke-width:2px,color:#fff
  style RETURN4 fill:#D97706,stroke:#B45309,stroke-width:2px,color:#fff
  style RETURN5 fill:#D97706,stroke:#B45309,stroke-width:2px,color:#fff
  
  %% Resultados
  style CLI fill:#DC2626,stroke:#991B1B,stroke-width:3px,color:#fff
  style SUCCESS_MSG fill:#10B981,stroke:#059669,stroke-width:3px,color:#fff
  style LOG fill:#047857,stroke:#065F46,stroke-width:3px,color:#fff
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
