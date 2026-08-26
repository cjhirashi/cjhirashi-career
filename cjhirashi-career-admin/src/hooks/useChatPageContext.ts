import { useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { CAREER_DOMAINS, CAREER_RESOURCES } from '@/config/careerResources'
import { resolveChatProfileKey } from '@/config/chatSectionProfiles'
import { BedrockPageContext } from '@/types/bedrock'

const STATIC_PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/metrics': 'Métricas',
  '/search-metrics': 'Métricas de Búsqueda',
  '/job-discovery': 'Descubrir vacantes',
  '/files': 'Archivos',
  '/linkedin': 'LinkedIn · Publicar',
  '/agent/chat': 'Chat General',
  '/profile': 'Perfil',
  '/change-password': 'Cambiar contraseña',
}

/** Find which career domain owns a resource key, if any. */
function findDomainKeyForResource(resourceKey: string): string | undefined {
  for (const domain of CAREER_DOMAINS) {
    if (domain.resourceKeys.includes(resourceKey)) return domain.key
  }
  return undefined
}

/**
 * Derives `BedrockPageContext` from the current React Router location.
 * Passed to the Bedrock harness on contextual chat turns so the agent knows
 * which screen the user is on (see api/src/services/bedrock/prompt.py).
 */
export function useChatPageContext(): BedrockPageContext {
  const { pathname } = useLocation()

  return useMemo(() => {
    const route = pathname

    if (STATIC_PAGE_TITLES[route]) {
      const ctx: BedrockPageContext = { route, page_title: STATIC_PAGE_TITLES[route] }
      ctx.chat_profile = resolveChatProfileKey(ctx) ?? undefined
      return ctx
    }

    const careerMatch = route.match(/^\/career\/([^/]+)(?:\/[^/]+)?$/)
    if (careerMatch) {
      const resourceKey = careerMatch[1]
      const resource = CAREER_RESOURCES[resourceKey]
      const domainKey = findDomainKeyForResource(resourceKey)
      const ctx: BedrockPageContext = {
        route,
        resource_key: resourceKey,
        page_title: resource?.label ?? resourceKey,
        domain_key: domainKey,
      }
      ctx.chat_profile = resolveChatProfileKey(ctx) ?? undefined
      return ctx
    }

    const agentMatch = route.match(/^\/agent\/([^/]+)(?:\/[^/]+)?$/)
    if (agentMatch) {
      const ctx: BedrockPageContext = {
        route,
        page_title: `Agente · ${agentMatch[1]}`,
      }
      ctx.chat_profile = resolveChatProfileKey(ctx) ?? undefined
      return ctx
    }

    const ctx: BedrockPageContext = { route, page_title: 'Esta pantalla' }
    ctx.chat_profile = resolveChatProfileKey(ctx) ?? undefined
    return ctx
  }, [pathname])
}
