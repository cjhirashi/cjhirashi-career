# ADR-031: Las fichas de proyecto pueden embeber HTML y mostrar imágenes publicados desde Synapse

## Estado

Aceptado — 2026-11-07 (petición de Carlos; implementado directo, sin spec).

## Contexto

Los agentes que documentan proyectos (AIRA, Tukey, Banzi) generan diagramas Archify y gráficas Plotly como HTML autocontenido y capturas como imágenes, y los guardan en Synapse. Subirlos a `files.cjhirashi.com` exige un token con rol `agent` que solo tienen AIRA y Paulina, y la herramienta `career_api` no alcanza `/files`. El bloque ` ```archify ` del portafolio solo aceptaba el host `files.cjhirashi.com`.

## Decisión

- El renderizador de markdown del portafolio (`Markdown.tsx`) acepta también URLs `https://synapse.cjhirashi.com/files/<uuid>` (solo esa ruta, con id UUID) en los bloques de contenido interactivo. Cualquier otro host o ruta muestra un error visible, como antes.
- Los bloques se pueden escribir como ` ```archify `, ` ```plotly ` o ` ```embed `; los tres usan el mismo iframe (`sandbox="allow-scripts allow-same-origin"`, 34 rem de alto).
- Las imágenes ya funcionaban con `![alt](url)` desde cualquier origen; no hubo cambio.
- El archivo debe ser **público** en Synapse (lo decide Carlos): uno privado devuelve 401 y el marco queda vacío.

## Seguridad

Synapse sirve sus HTML con `Content-Security-Policy: sandbox allow-scripts; default-src 'none'; connect-src 'none'`, sin `frame-ancestors` ni `X-Frame-Options`. El documento corre aislado, sin cookies, sin acceso a la sesión del portafolio ni a la red, y puede ser embebido desde otro origen. Por eso la lista blanca de hosts basta y no hizo falta tocar el servidor de Synapse.

## Verificación

2026-11-07, en producción con un proyecto temporal (ya eliminado): una imagen pública de Synapse cargó, un bloque `plotly` hacia una URL válida de Synapse generó su iframe, y una ruta no permitida de Synapse y un host ajeno mostraron el error. Sin errores de consola. No había aún un HTML público en Synapse; la política de cabeceras del HTML se verificó en `backend/app/routers/files.py`, no con un HTML real embebido.

## Consecuencias

- Tukey y Banzi publican gráficas y diagramas sin pasar por AIRA.
- Pendiente: probar con el primer HTML público real de Plotly o Archify.
