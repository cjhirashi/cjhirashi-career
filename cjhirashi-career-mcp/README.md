# MCP Tools Server (contenedor `mcp_tools_server`)

Servidor [FastMCP](https://modelcontextprotocol.io) que genera documentos profesionales en PDF (CVs y Cartas de Presentación) a partir de estructuras JSON, usando WeasyPrint y plantillas Jinja2, con transporte SSE.

Este directorio contiene **únicamente** el código del servidor MCP. La orquestación Docker (junto al futuro contenedor `frontend/`) vive en el `docker-compose.yml` de la raíz del proyecto.

## Tecnologías

- **Python 3.11** — Runtime environment
- **FastMCP** — Model Context Protocol framework (SSE transport)
- **WeasyPrint** — PDF rendering engine
- **Jinja2** — Template engine
- **Uvicorn** — ASGI server
- **Docker** — Imagen de este servicio (orquestada desde la raíz)

---

## Descripción

MCP Tools Server es un servidor especializado en la generación automatizada de documentos profesionales en PDF. Expone dos herramientas MCP (`crear_cv_pdf` y `crear_cover_letter_pdf`) que:

- **Aceptan JSON estructurado** como entrada
- **Renderizan plantillas Jinja2** con datos personalizados
- **Aplican estilos CSS paged media** optimizados para impresión
- **Generan PDFs profesionales** almacenados en volúmenes persistentes
- **Comunican vía SSE** a través del protocolo MCP

**Ideal para:** Agentes MCP, sistemas de recursos humanos, plataformas de empleo, herramientas de generación de documentos.

---

## Arquitectura

Para ver diagramas detallados, consulta **[../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)** que incluye:
- Diagrama general de componentes (con color-coding: Morado cliente, Verde servidor, Cyan almacenamiento)
- Flujo de datos completo con secuencias
- Topología de red Docker
- Decisiones de diseño clave

Diagrama simplificado del servidor:

```mermaid
graph TD
    A["MCP Client<br/>(HTTP/SSE)"] -->|8002| B["FastMCP Server<br/>(server.py)"]
    B -->|@mcp.tool| C["Tool Router"]
    C -->|crear_cv_pdf| D["CV Generator<br/>(tools/cv_generator.py)"]
    C -->|crear_cover_letter_pdf| E["Cover Generator<br/>(tools/cover_generator.py)"]
    D -->|Jinja2| F["CV Template<br/>(templates/cv_template.html)"]
    E -->|Jinja2| G["Cover Template<br/>(templates/cover_template.html)"]
    F -->|CSS Paged Media| H["WeasyPrint"]
    G -->|CSS Paged Media| H
    H -->|PDF| I["Persistent Storage<br/>(/mcp-outputs/)"]
    I -->|File Path| B
    B -->|Result String| A
```

### Flujo Principal

1. **Cliente MCP** → Conecta vía SSE a puerto 8002 (host) / 8000 (contenedor)
2. **FastMCP Server** → Recibe herramienta + parámetros JSON
3. **Tool Generator** → Parsea JSON, carga template, aplica estilos
4. **WeasyPrint** → Renderiza HTML → PDF
5. **Storage** → Almacena en `/mnt/disco2/cjhirashi-data/mcp-outputs/`
6. **Response** → Retorna ruta de archivo al cliente

### Decisiones de Diseño

- **CSS Paged Media:** Optimiza layout para impresión (márgenes, saltos de página)
- **Jinja2 Templates:** Flexible para múltiples formatos sin cambiar código
- **SSE Transport:** Comunicación unidireccional eficiente para MCP
- **Volúmenes Persistentes:** Los PDFs persisten después de reiniciar contenedor

Ver [COLOR_PALETTE.md](../COLOR_PALETTE.md) para entender el color-coding usado en todos los diagramas Mermaid del proyecto.

---

## Quick Start

> Todos los comandos `docker compose` se ejecutan desde la **raíz del proyecto** (donde vive `docker-compose.yml`), ya que ese archivo orquesta este servicio (`mcp-tools`) apuntando al contexto `./server`.

### 1. Iniciar el servidor

```bash
# Desde la raíz del proyecto
docker compose build --no-cache mcp-tools
docker compose up -d --force-recreate
```

### 2. Verificar estado

```bash
docker logs mcp_tools_server --tail 20 -f
```

Espera ver:
```
INFO:     Starting MCP server 'MCP-Tools-Server' with transport 'sse' on http://0.0.0.0:8000/sse
INFO:     Application startup complete.
```

### 3. Conectar cliente MCP

```
http://<IP_SERVIDOR>:8002/sse
```

### 4. Verificar outputs

```bash
ls /mnt/disco2/cjhirashi-data/mcp-outputs/cvs/
ls /mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters/
```

---

## Herramientas Expuestas

| Herramienta | Parámetros | Descripción |
|:---|:---|:---|
| `crear_cv_pdf` | `datos_cv_json` (str), `nombre_archivo` (str) | Genera CV profesional en PDF y lo almacena en `/mcp-outputs/cvs/` |
| `crear_cover_letter_pdf` | `datos_cover_json` (str), `nombre_archivo` (str) | Genera Carta de Presentación en PDF y la almacena en `/mcp-outputs/cover_letters/` |

---

## Ejemplos de Uso

### Generar un CV

**Solicitud:**
```json
{
  "tool": "crear_cv_pdf",
  "arguments": {
    "datos_cv_json": "{\"nombre\":\"Juan García\",\"email\":\"juan@example.com\",\"telefono\":\"+34 600 123 456\",\"titulo_profesional\":\"Senior Software Engineer\",\"resumen\":\"Ingeniero de software con 10 años de experiencia...\",\"experiencia\":[{\"empresa\":\"Tech Corp\",\"puesto\":\"Senior Developer\",\"fechas\":\"2020-2024\",\"descripcion\":\"Desarrollo de aplicaciones backend en Python\"}],\"educacion\":[{\"institucion\":\"Universidad de Madrid\",\"titulo\":\"Grado en Informática\",\"año\":\"2014\"}],\"habilidades\":[\"Python\",\"JavaScript\",\"React\",\"PostgreSQL\",\"Docker\",\"AWS\"]}",
    "nombre_archivo": "CV_JuanGarcia_2024.pdf"
  }
}
```

**Respuesta Exitosa:**
```json
{
  "result": "Éxito: PDF generado correctamente en '/mnt/disco2/cjhirashi-data/mcp-outputs/cvs/CV_JuanGarcia_2024.pdf'"
}
```

### Generar una Carta de Presentación

**Solicitud:**
```json
{
  "tool": "crear_cover_letter_pdf",
  "arguments": {
    "datos_cover_json": "{\"nombre\":\"Juan García\",\"email\":\"juan@example.com\",\"telefono\":\"+34 600 123 456\",\"empresa_destino\":\"TechCorp Solutions\",\"puesto\":\"Senior Software Architect\",\"persona_contacto\":\"María López\",\"fecha\":\"15 de Agosto de 2024\",\"introduccion\":\"Le escribo para expresar mi interés en la posición...\",\"cuerpo\":\"Con más de 10 años de experiencia...\",\"cierre\":\"Agradezco su consideración...\"}",
    "nombre_archivo": "CoverLetter_JuanGarcia_TechCorp.pdf"
  }
}
```

**Respuesta Exitosa:**
```json
{
  "result": "Éxito: PDF generado correctamente en '/mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters/CoverLetter_JuanGarcia_TechCorp.pdf'"
}
```

---

## Esquema de Datos Esperado

### CV (`crear_cv_pdf`)

```json
{
  "nombre": "Nombre Completo",
  "email": "email@example.com",
  "telefono": "+34 600 123 456",
  "ubicacion": "Ciudad, País",
  "titulo_profesional": "Especialidad / Puesto Actual",
  "resumen": "Resumen profesional o perfil personal",
  "experiencia": [
    {
      "empresa": "Nombre Empresa",
      "puesto": "Título del Puesto",
      "fechas": "2020-2024",
      "descripcion": "Responsabilidades y logros"
    }
  ],
  "educacion": [
    {
      "institucion": "Nombre Universidad/Instituto",
      "titulo": "Grado o Certificación",
      "año": "2014"
    }
  ],
  "habilidades": ["Habilidad1", "Habilidad2", "Habilidad3"],
  "certificaciones": [
    {
      "nombre": "Nombre Certificación",
      "institución": "Institución",
      "año": "2023"
    }
  ],
  "idiomas": [
    {
      "idioma": "Español",
      "nivel": "Nativo"
    }
  ]
}
```

### Carta de Presentación (`crear_cover_letter_pdf`)

```json
{
  "nombre": "Nombre Completo",
  "email": "email@example.com",
  "telefono": "+34 600 123 456",
  "empresa_destino": "Nombre de la Empresa",
  "puesto": "Título del Puesto Solicitado",
  "persona_contacto": "Nombre del Contacto",
  "fecha": "15 de Agosto de 2024",
  "introduccion": "Párrafo inicial expresando interés en la posición",
  "cuerpo": "Párrafo principal con competencias y experiencia relevante",
  "cierre": "Párrafo final con llamada a la acción"
}
```

---

## Testing

Para probar localmente sin Docker (desde `server/`):

```bash
cd server

# Instalar dependencias
pip install -r requirements.txt
# o
pipenv install

# Ejecutar tests
python test_cv.py
python test_cover.py
```

Los tests generan PDFs de ejemplo en `/mnt/disco2/cjhirashi-data/mcp-outputs/`.

---

## Troubleshooting

| Problema | Causa | Solución |
|:---|:---|:---|
| El contenedor no inicia | Dependencias faltantes o error de sintaxis | `docker logs mcp_tools_server` + Reconstruir: `docker compose build --no-cache mcp-tools` (desde la raíz) |
| PDFs no se generan | Permisos en volumen o JSON malformado | Verificar `/mnt/disco2/cjhirashi-data/mcp-outputs` existe + Validar JSON |
| Errores de CSS o fuentes | Rutas relativas incorrectas | Revisar `templates/css/style_1.css` + Ver `Guia PDF WeasyPrint y CSS paged media.md` |
| "Module not found" | sys.path incorrecto en contenedor | Reconstruir imagen Docker |

---

## Estructura del Proyecto (server/)

```
server/
├── tools/
│   ├── __init__.py
│   ├── cv_generator.py              # Lógica de generación CV
│   └── cover_generator.py           # Lógica de generación Cover Letter
├── templates/
│   ├── css/
│   │   └── style_1.css              # Estilos CSS paged media
│   ├── cover_template.html          # Template Jinja2 - Carta
│   └── cv_template.html             # Template Jinja2 - CV
├── Dockerfile                       # Definición imagen (contexto ./server)
├── requirements.txt                 # Dependencias Python
├── Pipfile / Pipfile.lock           # Dependencias Python (pipenv, alternativa)
├── server.py                        # Servidor FastMCP (entry point)
├── test_cv.py                       # Test unitario CV
├── test_cover.py                    # Test unitario Cover Letter
├── mcp_tools_server.md              # Guía operacional (logs, monitoreo, troubleshooting)
├── Guia PDF WeasyPrint y CSS paged media.md  # Referencia técnica CSS
└── README.md                        # Este archivo
```

---

## Configuración Avanzada

Para cambiar puertos, directorios o configuración de red:

- **`../docker-compose.yml`** (raíz) — Puertos expuestos (8002), volúmenes, red (network-cjhirashi-srv), contexto de build (`./server`)
- **Dockerfile** — Versión Python (3.11), dependencias del sistema
- **server.py** — Host/puerto del servidor MCP (0.0.0.0:8000)
- **tools/\*.py** — Rutas de salida (`/mnt/disco2/cjhirashi-data/mcp-outputs/...`)

---

## Configuración del Entorno

| Parámetro | Valor |
|:---|:---|
| **Puerto Interno (Contenedor)** | 8000 |
| **Puerto Expuesto (Host)** | 8002 |
| **Transporte MCP** | SSE (Server-Sent Events) |
| **Volumen Persistente** | `/mnt/disco2/cjhirashi-data/mcp-outputs` |
| **Red Docker** | `network-cjhirashi-srv` |

---

---

## Referencias y Documentación Relacionada

- **[../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)** — Diagramas de arquitectura completos y decisiones de diseño
- **[../docs/DATA_FLOW.md](../docs/DATA_FLOW.md)** — Flujos de datos detallados con manejo de errores
- **[../docs/NETWORK_TOPOLOGY.md](../docs/NETWORK_TOPOLOGY.md)** — Configuración de red, puertos y volúmenes
- **[../COLOR_PALETTE.md](../COLOR_PALETTE.md)** — Paleta de colores armónica para diagramas
- **[../CLAUDE.md](../CLAUDE.md)** — Guía de desarrollo para agentes y equipos

---

**Última actualización:** 2026-08-15  
**Contacto:** Carlos (cjhirashi@gmail.com)