import React from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
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
          <p className="text-3xl mb-3">🔎</p>
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
    <div>
      {config.description && (
        <p className="text-slate-600 dark:text-slate-400 mb-4">{config.description}</p>
      )}
      <CareerResourceView config={config} />
    </div>
  )
}

/** Redirect target for stray/legacy `/career` (no resource key). */
export const CareerIndexRedirect: React.FC = () => <Navigate to="/dashboard" replace />

export default CareerResourcePage
