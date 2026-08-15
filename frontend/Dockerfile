# syntax=docker/dockerfile:1
#
# Frontend de MCP Tools Server (React + TypeScript + Vite + Tailwind).
#
# Build multi-stage:
#   1. "build"   -> instala dependencias y genera el bundle estatico (dist/)
#   2. "runtime" -> sirve el bundle con Node.js (http-server)
#
# El reverse proxy (Caddy) en la red externa maneja enrutamiento y SSL.

# ---------------------------------------------------------------------------
# Etapa 1: build
# ---------------------------------------------------------------------------
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---------------------------------------------------------------------------
# Etapa 2: runtime
# ---------------------------------------------------------------------------
FROM node:20-alpine

WORKDIR /app

# Instalar http-server para servir archivos estaticos
RUN npm install -g http-server

# Copiar bundle compilado
COPY --from=build /app/dist ./dist

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8000/ >/dev/null 2>&1 || exit 1

# Servir archivos estaticos en puerto 8000
CMD ["http-server", "dist", "-p", "8000", "--cors"]
