import React from 'react'
import { SectionViewTabs, SectionViewTab } from '@/components/SectionViewTabs'

export interface SectionBreadcrumb {
  /** Section title, e.g. "Reportes de Falla". */
  section: string
  /** Record id shown after the title, e.g. "err-3". */
  id: string | number
  /** Optional human name shown after the id. */
  name?: string
}

interface SectionShellProps {
  /** Plain section title for list views. Ignored when `breadcrumb` is set. */
  title?: string
  /** Count badge next to the title (list views). */
  count?: number
  /** Title · id · name breadcrumb for detail views. */
  breadcrumb?: SectionBreadcrumb
  tabs: SectionViewTab[]
  activeTab: string
  /** Tab keys that navigate (the rest are inert indicators). */
  interactiveTabs?: string[]
  onTabSelect?: (key: string) => void
  /** Buttons rendered in `view-tabs-actions` (edit / save / resolve / …). */
  actions?: React.ReactNode
  /** `list` adds `table-list-body` (pins toolbar + footer, scrolls rows only). */
  variant?: 'list' | 'record'
  /** Render without the `.card` chrome — for embedding inside another card. */
  embedded?: boolean
  children: React.ReactNode
}

/**
 * The single source of truth for the frame of every Admin section: the
 * `card has-view-tabs` shell, its sticky header (title / breadcrumb + count +
 * folder tabs + action buttons) and the scrolling body. Every list and detail
 * view composes this instead of hand-rolling the markup.
 */
export const SectionShell: React.FC<SectionShellProps> = ({
  title,
  count,
  breadcrumb,
  tabs,
  activeTab,
  interactiveTabs,
  onTabSelect,
  actions,
  variant = 'record',
  embedded = false,
  children,
}) => {
  if (embedded) {
    return (
      <div>
        <div className="flex items-center justify-between gap-3 mb-3">
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide">
            {breadcrumb
              ? [breadcrumb.section, String(breadcrumb.id), breadcrumb.name]
                  .filter((p) => p != null && p !== '')
                  .join(' · ')
              : title}
          </h3>
          {actions ? <div className="view-tabs-actions">{actions}</div> : null}
        </div>
        {children}
      </div>
    )
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <div className="card has-view-tabs">
        <div className="card-header">
          <h2 className="font-semibold text-text flex items-center gap-2 min-w-0">
            {breadcrumb ? (
              <>
                <span className="truncate">{breadcrumb.section}</span>
                <span className="text-text-muted font-normal">·</span>
                <span className="mono text-primary font-normal flex-shrink-0">
                  {String(breadcrumb.id)}
                </span>
                {breadcrumb.name ? (
                  <>
                    <span className="text-text-muted font-normal">·</span>
                    <span className="truncate">{breadcrumb.name}</span>
                  </>
                ) : null}
              </>
            ) : (
              <>
                <span className="truncate">{title}</span>
                {typeof count === 'number' && <span className="badge badge-slate mono">{count}</span>}
              </>
            )}
          </h2>
          <div className="view-tabs-row">
            <SectionViewTabs
              views={tabs}
              activeKey={activeTab}
              interactiveKeys={interactiveTabs}
              onSelect={onTabSelect}
            />
            {actions ? <div className="view-tabs-actions">{actions}</div> : null}
          </div>
        </div>
        <div className={`card-body${variant === 'list' ? ' table-list-body' : ''}`}>{children}</div>
      </div>
    </div>
  )
}
