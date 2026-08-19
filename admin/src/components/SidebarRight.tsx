import React, { useState } from 'react'
import { useLocation } from 'react-router-dom'
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
}

/** Generic, always-accurate instructions for any of the 30 career-domain
 * resources, generated from its own config instead of requiring 30
 * hand-written descriptions (none of the resources set one). */
const getCareerResourceInstructions = (resourceKey: string): PageInstructions | null => {
  const resource = CAREER_RESOURCES[resourceKey]
  if (!resource) return null
  if (resource.mode === 'singleton') {
    return {
      title: resource.label,
      body: `Este es tu único registro de ${resource.labelSingular.toLowerCase()}. Edítalo con el botón de la tarjeta cuando cambie tu información — no se crean registros adicionales.`,
    }
  }
  const newLabel = `${resource.genderFeminine ? 'Nueva' : 'Nuevo'} ${resource.labelSingular}`
  return {
    title: resource.label,
    body: `Usa "${newLabel}" para agregar un registro. Desde la tabla puedes editar o eliminar cualquiera existente — los cambios se guardan de inmediato.`,
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
 * Only shown from the `xl` breakpoint up (see Layout.tsx) - on smaller
 * viewports the two off-canvas sidebars (left nav + this one) would fight
 * for the same drawer space.
 */
export const SidebarRight: React.FC<SidebarRightProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState<RightPanelTab>('instructions')
  const location = useLocation()
  const instructions = getPageInstructions(location.pathname)

  return (
    <aside
      className="hidden xl:flex xl:flex-col w-80 flex-shrink-0 glass-panel backdrop-blur-[20px] border-l border-border p-4 gap-4"
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
