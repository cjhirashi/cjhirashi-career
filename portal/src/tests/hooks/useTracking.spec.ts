import { describe, it, expect, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import * as trackingApi from '@/api/tracking'
import { useTrackClick, useTrackDownload } from '@/hooks/useTracking'

vi.mock('@/api/tracking')

describe('useTracking Hooks', () => {
  it('useTrackClick calls trackingApi.trackEvent', () => {
    const trackEventSpy = vi.spyOn(trackingApi, 'trackEvent' as never)

    const { result } = renderHook(() => useTrackClick())

    result.current.trackClick('test-button')

    expect(trackEventSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'click',
        target: 'test-button',
      })
    )
  })

  it('useTrackDownload calls trackingApi.trackEvent', () => {
    const trackEventSpy = vi.spyOn(trackingApi, 'trackEvent' as never)

    const { result } = renderHook(() => useTrackDownload())

    result.current.trackDownload('resume.pdf', 'application/pdf')

    expect(trackEventSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'download',
        target: 'resume.pdf',
        metadata: { fileType: 'application/pdf' },
      })
    )
  })
})
