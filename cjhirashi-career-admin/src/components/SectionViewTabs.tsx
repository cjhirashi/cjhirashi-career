import React from 'react'
import { useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  Calendar,
  Columns3,
  Eye,
  FileText,
  GanttChart,
  List,
  Pencil,
  type LucideIcon,
} from 'lucide-react'
import { useAdminSections } from '@/hooks/useAdminSections'
import { matchAdminSection } from '@/types/adminSections'

export interface SectionViewTab {
  key: string
  label: string
}

const VIEW_TAB_ICONS: Record<string, LucideIcon> = {
  list: List,
  kanban: Columns3,
  calendar: Calendar,
  gantt: GanttChart,
  view: Eye,
  record: Eye,
  edit: Pencil,
  main: FileText,
}

export function useSectionViewTabs(fallback: SectionViewTab[]): SectionViewTab[] {
  const { pathname } = useLocation()
  const { data: sections } = useAdminSections()
  const matched = matchAdminSection(pathname, sections ?? [])
  if (matched?.section.views.length) {
    return matched.section.views.map((view) => ({ key: view.key, label: view.label }))
  }
  return fallback
}

interface SectionViewTabsProps {
  views: SectionViewTab[]
  activeKey: string
  /** Keys that navigate. Other tabs are indicators only. */
  interactiveKeys?: string[]
  onSelect?: (key: string) => void
}

/** Folder-style tabs for the views of the current admin section. */
export const SectionViewTabs: React.FC<SectionViewTabsProps> = ({
  views,
  activeKey,
  interactiveKeys,
  onSelect,
}) => {
  if (views.length === 0) return null
  const clickable = new Set(interactiveKeys ?? [])
  return (
    <div className="view-tabs" role="tablist" aria-label="Vistas de la sección">
      {views.map((view) => {
        const selected = view.key === activeKey
        const isButton = clickable.has(view.key) && Boolean(onSelect)
        const className = clsx('view-tab', selected && 'is-active', !isButton && 'is-indicator')
        const Icon = VIEW_TAB_ICONS[view.key] ?? FileText
        const content = (
          <>
            <Icon className="view-tab-icon" size={14} strokeWidth={2.25} aria-hidden="true" />
            <span className="view-tab-label">{view.label}</span>
          </>
        )
        if (isButton) {
          return (
            <button
              key={view.key}
              type="button"
              role="tab"
              aria-selected={selected}
              className={className}
              title={view.label}
              onClick={() => onSelect?.(view.key)}
            >
              {content}
            </button>
          )
        }
        return (
          <span
            key={view.key}
            role="tab"
            aria-selected={selected}
            className={className}
            title={view.label}
          >
            {content}
          </span>
        )
      })}
    </div>
  )
}
