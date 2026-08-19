import { Link } from 'react-router-dom'
import { Project } from '@/types'
import { useTrackClick } from '@/hooks/useTracking'
import { MetricChips } from './MetricChips'

interface ProjectCardProps {
  project: Project
  featured?: boolean
}

export const ProjectCard = ({ project, featured }: ProjectCardProps) => {
  const { trackClick } = useTrackClick()

  return (
    <Link
      to={`/projects/${project.id}`}
      className="card group overflow-hidden hover:shadow-lg block"
      onClick={() => trackClick(`project-${project.id}`)}
    >
      {project.image_url && (
        <div className="relative w-full h-44 bg-gradient-to-br from-cyan-100 to-slate-100 dark:from-slate-800 dark:to-slate-900 overflow-hidden">
          <img
            src={project.image_url}
            alt={project.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
          {featured && <div className="badge badge-float absolute top-2 right-2">Destacado</div>}
        </div>
      )}

      <div className="p-5">
        <div className="flex items-center gap-2 mb-2 text-xs text-text-secondary mono">
          {project.category && <span className="badge mono">{project.category}</span>}
          {project.industry && <span className="badge badge-secondary">{project.industry}</span>}
          {project.year && <span>{project.year}</span>}
        </div>

        <h3 className="font-bold text-lg text-text mb-2">{project.title}</h3>
        {project.card_summary && (
          <p className="text-text-secondary text-sm mb-3 line-clamp-2">{project.card_summary}</p>
        )}

        <div className="mb-3">
          <MetricChips metrics={project.metrics} />
        </div>

        <span className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-medium text-sm inline-flex items-center">
          Ver caso →
        </span>
      </div>
    </Link>
  )
}
