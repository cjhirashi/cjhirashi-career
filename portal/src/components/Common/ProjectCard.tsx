import { Link } from 'react-router-dom'
import { Project } from '@/types'
import { useTrackClick } from '@/hooks/useTracking'

interface ProjectCardProps {
  project: Project
}

export const ProjectCard = ({ project }: ProjectCardProps) => {
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
        </div>
      )}

      <div className="p-5">
        <div className="flex items-center gap-2 mb-3">
          {project.category && <span className="badge mono">{project.category}</span>}
          {project.industry && <span className="badge badge-secondary">{project.industry}</span>}
        </div>

        <h3 className="font-bold text-lg text-text mb-2">{project.title}</h3>
        {project.card_summary && (
          <p className="text-text-secondary text-sm line-clamp-3">{project.card_summary}</p>
        )}
      </div>
    </Link>
  )
}
