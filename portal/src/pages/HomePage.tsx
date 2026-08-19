import { Link } from 'react-router-dom'
import { useHome } from '@/hooks/useHome'
import { useAbout } from '@/hooks/useAbout'
import { useTrackClick } from '@/hooks/useTracking'
import { ProjectCard } from '@/components/Common/ProjectCard'
import { BlogCard } from '@/components/Common/BlogCard'
import { MetricChips } from '@/components/Common/MetricChips'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'

export const HomePage = () => {
  const { data: home, isLoading, error } = useHome()
  const { data: about } = useAbout()
  const { trackClick } = useTrackClick()

  const handleCTA = (action: string) => {
    trackClick(`hero-${action}`)
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="No se pudo cargar el contenido de la Home" />

  const anchor = home?.anchor_project

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50/40 to-slate-50/40 dark:from-slate-900/40 dark:to-slate-950/40">
      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl hero-split">
          <div className="text-center content:text-left">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-text mb-4">
              {home?.hero_title || 'Carlos Jiménez Hirashi'}
            </h1>
            {home?.hero_subtitle && (
              <p className="text-xl sm:text-2xl text-primary font-semibold mb-4">{home.hero_subtitle}</p>
            )}
            {home?.hero_intro && (
              <p className="text-lg text-text-secondary max-w-2xl mx-auto content:mx-0 mb-8 whitespace-pre-wrap">
                {home.hero_intro}
              </p>
            )}

            <div className="flex flex-col sm:flex-row gap-4 justify-center content:justify-start">
              {anchor && (
                <Link
                  to={`/projects/${anchor.id}`}
                  onClick={() => handleCTA('anchor-case')}
                  className="btn px-8 py-3 font-semibold"
                >
                  {/* Split only on a dash surrounded by spaces (" - "/" — ") -
                      a bare hyphen with no spaces is part of a word (e.g.
                      "E-Commerce"), not a title/subtitle separator. */}
                  Ver Caso {anchor.title.split(/\s[-–—]\s/)[0].trim()}
                </Link>
              )}
              <Link
                to="/projects"
                onClick={() => handleCTA('view-projects')}
                className={anchor ? 'btn-secondary px-8 py-3 font-semibold' : 'btn px-8 py-3 font-semibold'}
              >
                Ver proyectos
              </Link>
            </div>
          </div>

          {about?.photo_url && (
            <div className="flex justify-center content:justify-end">
              <img
                src={about.photo_url}
                alt="Carlos A. Jiménez Hirashi"
                className="w-64 h-64 sm:w-80 sm:h-80 rounded-2xl object-cover border-4 border-primary shadow-glow"
              />
            </div>
          )}
        </div>
      </section>

      {/* Stats */}
      {home && home.stats.length > 0 && (
        <section className="py-12 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl grid grid-cols-2 sm:grid-cols-4 gap-6">
            {home.stats.map(stat => (
              <div key={stat.label} className="card text-center p-6">
                <div className="text-3xl font-bold text-primary mb-2">{stat.value}</div>
                <p className="text-text-secondary text-sm">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Flagship case study */}
      {anchor && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-5xl card overflow-hidden">
            {anchor.image_url && (
              <img src={anchor.image_url} alt={anchor.title} className="w-full h-64 object-cover" />
            )}
            <div className="p-8">
              <div className="flex items-center gap-2 mb-4 text-xs text-text-secondary mono">
                {anchor.year && <span>{anchor.year}</span>}
                {anchor.category && <span className="badge mono">{anchor.category}</span>}
                {anchor.industry && <span className="badge badge-secondary">{anchor.industry}</span>}
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-text mb-4">{anchor.title}</h2>
              {anchor.problem && <p className="text-text-secondary mb-4 whitespace-pre-wrap">{anchor.problem}</p>}
              <div className="mb-6">
                <MetricChips metrics={anchor.metrics} />
              </div>
              <Link
                to={`/projects/${anchor.id}`}
                onClick={() => handleCTA('anchor-detail')}
                className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-semibold"
              >
                Ver caso completo →
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* Featured Projects */}
      {home && home.featured_projects.length > 0 && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <div className="flex justify-between items-center mb-12">
              <h2 className="text-3xl font-bold text-text">Proyectos</h2>
              <Link
                to="/projects"
                className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-semibold"
              >
                Ver todos →
              </Link>
            </div>

            <div className="grid grid-cols-1 content:grid-cols-3 gap-6">
              {home.featured_projects.map(project => (
                <ProjectCard key={project.id} project={project} featured />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Featured Publications */}
      {home && home.featured_publications.length > 0 && (
        <section className="section-alt py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <div className="flex justify-between items-center mb-12">
              <h2 className="text-3xl font-bold text-text">Del blog</h2>
              <Link
                to="/blog"
                className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-semibold"
              >
                Ver todos →
              </Link>
            </div>

            <div className="grid grid-cols-1 content:grid-cols-3 gap-6">
              {home.featured_publications.map(post => (
                <BlogCard key={post.id} post={post} />
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
