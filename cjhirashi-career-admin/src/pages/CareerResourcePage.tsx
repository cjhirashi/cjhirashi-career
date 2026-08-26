import React from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { SearchX } from 'lucide-react'
import { CAREER_RESOURCES } from '@/config/careerResources'
import { CareerResourceView } from '@/components/career/CareerResourceView'

/**
 * Generic route for every career-domain (v2) resource: looks up the
 * `ResourceConfig` for `:resourceKey` in the registry and renders it through
 * `CareerResourceView`. Avoids declaring 30 near-identical routes/pages.
 */
export const CareerResourcePage: React.FC = () => {
  const { resourceKey } = useParams<{ resourceKey: string }>()
  const config = resourceKey ? CAREER_RESOURCES[resourceKey] : undefined

  if (!config) {
    return (
      <div className="card">
        <div className="card-body text-center py-12">
          <SearchX size={32} className="mx-auto mb-3 text-text-muted" aria-hidden="true" />
          <h1 className="text-lg font-semibold text-text">Recurso no encontrado</h1>
          <p className="text-text-secondary text-sm mt-2">
            No existe ningún recurso de carrera con la clave &quot;{resourceKey}&quot;.
          </p>
          <Link to="/dashboard" className="text-cyan-600 dark:text-cyan-400 hover:underline text-sm mt-4 inline-block">
            Volver al Dashboard
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <CareerResourceView key={config.key} config={config} listPath={`/career/${config.key}`} />
    </div>
  )
}

/** Redirect target for stray/legacy `/career` (no resource key). */
export const CareerIndexRedirect: React.FC = () => <Navigate to="/dashboard" replace />

export default CareerResourcePage
