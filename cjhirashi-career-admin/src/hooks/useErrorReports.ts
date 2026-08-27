import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { errorReportsApi } from '@/api/errorReports'
import { ErrorReportListParams } from '@/types/errorReports'

const KEY = ['error-reports'] as const

export function useErrorReports(params: ErrorReportListParams) {
  return useQuery({
    queryKey: [...KEY, 'list', params],
    queryFn: () => errorReportsApi.list(params),
    staleTime: 15_000,
  })
}

export function useErrorReport(reportId: string | undefined) {
  return useQuery({
    queryKey: [...KEY, 'detail', reportId],
    queryFn: () => errorReportsApi.get(reportId as string),
    enabled: Boolean(reportId),
  })
}

export function useErrorReportSummary() {
  return useQuery({
    queryKey: [...KEY, 'summary'],
    queryFn: errorReportsApi.summary,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })
}

export function useErrorReportUpdate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      reportId,
      resolved,
      resolutionNotes,
    }: {
      reportId: string
      resolved: boolean
      resolutionNotes?: string | null
    }) => errorReportsApi.update(reportId, { resolved, resolution_notes: resolutionNotes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: KEY })
    },
  })
}

export function useErrorReportDelete() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (reportId: string) => errorReportsApi.remove(reportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: KEY })
    },
  })
}
