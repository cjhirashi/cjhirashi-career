# MCP Frontend UI

Interfaz web para **MCP Tools Server**. Este contenedor es responsable de:

- Proveer una interfaz web para que usuarios generen documentos (CVs, Cartas de Presentación, y futuras herramientas)
- Comunicarse con el servidor MCP (`mcp_tools_server`) vía SSE en `http://mcp_tools_server:8000/sse` (dentro de la red Docker) o `http://<host>:8002/sse` (desde fuera)
- Presentar formularios dinámicos que generan el JSON esperado por cada herramienta MCP
- Listar y facilitar la descarga de los PDFs generados
- Gestionar historial de documentos generados

## Estado

Este directorio es actualmente un **placeholder/andamiaje**. La implementación real está pendiente y es responsabilidad del especialista `mcp-frontend-ui`.

## Estructura Esperada

```
frontend/
├── Dockerfile          # Build multi-stage (placeholder actual)
├── package.json        # Dependencias del proyecto (placeholder actual)
├── src/                 # Código fuente de la UI (pendiente)
└── README.md            # Este archivo
```

## Puerto

- **Interno (contenedor):** 8000
- **Expuesto (host):** 8003 (ver `docker-compose.yml` en la raíz del proyecto, servicio comentado `mcp-frontend`)

## Integración con el Servidor MCP

El frontend debe consumir las herramientas expuestas por el servidor MCP en `server/`:

| Herramienta | Descripción |
|---|---|
| `crear_cv_pdf` | Genera un CV profesional en PDF |
| `crear_cover_letter_pdf` | Genera una Carta de Presentación en PDF |

Ver `../server/README.md` y `../CLAUDE.md` para el schema JSON de entrada/salida de cada herramienta.

## Próximos Pasos

1. Elegir stack (React/Vue/Svelte + bundler)
2. Implementar cliente SSE hacia el servidor MCP
3. Construir formularios dinámicos por herramienta
4. Implementar listado/descarga de documentos generados
5. Completar `Dockerfile` y `package.json`
6. Descomentar y ajustar el servicio `mcp-frontend` en `docker-compose.yml` (raíz)
