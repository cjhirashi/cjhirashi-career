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
  FileText,
  Plug,
  ScrollText,
  ClipboardList,
  MessageCircle,
} from 'lucide-react'
import { CAREER_DOMAINS, CAREER_RESOURCES } from '@/config/careerResources'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

// Only the pages that still have real, standalone content. Every other
// legacy menu item (Identity/Competencies/Evidence/Job Strategies/
// Networking/Interviews) pointed at pre-career-domain (v1) pages superseded
// by the 30 resources under CAREER_DOMAINS below — removed rather than kept
// as dead links (see also App.tsx, which no longer routes to them).
const menuItems = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Métricas', path: '/metrics', icon: BarChart3 },
  { label: 'Archivos', path: '/files', icon: FolderOpen },
]

// LinkedIn isn't a generic career resource (no /career/:resourceKey page -
// it's the standalone OAuth/posting page at /linkedin), so it can't just be
// added to a domain's `resourceKeys` like the other 30 - it's spliced into
// the "Presencia Digital" accordion's rendering below instead, by key.
const LINKEDIN_DOMAIN_KEY = 'digital'

// Same idea for the search-strategy dashboard: not a generic /career/:key
// CRUD resource (it's an aggregated, read-only view over several of the 12
// Operativa de Búsqueda tables at /search-metrics), so it's spliced into
// that domain's accordion the same way, rendered first (as an overview)
// rather than after the 12 resource links.
const SEARCH_METRICS_DOMAIN_KEY = 'search'

// "Agente IA" - Agent Bedrock's own admin surface (cost, its knowledge base,
// what it remembers, its system prompt, its tools). Not a CAREER_DOMAINS
// entry: none of these are generic /career/:key CRUD resources except
// Metodologías Operativas, which is reused here via its existing route
// rather than duplicated. Uses the same expandedDomain toggle mechanism as
// the domains above, just with a key that isn't in CAREER_DOMAINS.
const AGENT_DOMAIN_KEY = 'agent'
const AGENT_LINKS = [
  { label: 'Chat General', path: '/agent/chat', icon: MessageCircle },
  { label: 'Plantillas PDF', path: '/agent/pdf-templates', icon: FileText },
  { label: 'Estilos PDF', path: '/agent/pdf-template-styles', icon: FileText },
  { label: 'Costo y Uso', path: '/agent/metrics', icon: BarChart3 },
  { label: 'Metodologías Operativas', path: '/career/operational-methodologies', icon: Workflow },
  { label: 'Memoria', path: '/agent/memory', icon: Brain },
  { label: 'Instrucciones', path: '/agent/instructions', icon: FileText },
  { label: 'Herramientas', path: '/agent/tools', icon: Plug },
  { label: 'Bitácora', path: '/agent/audit-log', icon: ScrollText },
  { label: 'Tareas', path: '/agent/tasks', icon: ClipboardList },
]

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const location = useLocation()
  // Which career domain accordion is expanded ("Identidad Profesional",
  // "Operativa de Búsqueda", ...). At most one at a time to keep the list
  // manageable - there are 30 resources across 5 domains. Domains render
  // directly in the sidebar (no outer "Carrera" wrapper to expand first).
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null)

  const isActive = (path: string): boolean => location.pathname === path
  const isCareerResourceActive = (resourceKey: string): boolean =>
    location.pathname === `/career/${resourceKey}`

  const closeMobileDrawer = () => {
    if (window.innerWidth < 768 && isOpen) onToggle()
  }

  const handleDomainToggle = (domainKey: string) => {
    // When the sidebar itself is collapsed (icon-only, desktop), clicking a
    // domain expands the sidebar first instead of trying to render a
    // sub-menu with no room for labels.
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
        // Glass Steel chrome: translucent, blurred glass panel (see
        // `.glass-panel` / `--bg-glass` in src/index.css) instead of the
        // previous flat, always-dark slate-800 background - it now adapts
        // to the active theme like the rest of the app.
        'glass-panel backdrop-blur-[20px] text-text transition-all duration-300 flex flex-col border-r border-border',
        // Mobile: off-canvas drawer that slides in/out over the content.
        // Desktop (md+): back in normal flow, width toggles expanded/collapsed.
        'fixed inset-y-0 left-0 z-40 md:static md:z-auto md:translate-x-0',
        isOpen ? 'translate-x-0 w-64' : '-translate-x-full w-64 md:translate-x-0 md:w-20'
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-end">
        <button
          onClick={onToggle}
          className="p-2 hover:bg-glass rounded-xl transition-colors"
          title={isOpen ? 'Contraer' : 'Expandir'}
        >
          <Menu size={20} aria-hidden="true" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            onClick={() => {
              // Close the drawer after navigating on mobile.
              if (window.innerWidth < 768 && isOpen) onToggle()
            }}
            aria-current={isActive(item.path) ? 'page' : undefined}
            className={clsx('sidebar-item', isActive(item.path) && 'is-active')}
            title={isOpen ? undefined : item.label}
          >
            <item.icon size={20} className="flex-shrink-0" aria-hidden="true" />
            {isOpen && <span className="text-sm font-medium truncate">{item.label}</span>}
          </Link>
        ))}

        {/* Career domain (v2) - the 30 resources, grouped into 5 logical
            domains (Identidad Profesional, Operativa de Búsqueda, Presencia
            Digital, Networking, Soporte - see careerResources.ts). Each
            domain is its own collapsible section directly in the sidebar,
            in the order the domains are approved/declared - no outer
            "Carrera" wrapper to expand first. */}
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
                      <Link
                        to="/job-discovery"
                        onClick={closeMobileDrawer}
                        aria-current={isActive('/job-discovery') ? 'page' : undefined}
                        className={clsx(
                          'flex items-center gap-1.5 pl-12 pr-4 py-1.5 rounded-xl text-sm truncate transition-colors',
                          isActive('/job-discovery')
                            ? 'text-primary bg-primary-light'
                            : 'text-text-secondary hover:bg-glass hover:text-text'
                        )}
                      >
                        <Search size={13} className="flex-shrink-0" aria-hidden="true" />
                        Descubrir vacantes
                      </Link>
                      <Link
                        to="/search-metrics"
                        onClick={closeMobileDrawer}
                        aria-current={isActive('/search-metrics') ? 'page' : undefined}
                        className={clsx(
                          'flex items-center gap-1.5 pl-12 pr-4 py-1.5 rounded-xl text-sm truncate transition-colors',
                          isActive('/search-metrics')
                            ? 'text-primary bg-primary-light'
                            : 'text-text-secondary hover:bg-glass hover:text-text'
                        )}
                      >
                        <LineChart size={13} className="flex-shrink-0" aria-hidden="true" />
                        Métricas de Búsqueda
                      </Link>
                      </>
                    )}
                    {domain.resourceKeys.map((resourceKey) => {
                      const resource = CAREER_RESOURCES[resourceKey]
                      if (!resource) return null
                      const path = `/career/${resourceKey}`
                      const active = isCareerResourceActive(resourceKey)
                      return (
                        <Link
                          key={resourceKey}
                          to={path}
                          onClick={closeMobileDrawer}
                          aria-current={active ? 'page' : undefined}
                          className={clsx(
                            'block pl-12 pr-4 py-1.5 rounded-xl text-sm truncate transition-colors',
                            active ? 'text-primary bg-primary-light' : 'text-text-secondary hover:bg-glass hover:text-text'
                          )}
                        >
                          {resource.label}
                        </Link>
                      )
                    })}
                    {domain.key === LINKEDIN_DOMAIN_KEY && (
                      <Link
                        to="/linkedin"
                        onClick={closeMobileDrawer}
                        aria-current={isActive('/linkedin') ? 'page' : undefined}
                        className={clsx(
                          'flex items-center gap-1.5 pl-12 pr-4 py-1.5 rounded-xl text-sm truncate transition-colors',
                          isActive('/linkedin')
                            ? 'text-primary bg-primary-light'
                            : 'text-text-secondary hover:bg-glass hover:text-text'
                        )}
                      >
                        <Linkedin size={13} className="flex-shrink-0" aria-hidden="true" />
                        LinkedIn · Publicar
                      </Link>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Agente IA - see AGENT_LINKS above. Same accordion mechanism as
            the career domains, just not one of them. */}
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
                    {AGENT_LINKS.map((link) => {
                      const active = isActive(link.path)
                      return (
                        <Link
                          key={link.path}
                          to={link.path}
                          onClick={closeMobileDrawer}
                          aria-current={active ? 'page' : undefined}
                          className={clsx(
                            'flex items-center gap-1.5 pl-12 pr-4 py-1.5 rounded-xl text-sm truncate transition-colors',
                            active ? 'text-primary bg-primary-light' : 'text-text-secondary hover:bg-glass hover:text-text'
                          )}
                        >
                          <link.icon size={13} className="flex-shrink-0" aria-hidden="true" />
                          {link.label}
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })()}
        </div>
      </nav>

      {/* Footer - just the version. User identity (avatar/name/role) already
          lives in the Navbar dropdown at the top - no need to repeat it
          here too. */}
      {isOpen && (
        <div className="p-3 border-t border-border">
          <p className="text-[11px] text-text-muted text-center">v0.1.0</p>
        </div>
      )}
    </aside>
  )
}
