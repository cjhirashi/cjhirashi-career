// ---------------------------------------------------------------------------
// Configuracion centralizada de la app.
//
// Prioridad de resolucion (de mayor a menor):
//   1. window.__MCP_CONFIG__   -> inyectado en runtime por docker-entrypoint.sh
//                                  (produccion, un solo build para todos los entornos)
//   2. import.meta.env.VITE_*  -> variables de build (desarrollo local con Vite)
//   3. Defaults calculados a partir de window.location (same-origin)
//
// Todas las rutas (SSE_PATH, FILES_BASE_PATH) son RELATIVAS al origen actual
// del frontend a proposito: tanto nginx (produccion) como el proxy de Vite
// (desarrollo) exponen /sse, /messages y /files como si fueran parte del
// mismo servidor, evitando por completo problemas de CORS y el uso de
// nombres DNS internos de Docker (p. ej. "mcp_tools_server") que no son
// resolubles desde el navegador del usuario.
// ---------------------------------------------------------------------------

declare global {
  interface Window {
    __MCP_CONFIG__?: {
      APP_NAME?: string;
      SSE_PATH?: string;
      FILES_BASE_PATH?: string;
    };
  }
}

function firstNonEmpty(...values: Array<string | undefined>): string | undefined {
  return values.find((v) => typeof v === "string" && v.trim().length > 0);
}

const runtimeConfig = typeof window !== "undefined" ? window.__MCP_CONFIG__ : undefined;

export const APP_NAME: string =
  firstNonEmpty(runtimeConfig?.APP_NAME, import.meta.env.VITE_APP_NAME) ??
  "MCP Tools Server";

export const SSE_PATH: string =
  firstNonEmpty(runtimeConfig?.SSE_PATH, import.meta.env.VITE_MCP_SSE_PATH) ?? "/sse";

export const FILES_BASE_PATH: string =
  firstNonEmpty(runtimeConfig?.FILES_BASE_PATH, import.meta.env.VITE_FILES_BASE_PATH) ??
  "/files";

/** URL absoluta del endpoint SSE, resuelta contra el origen actual. */
export function getSseUrl(): string {
  if (/^https?:\/\//i.test(SSE_PATH)) return SSE_PATH;
  return new URL(SSE_PATH, window.location.origin).toString();
}

/** URL base absoluta para archivos generados, resuelta contra el origen actual. */
export function getFilesBaseUrl(): string {
  if (/^https?:\/\//i.test(FILES_BASE_PATH)) return FILES_BASE_PATH;
  return new URL(FILES_BASE_PATH, window.location.origin).toString();
}

export const HISTORY_STORAGE_KEY = "mcp-frontend:history:v1";
export const THEME_STORAGE_KEY = "mcp-frontend:theme";
export const DRAFT_STORAGE_PREFIX = "mcp-frontend:draft:";

/** Timeouts de la capa de transporte MCP (ms). */
export const MCP_TIMEOUTS = {
  connectMs: 15_000,
  initializeMs: 15_000,
  toolCallMs: 120_000, // generar PDFs puede tardar unos segundos, damos margen
  reconnectBaseMs: 1_000,
  reconnectMaxMs: 30_000,
};
