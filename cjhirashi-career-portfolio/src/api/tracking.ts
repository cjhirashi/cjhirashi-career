import { apiClient } from './client'
import { TrackingEvent } from '@/types'
import { getCommonFields, getVisitorId, resetVisitorId } from '@/utils/tracker'

export const trackingApi = {
  /** Borra del servidor todo lo asociado al id de este navegador y genera uno nuevo (RF-053). */
  forgetMe: async (): Promise<void> => {
    const { siteKey } = getCommonFields()
    await apiClient.post('/events/forget', { siteKey, visitorId: getVisitorId() })
    resetVisitorId()
  },

  trackEvent: async (event: Omit<TrackingEvent, 'timestamp' | 'userAgent'>): Promise<void> => {
    const trackingEvent: TrackingEvent = {
      ...getCommonFields(),
      ...event,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
    }

    try {
      await apiClient.post('/events/track', trackingEvent)
    } catch (error) {
      // Silent fail for tracking - don't interrupt user experience
      console.error('Tracking error:', error)
    }
  },

  /** Same payload shape, sent via `sendBeacon` instead of axios - the only
   * transport reliable enough to actually leave the browser from a
   * `pagehide`/`visibilitychange` handler (a normal fetch/XHR can be aborted
   * mid-flight when the page unloads). Used for `page_duration` events. */
  trackEventBeacon: (event: Omit<TrackingEvent, 'timestamp' | 'userAgent'>): void => {
    const trackingEvent: TrackingEvent = {
      ...getCommonFields(),
      ...event,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
    }
    apiClient.postBeacon('/events/track', trackingEvent)
  },
}
