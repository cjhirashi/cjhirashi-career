import React from 'react'

interface ErrorBoundaryProps {
  children: React.ReactNode
}

interface ErrorBoundaryState {
  error: Error | null
}

/** Catches any render-time crash in the tree below it (e.g. an API response
 * with an unexpected shape reaching a `.map()`) so it shows a recoverable
 * screen instead of leaving the whole app blank - previously a single bad
 * response anywhere could unmount the entire React tree, which read to the
 * user as "no carga bien, hay que refrescar" with no visible error at all. */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    console.error('ErrorBoundary caught a render error:', error, info.componentStack)
  }

  render(): React.ReactNode {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6">
          <div className="card max-w-md w-full p-6 text-center space-y-4">
            <h1 className="text-lg font-semibold text-text">Algo salió mal</h1>
            <p className="text-text-secondary text-sm">
              Hubo un error inesperado al mostrar esta pantalla. Puedes intentar de nuevo o recargar la página.
            </p>
            <div className="flex items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => this.setState({ error: null })}
                className="btn-primary"
              >
                Reintentar
              </button>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="px-4 py-2 rounded-xl text-sm text-text-secondary hover:bg-glass hover:text-text transition-colors"
              >
                Recargar página
              </button>
            </div>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
