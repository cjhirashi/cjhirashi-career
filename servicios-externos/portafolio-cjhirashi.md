# Servicios externos requeridos por portafolio-cjhirashi

Este documento le dice a **cjhirashi-srv** (Caddy + Cloudflare Tunnel) qué
contenedores de este proyecto necesitan acceso público, y a qué subdominio.
Todos los contenedores listados aquí ya están en `network-cjhirashi-srv`
(red Docker bridge externa, compartida entre ambos proyectos) - Caddy solo
necesita enrutar el subdominio hacia `container_name:puerto`.

## Contenedores expuestos

| Subdominio | Contenedor | Puerto | Protocolo | Notas |
|---|---|---|---|---|
| `admin.cjhirashi.com` | `admin_panel` | 8000 | HTTP | Ya configurado |
| `portafolio.cjhirashi.com` | `portal_publico` | 8000 | HTTP | Ya configurado |
| `mcp.cjhirashi.com` | `mcp_server` | 8000 | HTTP (SSE) | Ya configurado |
| `files.cjhirashi.com` | `minio_storage` | 9000 | HTTP | **Nuevo** - ver detalle abajo |

## Nuevo: `files.cjhirashi.com` → `minio_storage:9000`

**Qué es:** bucket de archivos (MinIO, S3-compatible) para subir imágenes y
documentos desde el Admin Panel, con links públicos para referenciarlos
(por ejemplo dentro de campos de texto en Markdown: `![alt](url)`).

**Qué exponer:** únicamente el puerto **9000** (API S3 - descargas de
objetos con política pública de solo-lectura por bucket). El puerto 9001
(consola de administración de MinIO) **no debe exponerse** - se queda
interno, solo accesible dentro de la red Docker.

**Configuración Caddy sugerida:**

```
files.cjhirashi.com {
    reverse_proxy minio_storage:9000
}
```

Sin necesidad de reescritura de rutas ni headers especiales - MinIO sirve
los objetos directamente en `/<bucket>/<objeto>`, y las URLs públicas que
genera el backend (`api/src/services/storage_service.py`) ya usan ese
formato completo (ej. `https://files.cjhirashi.com/portafolio-cjhirashi/<archivo>`).

**Seguridad:** solo el bucket `portafolio-cjhirashi` tiene política de
lectura pública (aplicada automáticamente al arrancar `api_rest`, ver
`storage_service.ensure_bucket()`). Subir o borrar archivos siempre
requiere autenticación JWT contra la API (`POST/DELETE /files`) - lo único
público es la *lectura* de un objeto ya subido, y solo si se conoce su URL
exacta (no hay listado público del bucket).
