import React from 'react'
import { SectionViewTab } from '@/components/SectionViewTabs'
import { ColumnConfig } from '@/config/careerResources'
import { getErrorMessage } from '@/utils/errors'
import { SortState } from '@/utils/tableColumns'
import { SectionShell } from '@/components/section/SectionShell'
import { ColumnSettingsProps, SectionToolbar } from '@/components/section/SectionToolbar'
import { SectionTable } from '@/components/section/SectionTable'
import { SectionTableFooter } from '@/components/section/SectionTableFooter'

const DEFAULT_TABS: SectionViewTab[] = [{ key: 'list', label: 'Lista' }]

interface TableSectionTemplateProps<Row> {
  title: string
  count?: number
  tabs?: SectionViewTab[]
  activeTab?: string
  onTabSelect?: (key: string) => void
  interactiveTabs?: string[]
  headerActions?: React.ReactNode

  query?: {
    isLoading?: boolean
    isError?: boolean
    error?: unknown
    onRetry?: () => void
  }

  toolbar?: {
    search?: { value: string; onChange: (v: string) => void; placeholder?: string }
    filtersActive?: boolean
    onClearFilters?: () => void
    extra?: React.ReactNode
    columnSettings?: ColumnSettingsProps
  }

  table: {
    columns: ColumnConfig[]
    rows: Row[]
    getRowKey: (row: Row) => string
    idColumnKey?: string
    sort?: SortState
    onToggleSort?: (key: string) => void
    onRowClick?: (row: Row) => void
    rowClassName?: (row: Row) => string
    renderCell?: (row: Row, colKey: string) => React.ReactNode | undefined
    headerExtra?: (colKey: string) => React.ReactNode
    rowActions?: (row: Row) => React.ReactNode
    actionsLabel?: string
    emptyMessage: string
  }

  footer?:
    | { variant: 'count'; total?: number }
    | { variant: 'pager'; page: number; hasMore: boolean; onPageChange: (p: number) => void; pageSize: number; total?: number }
    | { variant: 'custom'; children: React.ReactNode }
}

/**
 * One declarative call for a standard Admin list view. Composes
 * `SectionShell` + `SectionToolbar` + `SectionTable` + `SectionTableFooter`.
 * Screens with a bespoke body (file upload, task boards) compose the
 * primitives directly instead.
 */
export function TableSectionTemplate<Row>({
  title,
  count,
  tabs = DEFAULT_TABS,
  activeTab = 'list',
  onTabSelect,
  interactiveTabs = [],
  headerActions,
  query,
  toolbar,
  table,
  footer,
}: TableSectionTemplateProps<Row>) {
  const isLoading = query?.isLoading ?? false
  const isError = query?.isError ?? false

  return (
    <SectionShell
      title={title}
      count={count}
      tabs={tabs}
      activeTab={activeTab}
      interactiveTabs={interactiveTabs}
      onTabSelect={onTabSelect}
      actions={headerActions}
      variant="list"
    >
      {toolbar && (
        <SectionToolbar
          search={toolbar.search}
          filtersActive={toolbar.filtersActive}
          onClearFilters={toolbar.onClearFilters}
          columnSettings={toolbar.columnSettings}
        >
          {toolbar.extra}
        </SectionToolbar>
      )}

      <SectionTable
        columns={table.columns}
        rows={table.rows}
        getRowKey={table.getRowKey}
        idColumnKey={table.idColumnKey}
        sort={table.sort}
        onToggleSort={table.onToggleSort}
        onRowClick={table.onRowClick}
        rowClassName={table.rowClassName}
        renderCell={table.renderCell}
        headerExtra={table.headerExtra}
        rowActions={table.rowActions}
        actionsLabel={table.actionsLabel}
        emptyMessage={table.emptyMessage}
        state={{
          isLoading,
          isError,
          errorMessage: query?.error ? getErrorMessage(query.error) : undefined,
          onRetry: query?.onRetry,
        }}
      />

      {!isLoading && !isError && footer && (
        footer.variant === 'count' ? (
          <SectionTableFooter variant="count" shown={table.rows.length} total={footer.total} />
        ) : footer.variant === 'pager' ? (
          <SectionTableFooter
            variant="pager"
            page={footer.page}
            hasMore={footer.hasMore}
            onPageChange={footer.onPageChange}
            shown={table.rows.length}
            pageSize={footer.pageSize}
            total={footer.total}
          />
        ) : (
          <SectionTableFooter variant="custom">{footer.children}</SectionTableFooter>
        )
      )}
    </SectionShell>
  )
}
