/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_NAME?: string;
  readonly VITE_MCP_SSE_PATH?: string;
  readonly VITE_FILES_BASE_PATH?: string;
  readonly VITE_MCP_PROXY_TARGET?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
