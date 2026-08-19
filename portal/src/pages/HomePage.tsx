import { Link } from 'react-router-dom'
import { useHome } from '@/hooks/useHome'
import { useTrackClick } from '@/hooks/useTracking'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'

export const HomePage = () => {
  const { data: home, isLoading, error } = useHome()
  const { trackClick } = useTrackClick()

  const handleCTA = (action: string) => {
    trackClick(`hero-${action}`)
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="No se pudo cargar el contenido de la Home" />

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50/40 to-slate-50/40 dark:from-slate-900/40 dark:to-slate-950/40">
      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-text mb-4">
            {home?.hero_title || 'Carlos Jiménez Hirashi'}
          </h1>
          {home?.hero_subtitle && (
            <p className="text-xl sm:text-2xl text-primary font-semibold mb-4">{home.hero_subtitle}</p>
          )}
          {home?.hero_intro && (
            <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-8 whitespace-pre-wrap">
              {home.hero_intro}
            </p>
          )}

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/projects"
              onClick={() => handleCTA('view-portfolio')}
              className="btn px-8 py-3 font-semibold"
            >
              Ver Proyectos
            </Link>
            <Link
              to="/contact"
              onClick={() => handleCTA('contact-cta')}
              className="btn-secondary px-8 py-3 font-semibold"
            >
              Contactar
            </Link>
          </div>
        </div>
      </section>

      {/* Featured Projects */}
      {home && home.featured_projects.length > 0 && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <div className="flex justify-between items-center mb-12">
              <h2 className="text-3xl font-bold text-text">Proyectos Destacados</h2>
              <Link
                to="/projects"
                className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-semibold"
              >
                Ver todos →
              </Link>
            </div>

            <div className="grid grid-cols-1 content:grid-cols-3 gap-6">
              {home.featured_projects.map(project => (
                <Link
                  key={project.id}
                  to={`/projects/${project.id}`}
                  className="card p-6 block hover:shadow-lg"
                  onClick={() => trackClick(`home-project-${project.id}`)}
                >
                  {project.category && <span className="badge mb-3">{project.category}</span>}
                  <h3 className="font-bold text-lg text-text mb-2">{project.title}</h3>
                  {project.card_summary && (
                    <p className="text-text-secondary text-sm line-clamp-3 mb-3">{project.card_summary}</p>
                  )}
                  {project.tech_stack.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {project.tech_stack.slice(0, 3).map(tech => (
                        <span key={tech} className="badge mono badge-secondary">
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Featured Publications */}
      {home && home.featured_publications.length > 0 && (
        <section className="section-alt py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl">
            <div className="flex justify-between items-center mb-12">
              <h2 className="text-3xl font-bold text-text">Del Blog</h2>
              <Link
                to="/blog"
                className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-semibold"
              >
                Ver todo →
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {home.featured_publications.map(post => (
                <Link
                  key={post.id}
                  to={`/blog/${post.slug ?? post.id}`}
                  className="card p-6 block hover:shadow-lg"
                  onClick={() => trackClick(`home-post-${post.id}`)}
                >
                  <h3 className="font-bold text-lg text-text mb-2 line-clamp-2">{post.title}</h3>
                  {post.excerpt && <p className="text-text-secondary text-sm line-clamp-2">{post.excerpt}</p>}
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* CTA Section */}
      <section className="section-alt py-16 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold text-text mb-4">¿Trabajamos juntos?</h2>
          <p className="text-text-secondary mb-8">
            Hablemos de cómo puedo ayudarte a llevar tu siguiente proyecto a la realidad.
          </p>
          <Link
            to="/contact"
            onClick={() => handleCTA('footer-cta')}
            className="btn inline-flex px-8 py-3 font-semibold"
          >
            Iniciar una conversación
          </Link>
        </div>
      </section>
    </div>
  )
}
