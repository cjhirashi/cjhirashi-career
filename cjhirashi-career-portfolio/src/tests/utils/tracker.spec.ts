import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import {
  captureOwnerToken,
  getCommonFields,
  getOwnerToken,
  getVisitorId,
  hasPrivacySignal,
  parseAttribution,
  resetVisitorId,
  takeAttribution,
} from '@/utils/tracker'

const setNavigator = (props: Record<string, unknown>) => {
  for (const [key, value] of Object.entries(props)) {
    Object.defineProperty(navigator, key, { configurable: true, get: () => value })
  }
}
const clearNavigator = () => {
  for (const key of ['doNotTrack', 'globalPrivacyControl']) delete (navigator as unknown as Record<string, unknown>)[key]
}

beforeEach(() => {
  window.localStorage.clear()
  window.sessionStorage.clear()
  window.history.replaceState(null, '', '/')
})
afterEach(() => {
  clearNavigator()
  vi.restoreAllMocks()
  vi.unstubAllEnvs()
})

describe('RF-050 visitorId', () => {
  it('crea un id aleatorio en localStorage y lo reutiliza', () => {
    const first = getVisitorId()
    expect(first).toMatch(/^[A-Za-z0-9_-]+$/)
    expect(window.localStorage.getItem('portfolio_visitor_id')).toBe(first)
    expect(getVisitorId()).toBe(first)
  })

  it('con Do Not Track usa solo un id de pestaña y no toca localStorage', () => {
    setNavigator({ doNotTrack: '1' })
    expect(hasPrivacySignal()).toBe(true)
    const id = getVisitorId()
    expect(window.localStorage.getItem('portfolio_visitor_id')).toBeNull()
    expect(window.sessionStorage.getItem('portfolio_tab_id')).toBe(id)
  })

  it('con Global Privacy Control usa solo un id de pestaña', () => {
    setNavigator({ globalPrivacyControl: true })
    expect(hasPrivacySignal()).toBe(true)
    getVisitorId()
    expect(window.localStorage.getItem('portfolio_visitor_id')).toBeNull()
  })

  it('con DNT no reutiliza un id persistente que quedó de antes', () => {
    const persistent = getVisitorId()
    setNavigator({ doNotTrack: '1' })
    expect(getVisitorId()).not.toBe(persistent)
  })

  it('si el almacenamiento está bloqueado, el id vive en memoria', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    const id = getVisitorId()
    expect(id).toBeTruthy()
    expect(getVisitorId()).toBe(id)
  })

  it('resetVisitorId genera uno distinto en la siguiente lectura', () => {
    const before = getVisitorId()
    resetVisitorId()
    expect(getVisitorId()).not.toBe(before)
  })
})

describe('RF-052 referrer, UTM e identificadores de clic', () => {
  it('toma el referrer externo y descarta el del propio sitio', () => {
    expect(parseAttribution('', 'https://www.google.com/search?q=x', 'cjhirashi.com').referrer).toBe('https://www.google.com/search?q=x')
    expect(parseAttribution('', 'https://cjhirashi.com/about', 'cjhirashi.com').referrer).toBeUndefined()
    expect(parseAttribution('', '', 'cjhirashi.com').referrer).toBeUndefined()
    expect(parseAttribution('', 'no es una url', 'cjhirashi.com').referrer).toBeUndefined()
  })

  it('conserva solo UTM e identificadores de clic conocidos', () => {
    const out = parseAttribution('?utm_source=linkedin&utm_campaign=cv&foo=bar&gclid=abc&token=secreto', '', 'cjhirashi.com')
    expect(out.utm).toEqual({ utm_source: 'linkedin', utm_campaign: 'cv' })
    expect(out.clickIds).toEqual({ gclid: 'abc' })
  })

  it('la atribución viaja una sola vez por visita', () => {
    window.history.replaceState(null, '', '/?utm_source=linkedin')
    expect(takeAttribution()?.utm).toEqual({ utm_source: 'linkedin' })
    expect(takeAttribution()).toBeNull()
  })
})

describe('RF-054 token del dueño', () => {
  it('guarda el token de ?owner= y lo quita de la URL', () => {
    window.history.replaceState(null, '', '/projects?owner=tok-123&x=1#top')
    captureOwnerToken()
    expect(getOwnerToken()).toBe('tok-123')
    expect(window.location.search).toBe('?x=1')
    expect(window.location.pathname + window.location.hash).toBe('/projects#top')
  })

  it('sin ?owner= no cambia nada', () => {
    captureOwnerToken()
    expect(getOwnerToken()).toBeUndefined()
  })

  it('el token guardado viaja en los campos comunes de todo evento', () => {
    window.localStorage.setItem('portfolio_owner_token', 'tok-9')
    vi.stubEnv('VITE_PORTAL_SITE_KEY', 'site-key-1')
    const common = getCommonFields()
    expect(common.ownerToken).toBe('tok-9')
    expect(common.siteKey).toBe('site-key-1')
    expect(common.visitorId).toBe(getVisitorId())
  })
})
