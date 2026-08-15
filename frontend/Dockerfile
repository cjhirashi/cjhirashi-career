# Frontend Dockerfile (template)
#
# Este Dockerfile es un placeholder. Sera reemplazado cuando el especialista
# mcp-frontend-ui implemente la interfaz web (React/Vue/Svelte).
#
# Convenciones esperadas:
#   - WORKDIR /app
#   - COPY . /app
#   - Puerto interno expuesto: 8000 (mapeado a 8003 en docker-compose.yml raiz)
#   - Variable de entorno MCP_SERVER_URL apuntando a http://mcp_tools_server:8000/sse
#
# Ejemplo (Node.js + Vite, ajustar segun stack elegido):
#
# FROM node:20-alpine AS build
# WORKDIR /app
# COPY package*.json ./
# RUN npm install
# COPY . .
# RUN npm run build
#
# FROM node:20-alpine
# WORKDIR /app
# COPY --from=build /app/dist ./dist
# COPY --from=build /app/package*.json ./
# RUN npm install --omit=dev
# EXPOSE 8000
# CMD ["npm", "run", "start"]

FROM node:20-alpine

WORKDIR /app

# TODO: Implementar build real del frontend
COPY . /app

EXPOSE 8000

CMD ["echo", "Frontend no implementado todavia. Ver frontend/README.md"]
