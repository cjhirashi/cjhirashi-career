import { useState } from 'react'
import { useProjects } from '@/hooks/useProjects'
import { ProjectCard } from '@/components/Common/ProjectCard'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'
import { useTrackClick } from '@/hooks/useTracking'

export const ProjectsPage = () => {
  const { data: projects, isLoading, error } = useProjects()
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null)
  const { trackClick } = useTrackClick()

  const handleFilter = (value: string) => {
    trackClick(`filter-${value}`)
    setSelectedFilter(selectedFilter === value ? null : value)
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="No se pudieron cargar los proyectos" />

  // A single flat filter bar combining category ("Systems", "Data"...) and
  // industry ("Salud", "Fintech"...) - matches cjhirashi.com's Proyectos page.
  const filters = Array.from(
    new Set((projects ?? []).flatMap(p => [p.category, p.industry].filter((v): v is string => !!v)))
  )

  const filteredProjects = selectedFilter
    ? projects?.filter(p => p.category === selectedFilter || p.industry === selectedFilter)
    : projects

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-text mb-4">Proyectos</h1>
          <p className="text-lg text-text-secondary">
            Sistemas de datos e IA diseñados para operar solos — incluso cuando fallar no es una opción.
          </p>
        </div>

        {/* Filter */}
        {filters.length > 0 && (
          <div className="mb-12">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  trackClick('filter-all')
                  setSelectedFilter(null)
                }}
                className={`mono px-4 py-2 rounded-full text-sm font-medium transition ${
                  selectedFilter === null
                    ? 'bg-cyan-600 text-white shadow-glow'
                    : 'bg-bg-card backdrop-blur-lg border border-border text-text-secondary hover:border-border-glass-hover hover:text-primary'
                }`}
              >
                Todos
              </button>
              {filters.map(filter => (
                <button
                  key={filter}
                  onClick={() => handleFilter(filter)}
                  className={`mono px-4 py-2 rounded-full text-sm font-medium transition ${
                    selectedFilter === filter
                      ? 'bg-cyan-600 text-white shadow-glow'
                      : 'bg-bg-card backdrop-blur-lg border border-border text-text-secondary hover:border-border-glass-hover hover:text-primary'
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Projects Grid */}
        {filteredProjects && filteredProjects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map(project => (
              <ProjectCard key={project.id} project={project} featured={project.is_featured} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-text-secondary text-lg">No hay proyectos para este filtro.</p>
          </div>
        )}
      </div>
    </div>
  )
}
