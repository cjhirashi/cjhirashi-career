/**
 * Envía una falla del SPA al registro central del sistema
 * (`POST /system/error-report`, ADR-018). Fire-and-forget: nunca lanza,
 * nunca bloquea, y usa `fetch` crudo para no re-entrar en el interceptor
 * de axios.
 */
// Inline (no import de '@/api/client') para evitar un ciclo de módulos con el
// interceptor de axios, que a su vez importa este archivo.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api'
const ENDPOINT = `${API_BASE_URL.replace(/\/$/, '')}/system/error-report`
const DEDUPE_WINDOW_MS = 10_000
const recent = new Map<string, number>()

export type ClientErrorSeverity = 'warning' | 'error' | 'critical'

interface ReportInput {
  message: string
  source: string
  severity?: ClientErrorSeverity
  error_type?: string
  stack_trace?: string
  context?: Record<string, unknown>
}

function shouldSkip(key: string): boolean {
  const now = Date.now()
  for (const [k, ts] of recent) {
    if (now - ts > DEDUPE_WINDOW_MS) recent.delete(k)
  }
  if (recent.has(key)) return true
  recent.set(key, now)
  return false
}

export function reportClientError(input: ReportInput): void {
  try {
    const message = (input.message || '').toString().slice(0, 4000)
    if (!message) return
    // No reportar fallos del propio endpoint de reporte.
    if ((input.context?.url as string | undefined)?.includes('/system/error-report')) return

    const key = `${input.source}|${message}`
    if (shouldSkip(key)) return

    const body = JSON.stringify({
      message,
      source: input.source.slice(0, 255),
      severity: input.severity ?? 'error',
      error_type: input.error_type?.slice(0, 120),
      stack_trace: input.stack_trace?.slice(0, 20000),
      context: { ...input.context, user_agent: navigator.userAgent, path: window.location.pathname },
    })

    void fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
    }).catch(() => {
      /* el registro es best-effort */
    })
  } catch {
    /* nunca romper el flujo del usuario por el registro */
  }
}
