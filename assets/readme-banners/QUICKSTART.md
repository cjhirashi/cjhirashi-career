# Quick Start — Banners README

_Cómo integrar los banners en 2 minutos._

## Paso 1: Editar el README

Abre el README de tu sección (server/, frontend/ o docs/).

## Paso 2: Agregar la Imagen al Inicio

Copia la línea correspondiente al inicio del archivo (después del código YAML front matter si existe):

### Para Server
```markdown
![Server README](../../assets/readme-banners/server-readme.svg)
```

### Para Frontend
```markdown
![Frontend README](../../assets/readme-banners/frontend-readme.svg)
```

### Para Docs
```markdown
![Documentation README](../../assets/readme-banners/docs-readme.svg)
```

## Paso 3: Guardar y Revisar

1. Guarda el archivo
2. Abre en GitHub o tu visor Markdown
3. Verifica que el banner aparezca correctamente

## Ejemplo Completo

```markdown
![Server README](../../assets/readme-banners/server-readme.svg)

# Server

MCP Tools Server basado en FastMCP...

## Descripción

El servidor implementa...

## Inicio Rápido

```bash
docker compose up
```
```

## Rutas Correctas por Sección

### server/README.md
```
../../assets/readme-banners/server-readme.svg
```
Subes 2 niveles desde `server/` hasta `mcp-server/`, luego entras a `assets/`.

### frontend/README.md
```
../../assets/readme-banners/frontend-readme.svg
```
Subes 2 niveles desde `frontend/` hasta `mcp-server/`, luego entras a `assets/`.

### docs/README.md
```
../../assets/readme-banners/docs-readme.svg
```
Subes 2 niveles desde `docs/` hasta `mcp-server/`, luego entras a `assets/`.

## Problemas Comunes

### El banner no aparece
- Verifica que la ruta sea correcta (usa las rutas de arriba)
- Asegúrate de que el archivo README esté en la carpeta correcta
- Recarga la página en GitHub

### El texto está cortado
- No cambies el SVG, espera a que se cargue la fuente
- Los navegadores tardan unos segundos en importar las fuentes de Google

## Personalización Avanzada

Si necesitas cambiar algo (tecnologías, descripción, etc.):

1. Edita el archivo SVG con un editor de texto
2. Busca el texto que quieres cambiar
3. Reemplaza solo el contenido entre las etiquetas `<text>`
4. Guarda y recarga el navegador

Ejemplo: Para cambiar tecnologías en `server-readme.svg`, busca:
```xml
<text x="40" y="348" class="footer-text">FastMCP • WeasyPrint • Jinja2 • Python • Docker  |  server/README.md</text>
```

Y reemplaza con:
```xml
<text x="40" y="348" class="footer-text">FastMCP • WeasyPrint • Nueva Tecnologia  |  server/README.md</text>
```

## Siguientes Pasos

- [Ver especificaciones técnicas](./README.md)
- [Ver ejemplos detallados](./EXAMPLES.md)
- [Ver plantilla base](./banner-readme-template.svg)

---

**Fecha:** 2026-08-15
