import { axiosInstance } from './client'
import {
  ErrorReportDetail,
  ErrorReportList,
  ErrorReportListParams,
  ErrorReportSummary,
} from '@/types/errorReports'

const TIMEOUT_MS = 20000

export const errorReportsApi = {
  list: async (params: ErrorReportListParams = {}): Promise<ErrorReportList> => {
    const response = await axiosInstance.get<ErrorReportList>('/settings/error-reports', {
      params,
      timeout: TIMEOUT_MS,
    })
    return response.data
  },

  summary: async (): Promise<ErrorReportSummary> => {
    const response = await axiosInstance.get<ErrorReportSummary>('/settings/error-reports/summary', {
      timeout: TIMEOUT_MS,
    })
    return response.data
  },

  get: async (reportId: string): Promise<ErrorReportDetail> => {
    const response = await axiosInstance.get<ErrorReportDetail>(
      `/settings/error-reports/${reportId}`,
      { timeout: TIMEOUT_MS },
    )
    return response.data
  },

  update: async (
    reportId: string,
    payload: { resolved: boolean; resolution_notes?: string | null },
  ): Promise<ErrorReportDetail> => {
    const response = await axiosInstance.patch<ErrorReportDetail>(
      `/settings/error-reports/${reportId}`,
      payload,
      { timeout: TIMEOUT_MS },
    )
    return response.data
  },

  remove: async (reportId: string): Promise<void> => {
    await axiosInstance.delete(`/settings/error-reports/${reportId}`, { timeout: TIMEOUT_MS })
  },
}
