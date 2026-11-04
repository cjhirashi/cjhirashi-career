import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { onCLS, onFCP, onINP, onLCP, onTTFB, type Metric } from 'web-vitals'
import { trackingApi } from '@/api/tracking'
import { PageEngagement } from '@/utils/engagement'
import { captureOwnerToken, isTrackingEnabled, takeAttribution } from '@/utils/tracker'

const FILE_EXTENSION = /\.(pdf|docx?|xlsx?|pptx?|zip|rar|7z|csv|txt|epub)$/i

export interface LinkEvent {
  type: 'download' | 'outbound'
  target: string
  targetUrl: string
}

/** Enlace a un archivo (descarga) o a otro sitio (saliente); el resto no se mide aquí. */
export const classifyLink = (anchor: HTMLAnchorElement, ownHost: string): LinkEvent | null => {
  let url: URL
  try {
    url = new URL(anchor.href)
  } catch {
    return null
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return null
  // Sin query ni hash: pueden llevar tokens.
  const targetUrl = `${url.origin}${url.pathname}`.slice(0, 1024)
  const fileName = decodeURIComponent(url.pathname.split('/').pop() || '')
  if (anchor.hasAttribute('download') || FILE_EXTENSION.test(url.pathname)) {
    return { type: 'download', target: (anchor.getAttribute('download') || fileName).slice(0, 255), targetUrl }
  }
  if (url.host !== ownHost) return { type: 'outbound', target: url.host.slice(0, 255), targetUrl }
  return null
}

/** Pageview (con referrer/UTM en la primera página de la visita) y, al salir, `page_leave`
 * con el tiempo activo y el scroll máximo. `page_leave` es el único aviso pasivo por página:
 * el servidor suma su `activeMs` a la visita. */
export const useTrackPageview = () => {
  const location = useLocation()

  useEffect(() => {
    if (!isTrackingEnabled()) return

    const page = location.pathname
    trackingApi.trackEvent({ type: 'pageview', page, ...(takeAttribution() ?? {}) })

    const engagement = new PageEngagement()
    engagement.start()

    // Se dispara al ocultar la pestaña, al cerrarla y al cambiar de ruta; un tramo vacío no se envía.
    const report = () => {
      const snapshot = engagement.snapshot()
      engagement.resetSegment()
      if (snapshot.durationMs < 100) return
      trackingApi.trackEventBeacon({ type: 'page_leave', page, ...snapshot })
    }
    const onVisibilityChange = () => {
      if (document.visibilityState === 'hidden') report()
    }

    document.addEventListener('visibilitychange', onVisibilityChange)
    window.addEventListener('pagehide', report)

    return () => {
      report()
      engagement.stop()
      document.removeEventListener('visibilitychange', onVisibilityChange)
      window.removeEventListener('pagehide', report)
    }
  }, [location.pathname])
}

/** Enlaces salientes y descargas, con un solo escucha delegado en el documento. */
export const useTrackLinks = () => {
  useEffect(() => {
    if (!isTrackingEnabled()) return

    const onClick = (event: MouseEvent) => {
      const anchor = (event.target as Element | null)?.closest?.('a[href]') as HTMLAnchorElement | null
      if (!anchor) return
      const link = classifyLink(anchor, window.location.host)
      if (link) trackingApi.trackEventBeacon({ ...link, page: window.location.pathname })
    }

    document.addEventListener('click', onClick)
    return () => document.removeEventListener('click', onClick)
  }, [])
}

/** LCP, INP, CLS, FCP y TTFB de la carga; se envían al ocultar la pestaña. */
export const useTrackWebVitals = () => {
  useEffect(() => {
    if (!isTrackingEnabled()) return

    const page = window.location.pathname
    const vitals: Record<string, number> = {}
    let lastSent = ''
    const record = (name: string) => (metric: Metric) => {
      vitals[name] = metric.value
    }

    onLCP(record('lcp'))
    onINP(record('inp'))
    onCLS(record('cls'))
    onFCP(record('fcp'))
    onTTFB(record('ttfb'))

    const flush = () => {
      const serialized = JSON.stringify(vitals)
      if (serialized === '{}' || serialized === lastSent) return
      lastSent = serialized
      trackingApi.trackEventBeacon({ type: 'web_vitals', page, vitals: { ...vitals } })
    }
    const onVisibilityChange = () => {
      if (document.visibilityState === 'hidden') flush()
    }

    document.addEventListener('visibilitychange', onVisibilityChange)
    window.addEventListener('pagehide', flush)
    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange)
      window.removeEventListener('pagehide', flush)
    }
  }, [])
}

/** Guarda el token del dueño de `/?owner=<token>` antes del primer pageview. */
export const useCaptureOwnerToken = () => {
  useEffect(() => {
    captureOwnerToken()
  }, [])
}

export const useTrackProjectOpen = (slug?: string | null, projectId?: string) => {
  useEffect(() => {
    if (!isTrackingEnabled() || !slug) return
    trackingApi.trackEvent({
      type: 'project_open',
      page: window.location.pathname,
      target: slug,
      props: { projectId, slug },
    })
  }, [slug, projectId])
}

export const useTrackClick = () => {
  const handleClick = (targetName: string, metadata?: Record<string, unknown>) => {
    if (!isTrackingEnabled()) return

    trackingApi.trackEvent({
      type: 'click',
      page: window.location.pathname,
      target: targetName,
      metadata,
    })
  }

  return { trackClick: handleClick }
}

export const useTrackDownload = () => {
  const handleDownload = (fileName: string, fileType?: string) => {
    if (!isTrackingEnabled()) return

    trackingApi.trackEvent({
      type: 'download',
      page: window.location.pathname,
      target: fileName,
      metadata: { fileType },
    })
  }

  return { trackDownload: handleDownload }
}
