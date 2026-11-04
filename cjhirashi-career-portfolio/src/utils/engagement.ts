/**
 * Mide una página: tiempo activo (pestaña visible y con interacción reciente)
 * y profundidad máxima de scroll (SPEC-0010, RF-051).
 */
export const IDLE_MS = 30_000
export const TICK_MS = 1_000

const INTERACTION_EVENTS = ['pointerdown', 'pointermove', 'keydown', 'scroll', 'touchstart', 'wheel'] as const

export interface EngagementSnapshot {
  activeMs: number
  scrollPct: number
  durationMs: number
}

export class PageEngagement {
  private activeMs = 0
  private maxScroll = 0
  private startedAt = 0
  private lastTick = 0
  private lastInteraction = 0
  private timer: ReturnType<typeof setInterval> | null = null

  constructor(private readonly now: () => number = () => performance.now()) {}

  start(): void {
    this.startedAt = this.lastTick = this.lastInteraction = this.now()
    for (const name of INTERACTION_EVENTS) window.addEventListener(name, this.onInteraction, { passive: true })
    window.addEventListener('scroll', this.sampleScroll, { passive: true })
    this.timer = setInterval(this.tick, TICK_MS)
    this.sampleScroll()
  }

  stop(): void {
    for (const name of INTERACTION_EVENTS) window.removeEventListener(name, this.onInteraction)
    window.removeEventListener('scroll', this.sampleScroll)
    if (this.timer) clearInterval(this.timer)
    this.timer = null
  }

  snapshot(): EngagementSnapshot {
    this.tick()
    this.sampleScroll()
    return {
      activeMs: Math.round(this.activeMs),
      scrollPct: this.maxScroll,
      durationMs: Math.round(this.now() - this.startedAt),
    }
  }

  /** Tras reportar un tramo: el tiempo vuelve a cero, el scroll máximo se conserva. */
  resetSegment(): void {
    this.activeMs = 0
    this.startedAt = this.lastTick = this.now()
  }

  private onInteraction = (): void => {
    this.lastInteraction = this.now()
  }

  // Suma el tiempo real transcurrido (con tope por si el equipo estuvo dormido).
  private tick = (): void => {
    const t = this.now()
    const delta = Math.min(t - this.lastTick, 2 * TICK_MS)
    this.lastTick = t
    if (delta > 0 && document.visibilityState === 'visible' && t - this.lastInteraction <= IDLE_MS) {
      this.activeMs += delta
    }
  }

  private sampleScroll = (): void => {
    const total = document.documentElement.scrollHeight
    if (!total) return
    const pct = Math.round(((window.scrollY + window.innerHeight) / total) * 100)
    this.maxScroll = Math.max(this.maxScroll, Math.min(100, Math.max(0, pct)))
  }
}
