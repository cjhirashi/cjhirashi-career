import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { CAREER_RESOURCES } from '@/config/careerResources'

const BASE_TITLE = 'Admin Panel'

// Exact-path titles - mirrors the labels used in Sidebar.tsx's menuItems /
// AGENT_LINKS / SETTINGS_LINKS so both stay in sync.
const STATIC_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/metrics': 'Métricas',
  '/search-metrics': 'Métricas de Búsqueda',
  '/job-discovery': 'Descubrir vacantes',
  '/files': 'Archivos',
  '/tasks': 'Tareas',
  '/linkedin': 'LinkedIn',
  '/profile': 'Perfil',
  '/change-password': 'Cambiar contraseña',
  '/agent/chat': 'Chat General',
  '/agent/metrics': 'Costo y Uso',
  '/agent/memory': 'Memoria',
  '/agent/instructions': 'Instrucciones',
  '/agent/tools': 'Herramientas',
  '/agent/audit-log': 'Bitácora',
  '/settings/agent-prompts': 'Prompts Globales',
  '/login': 'Iniciar sesión',
}

// Prefix titles - for routes with an optional trailing param
// (/settings/agents/:profileId?, /career/:resourceKey/:recordSlug?, etc).
const PREFIX_TITLES: [string, string][] = [
  ['/agent/pdf-template-styles', 'Estilos PDF'],
  ['/agent/pdf-templates', 'Plantillas PDF'],
  ['/settings/agents', 'Catálogo de Agentes'],
  ['/settings/sections', 'Secciones del Admin'],
]

const resolveSectionTitle = (pathname: string): string => {
  if (STATIC_TITLES[pathname]) return STATIC_TITLES[pathname]

  const careerMatch = pathname.match(/^\/career\/([^/]+)/)
  if (careerMatch) {
    const resource = CAREER_RESOURCES[careerMatch[1]]
    if (resource) return resource.label
  }

  const prefixMatch = PREFIX_TITLES.find(([prefix]) => pathname.startsWith(prefix))
  if (prefixMatch) return prefixMatch[1]

  return BASE_TITLE
}

/** Keeps the browser tab title as "Admin Panel - <Sección>" in sync with the route. */
export const usePageTitle = (): void => {
  const { pathname } = useLocation()

  useEffect(() => {
    const section = resolveSectionTitle(pathname)
    document.title = section === BASE_TITLE ? BASE_TITLE : `${BASE_TITLE} - ${section}`
  }, [pathname])
}
