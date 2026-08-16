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
    <div
      className="bg-white border border-slate-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
      onClick={handleProjectClick}
    >
      {/* Thumbnail */}
      {project.thumbnail && (
        <div className="relative w-full h-48 bg-gradient-to-br from-cyan-100 to-slate-100 overflow-hidden">
          <img
            src={project.thumbnail}
            alt={project.title}
            className="w-full h-full object-cover hover:scale-105 transition-transform"
            loading="lazy"
          />
          {featured && (
            <div className="absolute top-2 right-2 bg-cyan-600 text-white px-3 py-1 rounded-full text-xs font-semibold">
              Featured
            </div>
          )}
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        <h3 className="font-bold text-lg text-slate-900 mb-2">{project.title}</h3>
        <p className="text-slate-600 text-sm mb-3 line-clamp-2">
          {project.shortDescription || project.description}
        </p>

        {/* Technologies */}
        {project.technologies && project.technologies.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-1">
            {project.technologies.slice(0, 3).map(tech => (
              <span
                key={tech}
                className="inline-block bg-cyan-50 text-cyan-700 text-xs px-2 py-1 rounded"
              >
                {tech}
              </span>
            ))}
            {project.technologies.length > 3 && (
              <span className="inline-block bg-slate-100 text-slate-600 text-xs px-2 py-1 rounded">
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
              className="flex-1 bg-cyan-600 hover:bg-cyan-700 text-white py-2 px-3 rounded text-center text-sm font-medium transition"
            >
              View Project
            </a>
          )}
          {project.github && (
            <a
              href={project.github}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-900 py-2 px-3 rounded text-center text-sm font-medium transition"
            >
              GitHub
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
