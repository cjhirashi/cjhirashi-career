import { Link } from 'react-router-dom'
import { Anchor, BookOpen, Clock, Layers, Network, ShieldCheck, TrendingUp } from 'lucide-react'
import { useHome } from '@/hooks/useHome'
import { useAbout } from '@/hooks/useAbout'
import { useTrackClick } from '@/hooks/useTracking'
import { ProjectCard } from '@/components/Common/ProjectCard'
import { BlogCard } from '@/components/Common/BlogCard'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'
import { Markdown } from '@/components/Common/Markdown'
import { isShortMetric, parseMetrics } from '@/utils/metrics'

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
  // "Otros" is the About page's own fallback bucket for uncategorized skills
  // (see api/src/routes/public.py) - it's not a real area of expertise, so it
  // doesn't belong in this compact teaser row.
  const skillCategories = (about?.skill_groups ?? [])
    .map(group => group.category)
    .filter(category => category !== 'Otros')
  // The bento mini-grid is fixed-size stat cells - only short KPI-style
  // values ("3.5 meses") fit there; longer achievement sentences stay in
  // the narrative card's prose instead of being squeezed into a square.
  const anchorMetrics = parseMetrics(anchor?.metrics)
    .filter(([, value]) => isShortMetric(value))
    .slice(0, 3)

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50/40 to-slate-50/40 dark:from-slate-900/40 dark:to-slate-950/40">
      {/* Hero - single centered column: photo, role badge, headline, tagline, CTAs */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 text-center">
        <div className="mx-auto max-w-3xl flex flex-col items-center">
          {home?.hero_photo_url && (
            <img
              src={home.hero_photo_url}
              alt="Carlos A. Jiménez Hirashi"
              className="w-48 h-48 sm:w-56 sm:h-56 rounded-full object-cover border-4 border-primary shadow-glow mb-6"
            />
          )}

          {home?.hero_subtitle && (
            <span className="badge mb-6 flex items-center gap-1.5 text-sm">
              <ShieldCheck size={14} /> {home.hero_subtitle}
            </span>
          )}

          {home?.hero_title && (
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-text mb-6">
              {home.hero_title}
            </h1>
          )}

          {home?.hero_intro && (
            <Markdown className="text-lg max-w-xl mb-8">{home.hero_intro}</Markdown>
          )}

          {home && home.hero_ctas.length > 0 && (
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {home.hero_ctas.map((cta, index) => {
                const className = index === 0 ? 'btn px-8 py-3 font-semibold' : 'btn-secondary px-8 py-3 font-semibold'
                const onClick = () => handleCTA(`cta-${index}-${cta.label}`)
                return cta.url.startsWith('/') ? (
                  <Link key={cta.label} to={cta.url} onClick={onClick} className={className}>
                    {cta.label}
                  </Link>
                ) : (
                  <a
                    key={cta.label}
                    href={cta.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={onClick}
                    className={className}
                  >
                    {cta.label}
                  </a>
                )
              })}
            </div>
          )}
        </div>
      </section>

      {/* Stats */}
      {home && home.stats.length > 0 && (
        <section className="py-8 px-4 sm:px-6 lg:px-8 border-t border-border">
          <div className="mx-auto max-w-4xl grid grid-cols-2 sm:grid-cols-4 divide-x divide-border">
            {home.stats.map(stat => (
              <div key={stat.label} className="text-center px-4">
                <div className="text-3xl font-bold mb-1 text-primary">{stat.value}</div>
                <p className="text-text-secondary text-xs uppercase tracking-wide">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Flagship case study - bento layout: narrative card + a grid of
          metric/image cards, matching cjhirashi.com's case-study block. */}
      {anchor && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl grid grid-cols-1 lg:grid-cols-[1fr_1.5fr] gap-4">
            {/* Narrative card */}
            <div className="card p-6">
              <div className="flex items-start justify-between gap-2 mb-4">
                <h2 className="text-lg font-bold text-text flex items-center gap-2">
                  <Anchor size={16} className="text-primary flex-shrink-0" />
                  Caso ancla — {anchor.title}
                </h2>
                {anchor.year && <span className="text-xs text-text-muted flex-shrink-0">{anchor.year}</span>}
              </div>

              {anchor.problem && (
                <div className="mb-4">
                  <p className="text-xs font-bold text-primary uppercase tracking-wide flex items-center gap-1.5 mb-1.5">
                    <Clock size={12} /> Problema
                  </p>
                  <Markdown className="text-sm">{anchor.problem}</Markdown>
                </div>
              )}

              {anchor.architecture && (
                <div className="mb-4">
                  <p className="text-xs font-bold text-primary uppercase tracking-wide flex items-center gap-1.5 mb-1.5">
                    <Network size={12} /> Arquitectura
                  </p>
                  <Markdown className="text-sm">{anchor.architecture}</Markdown>
                </div>
              )}

              {anchor.solution && (
                <div className="rounded-lg p-4 bg-secondary-light border border-secondary-light">
                  <p className="text-xs font-bold text-secondary uppercase tracking-wide flex items-center gap-1.5 mb-1.5">
                    <TrendingUp size={12} /> Resultado
                  </p>
                  <Markdown className="text-sm">{anchor.solution}</Markdown>
                </div>
              )}
            </div>

            {/* Metrics + image mini-grid */}
            <div className="grid grid-cols-2 gap-4">
              {anchorMetrics.map(([label, value]) => (
                <div key={label} className="card p-6 flex flex-col items-center justify-center text-center">
                  <div className="text-2xl font-bold mb-1 text-primary">{String(value)}</div>
                  <p className="text-text-secondary text-xs">{label}</p>
                </div>
              ))}
              {anchor.image_url && (
                <div className="card overflow-hidden">
                  <img src={anchor.image_url} alt={anchor.title} className="w-full h-full object-cover" />
                </div>
              )}
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
                <ProjectCard key={project.id} project={project} />
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
              <h2 className="text-3xl font-bold text-text flex items-center gap-2">
                <BookOpen size={22} className="text-primary" /> Del blog
              </h2>
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

      {/* Stack técnico - compact teaser of expertise areas (skill_groups'
          categories), the full skill breakdown lives on About. */}
      {skillCategories.length > 0 && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-3xl font-bold text-text flex items-center justify-center gap-2 mb-8">
              <Layers size={22} className="text-primary" /> Stack técnico
            </h2>
            <div className="flex flex-wrap justify-center gap-3 mb-6">
              {skillCategories.map(category => (
                <span key={category} className="badge mono">
                  {category}
                </span>
              ))}
            </div>
            <Link
              to="/about"
              onClick={() => trackClick('home-ver-stack-completo')}
              className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-semibold"
            >
              Ver más en Sobre Mí →
            </Link>
          </div>
        </section>
      )}

      {/* Footer CTA */}
      <section className="section-alt py-16 px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-2xl sm:text-3xl font-bold text-text mb-6">¿Hablamos de tu próximo sistema?</h2>
        <Link to="/contact" onClick={() => trackClick('home-footer-cta')} className="btn inline-flex px-8 py-3 font-semibold">
          Hablemos
        </Link>
      </section>
    </div>
  )
}
