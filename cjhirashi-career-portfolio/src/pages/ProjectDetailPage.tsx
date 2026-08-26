import { Link, useParams } from 'react-router-dom'
import { useProjectById } from '@/hooks/useProjects'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'
import { MetricChips } from '@/components/Common/MetricChips'
import { Markdown } from '@/components/Common/Markdown'
import { useTrackClick } from '@/hooks/useTracking'

const Section = ({ title, content }: { title: string; content: string }) => (
  <div className="mb-8">
    <h2 className="text-xl font-bold text-text mb-3">{title}</h2>
    <Markdown>{content}</Markdown>
  </div>
)

export const ProjectDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const { data: project, isLoading, error } = useProjectById(id ?? '')
  const { trackClick } = useTrackClick()

  if (isLoading) return <LoadingSpinner />
  if (error || !project) return <ErrorMessage message="No se pudo cargar el proyecto" />

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <Link to="/projects" className="text-primary text-sm font-medium mb-6 inline-block">
          ← Volver a Proyectos
        </Link>

        {project.image_url && (
          <img
            src={project.image_url}
            alt={project.title}
            className="w-full h-64 sm:h-80 object-cover rounded-2xl mb-8"
          />
        )}

        <div className="flex flex-wrap items-center gap-2 mb-4">
          {project.category && <span className="badge mono">{project.category}</span>}
          {project.industry && <span className="badge badge-secondary">{project.industry}</span>}
          {project.year && <span className="badge badge-secondary mono">{project.year}</span>}
        </div>

        <h1 className="text-3xl sm:text-4xl font-bold text-text mb-4">{project.title}</h1>

        {project.card_summary && <p className="text-lg text-text-secondary mb-6">{project.card_summary}</p>}

        <div className="mb-8">
          <MetricChips metrics={project.metrics} />
        </div>

        <div className="flex gap-3 mb-10">
          {project.demo_url && (
            <a
              href={project.demo_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackClick(`project-demo-${project.id}`)}
              className="btn px-6 py-2 text-sm font-medium"
            >
              Ver demo
            </a>
          )}
          {project.github_url && (
            <a
              href={project.github_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackClick(`project-github-${project.id}`)}
              className="btn-secondary px-6 py-2 text-sm font-medium"
            >
              GitHub
            </a>
          )}
        </div>

        {project.detailed_summary && <Section title="Resumen" content={project.detailed_summary} />}
        {project.problem && <Section title="El problema" content={project.problem} />}
        {project.solution && <Section title="La solución" content={project.solution} />}
        {project.architecture && <Section title="Arquitectura" content={project.architecture} />}
        {project.approach_steps && <Section title="Enfoque" content={project.approach_steps} />}

        {project.tech_stack.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold text-text mb-3">Stack tecnológico</h2>
            <div className="flex flex-wrap gap-2">
              {project.tech_stack.map(tech => (
                <span key={tech} className="badge mono">
                  {tech}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
