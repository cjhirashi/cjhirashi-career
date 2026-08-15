import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  // Target del servidor MCP (contenedor mcp_tools_server) para desarrollo local.
  // En produccion, nginx hace este mismo proxy (ver frontend/nginx.conf).
  // Por defecto apunta al puerto expuesto en el host (docker-compose.yml raiz: "8002:8000").
  const proxyTarget = env.VITE_MCP_PROXY_TARGET || "http://localhost:8002";

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: true,
      port: 5173,
      proxy: {
        // Handshake SSE del protocolo MCP
        "/sse": {
          target: proxyTarget,
          changeOrigin: true,
          ws: false,
        },
        // Endpoint de mensajes JSON-RPC (sesion generada dinamicamente por el server MCP)
        "/messages": {
          target: proxyTarget,
          changeOrigin: true,
        },
        // Archivos generados (requiere que el proxyTarget tambien sirva /files;
        // en dev puro contra el server MCP esto no esta disponible salvo que se
        // apunte VITE_MCP_PROXY_TARGET a una instancia del frontend en produccion).
        "/files": {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: true,
      port: 4173,
    },
    build: {
      outDir: "dist",
      sourcemap: false,
      target: "es2020",
    },
  };
});
