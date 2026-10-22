import React, { useEffect, useRef, useState } from 'react'
import type { ComponentPropsWithoutRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ExtraProps } from 'react-markdown'
import { Maximize, ZoomIn, ZoomOut } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'

interface MarkdownProps {
  children: string
  className?: string
}

const MarkdownTable = ({
  children,
  node: _node,
  ...props
}: ComponentPropsWithoutRef<'table'> & ExtraProps) => (
  <div className="markdown-table-scroll">
    <table {...props}>{children}</table>
  </div>
)

/** Just the svg-pan-zoom instance methods MermaidDiagram actually uses -
 * the package's own ambient `export =` types don't cleanly describe its
 * callable default export, so this stands in for it instead of fighting
 * that. */
interface SvgPanZoomInstance {
  zoomIn(): void
  zoomOut(): void
  reset(): void
  resize(): void
  fit(): void
  center(): void
  destroy(): void
}

/** Recursively pulls the plain source text out of a fenced code block's
 * `children` - needed to hand Mermaid its raw diagram source. */
const extractText = (node: React.ReactNode): string => {
  if (typeof node === 'string') return node
  if (typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(extractText).join('')
  if (React.isValidElement<{ children?: React.ReactNode }>(node)) return extractText(node.props.children)
  return ''
}

/** Renders a ```mermaid fenced block as an actual diagram (SVG) instead of
 * text, matching the admin panel's record view. Re-renders on theme change
 * since Mermaid bakes colors into the SVG at render time rather than via
 * CSS custom properties. */
const MermaidDiagram: React.FC<{ code: string }> = ({ code }) => {
  const resolvedTheme = useUIStore(state => state.resolvedTheme)
  const [svg, setSvg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const idRef = useRef(`mermaid-${Math.random().toString(36).slice(2)}`)
  const containerRef = useRef<HTMLDivElement>(null)
  const panZoomRef = useRef<SvgPanZoomInstance | null>(null)

  useEffect(() => {
    let cancelled = false
    // Dynamic import: mermaid pulls in a large diagram-renderer/d3 dependency
    // tree - only pay for it when a page actually has a ```mermaid block,
    // instead of bundling it into everyone's page load.
    import('mermaid').then(({ default: mermaid }) => {
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

  // Wires up pan/drag + zoom on the rendered SVG once it's actually in the
  // DOM - needed for diagrams too big to read at their natural size.
  useEffect(() => {
    if (!svg || !containerRef.current) return
    const svgEl = containerRef.current.querySelector('svg')
    if (!svgEl) return

    let cancelled = false
    let instance: SvgPanZoomInstance | null = null
    let resizeObserver: ResizeObserver | null = null
    const container = containerRef.current
    // svg-pan-zoom's fit()/center() read the SVG's screen CTM, which is
    // only valid once the container has a real (non-zero) layout box -
    // during a resize/reflow burst (e.g. a full-page capture, or a window
    // resize mid-transition) it can observe a momentarily zero-size box and
    // throw "matrix not invertible". That's a transient browser-layout
    // race, not a broken diagram, so swallow it instead of letting it
    // surface as an unhandled rejection.
    const safePanZoomCall = (fn: () => void) => {
      try {
        fn()
      } catch {
        // ignore - see comment above
      }
    }
    import('svg-pan-zoom').then(({ default: svgPanZoom }) => {
      if (cancelled) return
      safePanZoomCall(() => {
        instance = svgPanZoom(svgEl, {
          zoomEnabled: true,
          panEnabled: true,
          controlIconsEnabled: false,
          fit: true,
          center: true,
          minZoom: 0.2,
          maxZoom: 10,
        }) as unknown as SvgPanZoomInstance
      })
      panZoomRef.current = instance
      resizeObserver = new ResizeObserver(() => {
        if (cancelled) return
        safePanZoomCall(() => {
          instance?.resize()
          instance?.fit()
          instance?.center()
        })
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
      <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-lg p-3 mb-3">
        No se pudo renderizar el diagrama Mermaid: {error}
      </div>
    )
  }

  if (!svg) {
    return <p className="text-xs text-text-muted mb-3">Renderizando diagrama...</p>
  }

  return (
    <div className="relative mb-3">
      <div ref={containerRef} className="mermaid-diagram" dangerouslySetInnerHTML={{ __html: svg }} />
      <div className="absolute bottom-2 right-2 flex items-center gap-1">
        <button
          type="button"
          onClick={() => panZoomRef.current?.zoomIn()}
          aria-label="Acercar"
          title="Acercar"
          className="p-1.5 rounded-lg text-text-secondary hover:text-primary bg-bg-glass"
        >
          <ZoomIn size={14} />
        </button>
        <button
          type="button"
          onClick={() => panZoomRef.current?.zoomOut()}
          aria-label="Alejar"
          title="Alejar"
          className="p-1.5 rounded-lg text-text-secondary hover:text-primary bg-bg-glass"
        >
          <ZoomOut size={14} />
        </button>
        <button
          type="button"
          onClick={() => panZoomRef.current?.reset()}
          aria-label="Restablecer vista"
          title="Restablecer vista"
          className="p-1.5 rounded-lg text-text-secondary hover:text-primary bg-bg-glass"
        >
          <Maximize size={14} />
        </button>
      </div>
    </div>
  )
}

/** Only this host may be framed by a ```archify block - the API locks
 * uploading a new file to the `agent` role (see `middleware/auth.py`'s
 * `file_upload` check), but nothing stops this markdown field itself from
 * being hand-edited with an arbitrary URL, so the iframe only ever loads
 * from the one bucket host we actually trust. */
const ARCHIFY_ALLOWED_HOST = 'files.cjhirashi.com'

/** Renders a ```archify fenced block - its body is the public URL of an
 * Archify-generated standalone HTML diagram (uploaded via `POST /files`) -
 * as a sandboxed iframe instead of a plain code block. */
const ArchifyDiagram: React.FC<{ url: string }> = ({ url }) => {
  const trimmed = url.trim()
  let isAllowed = false
  try {
    const parsed = new URL(trimmed)
    isAllowed = parsed.protocol === 'https:' && parsed.hostname === ARCHIFY_ALLOWED_HOST
  } catch {
    isAllowed = false
  }

  if (!isAllowed) {
    return (
      <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-lg p-3 mb-3">
        Diagrama Archify con URL no válida (debe ser https://{ARCHIFY_ALLOWED_HOST}/...): {trimmed}
      </div>
    )
  }

  return (
    <div className="mb-3">
      <iframe
        src={trimmed}
        title="Diagrama interactivo"
        loading="lazy"
        sandbox="allow-scripts allow-same-origin"
        className="archify-diagram"
      />
      <a
        href={trimmed}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-text-secondary hover:text-primary transition mt-1 inline-block"
      >
        Abrir diagrama en pantalla completa ↗
      </a>
    </div>
  )
}

/** ReactMarkdown's `pre` override: a ```mermaid block renders as a diagram
 * (via MermaidDiagram above) and a ```archify block as an embedded
 * interactive diagram (via ArchifyDiagram above), instead of a plain code
 * block. */
const MarkdownPre = ({
  children,
  node: _node,
  ...props
}: ComponentPropsWithoutRef<'pre'> & ExtraProps) => {
  const codeClassName =
    React.isValidElement<{ className?: string }>(children) && typeof children.props.className === 'string'
      ? children.props.className
      : ''
  const language = codeClassName.match(/language-(\w+)/)?.[1] ?? null

  if (language === 'mermaid') {
    return <MermaidDiagram code={extractText(children)} />
  }
  if (language === 'archify') {
    return <ArchifyDiagram url={extractText(children)} />
  }

  return <pre {...props}>{children}</pre>
}

/** Renders admin-authored Markdown text (bio, project narrative, work
 * history, blog posts, ...) the same way the admin panel's own record view
 * does - bold/italic, lists, links, tables, and ```mermaid fenced blocks as
 * actual diagrams. Uses the `.markdown-content` styles in index.css. */
export const Markdown = ({ children, className }: MarkdownProps) => (
  <div className={`markdown-content ${className ?? ''}`}>
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ table: MarkdownTable, pre: MarkdownPre }}>
      {children}
    </ReactMarkdown>
  </div>
)
