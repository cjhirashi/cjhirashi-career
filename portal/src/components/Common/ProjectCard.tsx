import { Project } from '@/types'
import { useTrackClick } from '@/hooks/useTracking'

interface ProjectCardProps {
  project: Project
  featured?: boolean
}

export const ProjectCard = ({ project, featured }: ProjectCardProps) => {
  const { trackClick } = useTrackClick()

  const handleProjectClick = () => {
    trackClick(`project-${project.id}`)
  }

  const handleViewProject = () => {
    trackClick(`project-view-${project.id}`)
  }

  return (
    <div className="card group overflow-hidden hover:shadow-lg" onClick={handleProjectClick}>
      {/* Thumbnail */}
      {project.thumbnail && (
        <div className="relative w-full h-48 bg-gradient-to-br from-cyan-100 to-slate-100 dark:from-slate-800 dark:to-slate-900 overflow-hidden">
          <img
            src={project.thumbnail}
            alt={project.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
          {featured && (
            <div className="badge badge-float absolute top-2 right-2">Featured</div>
          )}
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        <h3 className="font-bold text-lg text-text mb-2">{project.title}</h3>
        <p className="text-text-secondary text-sm mb-3 line-clamp-2">
          {project.shortDescription || project.description}
        </p>

        {/* Technologies */}
        {project.technologies && project.technologies.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-1">
            {project.technologies.slice(0, 3).map(tech => (
              <span key={tech} className="badge mono">
                {tech}
              </span>
            ))}
            {project.technologies.length > 3 && (
              <span className="badge badge-secondary mono">
                +{project.technologies.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Links */}
        <div className="flex gap-2">
          {project.link && (
            <a
              href={project.link}
              target="_blank"
              rel="noopener noreferrer"
              onClick={handleViewProject}
              className="btn flex-1 py-2 px-3 text-center text-sm font-medium"
            >
              View Project
            </a>
          )}
          {project.github && (
            <a
              href={project.github}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary flex-1 py-2 px-3 text-center text-sm font-medium"
            >
              GitHub
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
