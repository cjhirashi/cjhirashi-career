export type ErrorReportSeverity = 'warning' | 'error' | 'critical'

export interface ErrorReportItem {
  id: string
  message: string
  source: string
  error_type: string | null
  severity: ErrorReportSeverity | string
  resolved: boolean
  occurrences: number
  first_seen_at: string | null
  last_seen_at: string | null
  created_at: string | null
  resolved_at: string | null
  resolved_by: string | null
  resolution_notes: string | null
}

export interface ErrorReportDetail extends ErrorReportItem {
  stack_trace: string | null
  context: Record<string, unknown> | null
}

export interface ErrorReportList {
  items: ErrorReportItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface ErrorReportSummary {
  pending: number
  resolved: number
  by_severity: Record<string, number>
  newest_pending_at: string | null
}

export interface ErrorReportListParams {
  resolved?: boolean
  severity?: string
  source?: string
  q?: string
  page?: number
  page_size?: number
}

export const SEVERITY_LABEL: Record<string, string> = {
  warning: 'Aviso',
  error: 'Error',
  critical: 'Crítico',
}
