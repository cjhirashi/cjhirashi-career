import { Link } from 'react-router-dom'
import { Project } from '@/types'
import { useTrackClick } from '@/hooks/useTracking'

interface ProjectCardProps {
  project: Project
  featured?: boolean
}

export const ProjectCard = ({ project, featured }: ProjectCardProps) => {
  const { trackClick } = useTrackClick()

  return (
    <Link
      to={`/projects/${project.id}`}
      className="card group overflow-hidden hover:shadow-lg block p-5"
      onClick={() => trackClick(`project-${project.id}`)}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        {project.category && <span className="badge mono">{project.category}</span>}
        {featured && <div className="badge badge-secondary">Destacado</div>}
      </div>

      <h3 className="font-bold text-lg text-text mb-2">{project.title}</h3>
      {project.card_summary && (
        <p className="text-text-secondary text-sm mb-3 line-clamp-3">{project.card_summary}</p>
      )}

      {project.tech_stack.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {project.tech_stack.slice(0, 3).map(tech => (
            <span key={tech} className="badge mono badge-secondary">
              {tech}
            </span>
          ))}
          {project.tech_stack.length > 3 && (
            <span className="badge badge-secondary mono">+{project.tech_stack.length - 3}</span>
          )}
        </div>
      )}
    </Link>
  )
}
