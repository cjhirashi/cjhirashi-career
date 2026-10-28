import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { trackingApi } from '@/api/tracking'

const SESSION_STORAGE_KEY = 'portfolio_session_id'

const generateId = (): string =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`

/** One id per browser tab/session: `sessionStorage` survives page navigation
 * within the same tab (several pages = 1 visit) but resets on a new tab or
 * when the browser is reopened (= a new visit), matching how the admin
 * dashboard groups pageviews into "visitas". Falls back to a fresh id per
 * call if storage is unavailable (private mode, SSR) — tracking still works,
 * it just can't group that visitor's pageviews. */
const getOrCreateSessionId = (): string => {
  try {
    const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY)
    if (existing) return existing
    const fresh = generateId()
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, fresh)
    return fresh
  } catch {
    return generateId()
  }
}

export const useTrackPageview = () => {
  const location = useLocation()

  useEffect(() => {
    const enabled = import.meta.env.VITE_TRACKING_ENABLED !== 'false'

    if (!enabled) return

    const page = location.pathname
    const sessionId = getOrCreateSessionId()
    const enteredAt = performance.now()
    let reported = false

    trackingApi.trackEvent({ type: 'pageview', page, sessionId })

    // How long the visitor actually stayed on `page` - fired once, on
    // whichever happens first: SPA route change (effect cleanup), tab
    // hidden/backgrounded, or the tab/browser closing outright. sendBeacon
    // (via trackEventBeacon) is required for the last two: a normal
    // fetch/XHR can be aborted mid-flight once the page starts unloading.
    const reportDuration = () => {
      if (reported) return
      reported = true
      const durationMs = Math.round(performance.now() - enteredAt)
      trackingApi.trackEventBeacon({ type: 'page_duration', page, sessionId, durationMs })
    }

    const onVisibilityChange = () => {
      if (document.visibilityState === 'hidden') reportDuration()
    }

    document.addEventListener('visibilitychange', onVisibilityChange)
    window.addEventListener('pagehide', reportDuration)

    return () => {
      reportDuration()
      document.removeEventListener('visibilitychange', onVisibilityChange)
      window.removeEventListener('pagehide', reportDuration)
    }
  }, [location.pathname])
}

export const useTrackClick = () => {
  const handleClick = (targetName: string, metadata?: Record<string, unknown>) => {
    const enabled = import.meta.env.VITE_TRACKING_ENABLED !== 'false'

    if (!enabled) return

    trackingApi.trackEvent({
      type: 'click',
      page: window.location.pathname,
      target: targetName,
      metadata,
      sessionId: getOrCreateSessionId(),
    })
  }

  return { trackClick: handleClick }
}

export const useTrackDownload = () => {
  const handleDownload = (fileName: string, fileType?: string) => {
    const enabled = import.meta.env.VITE_TRACKING_ENABLED !== 'false'

    if (!enabled) return

    trackingApi.trackEvent({
      type: 'download',
      page: window.location.pathname,
      target: fileName,
      metadata: { fileType },
      sessionId: getOrCreateSessionId(),
    })
  }

  return { trackDownload: handleDownload }
}
