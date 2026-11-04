import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { useCareerList } from '@/hooks/useCareerResource'
import { AnnotationsPanel } from '@/components/career/portal/settings/AnnotationsPanel'
import { FunnelsPanel } from '@/components/career/portal/settings/FunnelsPanel'
import { GoalsPanel } from '@/components/career/portal/settings/GoalsPanel'

/** Metas, embudos y anotaciones de la analítica del portafolio (SPEC-0010): se crean aquí o por la API. */
export const PortalSettingsPage: React.FC = () => {
  const { data: sites, isLoading } = useCareerList<{ id: string; name: string }>('portal-sites', { limit: 1 })
  const site = sites?.[0]

  return (
    <div>
      <Link to="/metrics" className="inline-flex items-center gap-1.5 text-sm text-primary mb-4">
        <ArrowLeft size={15} aria-hidden="true" /> Volver a Métricas
      </Link>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-text">Configuración de la analítica</h1>
        <p className="text-text-secondary mt-2">
          Define qué cuenta como éxito, los recorridos que quieres seguir y las marcas de la gráfica. Los cambios se ven en
          Métricas en cuanto se guardan.
        </p>
      </div>

      {isLoading && <LoadingSpinner fullScreen={false} message="Cargando…" />}
      {!isLoading && !site && (
        <p className="text-text-secondary text-sm" role="alert">No hay un sitio de analítica configurado.</p>
      )}
      {site && (
        <div className="space-y-6">
          <GoalsPanel siteId={site.id} />
          <FunnelsPanel siteId={site.id} />
          <AnnotationsPanel siteId={site.id} />
        </div>
      )}
    </div>
  )
}
