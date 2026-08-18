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
  if (error) return <ErrorMessage message="Failed to load projects" />

  // Extract unique technologies
  const allTechs = Array.from(new Set(projects?.flatMap(p => p.technologies) || []))

  // Filter projects
  const filteredProjects = selectedTech
    ? projects?.filter(p => p.technologies.includes(selectedTech))
    : projects

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-text mb-4">My Projects</h1>
          <p className="text-lg text-text-secondary">
            A selection of projects that showcase my skills and expertise.
          </p>
        </div>

        {/* Filter */}
        {allTechs.length > 0 && (
          <div className="mb-12">
            <h2 className="text-sm font-bold text-text-secondary uppercase tracking-wide mb-4">
              Filter by Technology
            </h2>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  trackClick('filter-all')
                  setSelectedTech(null)
                }}
                className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                  selectedTech === null
                    ? 'bg-cyan-600 text-white dark:bg-cyan-500'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
                }`}
              >
                All Projects
              </button>
              {allTechs.map(tech => (
                <button
                  key={tech}
                  onClick={() => handleTechFilter(tech)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                    selectedTech === tech
                      ? 'bg-cyan-600 text-white dark:bg-cyan-500'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
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
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-text-secondary text-lg">No projects found for this filter.</p>
          </div>
        )}

        {/* Download CV */}
        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold text-text mb-6">Want to know more?</h2>
          <button
            onClick={() => trackClick('download-cv')}
            className="bg-primary hover:opacity-90 text-on-primary px-8 py-3 rounded-lg font-semibold transition"
          >
            Download Full CV
          </button>
        </div>
      </div>
    </div>
  )
}
