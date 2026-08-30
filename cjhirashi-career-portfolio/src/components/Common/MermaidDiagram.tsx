import React, { useEffect, useRef, useState } from 'react'
import { Maximize, ZoomIn, ZoomOut } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'

/** Just the svg-pan-zoom instance methods this component actually uses - the
 * package's ambient `export =` types don't cleanly describe its callable
 * default export, so this stands in for it instead of fighting that. */
interface SvgPanZoomInstance {
  zoomIn(): void
  zoomOut(): void
  reset(): void
  resize(): void
  fit(): void
  center(): void
  destroy(): void
}

/**
 * Renders a ```mermaid fenced block as an actual diagram (SVG) instead of
 * text - mirrors the admin panel's CareerResourceView pipeline so a project
 * "Arquitectura" narrative or a blog post reads the same on the public
 * portal as it does in the admin record view.
 *
 * Re-renders on theme change because Mermaid bakes colors into the SVG at
 * render time rather than via CSS custom properties. `mermaid` and
 * `svg-pan-zoom` are dynamically imported: both pull in a large
 * d3/diagram-renderer dependency tree, so only a page that actually has a
 * ```mermaid block pays for them instead of every visitor.
 */
export const MermaidDiagram: React.FC<{ code: string }> = ({ code }) => {
  const resolvedTheme = useUIStore((state) => state.resolvedTheme)
  const [svg, setSvg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const idRef = useRef(`mermaid-${Math.random().toString(36).slice(2)}`)
  const containerRef = useRef<HTMLDivElement>(null)
  const panZoomRef = useRef<SvgPanZoomInstance | null>(null)

  useEffect(() => {
    let cancelled = false
    import('mermaid')
      .then(({ default: mermaid }) => {
        if (cancelled) return
        mermaid.initialize({
          startOnLoad: false,
          theme: resolvedTheme === 'dark' ? 'dark' : 'default',
          securityLevel: 'strict',
        })
        return mermaid.render(idRef.current, code)
      })
      .then((result) => {
        if (!cancelled && result) {
          setSvg(result.svg)
          setError(null)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err))
      })
    return () => {
      cancelled = true
    }
  }, [code, resolvedTheme])

  // Wires up pan/drag + zoom on the rendered SVG once it's in the DOM - for
  // diagrams too big to read at their natural size, so a large diagram gives
  // something to pan/zoom within instead of just growing the page.
  useEffect(() => {
    if (!svg || !containerRef.current) return
    const svgEl = containerRef.current.querySelector('svg')
    if (!svgEl) return

    let cancelled = false
    let instance: SvgPanZoomInstance | null = null
    let resizeObserver: ResizeObserver | null = null
    const container = containerRef.current
    import('svg-pan-zoom').then(({ default: svgPanZoom }) => {
      if (cancelled) return
      instance = svgPanZoom(svgEl, {
        zoomEnabled: true,
        panEnabled: true,
        controlIconsEnabled: false,
        fit: true,
        center: true,
        minZoom: 0.2,
        maxZoom: 10,
      }) as unknown as SvgPanZoomInstance
      panZoomRef.current = instance
      // The container's size can keep settling past the SVG landing in the
      // DOM (layout, a window resize) - re-fit on every real size change
      // instead of a one-off, which also fires once immediately on observe().
      resizeObserver = new ResizeObserver(() => {
        if (cancelled) return
        instance?.resize()
        instance?.fit()
        instance?.center()
      })
      resizeObserver.observe(container)
    })

    return () => {
      cancelled = true
      resizeObserver?.disconnect()
      instance?.destroy()
      panZoomRef.current = null
    }
  }, [svg])

  if (error) {
    return (
      <div className="mermaid-diagram-error">
        No se pudo renderizar el diagrama Mermaid: {error}
      </div>
    )
  }

  if (!svg) {
    return <p className="mermaid-diagram-loading">Renderizando diagrama...</p>
  }

  return (
    <div className="mermaid-diagram-wrap">
      <div
        ref={containerRef}
        className="mermaid-diagram"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
      <div className="mermaid-diagram-controls">
        <button
          type="button"
          onClick={() => panZoomRef.current?.zoomIn()}
          aria-label="Acercar"
          title="Acercar"
          className="mermaid-zoom-btn"
        >
          <ZoomIn size={14} />
        </button>
        <button
          type="button"
          onClick={() => panZoomRef.current?.zoomOut()}
          aria-label="Alejar"
          title="Alejar"
          className="mermaid-zoom-btn"
        >
          <ZoomOut size={14} />
        </button>
        <button
          type="button"
          onClick={() => panZoomRef.current?.reset()}
          aria-label="Restablecer vista"
          title="Restablecer vista"
          className="mermaid-zoom-btn"
        >
          <Maximize size={14} />
        </button>
      </div>
    </div>
  )
}
