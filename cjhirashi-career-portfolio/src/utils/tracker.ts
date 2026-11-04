/**
 * Identidad, privacidad y atribución del rastreador (SPEC-0010, RF-050, RF-052, RF-054).
 * Nada aquí envía eventos: solo decide qué id usar y qué campos comunes llevan.
 */
import type { TrackingEvent } from '@/types'

const VISITOR_KEY = 'portfolio_visitor_id'
const TAB_KEY = 'portfolio_tab_id'
const SESSION_KEY = 'portfolio_session_id'
const OWNER_KEY = 'portfolio_owner_token'
const ATTRIBUTION_SENT_KEY = 'portfolio_attribution_sent'

const UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'] as const
const CLICK_ID_KEYS = ['gclid', 'fbclid', 'msclkid', 'ttclid', 'twclid', 'li_fat_id'] as const

export interface Attribution {
  referrer?: string
  utm?: Record<string, string>
  clickIds?: Record<string, string>
}

// Tras pedir el borrado el visitante no vuelve a medirse hasta recargar la página:
// de lo contrario la propia página de privacidad le crearía un id nuevo al salir.
let suppressed = false
export const suppressTracking = (): void => {
  suppressed = true
}
export const isTrackingSuppressed = (): boolean => suppressed

export const isTrackingEnabled = (): boolean => import.meta.env.VITE_TRACKING_ENABLED !== 'false' && !suppressed

export const generateId = (): string =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`

// Si el navegador bloquea el almacenamiento, el id vive en memoria: la pestaña
// sigue contando como un visitante, pero no se agrupa entre cargas completas.
const memory: Record<string, string> = {}

const readOrCreate = (store: () => Storage, key: string): string => {
  try {
    const existing = store().getItem(key)
    if (existing) return existing
    const fresh = generateId()
    store().setItem(key, fresh)
    return fresh
  } catch {
    memory[key] ??= generateId()
    return memory[key]
  }
}

/** Do Not Track o Global Privacy Control activos (RF-050). */
export const hasPrivacySignal = (): boolean => {
  const nav = navigator as Navigator & { globalPrivacyControl?: boolean; msDoNotTrack?: string }
  const win = window as Window & { doNotTrack?: string }
  return (
    nav.doNotTrack === '1' ||
    nav.doNotTrack === 'yes' ||
    win.doNotTrack === '1' ||
    nav.msDoNotTrack === '1' ||
    nav.globalPrivacyControl === true
  )
}

/** Id persistente en localStorage; con DNT/GPC, un id que muere con la pestaña. */
export const getVisitorId = (): string =>
  hasPrivacySignal() ? readOrCreate(() => window.sessionStorage, TAB_KEY) : readOrCreate(() => window.localStorage, VISITOR_KEY)

/** Una visita = una pestaña (sessionStorage). */
export const getSessionId = (): string => readOrCreate(() => window.sessionStorage, SESSION_KEY)

/** Borra el id local para que el siguiente evento sea de un visitante nuevo (RF-053). */
export const resetVisitorId = (): void => {
  try {
    window.localStorage.removeItem(VISITOR_KEY)
    window.sessionStorage.removeItem(TAB_KEY)
  } catch {
    // sin almacenamiento no hay nada que borrar
  }
  delete memory[VISITOR_KEY]
  delete memory[TAB_KEY]
}

/** `/?owner=<token>`: guarda el token y lo quita de la URL (RF-054). */
export const captureOwnerToken = (): void => {
  try {
    const url = new URL(window.location.href)
    const token = url.searchParams.get('owner')
    if (!token) return
    window.localStorage.setItem(OWNER_KEY, token)
    url.searchParams.delete('owner')
    window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}${url.hash}`)
  } catch {
    // el rastreo nunca debe romper la página
  }
}

export const getOwnerToken = (): string | undefined => {
  try {
    return window.localStorage.getItem(OWNER_KEY) ?? undefined
  } catch {
    return undefined
  }
}

/** Referrer externo, UTM e identificadores de clic de una URL de entrada (RF-052). */
export const parseAttribution = (search: string, referrer: string, host: string): Attribution => {
  const out: Attribution = {}
  try {
    if (referrer && new URL(referrer).host !== host) out.referrer = referrer.slice(0, 1024)
  } catch {
    // referrer ilegible: se ignora
  }
  const params = new URLSearchParams(search)
  const pick = (keys: readonly string[]) => {
    const found: Record<string, string> = {}
    for (const key of keys) {
      const value = params.get(key)
      if (value) found[key] = value.slice(0, 255)
    }
    return Object.keys(found).length ? found : undefined
  }
  const utm = pick(UTM_KEYS)
  const clickIds = pick(CLICK_ID_KEYS)
  if (utm) out.utm = utm
  if (clickIds) out.clickIds = clickIds
  return out
}

/** La atribución viaja solo en el primer pageview de la visita; después, `null`. */
export const takeAttribution = (): Attribution | null => {
  try {
    if (window.sessionStorage.getItem(ATTRIBUTION_SENT_KEY)) return null
    window.sessionStorage.setItem(ATTRIBUTION_SENT_KEY, '1')
  } catch {
    // sin sessionStorage: se envía en cada pageview, no se pierde
  }
  return parseAttribution(window.location.search, document.referrer, window.location.host)
}

/** Campos que llevan todos los eventos. */
export const getCommonFields = (): Pick<TrackingEvent, 'siteKey' | 'visitorId' | 'sessionId' | 'ownerToken' | 'screen' | 'title'> => ({
  siteKey: import.meta.env.VITE_PORTAL_SITE_KEY || undefined,
  visitorId: getVisitorId(),
  sessionId: getSessionId(),
  ownerToken: getOwnerToken(),
  screen: `${window.screen.width}x${window.screen.height}`,
  title: document.title ? document.title.slice(0, 500) : undefined,
})
