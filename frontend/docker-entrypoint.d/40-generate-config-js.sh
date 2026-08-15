#!/bin/sh
# Generado automaticamente en cada arranque del contenedor por el mecanismo
# oficial de extensibilidad de la imagen nginx:alpine (ejecuta todos los
# scripts en /docker-entrypoint.d/ antes de iniciar nginx).
#
# Escribe /usr/share/nginx/html/config.js con la configuracion en tiempo de
# ejecucion, leida de variables de entorno del contenedor (ver Dockerfile y
# docker-compose.yml). El frontend (src/config.ts) lee este archivo desde
# window.__MCP_CONFIG__.
set -eu

CONFIG_JS="/usr/share/nginx/html/config.js"

cat > "$CONFIG_JS" <<EOF
window.__MCP_CONFIG__ = {
  APP_NAME: "${APP_NAME:-MCP Tools Server}",
  SSE_PATH: "${MCP_SSE_PATH:-/sse}",
  FILES_BASE_PATH: "${MCP_FILES_BASE_PATH:-/files}"
};
EOF

echo "[40-generate-config-js] config.js generado en tiempo de ejecucion:"
cat "$CONFIG_JS"
