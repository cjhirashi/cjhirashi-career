import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/api/client'
import { trackingApi } from '@/api/tracking'
import { getVisitorId } from '@/utils/tracker'

vi.mock('@/api/client', () => ({ apiClient: { post: vi.fn().mockResolvedValue({}), postBeacon: vi.fn() } }))

beforeEach(() => {
  vi.clearAllMocks()
  window.localStorage.clear()
  window.sessionStorage.clear()
  vi.stubEnv('VITE_PORTAL_SITE_KEY', 'site-key-1')
})
afterEach(() => {
  vi.unstubAllEnvs()
})

describe('trackingApi', () => {
  it('todo evento lleva siteKey, visitorId, sessionId y token del dueño', async () => {
    window.localStorage.setItem('portfolio_owner_token', 'tok-1')
    await trackingApi.trackEvent({ type: 'click', page: '/', target: 'x' })
    const sent = vi.mocked(apiClient.post).mock.calls[0][1] as Record<string, unknown>
    expect(vi.mocked(apiClient.post).mock.calls[0][0]).toBe('/events/track')
    expect(sent).toMatchObject({ type: 'click', siteKey: 'site-key-1', visitorId: getVisitorId(), ownerToken: 'tok-1' })
    expect(sent.sessionId).toBeTruthy()
  })

  it('el envío por beacon lleva los mismos campos comunes', () => {
    trackingApi.trackEventBeacon({ type: 'page_leave', page: '/' })
    const [url, body] = vi.mocked(apiClient.postBeacon).mock.calls[0]
    expect(url).toBe('/events/track')
    expect(body).toMatchObject({ type: 'page_leave', siteKey: 'site-key-1', visitorId: getVisitorId() })
  })

  it('un fallo de red no interrumpe al visitante', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce(new Error('offline'))
    vi.spyOn(console, 'error').mockImplementation(() => {})
    await expect(trackingApi.trackEvent({ type: 'click', page: '/' })).resolves.toBeUndefined()
  })

  it('RF-053 forgetMe pide el borrado con el id actual y genera uno nuevo', async () => {
    const before = getVisitorId()
    await trackingApi.forgetMe()
    expect(apiClient.post).toHaveBeenCalledWith('/events/forget', { siteKey: 'site-key-1', visitorId: before })
    expect(getVisitorId()).not.toBe(before)
  })

  it('RF-053 si el borrado falla, conserva el id para poder reintentar', async () => {
    const before = getVisitorId()
    vi.mocked(apiClient.post).mockRejectedValueOnce(new Error('500'))
    await expect(trackingApi.forgetMe()).rejects.toThrow()
    expect(getVisitorId()).toBe(before)
  })
})

describe('RF-053 tras borrar los datos no se vuelve a medir hasta recargar', () => {
  const fresh = async () => {
    vi.resetModules()
    vi.doMock('@/api/client', () => ({ apiClient: { post: vi.fn().mockResolvedValue({}), postBeacon: vi.fn() } }))
    const client = (await import('@/api/client')).apiClient
    const api = (await import('@/api/tracking')).trackingApi
    return { client, api }
  }

  it('después de forgetMe ni los eventos normales ni los de salida se envían', async () => {
    const { client, api } = await fresh()
    await api.forgetMe()
    vi.mocked(client.post).mockClear()

    await api.trackEvent({ type: 'pageview', page: '/privacy' })
    api.trackEventBeacon({ type: 'page_leave', page: '/privacy', activeMs: 900 })

    expect(client.post).not.toHaveBeenCalled()
    expect(client.postBeacon).not.toHaveBeenCalled()
  })

  it('si el borrado falla, el rastreo sigue activo', async () => {
    const { client, api } = await fresh()
    vi.mocked(client.post).mockRejectedValueOnce(new Error('500'))
    await expect(api.forgetMe()).rejects.toThrow()

    await api.trackEvent({ type: 'click', page: '/privacy' })
    expect(client.post).toHaveBeenLastCalledWith('/events/track', expect.objectContaining({ type: 'click' }))
  })
})
