# MCP Tools Server — Claude Development Guide

## Project Overview

**MCP Tools Server** es un servidor [Model Context Protocol (MCP)](https://modelcontextprotocol.io) basado en FastMCP que expone herramientas para generar documentos profesionales en PDF (CVs y Cartas de Presentación) a partir de estructuras JSON.

El servidor corre en un contenedor Docker, comunica mediante SSE (Server-Sent Events), y almacena los PDFs generados en volúmenes persistentes.

---

## Core Architecture

### How It Works

1. **FastMCP Server** (`server.py`): Punto de entrada que define dos herramientas MCP decoradas con `@mcp.tool()`
   - `crear_cv_pdf(datos_cv_json, nombre_archivo)` → Genera CV en PDF
   - `crear_cover_letter_pdf(datos_cover_json, nombre_archivo)` → Genera cover letter en PDF

2. **PDF Generators** (`tools/cv_generator.py`, `tools/cover_generator.py`)
   - Parsean JSON de entrada
   - Cargan plantillas Jinja2 HTML
   - Aplican estilos CSS y CSS paged media (para impresión)
   - Renderizan a PDF con WeasyPrint

3. **Templates** (`templates/`)
   - `cv_template.html`, `cover_template.html`: Plantillas Jinja2
   - `css/style_1.css`: Estilos globales + media queries para PDF

4. **Containerization** (Docker + Compose)
   - Ejecuta el servidor en Python 3.11 con FastMCP + Uvicorn
   - Expone puerto 8002 en el host → puerto 8000 en el contenedor
   - Monta volumen persistente para outputs: `/mnt/disco2/cjhirashi-data/mcp-outputs`
   - Conecta a red externa `network-cjhirashi-srv`

### Data Flow

```
MCP Client 
  → HTTP/SSE (8002) 
  → FastMCP Server (server.py)
  → Tool Handler (crear_cv_pdf / crear_cover_letter_pdf)
  → Generator (cv_generator / cover_generator)
  → Jinja2 + WeasyPrint
  → PDF File (/mcp-outputs/cvs/ o /mcp-outputs/cover_letters/)
```

---

## Project Structure

```
mcp-server/
├── server.py                          # FastMCP server + tool definitions
├── tools/
│   ├── __init__.py
│   ├── cv_generator.py               # CV PDF generation logic
│   └── cover_generator.py            # Cover letter PDF generation logic
├── templates/
│   ├── cv_template.html              # CV Jinja2 template
│   ├── cover_template.html           # Cover letter Jinja2 template
│   └── css/
│       └── style_1.css               # Global styles (CSS paged media)
├── Dockerfile                         # Container image definition
├── docker-compose.yml                # Service orchestration
├── test_cv.py                        # Unit test for CV generation
├── test_cover.py                     # Unit test for cover letter generation
├── README.md                         # User documentation
├── CLAUDE.md                         # This file
├── mcp_tools_server.md               # Operational guide
└── Guia PDF WeasyPrint y CSS paged media.md  # Technical guide (PDF styling)
```

---

## Key Files & Their Purpose

| File | Purpose |
|------|---------|
| **server.py** | Defines FastMCP server + exposes tool endpoints |
| **tools/cv_generator.py** | Renders CV JSON → PDF (Jinja2 + WeasyPrint) |
| **tools/cover_generator.py** | Renders cover letter JSON → PDF (Jinja2 + WeasyPrint) |
| **templates/cv_template.html** | Jinja2 template for CV structure |
| **templates/cover_template.html** | Jinja2 template for cover letter structure |
| **templates/css/style_1.css** | Shared CSS with print media queries |
| **Dockerfile** | Python 3.11 image with FastMCP, WeasyPrint, Jinja2 |
| **docker-compose.yml** | Service config + volume/network mappings |
| **test_cv.py, test_cover.py** | Unit tests (run locally or in container) |
| **mcp_tools_server.md** | Operational procedures (logs, troubleshooting) |

---

## Development Workflow

### Local Setup (Without Docker)

```bash
# Install dependencies (assumes pipenv or pip)
pipenv install --dev
# or
pip install fastmcp weasyprint jinja2

# Run tests
python test_cv.py
python test_cover.py

# Start server locally (for debugging)
python server.py
# Listens on http://localhost:8000/sse
```

### Docker Workflow

```bash
# Build image + start container
docker build --network=host --no-cache -t mcp-server-mcp-tools:latest . && \
docker compose up -d --force-recreate

# Check logs
docker logs mcp_tools_server --tail 20 -f

# Stop container
docker compose down

# Access outputs
ls /mnt/disco2/cjhirashi-data/mcp-outputs/cvs/
ls /mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters/
```

### Making Changes

1. **Edit templates** → No rebuild needed, templates are mounted as volumes
2. **Edit CSS** → Changes picked up on next request (no rebuild)
3. **Edit Python code (server.py, tools/)** → Rebuild Docker image

```bash
# After code changes
docker build --network=host --no-cache -t mcp-server-mcp-tools:latest .
docker compose up -d --force-recreate
docker logs mcp_tools_server --tail 20 -f
```

---

## Tool Definitions & JSON Schemas

### crear_cv_pdf

**Input:**
```json
{
  "datos_cv_json": "{\"nombre\":\"John Doe\",\"email\":\"john@example.com\",...}",
  "nombre_archivo": "cv_johndoe.pdf"
}
```

**Output:**
```
"Éxito: PDF generado correctamente en '/mnt/disco2/cjhirashi-data/mcp-outputs/cvs/cv_johndoe.pdf'"
```

The `datos_cv_json` string is parsed into a dict and passed to Jinja2's `template.render(**datos)`. See `templates/cv_template.html` for expected keys.

### crear_cover_letter_pdf

**Input:**
```json
{
  "datos_cover_json": "{\"nombre\":\"John Doe\",\"empresa\":\"Acme Inc\",...}",
  "nombre_archivo": "cover_johndoe.pdf"
}
```

**Output:**
```
"Éxito: PDF generado correctamente en '/mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters/cover_johndoe.pdf'"
```

---

## Important Patterns & Conventions

### WeasyPrint + CSS Paged Media

- **Base URL resolution:** WeasyPrint needs `base_url=templates_dir` to resolve CSS imports and relative asset paths
- **CSS paged media:** Use `@page`, `@page:first`, margin rules, etc. in `style_1.css` for PDF-specific layout
- See `Guia PDF WeasyPrint y CSS paged media.md` for detailed CSS paged media guidance

### Jinja2 Template Rendering

```python
env = Environment(loader=FileSystemLoader(templates_dir))
template = env.get_template("cv_template.html")
html_out = template.render(**datos)  # datos is a dict, unpacked as kwargs
```

Pass data as a dict with keys matching template variables. Example:
```json
{
  "nombre": "John Doe",
  "titulo_profesional": "Senior Software Engineer",
  "experiencia": [
    {"empresa": "Acme", "puesto": "Engineer", "años": "2020-2024"}
  ]
}
```

### Error Handling

Both generators wrap logic in try/except and return error messages:
```python
try:
    datos = json.loads(datos_cv_json)
    ruta_resultado = generar_cv(datos, nombre_archivo)
    return f"Éxito: PDF generado correctamente en '{ruta_resultado}'"
except Exception as e:
    return f"Error generando PDF: {str(e)}"
```

**Note:** Errors are returned as strings, not exceptions. Clients should inspect the string for "Error" prefix.

### Output Paths

- CVs: `/mnt/disco2/cjhirashi-data/mcp-outputs/cvs/`
- Cover Letters: `/mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters/`

Paths are hardcoded in `cv_generator.py` and `cover_generator.py`. These directories are created on first use (`os.makedirs(..., exist_ok=True)`).

---

## Testing

### Unit Tests

```bash
# Test CV generation with sample data
python test_cv.py

# Test cover letter generation with sample data
python test_cover.py
```

These tests run locally and generate PDFs into the output directory.

### Integration Tests

1. Start the container
2. Make HTTP POST to `http://localhost:8002/sse` with MCP protocol messages
3. Verify PDFs appear in output directories

---

## Debugging Tips

### Logs
```bash
docker logs mcp_tools_server --tail 50 -f
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "Module not found" (cv_generator, cover_generator) | Rebuild Docker image; check `sys.path` in Dockerfile |
| "CSS not found" | Ensure `base_url=templates_dir` in WeasyPrint call; check template relative paths |
| "Permission denied" (output dir) | Check volume mounts in docker-compose.yml; ensure `/mnt/disco2/cjhirashi-data/mcp-outputs` exists on host |
| "JSON decode error" | Validate input JSON string before passing to `json.loads()` |
| "Template not found" | Verify template file exists in `templates/` folder; check template name spelling |

### Direct Testing in Container

```bash
docker exec -it mcp_tools_server python -c "
from tools.cv_generator import generar_cv
datos = {'nombre': 'Test', 'titulo': 'Engineer'}
generar_cv(datos, 'test.pdf')
"
```

---

## Deployment & Operations

See **mcp_tools_server.md** for:
- Startup procedures
- Log monitoring
- Service health checks
- Restart policies
- Output cleanup

---

## Dependencies

### Python Packages
- **fastmcp**: MCP server framework
- **weasyprint**: PDF rendering engine
- **jinja2**: Template engine
- **python-dotenv** (optional): Environment configuration

### System Requirements
- Python 3.11+
- libffi, libssl (system libs for WeasyPrint)
- Docker & Docker Compose

See `Dockerfile` for exact dependency versions.

---

## Agentes Globales del Ecosistema

Este proyecto integra con los siguientes agentes especializados del ecosistema **cjhirashi**:

### 🐳 [docker](~/.claude/agents/docker.md)
**Cuándo usar:** Cambios a Dockerfile, docker-compose.yml, imágenes, volúmenes, redes

**Típico:**
- Optimizar Dockerfile (multi-stage, tamaño)
- Ajustar volúmenes persistentes
- Conectar contenedores a redes
- Cambios de puerto o configuración de servicio

**NO:** Código Python de la aplicación

---

### 🔗 [arquitectura-red](~/.claude/agents/arquitectura-red.md)
**Cuándo usar:** Integración con otros proyectos, conflictos de puertos, diseño de redes

**Típico:**
- Validar que el servidor MCP se conecta correctamente a `network-cjhirashi-srv`
- Verificar DNS entre servicios (ej: mcp-tools → caddy)
- Proponer cambios a topología de redes si hay conflictos

**Contexto relevante:**
- Red interna: `network-cjhirashi-srv` (aislada, local al proyecto)
- Red compartida: `infraestructura_default` (inter-proyectos, si es necesario)
- Volumen persistente: `/mnt/disco2/cjhirashi-data/mcp-outputs/` (almacenamiento secundario)

---

### 🛠️ [desarrollo-mcps](~/.claude/agents/desarrollo-mcps.md)
**Cuándo usar:** Cambios al protocolo MCP, nuevas herramientas, esquema de parámetros

**Típico:**
- Agregar nuevas `@mcp.tool()` al server
- Modificar esquema JSON de entrada/salida
- Cambios a transporte SSE o configuración MCP
- Validación de permisos en herramientas

**NO:** Lógica de generación de PDFs (eso es lógica de negocio)

---

### 📚 [documentacion-tecnica](~/.claude/agents/documentacion-tecnica.md)
**Cuándo usar:** Actualizar README, CLAUDE.md, docstrings, agregar diagramas

**Típico:**
- Mantener README.md sincronizado
- Escribir guías de troubleshooting
- Crear diagramas Mermaid de arquitectura
- Documentar nuevas funciones públicas

---

### 🔧 [git-control-versiones](~/.claude/agents/git-control-versiones.md)
**Cuándo usar:** Commits, branches, merges, rebase

**Típico:**
- Crear commits después de cambios
- Hacer PR a rama principal
- Resolver conflictos de merge
- Reescribir historia si necesario

---

## Flujo de Trabajo Recomendado

| Tipo de Cambio | Agente Principal | Agente Secundario | Checklist |
|---|---|---|---|
| **Agregar documento PDF** | `desarrollo-mcps` | — | [ ] Nueva tool MCP [ ] JSON schema [ ] Tests [ ] Logs |
| **Cambiar estilos CSS** | Tu trabajo | `documentacion-tecnica` | [ ] Cambio CSS [ ] Actualizar guía [ ] Test visual |
| **Optimizar Docker** | `docker` | `arquitectura-red` | [ ] Dockerfile/compose [ ] Red validada [ ] Volúmenes correctos |
| **Cambiar puertos/redes** | `arquitectura-red` | `docker` | [ ] Red sin conflictos [ ] Compose actualizado [ ] DNS validado |
| **Hacer release** | `git-control-versiones` | — | [ ] Commits limpios [ ] PR abierto [ ] Tests pasan |

---

## Future Improvements

- [ ] Add environment variables for output directory paths (currently hardcoded)
- [ ] Support additional document types (invoices, letters, reports)
- [ ] Add template selection parameter to tool calls
- [ ] Implement file cleanup / retention policies
- [ ] Add signature/watermark support
- [ ] Cache compiled templates for performance
- [ ] Add rate limiting / request validation

---

## Quick Reference

**Start server:**
```bash
docker compose up -d --force-recreate
```

**View logs:**
```bash
docker logs mcp_tools_server -f
```

**Rebuild after code changes:**
```bash
docker build --network=host --no-cache -t mcp-server-mcp-tools:latest . && \
docker compose up -d --force-recreate
```

**Access generated files:**
```bash
/mnt/disco2/cjhirashi-data/mcp-outputs/cvs/
/mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters/
```

**Test locally:**
```bash
python test_cv.py
python test_cover.py
```

---

**Last Updated:** 2026-08-14  
**Maintainer:** Carlos (cjhirashi@gmail.com)
