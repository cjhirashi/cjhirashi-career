# syntax=docker/dockerfile:1
#
# Frontend de MCP Tools Server (React + TypeScript + Vite + Tailwind).
#
# Build multi-stage:
#   1. "build"   -> instala dependencias y genera el bundle estatico (dist/)
#   2. "runtime" -> sirve el bundle con nginx, actuando ademas como reverse
#                   proxy mismo-origen hacia el servidor MCP (SSE/JSON-RPC)
#                   y como servidor de solo lectura para los PDFs generados
#                   (ver nginx.conf.template para el detalle de rutas).

# ---------------------------------------------------------------------------
# Etapa 1: build
# ---------------------------------------------------------------------------
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

# ---------------------------------------------------------------------------
# Etapa 2: runtime
# ---------------------------------------------------------------------------
FROM nginx:1.27-alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html

# Plantilla de configuracion de nginx: la imagen base ejecuta `envsubst`
# automaticamente sobre /etc/nginx/templates/*.template al arrancar,
# generando /etc/nginx/conf.d/default.conf con las variables de entorno
# (MCP_UPSTREAM, etc.) ya sustituidas.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Hook de arranque (mecanismo oficial /docker-entrypoint.d/ de la imagen
# nginx:alpine): genera config.js con la configuracion en tiempo de
# ejecucion antes de iniciar nginx.
COPY docker-entrypoint.d/40-generate-config-js.sh /docker-entrypoint.d/40-generate-config-js.sh
RUN chmod +x /docker-entrypoint.d/40-generate-config-js.sh

# Valores por defecto; sobreescribibles en docker-compose.yml (raiz) sin
# reconstruir la imagen.
ENV APP_NAME="MCP Tools Server" \
    MCP_UPSTREAM="mcp_tools_server:8000" \
    MCP_SSE_PATH="/sse" \
    MCP_FILES_BASE_PATH="/files"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8000/ >/dev/null 2>&1 || exit 1

# ENTRYPOINT/CMD heredados de la imagen base nginx:alpine
# (/docker-entrypoint.sh -> procesa templates y /docker-entrypoint.d/ ->
# nginx -g 'daemon off;').
