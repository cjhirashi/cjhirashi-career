import React, { useState } from 'react'
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
  type LucideIcon,
} from 'lucide-react'
import {
  CAREER_DOMAINS,
  CAREER_RESOURCES,
  isTableResource,
  resourceNavIcon,
} from '@/config/careerResources'
import { useSidebarCounts } from '@/hooks/useSidebarCounts'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

const menuItems = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Métricas', path: '/metrics', icon: BarChart3 },
  { label: 'Archivos', path: '/files', icon: FolderOpen, table: true as const },
  { label: 'Tareas', path: '/tasks', icon: ClipboardList, table: true as const, countKey: 'tasks' as const },
]

const LINKEDIN_DOMAIN_KEY = 'digital'
const SEARCH_METRICS_DOMAIN_KEY = 'search'
const AGENT_DOMAIN_KEY = 'agent'

type AgentCountKey = 'pdfTemplates' | 'pdfStyles' | 'methodologies' | 'tools'

const AGENT_LINKS: {
  label: string
  path: string
  icon: LucideIcon
  countKey?: AgentCountKey
}[] = [
  { label: 'Chat General', path: '/agent/chat', icon: MessageCircle },
  { label: 'Plantillas PDF', path: '/agent/pdf-templates', icon: FileText, countKey: 'pdfTemplates' },
  { label: 'Estilos PDF', path: '/agent/pdf-template-styles', icon: Palette, countKey: 'pdfStyles' },
  { label: 'Costo y Uso', path: '/agent/metrics', icon: BarChart3 },
  {
    label: 'Metodologías Operativas',
    path: '/career/operational-methodologies',
    icon: Workflow,
    countKey: 'methodologies',
  },
  { label: 'Memoria', path: '/agent/memory', icon: Brain },
  { label: 'Instrucciones', path: '/agent/instructions', icon: FileText },
  { label: 'Herramientas', path: '/agent/tools', icon: Plug, countKey: 'tools' },
  { label: 'Bitácora', path: '/agent/audit-log', icon: ScrollText },
]

const SETTINGS_DOMAIN_KEY = 'settings'
const SETTINGS_LINKS: { label: string; path: string; icon: LucideIcon; countKey?: 'catalog' | 'sections' }[] = [
  { label: 'Catálogo de Agentes', path: '/settings/agents', icon: Library, countKey: 'catalog' },
  { label: 'Secciones del Admin', path: '/settings/sections', icon: LayoutGrid, countKey: 'sections' },
]

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
  const counts = useSidebarCounts(expandedDomain)

  const isActive = (path: string): boolean =>
    location.pathname === path || location.pathname.startsWith(`${path}/`)
  const isCareerResourceActive = (resourceKey: string): boolean => {
    const path = `/career/${resourceKey}`
    return location.pathname === path || location.pathname.startsWith(`${path}/`)
  }

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
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            onClick={() => {
              if (window.innerWidth < 768 && isOpen) onToggle()
            }}
            aria-current={isActive(item.path) ? 'page' : undefined}
            aria-label={
              item.table && item.path === '/files' && typeof counts.files === 'number'
                ? `${item.label}, ${counts.files} registros`
                : item.table && item.path === '/tasks' && typeof counts.tasks === 'number'
                  ? `${item.label}, ${counts.tasks} registros`
                  : undefined
            }
            className={clsx('sidebar-item', isActive(item.path) && 'is-active')}
            title={isOpen ? undefined : item.label}
          >
            <item.icon size={20} className="flex-shrink-0" aria-hidden="true" />
            {isOpen && <span className="text-sm font-medium truncate min-w-0 flex-1">{item.label}</span>}
            {isOpen && item.table && (
              <RecordCount count={item.path === '/tasks' ? counts.tasks : counts.files} />
            )}
          </Link>
        ))}

        <div className="pt-2 mt-2 border-t border-border space-y-1">
          {CAREER_DOMAINS.map((domain) => {
            const isDomainExpanded = expandedDomain === domain.key
            return (
              <div key={domain.key}>
                <button
                  type="button"
                  onClick={() => handleDomainToggle(domain.key)}
                  className="sidebar-item w-full justify-between"
                  title={isOpen ? undefined : domain.label}
                  aria-expanded={isDomainExpanded}
                >
                  <span className="flex items-center gap-3 min-w-0">
                    <domain.icon size={20} className="flex-shrink-0" aria-hidden="true" />
                    {isOpen && <span className="text-sm font-medium truncate">{domain.label}</span>}
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
                    {domain.key === SEARCH_METRICS_DOMAIN_KEY && (
                      <>
                        <SidebarSubLink
                          to="/job-discovery"
                          label="Descubrir vacantes"
                          icon={Search}
                          active={isActive('/job-discovery')}
                          onClick={closeMobileDrawer}
                        />
                        <SidebarSubLink
                          to="/search-metrics"
                          label="Métricas de Búsqueda"
                          icon={LineChart}
                          active={isActive('/search-metrics')}
                          onClick={closeMobileDrawer}
                        />
                      </>
                    )}
                    {domain.resourceKeys.map((resourceKey) => {
                      const resource = CAREER_RESOURCES[resourceKey]
                      if (!resource) return null
                      const path = `/career/${resourceKey}`
                      return (
                        <SidebarSubLink
                          key={resourceKey}
                          to={path}
                          label={resource.label}
                          icon={resourceNavIcon(resourceKey)}
                          active={isCareerResourceActive(resourceKey)}
                          count={isTableResource(resource) ? counts.career[resourceKey] : undefined}
                          onClick={closeMobileDrawer}
                        />
                      )
                    })}
                    {domain.key === LINKEDIN_DOMAIN_KEY && (
                      <SidebarSubLink
                        to="/linkedin"
                        label="LinkedIn · Publicar"
                        icon={Linkedin}
                        active={isActive('/linkedin')}
                        onClick={closeMobileDrawer}
                      />
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        <div className="pt-2 mt-2 border-t border-border space-y-1">
          {(() => {
            const isAgentExpanded = expandedDomain === AGENT_DOMAIN_KEY
            return (
              <div>
                <button
                  type="button"
                  onClick={() => handleDomainToggle(AGENT_DOMAIN_KEY)}
                  className="sidebar-item w-full justify-between"
                  title={isOpen ? undefined : 'Agente IA'}
                  aria-expanded={isAgentExpanded}
                >
                  <span className="flex items-center gap-3 min-w-0">
                    <Bot size={20} className="flex-shrink-0" aria-hidden="true" />
                    {isOpen && <span className="text-sm font-medium truncate">Agente IA</span>}
                  </span>
                  {isOpen && (
                    <ChevronDown
                      size={16}
                      className={clsx('flex-shrink-0 transition-transform', isAgentExpanded && 'rotate-180')}
                    />
                  )}
                </button>

                {isOpen && isAgentExpanded && (
                  <div className="mt-1 space-y-0.5 mb-1">
                    {AGENT_LINKS.map((link) => (
                      <SidebarSubLink
                        key={link.path}
                        to={link.path}
                        label={link.label}
                        icon={link.icon}
                        active={isActive(link.path)}
                        count={link.countKey ? counts.agent[link.countKey] : undefined}
                        onClick={closeMobileDrawer}
                      />
                    ))}
                  </div>
                )}
              </div>
            )
          })()}
        </div>

        <div className="pt-2 mt-2 border-t border-border space-y-1">
          {(() => {
            const isSettingsExpanded = expandedDomain === SETTINGS_DOMAIN_KEY
            return (
              <div>
                <button
                  type="button"
                  onClick={() => handleDomainToggle(SETTINGS_DOMAIN_KEY)}
                  className="sidebar-item w-full justify-between"
                  title={isOpen ? undefined : 'Settings'}
                  aria-expanded={isSettingsExpanded}
                >
                  <span className="flex items-center gap-3 min-w-0">
                    <Settings size={20} className="flex-shrink-0" aria-hidden="true" />
                    {isOpen && <span className="text-sm font-medium truncate">Settings</span>}
                  </span>
                  {isOpen && (
                    <ChevronDown
                      size={16}
                      className={clsx('flex-shrink-0 transition-transform', isSettingsExpanded && 'rotate-180')}
                    />
                  )}
                </button>

                {isOpen && isSettingsExpanded && (
                  <div className="mt-1 space-y-0.5 mb-1">
                    {SETTINGS_LINKS.map((link) => (
                      <SidebarSubLink
                        key={link.path}
                        to={link.path}
                        label={link.label}
                        icon={link.icon}
                        active={isActive(link.path)}
                        count={link.countKey ? counts.settings[link.countKey] : undefined}
                        onClick={closeMobileDrawer}
                      />
                    ))}
                  </div>
                )}
              </div>
            )
          })()}
        </div>
      </nav>

      {isOpen && (
        <div className="p-3 border-t border-border">
          <p className="text-[11px] text-text-muted text-center">v0.1.0</p>
        </div>
      )}
    </aside>
  )
}
