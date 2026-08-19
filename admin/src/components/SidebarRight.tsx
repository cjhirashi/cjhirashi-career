import React from 'react'
import { Sparkles } from 'lucide-react'

/**
 * Right-hand panel reserved for the future in-Admin AI assistant (AWS
 * Bedrock, see CLAUDE.md "Agent Bedrock" - only reachable from the Admin
 * Panel, never exposed directly). The backend for that assistant does not
 * exist yet, so this is intentionally a static "coming soon" placeholder
 * with the same glass look as the rest of the chrome - no chat input, no
 * fake interactivity.
 *
 * Only shown from the `xl` breakpoint up: on smaller viewports the two
 * off-canvas sidebars (left nav + this one) would fight for the same
 * drawer space, so we simply hide it rather than complicate the existing
 * mobile drawer mechanics in Sidebar.tsx/Layout.tsx.
 */
export const SidebarRight: React.FC = () => {
  return (
    <aside
      className="hidden xl:flex xl:flex-col w-80 flex-shrink-0 glass-panel backdrop-blur-[20px] border-l border-border p-4"
      aria-label="Asistente IA"
    >
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
          El asistente impulsado por IA para ayudarte a gestionar tu carrera todavía no está disponible en este panel.
        </p>
      </div>
    </aside>
  )
}
