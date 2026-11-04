import { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { trackingApi } from '@/api/tracking'
import {
  classifyLink,
  useCaptureOwnerToken,
  useTrackLinks,
  useTrackPageview,
  useTrackProjectOpen,
  useTrackWebVitals,
} from '@/hooks/useTracking'

vi.mock('@/api/tracking')

const vitalsCallbacks: Record<string, (m: { value: number }) => void> = {}
vi.mock('web-vitals', () => ({
  onLCP: (cb: (m: { value: number }) => void) => (vitalsCallbacks.lcp = cb),
  onINP: (cb: (m: { value: number }) => void) => (vitalsCallbacks.inp = cb),
  onCLS: (cb: (m: { value: number }) => void) => (vitalsCallbacks.cls = cb),
  onFCP: (cb: (m: { value: number }) => void) => (vitalsCallbacks.fcp = cb),
  onTTFB: (cb: (m: { value: number }) => void) => (vitalsCallbacks.ttfb = cb),
}))

const wrapper = ({ children }: { children: ReactNode }) => <MemoryRouter initialEntries={['/projects']}>{children}</MemoryRouter>
const anchor = (href: string, attrs: Record<string, string> = {}) => {
  const a = document.createElement('a')
  a.setAttribute('href', href)
  for (const [k, v] of Object.entries(attrs)) a.setAttribute(k, v)
  document.body.appendChild(a)
  return a as HTMLAnchorElement
}
const setVisibility = (state: 'visible' | 'hidden') => {
  Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => state })
  document.dispatchEvent(new Event('visibilitychange'))
}

beforeEach(() => {
  vi.clearAllMocks()
  window.localStorage.clear()
  window.sessionStorage.clear()
  window.history.replaceState(null, '', '/')
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date', 'performance'] })
})
afterEach(() => {
  vi.useRealTimers()
  document.body.innerHTML = ''
  setVisibility('visible')
})

describe('RF-052 useTrackPageview', () => {
  it('manda el pageview con referrer y UTM solo en la primera página', () => {
    window.history.replaceState(null, '', '/?utm_source=linkedin')
    Object.defineProperty(document, 'referrer', { configurable: true, value: 'https://www.google.com/' })
    renderHook(() => useTrackPageview(), { wrapper })

    expect(trackingApi.trackEvent).toHaveBeenCalledTimes(1)
    expect(trackingApi.trackEvent).toHaveBeenCalledWith({
      type: 'pageview',
      page: '/projects',
      referrer: 'https://www.google.com/',
      utm: { utm_source: 'linkedin' },
    })
  })

  it('la segunda página de la visita ya no lleva atribución', () => {
    window.sessionStorage.setItem('portfolio_attribution_sent', '1')
    renderHook(() => useTrackPageview(), { wrapper })
    expect(trackingApi.trackEvent).toHaveBeenCalledWith({ type: 'pageview', page: '/projects' })
  })
})

describe('RF-051 page_leave', () => {
  it('al salir manda un único page_leave con tiempo activo y scroll', () => {
    const { unmount } = renderHook(() => useTrackPageview(), { wrapper })
    window.dispatchEvent(new Event('pointerdown'))
    act(() => vi.advanceTimersByTime(3000))
    unmount()

    const leaves = vi.mocked(trackingApi.trackEventBeacon).mock.calls.filter(([e]) => e.type === 'page_leave')
    expect(leaves).toHaveLength(1)
    expect(leaves[0][0]).toMatchObject({ type: 'page_leave', page: '/projects' })
    expect(leaves[0][0].activeMs).toBeGreaterThanOrEqual(0)
    expect(leaves[0][0]).toHaveProperty('scrollPct')
    expect(leaves[0][0].durationMs).toBeGreaterThanOrEqual(100)
  })

  it('ocultar la pestaña y salir no duplica el aviso', () => {
    const { unmount } = renderHook(() => useTrackPageview(), { wrapper })
    act(() => vi.advanceTimersByTime(2000))
    setVisibility('hidden')
    unmount()
    expect(vi.mocked(trackingApi.trackEventBeacon).mock.calls.filter(([e]) => e.type === 'page_leave')).toHaveLength(1)
  })

  it('nunca manda page_duration (el servidor ya suma page_leave)', () => {
    const { unmount } = renderHook(() => useTrackPageview(), { wrapper })
    act(() => vi.advanceTimersByTime(2000))
    unmount()
    expect(vi.mocked(trackingApi.trackEventBeacon).mock.calls.some(([e]) => e.type === 'page_duration')).toBe(false)
  })
})

describe('RF-051 enlaces salientes y descargas', () => {
  it('classifyLink distingue saliente, descarga y enlace interno', () => {
    expect(classifyLink(anchor('https://github.com/cjhirashi?tab=repos'), 'cjhirashi.com')).toEqual({
      type: 'outbound',
      target: 'github.com',
      targetUrl: 'https://github.com/cjhirashi',
    })
    expect(classifyLink(anchor('https://cjhirashi.com/files/CV%20Carlos.pdf?x=1'), 'cjhirashi.com')).toEqual({
      type: 'download',
      target: 'CV Carlos.pdf',
      targetUrl: 'https://cjhirashi.com/files/CV%20Carlos.pdf',
    })
    expect(classifyLink(anchor('/blog', { download: 'archivo.bin' }), 'localhost:3000')?.type).toBe('download')
    expect(classifyLink(anchor('https://cjhirashi.com/projects'), 'cjhirashi.com')).toBeNull()
    expect(classifyLink(anchor('mailto:a@b.com'), 'cjhirashi.com')).toBeNull()
  })

  it('un clic en un enlace externo manda un evento outbound sin query ni hash', () => {
    renderHook(() => useTrackLinks(), { wrapper })
    const link = anchor('https://www.linkedin.com/in/cjhirashi?utm=1#x')
    link.click()
    expect(trackingApi.trackEventBeacon).toHaveBeenCalledWith({
      type: 'outbound',
      target: 'www.linkedin.com',
      targetUrl: 'https://www.linkedin.com/in/cjhirashi',
      page: window.location.pathname,
    })
  })

  it('un clic fuera de un enlace no manda nada', () => {
    renderHook(() => useTrackLinks(), { wrapper })
    document.body.click()
    expect(trackingApi.trackEventBeacon).not.toHaveBeenCalled()
  })
})

describe('RF-051 Web Vitals', () => {
  it('manda LCP, INP y CLS al ocultar la pestaña, una sola vez por valor', () => {
    renderHook(() => useTrackWebVitals(), { wrapper })
    vitalsCallbacks.lcp({ value: 1200 })
    vitalsCallbacks.inp({ value: 80 })
    vitalsCallbacks.cls({ value: 0.02 })
    setVisibility('hidden')
    setVisibility('hidden')

    expect(trackingApi.trackEventBeacon).toHaveBeenCalledTimes(1)
    expect(trackingApi.trackEventBeacon).toHaveBeenCalledWith({
      type: 'web_vitals',
      page: window.location.pathname,
      vitals: { lcp: 1200, inp: 80, cls: 0.02 },
    })
  })

  it('sin ninguna métrica no manda nada', () => {
    renderHook(() => useTrackWebVitals(), { wrapper })
    setVisibility('hidden')
    expect(trackingApi.trackEventBeacon).not.toHaveBeenCalled()
  })
})

describe('RF-051 apertura de proyecto', () => {
  it('manda project_open con el slug', () => {
    renderHook(() => useTrackProjectOpen('mi-proyecto', 'prj-1'), { wrapper })
    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'project_open', target: 'mi-proyecto', props: { projectId: 'prj-1', slug: 'mi-proyecto' } })
    )
  })

  it('sin slug no manda nada', () => {
    renderHook(() => useTrackProjectOpen(null, 'prj-1'), { wrapper })
    expect(trackingApi.trackEvent).not.toHaveBeenCalled()
  })
})

describe('RF-054 useCaptureOwnerToken', () => {
  it('guarda el token del dueño al montar', () => {
    window.history.replaceState(null, '', '/?owner=tok-77')
    renderHook(() => useCaptureOwnerToken(), { wrapper })
    expect(window.localStorage.getItem('portfolio_owner_token')).toBe('tok-77')
  })
})
