# Guía Operativa: Funcionamiento y Administración del Contenedor MCP

Este documento describe la arquitectura interna, el flujo de datos y los procedimientos operativos estándar para la administración, monitoreo y mantenimiento del contenedor **`mcp_tools_server`**.

---

## 🏗️ 1. Arquitectura y Funcionamiento Interno

El contenedor encapsula la lógica de ejecución del servidor de herramientas MCP, aislando las dependencias del sistema operativo (librerías de renderizado gráfico/tipográfico) y el entorno de ejecución de Python.

### 🔄 Flujo de Datos y Vida de una Petición

```text
[ Cliente MCP ] 
       │
       │  Petición HTTP / SSE (ej. POST /sse)
       ▼
[ Host: Puerto 8002 ]
       │  Mapeo de Puerto (Docker Bridge / Network External)
       ▼
[ Contenedor: Puerto 8000 ]
       │
       ├─► [ Uvicorn (ASGI Server) ] ──► Mantiene el canal SSE y gestiona la entrada/salida
       │
       └─► [ FastMCP Framework ]
                 │
                 ├─► Recibe JSON (`datos_cv_json` / `datos_cover_json`)
                 ├─► Parsea datos con `json.loads()`
                 ├─► Procesa plantillas Jinja2 (`/app/templates`)
                 ├─► Compila PDF vía WeasyPrint + Cairo + Pango
                 │
                 └─► Escribe archivo en `/app/mnt/disco2/cjhirashi-data/mcp-outputs/`
                               │
                               ▼
            [ Disco del Host: /mnt/disco2/... ] (Volumen Persistente)
```

### 🧩 Componentes Clave dentro del Contenedor

1. **Capa Base OS (`python:3.11-bookworm`):**
   Proporciona el runtime de Python 3.11 sobre Debian Bookworm, incluyendo paquetes del sistema esenciales para el motor gráfico de WeasyPrint: `libpango-1.0-0`, `libpangocairo-1.0-0`, `libcairo2`, `shared-mime-info` y `fonts-liberation`.

2. **Servidor ASGI (`Uvicorn`):**
   Escucha directamente en la interfaz `0.0.0.0` y puerto `8000`. Administra las conexiones asíncronas persistentes requeridas por el protocolo SSE (Server-Sent Events).

3. **Aplicación (`FastMCP` + `server.py`):**
   Expone los métodos `@mcp.tool()` registrados (`crear_cv_pdf` y `crear_cover_letter_pdf`), encargados de procesar las solicitudes y llamar a los generadores contenidos en la carpeta `tools/`.

4. **Persistencia de Archivos:**
   Cualquier PDF generado por el proceso se almacena en la ruta montada del host `/mnt/disco2/cjhirashi-data/mcp-outputs`, lo que garantiza que los archivos generados no se pierdan si el contenedor es destruido o recreado.

---

## 🛠️ 2. Guía de Operación y Mantenimiento

### 🟢 Arrancar el Servicio

Para iniciar el contenedor utilizando la configuración definida en `docker-compose.yml`:

```bash
docker compose up -d
```

### 🔴 Detener el Servicio

Para detener el contenedor de forma segura sin borrar volúmenes ni imágenes:

```bash
docker compose stop
```

Si se requiere detener y remover el contenedor:

```bash
docker compose down
```

### 🔄 Reconstrucción Limpia (Despliegue de Cambios)

Cuando se modifique el `Dockerfile`, `server.py`, plantillas en `templates/` o herramientas en `tools/`, se debe forzar la recompilación sin caché y la recreación del contenedor:

```bash
docker build --network=host --no-cache -t mcp-server-mcp-tools:latest . && docker compose up -d --force-recreate
```

---

## 🔍 3. Monitoreo y Diagnóstico

### 📊 Estado del Contenedor

Para verificar que el servicio se encuentre en estado `Up` y revisar el mapeo de puertos:

```bash
docker ps --filter "name=mcp_tools_server"
```

### 📜 Inspección de Logs en Tiempo Real

Para monitorear las peticiones entrantes, generación de documentos o posibles errores de Python en vivo:

```bash
docker logs mcp_tools_server --tail 50 -f
```

### 🐚 Acceso Interactivo a la Consola del Contenedor

Para inspeccionar el sistema de archivos interno, verificar librerías o revisar rutas de salida dentro del contenedor:

```bash
docker exec -it mcp_tools_server bash
```

---

## 🚨 4. Solución de Problemas Frecuentes (Troubleshooting)

| Síntoma / Error | Causa Probable | Acción Correctiva |
| :--- | :--- | :--- |
| `Status: Restarting (1)` | Excepción en código Python al arrancar (`server.py`). | Ejecutar `docker logs mcp_tools_server --tail 30` para identificar el traceback del error. |
| `TypeError: FastMCP() no longer accepts host` | Argumentos de red pasados al constructor `FastMCP()`. | Asegurarse de instanciar `mcp = FastMCP("Nombre")` e indicar `host` y `port` únicamente en `mcp.run()`. |
| `exit code: 100` en Build | Fallo de DNS o conexión a repositorios de Debian. | Compilar siempre utilizando el parámetro `--network=host` en el comando de `docker build`. |
| Error escribiendo PDF / Permisos | Ruta del volumen inexistente o sin permisos en el host. | Verificar que `/mnt/disco2/cjhirashi-data/mcp-outputs` exista en el host con permisos de lectura/escritura. |