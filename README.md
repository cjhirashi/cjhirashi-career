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
├── CLAUDE.md                            # Guía para desarrolladores
├── mcp_tools_server.md                  # Guía operacional
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

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Generar un CV

```json
{
  "tool": "crear_cv_pdf",
  "arguments": {
    "datos_cv_json": "{\"nombre\":\"Juan García\",\"email\":\"juan@example.com\",\"telefono\":\"+34 600 123 456\",\"titulo_profesional\":\"Senior Software Engineer\",\"resumen\":\"Ingeniero de software con 10 años de experiencia...\",\"experiencia\":[{\"empresa\":\"Tech Corp\",\"puesto\":\"Senior Developer\",\"fechas\":\"2020-2024\",\"descripcion\":\"Desarrollo de aplicaciones backend en Python\"},{\"empresa\":\"StartUp Inc\",\"puesto\":\"Full Stack Developer\",\"fechas\":\"2018-2020\",\"descripcion\":\"Desarrollo web full-stack con React y Node.js\"}],\"educacion\":[{\"institucion\":\"Universidad de Madrid\",\"titulo\":\"Grado en Informática\",\"año\":\"2014\"}],\"habilidades\":[\"Python\",\"JavaScript\",\"React\",\"PostgreSQL\",\"Docker\",\"AWS\"]}",
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

### Ejemplo 2: Generar una Carta de Presentación

```json
{
  "tool": "crear_cover_letter_pdf",
  "arguments": {
    "datos_cover_json": "{\"nombre\":\"Juan García\",\"email\":\"juan@example.com\",\"telefono\":\"+34 600 123 456\",\"empresa_destino\":\"TechCorp Solutions\",\"puesto\":\"Senior Software Architect\",\"persona_contacto\":\"María López\",\"fecha\":\"15 de Agosto de 2024\",\"introduccion\":\"Le escribo para expresar mi interés en la posición de Senior Software Architect...\",\"cuerpo\":\"Con más de 10 años de experiencia en desarrollo de software...\",\"cierre\":\"Agradezco su consideración y quedo atento a sus comentarios.\"}",
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

## 📝 Esquema de Datos Esperado

### CV (crear_cv_pdf)

El parámetro `datos_cv_json` debe ser una cadena JSON (stringificada) con la siguiente estructura:

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
    },
    {
      "idioma": "Inglés",
      "nivel": "Fluido"
    }
  ]
}
```

### Carta de Presentación (crear_cover_letter_pdf)

El parámetro `datos_cover_json` debe ser una cadena JSON con la siguiente estructura:

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

## 🧪 Testing

Para probar localmente sin Docker:

```bash
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

## ❓ Troubleshooting

### El contenedor no inicia

```bash
# Verificar logs detallados
docker logs mcp_tools_server

# Reconstruir sin caché
docker build --network=host --no-cache -t mcp-server-mcp-tools:latest .
docker compose up -d --force-recreate
```

### PDFs no se generan

- Verificar que `/mnt/disco2/cjhirashi-data/mcp-outputs/` existe y tiene permisos de escritura
- Revisar que el JSON de entrada está bien formateado (sin caracteres especiales sin escape)
- Consultar logs: `docker logs mcp_tools_server -f`

### Errores de CSS o fuentes

- Verificar que `templates/css/style_1.css` existe
- Revisar rutas relativas en plantillas (usar rutas relativas a `templates/`)
- Ver `Guia PDF WeasyPrint y CSS paged media.md` para referencias de CSS media queries

---

## 📚 Documentación Completa

- **CLAUDE.md** — Guía completa para desarrolladores, arquitectura interna, patrones de desarrollo
- **mcp_tools_server.md** — Procedimientos operacionales, monitoreo, troubleshooting avanzado
- **Guia PDF WeasyPrint y CSS paged media.md** — Referencia técnica de estilos CSS y paged media

---

## 🔧 Configuración Avanzada

Para cambiar puertos, directorios de salida o configuración de red, editar:

- `docker-compose.yml` — Puertos, volúmenes, variables de entorno, red
- `Dockerfile` — Versión de Python, dependencias del sistema
- `server.py` — Parámetros del servidor (host, puerto, transporte)
- `tools/cv_generator.py` y `tools/cover_generator.py` — Rutas de salida

---

**Última actualización:** Agosto 2024  
**Contacto:** Carlos (cjhirashi@gmail.com)