/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_TRACKING_ENABLED: string
  readonly VITE_PORTAL_SITE_KEY?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
