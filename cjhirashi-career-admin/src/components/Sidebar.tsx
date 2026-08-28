import React, { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  ChevronDown,
  Menu,
  LayoutDashboard,
  BarChart3,
  FolderOpen,
  Linkedin,
  LineChart,
  Search,
  Bot,
  Workflow,
  Brain,
  Library,
  FileText,
  Palette,
  Plug,
  ScrollText,
  ClipboardList,
  MessageCircle,
  Settings,
  LayoutGrid,
  SquareStack,
  SlidersHorizontal,
  AlertTriangle,
  Compass,
  Globe,
  Handshake,
  Tag,
  Circle,
  Folder,
  type LucideIcon,
} from 'lucide-react'
import { CAREER_RESOURCES, isTableResource, resourceNavIcon } from '@/config/careerResources'
import { useNavTree } from '@/hooks/useNavTree'
import { NavGroup, NavSection } from '@/types/adminSections'
import { useSidebarCounts } from '@/hooks/useSidebarCounts'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

/**
 * Static top-level entries always visible outside any collapsible group
 * (Sidebar UX decision, not backend structure — these `system_name`s still
 * come from the nav-tree, only their "pinned/flat" placement is local).
 */
const PINNED_SYSTEM_NAMES = ['dashboard', 'metrics', 'files', 'agent-tasks']
const PINNED_COUNT_KEYS: Record<string, 'files' | 'tasks' | undefined> = {
  files: 'files',
  'agent-tasks': 'tasks',
}

/**
 * Icon per section `system_name` (stable backend key — ADR-023's `NavSection`
 * has no icon field on purpose, presentation lives entirely in the frontend).
 * `career-*` sections resolve through `resourceNavIcon` instead (see
 * `iconForSection`), so they aren't listed here.
 */
const SECTION_ICONS: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  metrics: BarChart3,
  'search-metrics': LineChart,
  'agent-metrics': BarChart3,
  files: FolderOpen,
  'agent-tasks': ClipboardList,
  'linkedin-publish': Linkedin,
  'job-discovery': Search,
  'pdf-templates': FileText,
  'pdf-styles': Palette,
  'agent-chat': MessageCircle,
  'agent-memory': Brain,
  'agent-instructions': FileText,
  'agent-tools': Plug,
  'agent-audit-log': ScrollText,
  'career-operational-methodologies': Workflow,
  'settings-agents': Library,
  'settings-sections': LayoutGrid,
  'settings-views': SquareStack,
  'settings-agent-prompts': SlidersHorizontal,
  'settings-error-reports': AlertTriangle,
}

/** Icon per group `system_name` (frozen list, ADR-023 `_FROZEN_GROUPS`). */
const GROUP_ICONS: Record<string, LucideIcon> = {
  'professional-identity': Compass,
  'search-ops': Search,
  'digital-presence': Globe,
  networking: Handshake,
  support: Tag,
  'agent-ai': Bot,
  settings: Settings,
}

function iconForSection(section: NavSection): LucideIcon {
  if (section.system_name.startsWith('career-')) {
    return resourceNavIcon(section.system_name.replace(/^career-/, ''))
  }
  return SECTION_ICONS[section.system_name] ?? Circle
}

function iconForGroup(group: NavGroup): LucideIcon {
  return GROUP_ICONS[group.system_name] ?? Folder
}

/** Table career resources show a record-count badge; singletons don't. */
function countForSection(
  section: NavSection,
  career: Record<string, number | undefined>
): number | undefined {
  if (!section.system_name.startsWith('career-')) return undefined
  const resourceKey = section.system_name.replace(/^career-/, '')
  if (!isTableResource(CAREER_RESOURCES[resourceKey])) return undefined
  return career[resourceKey]
}

const RecordCount: React.FC<{ count?: number }> = ({ count }) => {
  if (typeof count !== 'number') return null
  return (
    <span className="sidebar-count" title={`${count} registros`} aria-hidden="true">
      {count}
    </span>
  )
}

const SidebarSubLink: React.FC<{
  to: string
  label: string
  icon: LucideIcon
  active: boolean
  count?: number
  onClick: () => void
}> = ({ to, label, icon: Icon, active, count, onClick }) => (
  <Link
    to={to}
    onClick={onClick}
    aria-current={active ? 'page' : undefined}
    aria-label={typeof count === 'number' ? `${label}, ${count} registros` : undefined}
    className={clsx('sidebar-subitem', active && 'is-active')}
  >
    <Icon size={13} className="flex-shrink-0" aria-hidden="true" />
    <span className="truncate min-w-0 flex-1">{label}</span>
    <RecordCount count={count} />
  </Link>
)

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const location = useLocation()
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null)
  const { data: navTree } = useNavTree()
  const counts = useSidebarCounts(expandedDomain)

  const isActive = (path: string): boolean =>
    location.pathname === path || location.pathname.startsWith(`${path}/`)

  const closeMobileDrawer = () => {
    if (window.innerWidth < 768 && isOpen) onToggle()
  }

  const handleDomainToggle = (domainKey: string) => {
    if (!isOpen) {
      onToggle()
      setExpandedDomain(domainKey)
      return
    }
    setExpandedDomain((current) => (current === domainKey ? null : domainKey))
  }

  const groups = useMemo(() => navTree?.groups ?? [], [navTree])

  const pinnedItems = useMemo(() => {
    const bySystemName = new Map<string, NavSection>()
    for (const group of groups) {
      for (const section of group.sections) {
        bySystemName.set(section.system_name, section)
      }
    }
    return PINNED_SYSTEM_NAMES.map((name) => bySystemName.get(name)).filter(
      (s): s is NavSection => Boolean(s?.path)
    )
  }, [groups])

  const pinnedSystemNames = new Set(PINNED_SYSTEM_NAMES)
  const accordionGroups = groups.filter((group) =>
    group.sections.some((section) => !pinnedSystemNames.has(section.system_name))
  )

  return (
    <aside
      className={clsx(
        'glass-panel backdrop-blur-[20px] text-text transition-all duration-300 flex flex-col border-r border-border',
        'fixed inset-y-0 left-0 z-40 md:static md:z-auto md:translate-x-0',
        isOpen ? 'translate-x-0 w-64' : '-translate-x-full w-64 md:translate-x-0 md:w-20'
      )}
    >
      <div className="p-4 border-b border-border flex items-center justify-end">
        <button
          onClick={onToggle}
          className="p-2 hover:bg-glass rounded-xl transition-colors"
          title={isOpen ? 'Contraer' : 'Expandir'}
        >
          <Menu size={20} aria-hidden="true" />
        </button>
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {pinnedItems.map((section) => {
          const Icon = iconForSection(section)
          const countKey = PINNED_COUNT_KEYS[section.system_name]
          const count = countKey ? counts.pinned[countKey] : undefined
          return (
            <Link
              key={section.id}
              to={section.path as string}
              onClick={() => {
                if (window.innerWidth < 768 && isOpen) onToggle()
              }}
              aria-current={isActive(section.path as string) ? 'page' : undefined}
              aria-label={typeof count === 'number' ? `${section.label}, ${count} registros` : undefined}
              className={clsx('sidebar-item', isActive(section.path as string) && 'is-active')}
              title={isOpen ? undefined : section.label}
            >
              <Icon size={20} className="flex-shrink-0" aria-hidden="true" />
              {isOpen && <span className="text-sm font-medium truncate min-w-0 flex-1">{section.label}</span>}
              {isOpen && typeof count === 'number' && <RecordCount count={count} />}
            </Link>
          )
        })}

        {accordionGroups.map((group) => {
          const isDomainExpanded = expandedDomain === group.system_name
          const GroupIcon = iconForGroup(group)
          const sections = group.sections.filter(
            (section) => !pinnedSystemNames.has(section.system_name) && section.path
          )
          return (
            <div key={group.id} className="pt-2 mt-2 border-t border-border space-y-1">
              <button
                type="button"
                onClick={() => handleDomainToggle(group.system_name)}
                className="sidebar-item w-full justify-between"
                title={isOpen ? undefined : group.name}
                aria-expanded={isDomainExpanded}
              >
                <span className="flex items-center gap-3 min-w-0">
                  <GroupIcon size={20} className="flex-shrink-0" aria-hidden="true" />
                  {isOpen && <span className="text-sm font-medium truncate">{group.name}</span>}
                </span>
                {isOpen && (
                  <ChevronDown
                    size={16}
                    className={clsx('flex-shrink-0 transition-transform', isDomainExpanded && 'rotate-180')}
                  />
                )}
              </button>

              {isOpen && isDomainExpanded && (
                <div className="mt-1 space-y-0.5 mb-1">
                  {sections.map((section) => (
                    <SidebarSubLink
                      key={section.id}
                      to={section.path as string}
                      label={section.label}
                      icon={iconForSection(section)}
                      active={isActive(section.path as string)}
                      count={countForSection(section, counts.career)}
                      onClick={closeMobileDrawer}
                    />
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </nav>

      {isOpen && (
        <div className="p-3 border-t border-border">
          <p className="text-[11px] text-text-muted text-center">v0.1.0</p>
        </div>
      )}
    </aside>
  )
}
