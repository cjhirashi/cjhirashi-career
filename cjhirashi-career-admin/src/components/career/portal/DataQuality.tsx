import React from 'react'
import { ShieldCheck } from 'lucide-react'
import { SectionCard } from '@/components/career/MetricsCharts'
import type { PortalQuery } from '@/types/portalAnalytics'
import { formatNumber, formatRate } from './format'

/** Por debajo de esto un porcentaje dice poco: el tablero lo advierte (RF-062, RF-037). */
export const SMALL_SAMPLE = 100

interface Props {
  query: PortalQuery
  visits: number
  visitors: number
  /** Visitas del mismo rango sin excluir bots; sirve para calcular su proporción. */
  visitsWithBots: number | null
}

export const botShare = (visitsWithBots: number | null, visitsClean: number, excludingBots: boolean): number | null => {
  if (!visitsWithBots) return null
  return excludingBots ? Math.max(0, (visitsWithBots - visitsClean) / visitsWithBots) : null
}

export const DataQuality: React.FC<Props> = ({ query, visits, visitors, visitsWithBots }) => {
  const share = botShare(visitsWithBots, visits, query.excludeBots)
  const filters = Object.entries(query.filters)
  return (
    <SectionCard title="Calidad de los datos" subtitle="Qué tan sólidas son las cifras de arriba" icon={ShieldCheck}>
      <dl className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <dt className="text-text-secondary text-xs">Muestra</dt>
          <dd className="text-text mono">{formatNumber(visits)} visitas · {formatNumber(visitors)} visitantes</dd>
        </div>
        <div>
          <dt className="text-text-secondary text-xs">Bots detectados</dt>
          <dd className="text-text mono">{share === null ? (query.excludeBots ? '—' : 'incluidos') : formatRate(share)}</dd>
        </div>
        <div>
          <dt className="text-text-secondary text-xs">Mis visitas</dt>
          <dd className="text-text">{query.excludeOwner ? 'excluidas' : 'incluidas'}</dd>
        </div>
        <div>
          <dt className="text-text-secondary text-xs">Filtros</dt>
          <dd className="text-text">{filters.length === 0 ? 'ninguno' : filters.map(([k, v]) => `${k}: ${v}`).join(', ')}</dd>
        </div>
      </dl>
      {visits < SMALL_SAMPLE && (
        <p className="mt-4 text-xs text-warning-text" role="note">
          Muestra pequeña ({formatNumber(visits)} visitas): los porcentajes y comparaciones pueden cambiar mucho con pocas visitas más.
        </p>
      )}
    </SectionCard>
  )
}
