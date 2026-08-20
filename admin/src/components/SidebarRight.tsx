import React, { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import { Sparkles, MessageCircle, BookOpen, X } from 'lucide-react'
import { CAREER_RESOURCES } from '@/config/careerResources'

type RightPanelTab = 'chat' | 'instructions'

interface PageInstructions {
  title: string
  body: string
}

const STATIC_INSTRUCTIONS: Record<string, PageInstructions> = {
  '/dashboard': {
    title: 'Dashboard',
    body: 'Resumen general de tu actividad de carrera: conteos rápidos y tu actividad de búsqueda semanal (aplicaciones, respuestas y entrevistas). Los datos se calculan solos a partir de lo que registres en las secciones de Carrera.',
  },
  '/metrics': {
    title: 'Métricas',
    body: 'Vista de métricas del portafolio público y del panel. Por ahora son cifras de referencia — se llenan solas conforme haya tráfico e interacciones reales.',
  },
  '/search-metrics': {
    title: 'Métricas de Búsqueda',
    body: 'Visualización gráfica de la Operativa de Búsqueda: embudo de vacantes a ofertas, triage de vacantes (fit %, evaluación, track), segmentos de mercado, networking, empresas diana, el rubro de Factores de Fit y el avance del plan de búsqueda activo. Todo se calcula en vivo desde las 12 tablas del dominio — no es información que se edite aquí.',
  },
  '/files': {
    title: 'Archivos',
    body: 'Sube cualquier archivo (imágenes, documentos) y obtén un link público para referenciarlo donde quieras, por ejemplo dentro de un campo Markdown con ![descripción](link). "Copiar link" copia la URL pública; "Eliminar" borra el archivo del bucket de forma permanente.',
  },
}

/** Instructions for any of the 30+ career-domain resources: leads with the
 * resource's own `description` (what the table is actually for - see
 * careerResources.ts, sourced from the Metodologías Operativas) and appends
 * a generic action hint derived from its config, instead of requiring a
 * hand-written action sentence per resource too. */
const getCareerResourceInstructions = (resourceKey: string): PageInstructions | null => {
  const resource = CAREER_RESOURCES[resourceKey]
  if (!resource) return null

  const intro = resource.description ? `${resource.description} ` : ''

  if (resource.mode === 'singleton') {
    return {
      title: resource.label,
      body: `${intro}Este es tu único registro de ${resource.labelSingular.toLowerCase()}. Edítalo con el botón de la tarjeta cuando cambie tu información — no se crean registros adicionales.`,
    }
  }
  const newLabel = `${resource.genderFeminine ? 'Nueva' : 'Nuevo'} ${resource.labelSingular}`
  return {
    title: resource.label,
    body: `${intro}Usa "${newLabel}" para agregar un registro. Desde la tabla puedes editar o eliminar cualquiera existente — los cambios se guardan de inmediato.`,
  }
}

const getPageInstructions = (pathname: string): PageInstructions => {
  if (STATIC_INSTRUCTIONS[pathname]) return STATIC_INSTRUCTIONS[pathname]

  const careerMatch = pathname.match(/^\/career\/([^/]+)$/)
  if (careerMatch) {
    const instructions = getCareerResourceInstructions(careerMatch[1])
    if (instructions) return instructions
  }

  return {
    title: 'Esta pantalla',
    body: 'Todavía no hay instrucciones específicas para esta pantalla.',
  }
}

interface SidebarRightProps {
  onClose: () => void
}

/**
 * Right-hand panel with two modes, switched by a Glass Steel pill:
 * - "Chat": reserved for the future in-Admin AI assistant (AWS Bedrock, see
 *   CLAUDE.md "Agent Bedrock"). The backend for that assistant does not
 *   exist yet, so this stays a static "coming soon" placeholder - no chat
 *   input, no fake interactivity.
 * - "Instrucciones": contextual help for whatever page is currently open,
 *   derived from the route (career-domain resources pull their blurb from
 *   their own config, so this never goes stale as resources are added).
 *
 * Responsive behavior (mirrors the left Sidebar's mobile-drawer pattern,
 * see Layout.tsx for the matching backdrop):
 * - Mobile (<md): full-screen overlay above the work area.
 * - Tablet (md-lg): overlay anchored to the right edge, not full width.
 * - Desktop (xl+): back in normal flow alongside the main content, same
 *   as before.
 */
export const SidebarRight: React.FC<SidebarRightProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState<RightPanelTab>('instructions')
  const location = useLocation()
  const instructions = getPageInstructions(location.pathname)

  return (
    <aside
      className={clsx(
        'glass-panel backdrop-blur-[20px] flex flex-col border-l border-border p-4 gap-4',
        'fixed inset-0 z-50 w-full',
        'md:inset-y-0 md:left-auto md:right-0 md:w-96 md:max-w-[90vw] md:rounded-l-2xl',
        'xl:static xl:z-auto xl:w-80 xl:h-auto xl:flex-shrink-0 xl:rounded-none'
      )}
      aria-label="Panel de asistencia"
    >
      {/* Header: tab switch (chat / instrucciones) + hide button */}
      <div className="flex items-center justify-between gap-2 flex-shrink-0">
        <div className="theme-pill" role="group" aria-label="Modo del panel">
          <button
            type="button"
            className="theme-pill-btn"
            aria-pressed={activeTab === 'chat'}
            onClick={() => setActiveTab('chat')}
            title="Chat del asistente"
          >
            <MessageCircle size={15} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="theme-pill-btn"
            aria-pressed={activeTab === 'instructions'}
            onClick={() => setActiveTab('instructions')}
            title="Instrucciones de la pantalla"
          >
            <BookOpen size={15} aria-hidden="true" />
          </button>
          <span className="theme-pill-indicator" data-pos={activeTab === 'chat' ? '0' : '1'} aria-hidden="true" />
        </div>

        <button
          type="button"
          onClick={onClose}
          className="p-1.5 rounded-lg text-text-secondary hover:bg-glass hover:text-text transition-colors flex-shrink-0"
          aria-label="Ocultar panel"
          title="Ocultar panel"
        >
          <X size={16} aria-hidden="true" />
        </button>
      </div>

      {/* Body */}
      {activeTab === 'chat' ? (
        <div className="card p-6 flex flex-col items-center text-center gap-3 flex-1 justify-center">
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ background: 'var(--primary-light)' }}
          >
            <Sparkles className="text-primary" size={22} aria-hidden="true" />
          </div>
          <h2 className="font-semibold text-text">Asistente IA</h2>
          <span className="badge badge-cyan">Próximamente</span>
          <p className="text-text-secondary text-sm">
            El asistente impulsado por IA para ayudarte a gestionar tu carrera todavía no está disponible en este
            panel.
          </p>
        </div>
      ) : (
        <div className="card p-5 flex-1 overflow-y-auto">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen size={16} className="text-primary flex-shrink-0" aria-hidden="true" />
            <h2 className="font-semibold text-text text-sm">{instructions.title}</h2>
          </div>
          <p className="text-text-secondary text-sm leading-relaxed">{instructions.body}</p>
        </div>
      )}
    </aside>
  )
}
