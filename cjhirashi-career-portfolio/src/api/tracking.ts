import { apiClient } from './client'
import { TrackingEvent } from '@/types'

export const trackingApi = {
  trackEvent: async (event: Omit<TrackingEvent, 'timestamp' | 'userAgent'>): Promise<void> => {
    const trackingEvent: TrackingEvent = {
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
}
