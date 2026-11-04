import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { IDLE_MS, PageEngagement } from '@/utils/engagement'

let now = 0
let visibility: 'visible' | 'hidden' = 'visible'
const setScroll = (scrollY: number, total = 2000, viewport = 800) => {
  Object.defineProperty(document.documentElement, 'scrollHeight', { configurable: true, value: total })
  Object.defineProperty(window, 'innerHeight', { configurable: true, value: viewport })
  Object.defineProperty(window, 'scrollY', { configurable: true, value: scrollY })
}
const advance = (ms: number) => {
  now += ms
}

let engagement: PageEngagement
beforeEach(() => {
  vi.useFakeTimers()
  now = 0
  visibility = 'visible'
  Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => visibility })
  setScroll(0)
  engagement = new PageEngagement(() => now)
})
afterEach(() => {
  engagement.stop()
  vi.useRealTimers()
})

describe('RF-051 tiempo activo', () => {
  it('cuenta el tiempo con la pestaña visible e interacción reciente', () => {
    engagement.start()
    advance(1000)
    window.dispatchEvent(new Event('pointermove'))
    advance(1000)
    expect(engagement.snapshot().activeMs).toBe(2000)
  })

  it('no cuenta el tiempo sin interacción pasados 30 s', () => {
    engagement.start()
    advance(IDLE_MS)
    engagement.snapshot() // dentro del margen
    for (let i = 0; i < 10; i++) {
      advance(1000)
      engagement.snapshot()
    }
    const after = engagement.snapshot().activeMs
    advance(5000)
    expect(engagement.snapshot().activeMs).toBe(after)
  })

  it('no cuenta el tiempo con la pestaña oculta', () => {
    engagement.start()
    visibility = 'hidden'
    advance(1000)
    expect(engagement.snapshot().activeMs).toBe(0)
  })

  it('no suma de golpe un salto largo (equipo dormido)', () => {
    engagement.start()
    advance(10 * 60 * 1000)
    expect(engagement.snapshot().activeMs).toBeLessThanOrEqual(2000)
  })

  it('mide la duración total aunque no haya actividad', () => {
    engagement.start()
    advance(4000)
    expect(engagement.snapshot().durationMs).toBe(4000)
  })

  it('resetSegment pone el tiempo en cero y conserva el scroll máximo', () => {
    engagement.start()
    setScroll(1200)
    advance(1000)
    window.dispatchEvent(new Event('scroll'))
    expect(engagement.snapshot().scrollPct).toBe(100)
    engagement.resetSegment()
    const after = engagement.snapshot()
    expect(after.activeMs).toBe(0)
    expect(after.scrollPct).toBe(100)
  })
})

describe('RF-051 profundidad de scroll', () => {
  it('guarda el máximo, no el último valor', () => {
    engagement.start()
    setScroll(600)
    window.dispatchEvent(new Event('scroll'))
    setScroll(100)
    window.dispatchEvent(new Event('scroll'))
    expect(engagement.snapshot().scrollPct).toBe(70)
  })

  it('una página que cabe en la pantalla cuenta como 100 %', () => {
    setScroll(0, 700, 800)
    engagement.start()
    expect(engagement.snapshot().scrollPct).toBe(100)
  })
})
