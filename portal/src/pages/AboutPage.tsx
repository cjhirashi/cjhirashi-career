import { Link } from 'react-router-dom'
import { useAbout } from '@/hooks/useAbout'
import { useTrackClick } from '@/hooks/useTracking'
import { MetricChips } from '@/components/Common/MetricChips'
import { Markdown } from '@/components/Common/Markdown'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'
import { format, parseISO } from 'date-fns'

const formatMonthYear = (value: string | null) => {
  if (!value) return 'Presente'
  try {
    return format(parseISO(value), 'MMM yyyy')
  } catch {
    return value
  }
}

export const AboutPage = () => {
  const { data: about, isLoading, error } = useAbout()
  const { trackClick } = useTrackClick()

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="No se pudo cargar el contenido de Sobre Mí" />

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 text-center">
        <div className="mx-auto max-w-3xl">
          {about?.photo_url && (
            <img
              src={about.photo_url}
              alt="Carlos A. Jiménez Hirashi"
              className="w-40 h-40 rounded-full object-cover border-4 border-primary shadow-glow mx-auto mb-6"
            />
          )}
          {about?.name && (
            <p className="text-2xl sm:text-3xl font-bold text-text mb-3">{about.name}</p>
          )}
          {about?.professional_tagline && (
            <p className="text-lg text-primary font-semibold mb-4">{about.professional_tagline}</p>
          )}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/contact"
              onClick={() => trackClick('about-hablemos')}
              className="btn px-8 py-3 font-semibold"
            >
              Hablemos
            </Link>
            <Link
              to="/projects"
              onClick={() => trackClick('about-ver-proyectos')}
              className="btn-secondary px-8 py-3 font-semibold"
            >
              Ver proyectos
            </Link>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 pb-16 space-y-16">
        {/* Historia + Propuesta de valor */}
        {(about?.bio_summary || about?.unique_value_proposition) && (
          <section className="space-y-8">
            {about?.bio_summary && (
              <div>
                <h2 className="text-2xl font-bold text-text mb-4">Mi historia</h2>
                <Markdown>{about.bio_summary}</Markdown>
              </div>
            )}
            {about?.unique_value_proposition && (
              <div>
                <h2 className="text-2xl font-bold text-text mb-4">Propuesta de valor</h2>
                <Markdown>{about.unique_value_proposition}</Markdown>
              </div>
            )}
          </section>
        )}

        {/* 1. Experiencia */}
        {about && about.work_history.length > 0 && (
          <section>
            <h2 className="text-2xl font-bold text-text mb-8">Experiencia</h2>
            <div className="space-y-8">
              {about.work_history.map((item, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-3 h-3 rounded-full bg-cyan-600 shadow-glow mt-2"></div>
                  </div>
                  <div className="flex-grow pb-2 border-l border-border pl-6">
                    <p className="text-sm font-bold text-primary mono">
                      {formatMonthYear(item.start_date)} - {formatMonthYear(item.end_date)}
                    </p>
                    <h3 className="text-lg font-bold text-text">{item.role_title}</h3>
                    <p className="text-text-secondary font-medium">{item.company}</p>
                    {(item.narrative || item.description) && (
                      <Markdown className="text-sm mt-2">{item.narrative || item.description!}</Markdown>
                    )}
                    {item.achievements && (
                      <div className="mt-2">
                        <p className="text-sm font-semibold text-text">Caso de éxito:</p>
                        <Markdown className="text-sm">{item.achievements}</Markdown>
                      </div>
                    )}
                    {item.key_metrics != null && (
                      <div className="mt-3">
                        <MetricChips metrics={item.key_metrics} />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 2. Habilidades Técnicas (agrupadas por categoría) */}
        {about && about.skill_groups.length > 0 && (
          <section>
            <h2 className="text-2xl font-bold text-text mb-8">Habilidades Técnicas</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
              {about.skill_groups.map(group => (
                <div key={group.category}>
                  <h3 className="text-sm font-bold text-text-secondary uppercase tracking-wide mb-3">
                    {group.category}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {group.skills.map(skill => (
                      <span key={skill} className="badge mono">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 3. Certificaciones */}
        {about && about.certifications.length > 0 && (
          <section>
            <h2 className="text-2xl font-bold text-text mb-8">Certificaciones</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {about.certifications.map((cert, index) => (
                <div key={index} className="card p-4">
                  <h3 className="font-bold text-text">{cert.name}</h3>
                  <p className="text-text-secondary text-sm">
                    {[cert.institution, cert.year].filter(Boolean).join(' · ')}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      {/* Footer CTA */}
      <section className="section-alt py-16 px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-2xl sm:text-3xl font-bold text-text mb-6">¿Un sistema que no puede fallar?</h2>
        <Link
          to="/contact"
          onClick={() => trackClick('about-footer-cta')}
          className="btn inline-flex px-8 py-3 font-semibold"
        >
          Hablemos
        </Link>
      </section>
    </div>
  )
}
