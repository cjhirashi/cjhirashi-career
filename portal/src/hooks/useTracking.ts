import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { trackingApi } from '@/api/tracking'

export const useTrackPageview = () => {
  const location = useLocation()

  useEffect(() => {
    const enabled = import.meta.env.VITE_TRACKING_ENABLED !== 'false'

    if (!enabled) return

    trackingApi.trackEvent({
      type: 'pageview',
      page: location.pathname,
    })
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
    })
  }

  return { trackDownload: handleDownload }
}
