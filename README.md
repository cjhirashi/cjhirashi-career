# MCP Tools Server

Servidor de herramientas para **Model Context Protocol (MCP)** basado en **FastMCP** y desplegado en un entorno contenedorizado con Docker. Este servicio expone endpoints mediante transporte SSE (Server-Sent Events) para la generación automatizada de documentos profesionales en formato PDF (CVs y Cartas de Presentación) a partir de estructuras JSON.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.11 (Base Debian Bookworm)
* **Framework MCP:** `fastmcp` (Transporte SSE)
* **Servidor Web ASGI:** Uvicorn
* **Motor de Renderizado PDF:** WeasyPrint + Jinja2
* **Contenedorización:** Docker & Docker Compose

---

## 📋 Herramientas Expuestas (@mcp.tool)

El servidor expone las siguientes herramientas para ser consumidas por clientes MCP:

| Herramienta | Parámetros | Descripción |
| :--- | :--- | :--- |
| `crear_cv_pdf` | `datos_cv_json` (str), `nombre_archivo` (str) | Genera un CV profesional en PDF procesando un JSON estructurado y lo almacena en `/mcp-outputs/cvs`. |
| `crear_cover_letter_pdf` | `datos_cover_json` (str), `nombre_archivo` (str) | Genera una Carta de Presentación en PDF procesando un JSON estructurado y la almacena en `/mcp-outputs/cover_letters`. |

---

## 📁 Estructura del Proyecto

```text
mcp-server/
├── templates/
│   ├── css/
│   │   └── style_1.css
│   ├── cover_template.html
│   └── cv_template.html
├── tools/
│   ├── __init__.py
│   ├── cover_generator.py
│   └── cv_generator.py
├── docker-compose.yml
├── Dockerfile
├── Guia PDF WeasyPrint y CSS paged media.md
├── Pipfile
├── Pipfile.lock
├── README.md
├── server.py
├── test_cover.py
└── test_cv.py
```

---

## ⚙️ Configuración del Entorno

### Puertos y Volúmenes
* **Puerto Interno (Contenedor):** `8000`
* **Puerto Expuesto (Host):** `8002`
* **Volumen Persistente:** Mapeado a `/mnt/disco2/cjhirashi-data/mcp-outputs` en el host para garantizar la permanencia de los PDFs generados.
* **Red Externa:** `network-cjhirashi-srv`

---

## 🚀 Despliegue y Ejecución

### 1. Construcción de la Imagen y Levantamiento del Servicio

Para construir la imagen Docker utilizando la red del host (evitando problemas de DNS/red durante el `apt-get` o `pip install`) y levantar el contenedor en segundo plano:

```bash
docker build --network=host --no-cache -t mcp-server-mcp-tools:latest . && docker compose up -d --force-recreate
```

### 2. Verificación de Estado y Logs

Para confirmar que el servidor Uvicorn arrancó correctamente y el transporte SSE está activo:

```bash
docker logs mcp_tools_server --tail 20 -f
```

La salida esperada en los logs debe ser similar a:

```text
INFO:     Starting MCP server 'MCP-Tools-Server' with transport 'sse' on [http://0.0.0.0:8000/sse](http://0.0.0.0:8000/sse)
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on [http://0.0.0.0:8000](http://0.0.0.0:8000) (Press CTRL+C to quit)
```

---

## 🔌 Endpoint de Conexión MCP

Los clientes MCP pueden conectarse al servidor a través del endpoint SSE expuesto:

```text
http://<IP_DEL_SERVIDOR>:8002/sse
```