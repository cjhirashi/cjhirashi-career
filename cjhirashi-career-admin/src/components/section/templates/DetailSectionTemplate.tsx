import React from 'react'
import { useNavigate } from 'react-router-dom'
import { SectionViewTab } from '@/components/SectionViewTabs'
import { SectionShell } from '@/components/section/SectionShell'

const DEFAULT_TABS: SectionViewTab[] = [
  { key: 'list', label: 'Lista' },
  { key: 'view', label: 'Detalle' },
]

interface DetailSectionTemplateProps {
  /** Section title, e.g. "Reportes de Falla". */
  sectionTitle: string
  /** Route of the list view; the "Lista" tab navigates here. */
  listPath: string
  record: { id: string | number; name?: string }
  tabs?: SectionViewTab[]
  activeTab?: string
  /** Extra interactive tab keys beyond `list` (e.g. `edit`). */
  interactiveTabs?: string[]
  onTabSelect?: (key: string) => void
  /** Buttons in `view-tabs-actions` (edit / save / resolve / delete …). */
  actions?: React.ReactNode
  children: React.ReactNode
}

/**
 * The frame for a section's detail (`:id`) page: the same `SectionShell` as the
 * list, with the `title · id · name` breadcrumb, folder tabs (Lista active-back
 * to `listPath`) and an actions slot. The body is whatever the caller passes —
 * usually a `SectionRecordView`, an edit form, or both by tab.
 */
export const DetailSectionTemplate: React.FC<DetailSectionTemplateProps> = ({
  sectionTitle,
  listPath,
  record,
  tabs = DEFAULT_TABS,
  activeTab = 'view',
  interactiveTabs = ['list'],
  onTabSelect,
  actions,
  children,
}) => {
  const navigate = useNavigate()
  return (
    <SectionShell
      breadcrumb={{ section: sectionTitle, id: record.id, name: record.name }}
      tabs={tabs}
      activeTab={activeTab}
      interactiveTabs={interactiveTabs}
      onTabSelect={(key) => {
        if (onTabSelect) return onTabSelect(key)
        if (key === 'list') navigate(listPath)
      }}
      actions={actions}
    >
      {children}
    </SectionShell>
  )
}
