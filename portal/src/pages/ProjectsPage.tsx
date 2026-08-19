import { useState } from 'react'
import { useProjects } from '@/hooks/useProjects'
import { ProjectCard } from '@/components/Common/ProjectCard'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'
import { useTrackClick } from '@/hooks/useTracking'

export const ProjectsPage = () => {
  const { data: projects, isLoading, error } = useProjects()
  const [selectedTech, setSelectedTech] = useState<string | null>(null)
  const { trackClick } = useTrackClick()

  const handleTechFilter = (tech: string) => {
    trackClick(`filter-${tech}`)
    setSelectedTech(selectedTech === tech ? null : tech)
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="No se pudieron cargar los proyectos" />

  const allTechs = Array.from(new Set(projects?.flatMap(p => p.tech_stack) || []))

  const filteredProjects = selectedTech
    ? projects?.filter(p => p.tech_stack.includes(selectedTech))
    : projects

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-text mb-4">Mis Proyectos</h1>
          <p className="text-lg text-text-secondary">
            Una selección de proyectos que muestran mis habilidades y experiencia.
          </p>
        </div>

        {/* Filter */}
        {allTechs.length > 0 && (
          <div className="mb-12">
            <h2 className="text-sm font-bold text-text-secondary uppercase tracking-wide mb-4">
              Filtrar por tecnología
            </h2>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  trackClick('filter-all')
                  setSelectedTech(null)
                }}
                className={`mono px-4 py-2 rounded-full text-sm font-medium transition ${
                  selectedTech === null
                    ? 'bg-cyan-600 text-white shadow-glow'
                    : 'bg-bg-card backdrop-blur-lg border border-border text-text-secondary hover:border-border-glass-hover hover:text-primary'
                }`}
              >
                Todos los proyectos
              </button>
              {allTechs.map(tech => (
                <button
                  key={tech}
                  onClick={() => handleTechFilter(tech)}
                  className={`mono px-4 py-2 rounded-full text-sm font-medium transition ${
                    selectedTech === tech
                      ? 'bg-cyan-600 text-white shadow-glow'
                      : 'bg-bg-card backdrop-blur-lg border border-border text-text-secondary hover:border-border-glass-hover hover:text-primary'
                  }`}
                >
                  {tech}
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
