import React, { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { MessageCircle, BookOpen, X } from 'lucide-react'
import { CAREER_RESOURCES } from '@/config/careerResources'
import { ChatWindow } from '@/components/bedrock/ChatWindow'
import { MarkdownTable } from '@/components/MarkdownTable'
import { useChatPageContext } from '@/hooks/useChatPageContext'
import { useAdminSections } from '@/hooks/useAdminSections'
import { matchAdminSection } from '@/types/adminSections'

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
  '/job-discovery': {
    title: 'Descubrir vacantes',
    body: 'Pide al agente en el chat que busque (Indeed, Get on Board, Remotive, RemoteOK). Te devolverá refs L1, L2… Autoriza cuáles guardar (“guarda L1 y L3” o “todas menos L2”) y las crea como vacantes pending_review para seguimiento. LinkedIn solo abre la búsqueda oficial: pega cada jobs/view para importar. Marcar y guardar en esta pantalla también autoriza.',
  },
  '/agent/instructions': {
    title: 'Instrucciones',
    body: 'Suffix por especialista, sumado al prompt base global (Settings → Prompts Globales). Los cambios aplican en el siguiente mensaje.',
  },
  '/settings/agent-prompts': {
    title: 'Prompts Globales',
    body: 'System prompt base y reglas globales (grounding/no-alucinar + asignación de metodologías) que aplican a TODOS los agentes. Los cambios aplican en el siguiente mensaje.',
  },
  '/settings/agents': {
    title: 'Catálogo de Agentes',
    body: 'Tabla de agentes del sistema. Ábrelos para verlos o editar overrides (prompt, metodologías, secciones, delegación y memoria). No se pueden crear ni eliminar: están definidos en código.',
  },
  '/settings/sections': {
    title: 'Secciones del Admin',
    body: 'Registro de pantallas: tipo tabla/funcional/métricas/bucket, agente con dominio, vistas e instrucciones de este sidebar.',
  },
  '/settings/error-reports': {
    title: 'Reportes de Falla',
    body: 'Bitácora de errores capturados automáticamente en todo el sistema (API, agentes, schedulers, SPA). Un reporte "pendiente" aún no se revisa; ábrelo para ver el traceback y el contexto. Márcalo como "resuelto" (con una nota) sólo cuando el problema ya se corrigió en el código; "reabrir" lo devuelve a pendiente. Errores repetidos con la misma huella no crean filas nuevas: suman ocurrencias.',
  },
  '/files': {
    title: 'Archivos',
    body: 'Sube cualquier archivo (imágenes, documentos) y obtén un link público para referenciarlo donde quieras, por ejemplo dentro de un campo Markdown con ![descripción](link). "Copiar link" copia la URL pública; "Eliminar" borra el archivo del bucket de forma permanente.',
  },
  '/tasks': {
    title: 'Tareas',
    body: 'Tablero de trabajo: lista, kanban, calendario y Gantt. Una tarea puede ser tuya (manual) o de un agente del catálogo. Si asignas un agente y una fecha/hora, el scheduler de la API la ejecuta a esa hora aunque no estés en sesión. "Ejecutar ahora" dispara al agente de inmediato.',
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
  if (pathname.startsWith('/settings/agents')) return STATIC_INSTRUCTIONS['/settings/agents']
  if (pathname.startsWith('/settings/sections')) return STATIC_INSTRUCTIONS['/settings/sections']
  if (pathname.startsWith('/agent/catalog')) return STATIC_INSTRUCTIONS['/settings/agents']

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
 * - "Chat": Agent Bedrock, the in-Admin AI assistant (see CLAUDE.md "Agent
 *   Bedrock" and `components/bedrock/ChatWindow.tsx`) - full read/write
 *   access to the career-domain tables, backed by Harness local (Converse API).
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
  const { data: sections } = useAdminSections()
  const matched = matchAdminSection(location.pathname, sections ?? [])
  const instructions = matched
    ? { title: matched.view.sidebar_title, body: matched.view.sidebar_body }
    : getPageInstructions(location.pathname)
  const pageContext = useChatPageContext()

  // feature 001: el chat contextual sólo si la sección tiene un agente L2
  // asignado; las instrucciones sólo si la vista tiene texto. Rutas que no
  // hacen match con ninguna sección conservan el comportamiento anterior.
  const hasChat = matched ? matched.section.agent_profile_id != null : true
  const hasInstructions = matched ? Boolean(instructions.body?.trim()) : true
  const effectiveTab: RightPanelTab =
    activeTab === 'chat' && hasChat
      ? 'chat'
      : activeTab === 'instructions' && hasInstructions
        ? 'instructions'
        : hasInstructions
          ? 'instructions'
          : 'chat'

  if (!hasChat && !hasInstructions) return null

  const showTabSwitch = hasChat && hasInstructions

  return (
    <aside
      className={clsx(
        'glass-panel backdrop-blur-[20px] flex flex-col border-l border-border p-4 gap-4 min-w-0',
        'fixed inset-0 z-50 w-full',
        'md:inset-y-0 md:left-auto md:right-0 md:w-96 md:max-w-[90vw] md:rounded-l-2xl',
        'xl:static xl:z-auto xl:w-80 xl:h-auto xl:flex-shrink-0 xl:rounded-none'
      )}
      aria-label="Panel de asistencia"
    >
      {/* Header: tab switch (chat / instrucciones) + hide button */}
      <div className="flex items-center justify-between gap-2 flex-shrink-0">
        {showTabSwitch ? (
          <div className="theme-pill" role="group" aria-label="Modo del panel">
            <button
              type="button"
              className="theme-pill-btn"
              aria-pressed={effectiveTab === 'chat'}
              onClick={() => setActiveTab('chat')}
              title="Chat del asistente"
            >
              <MessageCircle size={15} aria-hidden="true" />
            </button>
            <button
              type="button"
              className="theme-pill-btn"
              aria-pressed={effectiveTab === 'instructions'}
              onClick={() => setActiveTab('instructions')}
              title="Instrucciones de la pantalla"
            >
              <BookOpen size={15} aria-hidden="true" />
            </button>
            <span
              className="theme-pill-indicator"
              data-pos={effectiveTab === 'chat' ? '0' : '1'}
              aria-hidden="true"
            />
          </div>
        ) : (
          <span className="flex items-center gap-2 text-text text-sm font-semibold">
            {effectiveTab === 'chat' ? (
              <MessageCircle size={15} aria-hidden="true" />
            ) : (
              <BookOpen size={15} aria-hidden="true" />
            )}
            {effectiveTab === 'chat' ? 'Chat del asistente' : 'Instrucciones'}
          </span>
        )}

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
      {effectiveTab === 'chat' ? (
        <ChatWindow chatSurface="contextual" pageContext={pageContext} />
      ) : (
        <div className="card p-5 flex-1 overflow-y-auto">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen size={16} className="text-primary flex-shrink-0" aria-hidden="true" />
            <h2 className="font-semibold text-text text-sm">{instructions.title}</h2>
          </div>
          <div className="markdown-body text-text-secondary text-sm leading-relaxed">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ table: MarkdownTable }}>
              {instructions.body}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </aside>
  )
}
