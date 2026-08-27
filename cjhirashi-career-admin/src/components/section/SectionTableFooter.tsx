import React from 'react'

interface CountFooter {
  /** Rows shown on screen right now. */
  shown: number
  /** Total across all pages, when known. */
  total?: number
}

interface PageFooter {
  page: number
  hasMore: boolean
  onPageChange: (page: number) => void
  /** Rows on the current page (for the "N–M" label). */
  shown: number
  pageSize: number
  total?: number
}

type SectionTableFooterProps =
  | ({ variant: 'count' } & CountFooter)
  | ({ variant: 'pager' } & PageFooter)
  | { variant: 'custom'; children: React.ReactNode }

/** The `table-footer`: a "showing N–M" label, optionally with prev/next paging. */
export const SectionTableFooter: React.FC<SectionTableFooterProps> = (props) => {
  if (props.variant === 'custom') {
    return <div className="table-footer">{props.children}</div>
  }

  if (props.variant === 'count') {
    return (
      <div className="table-footer">
        <span className="text-xs text-text-secondary">
          Mostrando {props.shown === 0 ? 0 : 1}–{props.shown}
          {typeof props.total === 'number' ? ` de ${props.total}` : ''}
        </span>
      </div>
    )
  }

  const { page, hasMore, onPageChange, shown, pageSize, total } = props
  const from = shown === 0 ? 0 : (page - 1) * pageSize + 1
  const to = (page - 1) * pageSize + shown
  return (
    <div className="table-footer flex items-center justify-between">
      <span className="text-xs text-text-secondary">
        {from}–{to}
        {typeof total === 'number' ? ` de ${total}` : ''}
      </span>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="btn-secondary btn-small"
          disabled={page <= 1}
          onClick={() => onPageChange(Math.max(1, page - 1))}
        >
          Anterior
        </button>
        <span className="text-xs text-text-secondary">Página {page}</span>
        <button
          type="button"
          className="btn-secondary btn-small"
          disabled={!hasMore}
          onClick={() => onPageChange(page + 1)}
        >
          Siguiente
        </button>
      </div>
    </div>
  )
}
