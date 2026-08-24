import React, { useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  ArrowUpDown,
  Check,
  ChevronLeft,
  ChevronRight,
  Copy,
  Eye,
  EyeOff,
  FileDown,
  Maximize,
  Pencil,
  Plus,
  Search,
  Trash2,
  X,
  ZoomIn,
  ZoomOut,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize'
import rehypeHighlight from 'rehype-highlight'
import { useThemeStore } from '@/stores/themeStore'
import { FieldConfig, FieldType, ResourceConfig } from '@/config/careerResources'
import { useCareerList, useCareerMutations, useCareerCount } from '@/hooks/useCareerResource'
import { usePdfTemplateList, usePdfTemplateMutations, usePdfTemplateCount } from '@/hooks/usePdfTemplateResource'
import {
  usePdfTemplateStyleList,
  usePdfTemplateStyleMutations,
  usePdfTemplateStyleCount,
} from '@/hooks/usePdfTemplateStyleResource'
import { careerApi } from '@/api/career'
import { pdfTemplatesApi } from '@/api/pdfTemplates'
import { CareerEntity } from '@/types/career'
import { getBlobErrorMessage, getErrorMessage, assertPdfBlob } from '@/utils/errors'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ResourceForm } from './ResourceForm'
import { useFkLabel } from '@/hooks/useFkOptions'
import { GitHubReposPanel } from './GitHubReposPanel'
import { formatCellValue } from './careerFieldUtils'
import { formatDate, formatDateTime } from '@/utils/formatters'
import { ThemedSelect } from '@/components/ThemedSelect'

export interface ParentFilter {
  field: string
  value: number
}

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

/**
 * Sanitize schema for raw HTML inside Markdown fields (centering an image,
 * flex columns, etc. - things Markdown syntax alone can't express). Starts
 * from rehype-sanitize's default (already blocks <script>, event handler
 * attributes like onclick, and javascript: URLs) and only adds `style` as
 * an allowed attribute on every tag, since that's what layout tricks need.
 */
const markdownSanitizeSchema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    '*': [...(defaultSchema.attributes?.['*'] ?? []), 'style'],
    // rehype-highlight tags code/span with `className="hljs-*"` for syntax
    // coloring - keep those explicit so a sanitize-schema change elsewhere
    // can't silently strip them.
    code: [...(defaultSchema.attributes?.code ?? []), 'className'],
    span: [...(defaultSchema.attributes?.span ?? []), 'className'],
  },
}

/** Recursively pulls the plain source text out of a fenced code block's
 * `children` (a <code> element whose own children are either a single
 * string or, once rehype-highlight has tokenized a recognized language,
 * a tree of <span>s) - needed to hand Mermaid its raw diagram source,
 * unaffected by whatever syntax-highlighting markup wrapped around it. */
const extractText = (node: React.ReactNode): string => {
  if (typeof node === 'string') return node
  if (typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(extractText).join('')
  if (React.isValidElement<{ children?: React.ReactNode }>(node)) return extractText(node.props.children)
  return ''
}

/** Renders a ```mermaid fenced block as an actual diagram (SVG) instead of
 * text. Re-renders on theme change since Mermaid bakes colors into the SVG
 * at render time rather than via CSS custom properties. */
const MermaidDiagram: React.FC<{ code: string }> = ({ code }) => {
  const resolvedTheme = useThemeStore((state) => state.resolvedTheme)
  const [svg, setSvg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const idRef = useRef(`mermaid-${Math.random().toString(36).slice(2)}`)
  const containerRef = useRef<HTMLDivElement>(null)
  const panZoomRef = useRef<SvgPanZoomInstance | null>(null)

  useEffect(() => {
    let cancelled = false
    // Dynamic import: mermaid pulls in a large diagram-renderer/d3/katex
    // dependency tree - only pay for it when a page actually has a
    // ```mermaid block, instead of bundling it into everyone's page load.
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
  // DOM - needed for diagrams too big to read at their natural size instead
  // of just growing the page. Dynamically imported for the same reason as
  // mermaid itself: only pages with a diagram pay for it.
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
      // The container's size can keep settling well past the SVG landing in
      // the DOM (card hover transforms, the record view's own layout, a
      // desktop/tablet window resize) - a one-off re-fit after a single
      // frame only fixed the initial-mount race and still left the diagram
      // fit to a stale size afterwards. Re-fit on every real size change
      // instead, which also fires once immediately on observe().
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
          className="p-1.5 rounded-lg text-text-secondary hover:text-text bg-glass"
        >
          <ZoomIn size={14} />
        </button>
        <button
          type="button"
          onClick={() => panZoomRef.current?.zoomOut()}
          aria-label="Alejar"
          title="Alejar"
          className="p-1.5 rounded-lg text-text-secondary hover:text-text bg-glass"
        >
          <ZoomOut size={14} />
        </button>
        <button
          type="button"
          onClick={() => panZoomRef.current?.reset()}
          aria-label="Restablecer vista"
          title="Restablecer vista"
          className="p-1.5 rounded-lg text-text-secondary hover:text-text bg-glass"
        >
          <Maximize size={14} />
        </button>
      </div>
    </div>
  )
}

/** Wraps a fenced code block's `<pre>` with a language label (from the
 * fence's info string, e.g. ` ```js `) and a copy-to-clipboard button shown
 * on hover. Used as ReactMarkdown's `pre` component override, so `children`
 * is already the syntax-highlighted `<code className="language-js ...">`
 * from rehype-highlight - the label just reads that class back out instead
 * of re-deriving it. A ```mermaid block renders as a diagram instead, via
 * MermaidDiagram above - no point syntax-highlighting or offering to copy
 * a "language" that isn't one. */
const CodeBlockPre: React.FC<React.HTMLAttributes<HTMLPreElement>> = ({ children, ...props }) => {
  const [copied, setCopied] = useState(false)
  const preRef = useRef<HTMLPreElement>(null)

  const codeClassName =
    React.isValidElement<{ className?: string }>(children) && typeof children.props.className === 'string'
      ? children.props.className
      : ''
  const language = codeClassName.match(/language-(\w+)/)?.[1] ?? null

  if (language === 'mermaid') {
    return <MermaidDiagram code={extractText(children)} />
  }

  const handleCopy = () => {
    const text = preRef.current?.textContent ?? ''
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div className="relative">
      <pre ref={preRef} {...props} className={language ? 'has-code-lang' : props.className}>
        {children}
      </pre>
      {language && (
        <span className="absolute top-2 left-3 text-[10px] font-mono uppercase tracking-wide text-text-muted select-none">
          {language}
        </span>
      )}
      <button
        type="button"
        onClick={handleCopy}
        aria-label={copied ? 'Copiado' : 'Copiar código'}
        title={copied ? 'Copiado' : 'Copiar código'}
        className="absolute top-2 right-2 p-1.5 rounded-lg text-text-secondary hover:text-text bg-glass"
      >
        {copied ? <Check size={14} /> : <Copy size={14} />}
      </button>
    </div>
  )
}

interface CareerResourceViewProps {
  config: ResourceConfig
  pageSize?: number
  /** When `pdf-templates`, uses `/pdf-templates` CRUD instead of `/career/{key}`. */
  apiMode?: 'career' | 'pdf-templates' | 'pdf-template-styles'
  /** When set, the view fetches up to 100 rows and filters client-side by `field === value` (used for drill-down/nested resources; the backend has no per-field filter query param). */
  parentFilter?: ParentFilter
  /** Fixed values merged into every create/edit payload, hidden from the form (typically the parent FK for a nested resource). */
  presetValues?: Record<string, unknown>
  title?: string
  hideTitle?: boolean
  /** Extra button rendered per row, before Edit/Delete (e.g. "Ver detalle" for drill-down). */
  renderExtraRowAction?: (item: CareerEntity) => React.ReactNode
  /** Extra class applied to a row to highlight the current drill-down selection. */
  rowClassName?: (item: CareerEntity) => string
}

/** What the card is currently showing, in place of a popup modal - the card
 * grows/shrinks with whichever content is active instead of being capped to
 * a fixed height, and the page itself scrolls if needed. */
type ViewState = 'list' | 'view' | 'edit' | 'create'

const Badge: React.FC<{ color: 'cyan' | 'slate' | 'success' | 'error' | 'warning'; children: React.ReactNode }> = ({
  color,
  children,
}) => <span className={`badge badge-${color}`}>{children}</span>

/** Resolves and displays a FK id as "id — Name". Separate component so the
 * hook call is always at the top level (rules of hooks). */
const FkFieldValue: React.FC<{
  id: string
  fkResource: string
  fkLabelField?: string | string[]
  fkApi?: 'career' | 'pdf-template-styles'
}> = ({ id, fkResource, fkLabelField, fkApi = 'career' }) => {
  const label = useFkLabel(fkResource, id, fkLabelField, fkApi)
  return <span className="font-mono text-xs">{label}</span>
}

/** Read-only rendering of a single field's value, matching its `FieldType` -
 * no truncation (unlike the table's `formatCellValue`), since this is the
 * one place meant to show the complete content. */
const FieldValue: React.FC<{ value: unknown; type: FieldType; field?: FieldConfig }> = ({ value, type, field }) => {
  if (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) {
    return <span className="text-text-muted">—</span>
  }

  if (type === 'fk-select' && field?.fkResource) {
    return (
      <FkFieldValue
        id={String(value)}
        fkResource={field.fkResource}
        fkLabelField={field.fkLabelField}
        fkApi={field.fkApi}
      />
    )
  }

  switch (type) {
    case 'code':
      return (
        <pre className="text-xs bg-glass rounded-lg p-3 overflow-x-auto whitespace-pre-wrap break-words font-mono">
          {String(value)}
        </pre>
      )
    case 'boolean':
      return <>{value ? 'Sí' : 'No'}</>
    case 'date':
      return <>{typeof value === 'string' ? formatDate(value) : String(value)}</>
    case 'datetime':
      return <>{typeof value === 'string' ? formatDateTime(value) : String(value)}</>
    case 'json':
      return (
        <pre className="text-xs bg-glass rounded-lg p-3 overflow-x-auto whitespace-pre-wrap break-words">
          {JSON.stringify(value, null, 2)}
        </pre>
      )
    case 'textarea':
      // Long free-text fields (bio, narratives, etc.) are authored as
      // Markdown in the form's plain textarea - rendered here instead of
      // guessing paragraph breaks from raw line breaks, so real Markdown
      // (blank line between paragraphs, **bold**, lists, ...) shows up
      // properly, and plain prose with no Markdown syntax still renders
      // fine as ordinary paragraphs.
      return (
        <div className="markdown-body">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw, [rehypeSanitize, markdownSanitizeSchema], rehypeHighlight]}
            components={{ pre: CodeBlockPre }}
          >
            {String(value)}
          </ReactMarkdown>
        </div>
      )
    default:
      if (Array.isArray(value)) {
        return (
          <ul className="list-disc list-inside space-y-0.5">
            {value.map((v, idx) => (
              <li key={idx}>{String(v)}</li>
            ))}
          </ul>
        )
      }
      if (typeof value === 'object') {
        return (
          <pre className="text-xs bg-glass rounded-lg p-3 overflow-x-auto whitespace-pre-wrap break-words">
            {JSON.stringify(value, null, 2)}
          </pre>
        )
      }
      return <span className="whitespace-pre-wrap break-words">{String(value)}</span>
  }
}

/** Automatic "Metadatos" section for whichever of id/created_at/updated_at
 * the record actually carries (not every career table has all three, see
 * types/career.ts) - its own component so PDF-exportable resources can
 * place it after the print preview instead of right after "Información"
 * (see the `showMeta` prop on `RecordView` below and where CareerResourceView
 * renders this separately for that case). */
const RecordMetadata: React.FC<{ item: CareerEntity }> = ({ item }) => {
  const metaEntries = useMemo(() => {
    const entries: { label: string; value: string }[] = []
    if (item.id != null) entries.push({ label: 'ID', value: String(item.id) })
    if (typeof item.created_at === 'string') entries.push({ label: 'Creado', value: formatDateTime(item.created_at) })
    if (typeof item.updated_at === 'string')
      entries.push({ label: 'Última actualización', value: formatDateTime(item.updated_at) })
    return entries
  }, [item])

  if (metaEntries.length === 0) return null

  return (
    <div className="pt-4 border-t border-border">
      <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">Metadatos</h3>
      <dl className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {metaEntries.map((entry) => (
          <div key={entry.label}>
            <dt className="text-xs text-text-secondary mb-1">{entry.label}</dt>
            <dd className="text-sm text-text">{entry.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

/** Every field the record has, in full - not just the table's summary
 * columns - under an "Información" heading, plus (by default) the
 * "Metadatos" section right after it. Pass `showMeta={false}` to suppress
 * that and render `<RecordMetadata>` separately instead - used for
 * PDF-exportable resources, which place it after the print preview. */
const RecordView: React.FC<{
  item: CareerEntity
  fields: FieldConfig[]
  resourceKey?: string
  showMeta?: boolean
}> = ({ item, fields, resourceKey, showMeta = true }) => {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">Información</h3>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {fields.map((field) => (
            <div key={field.name} className={field.fullWidth ? 'md:col-span-2' : ''}>
              <dt className="text-xs text-text-secondary mb-1">{field.label}</dt>
              <dd className="text-sm text-text">
                <FieldValue value={item[field.name]} type={field.type} field={field} />
              </dd>
            </div>
          ))}
        </dl>
      </div>

      {showMeta && <RecordMetadata item={item} />}

      {resourceKey === 'github-profile' && <GitHubReposPanel />}
    </div>
  )
}

const ProjectCard: React.FC<{
  item: CareerEntity
  config: ResourceConfig
  onView: () => void
  onEdit: () => void
  onDelete: () => void
}> = ({ item, config, onView, onEdit, onDelete }) => {
  const [headingCol, ...restCols] = config.columns
  const summary =
    typeof item.card_summary === 'string'
      ? item.card_summary
      : typeof item.detailed_summary === 'string'
        ? item.detailed_summary
        : null
  const techStack = Array.isArray(item.tech_stack) ? (item.tech_stack as unknown[]) : null

  return (
    <div
      className="card p-5 flex flex-col gap-3 cursor-pointer"
      onClick={onView}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onView()
        }
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-text text-lg">{String(item[headingCol.key] ?? '—')}</h3>
        <div className="flex gap-1 flex-shrink-0">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onEdit()
            }}
            aria-label="Editar"
            className="p-1.5 rounded text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-cyan-600"
          >
            <Pencil size={15} />
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
            aria-label="Eliminar"
            className="p-1.5 rounded text-text-secondary hover:bg-red-50 dark:hover:bg-red-950/40 hover:text-red-600"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {restCols.map((col) => {
          const val = item[col.key]
          if (val === null || val === undefined || val === '') return null
          if (col.format === 'boolean') return val ? (
            <Badge key={col.key} color="cyan">{col.label}</Badge>
          ) : null
          if (col.format === 'badge')
            return (
              <Badge key={col.key} color={col.badgeColor ? col.badgeColor(val) : 'slate'}>
                {String(val)}
              </Badge>
            )
          return (
            <Badge key={col.key} color="slate">
              {col.label}: {formatCellValue(val, col.format)}
            </Badge>
          )
        })}
      </div>

      {summary && <p className="text-text-secondary text-sm line-clamp-3">{summary}</p>}

      {techStack && techStack.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {techStack.slice(0, 8).map((t, idx) => (
            <span
              key={idx}
              className="text-xs px-2 py-0.5 rounded bg-cyan-50 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300"
            >
              {String(t)}
            </span>
          ))}
        </div>
      )}

      {(typeof item.github_url === 'string' || typeof item.demo_url === 'string') && (
        <div className="flex gap-3 text-xs pt-1">
          {typeof item.github_url === 'string' && item.github_url && (
            <a href={item.github_url} target="_blank" rel="noreferrer" className="text-cyan-600 dark:text-cyan-400 hover:underline" onClick={(e) => e.stopPropagation()}>
              GitHub
            </a>
          )}
          {typeof item.demo_url === 'string' && item.demo_url && (
            <a href={item.demo_url} target="_blank" rel="noreferrer" className="text-cyan-600 dark:text-cyan-400 hover:underline" onClick={(e) => e.stopPropagation()}>
              Demo
            </a>
          )}
        </div>
      )}
    </div>
  )
}

export const CareerResourceView: React.FC<CareerResourceViewProps> = ({
  config,
  pageSize = 20,
  apiMode = 'career',
  parentFilter,
  presetValues,
  title,
  hideTitle,
  renderExtraRowAction,
  rowClassName,
}) => {
  const usesPdfTemplatesApi = apiMode === 'pdf-templates'
  const usesPdfTemplateStylesApi = apiMode === 'pdf-template-styles'
  const usesExternalPdfApi = usesPdfTemplatesApi || usesPdfTemplateStylesApi
  const isSingleton = config.mode === 'singleton'
  const isNested = !!parentFilter
  // Search/sort only apply to a resource's own top-level list - a nested
  // sub-list (e.g. applications shown inside a vacancy) is already a small,
  // pre-filtered slice, and a singleton has no list to sort/search at all.
  const supportsListControls = !isSingleton && !isNested
  const [skip, setSkip] = useState(0)
  const limit = isNested ? 100 : isSingleton ? 1 : pageSize

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const [sortBy, setSortBy] = useState<string | undefined>(undefined)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const toggleSort = (key: string) => {
    setSkip(0)
    setSortBy((current) => {
      if (current !== key) {
        setSortDir('asc')
        return key
      }
      setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'))
      return key
    })
  }

  // Any change to search/sort invalidates the current page offset.
  useEffect(() => {
    setSkip(0)
  }, [search, sortBy, sortDir])

  const listParams = {
    skip: isNested || isSingleton ? 0 : skip,
    limit,
    sortBy: supportsListControls ? sortBy : undefined,
    sortDir: supportsListControls ? sortDir : undefined,
    search: supportsListControls ? search || undefined : undefined,
  }

  const careerListQuery = useCareerList<CareerEntity>(config.key, listParams, !usesExternalPdfApi)
  const pdfListQuery = usePdfTemplateList(listParams, usesPdfTemplatesApi)
  const pdfStyleListQuery = usePdfTemplateStyleList(listParams, usesPdfTemplateStylesApi)
  const { data, isLoading, isError, error, refetch } = usesPdfTemplateStylesApi
    ? pdfStyleListQuery
    : usesPdfTemplatesApi
      ? pdfListQuery
      : careerListQuery

  const careerMutations = useCareerMutations<CareerEntity>(config.key)
  const pdfMutations = usePdfTemplateMutations()
  const pdfStyleMutations = usePdfTemplateStyleMutations()
  const { createMutation, updateMutation, deleteMutation } = usesPdfTemplateStylesApi
    ? pdfStyleMutations
    : usesPdfTemplatesApi
      ? pdfMutations
      : careerMutations

  const careerCountQuery = useCareerCount(config.key, !isSingleton && !isNested && !usesExternalPdfApi)
  const pdfCountQuery = usePdfTemplateCount(!isSingleton && !isNested && usesPdfTemplatesApi)
  const pdfStyleCountQuery = usePdfTemplateStyleCount(!isSingleton && !isNested && usesPdfTemplateStylesApi)
  const { data: totalCount } = usesPdfTemplateStylesApi
    ? pdfStyleCountQuery
    : usesPdfTemplatesApi
      ? pdfCountQuery
      : careerCountQuery

  const items = useMemo(() => {
    if (!data) return []
    if (isNested && parentFilter) {
      return data.filter((item) => item[parentFilter.field] === parentFilter.value)
    }
    return data
  }, [data, isNested, parentFilter])

  // Table / view / edit / create all render in place of each other, inside
  // the same card - no popup. The card has no max-height anywhere in this
  // component, so it always grows to fit whichever of these is active and
  // the page (see Layout.tsx's `<main>`) scrolls if it doesn't fit the
  // viewport, instead of a cramped inner scrollbox.
  const [viewState, setViewState] = useState<ViewState>('list')
  const [activeItem, setActiveItem] = useState<CareerEntity | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  // Singleton mode (e.g. `identity`) has no table to come back to - it's
  // just "showing the one record" vs "editing it", not the 4-way
  // list/view/edit/create state the rest of this component uses.
  const [isEditingSingleton, setIsEditingSingleton] = useState(false)

  // PDF-exportable resources only (`config.pdfExportField` set, see
  // careerResources.ts) - "Generar PDF" (download) and the auto-loading
  // print preview below. Scoped to the single record shown in the detail
  // view, so plain component state is enough (no per-row tracking needed).
  const isPdfExportable = Boolean(config.pdfExportField || config.pdfPreviewSource === 'template-render')
  const recordViewFields = useMemo(() => {
    if (!isPdfExportable) return config.fields
    const hidden = new Set(
      config.pdfPreviewHiddenFields ?? (config.pdfExportField ? [config.pdfExportField] : [])
    )
    return config.fields.filter((field) => !hidden.has(field.name))
  }, [config.fields, config.pdfExportField, config.pdfPreviewHiddenFields, isPdfExportable])
  const [pdfDownloading, setPdfDownloading] = useState(false)
  const [pdfError, setPdfError] = useState<string | null>(null)

  // Print preview: renders the *actual* generated PDF (same endpoint as
  // "Generar PDF", just embedded instead of downloaded) in an <iframe> -
  // guarantees the preview is pixel-identical to the real PDF, since it IS
  // the real PDF, rather than a second hand-maintained approximation of
  // WeasyPrint's CSS living in this component too. Loads automatically when
  // opening a PDF-exportable record's detail view (replacing the raw
  // `pdfExportField` text there - see the render below), `pdfPreviewVisible`
  // is just a show/hide toggle over whatever's already been fetched, so
  // toggling it off and back on doesn't re-trigger WeasyPrint.
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null)
  const [pdfPreviewLoading, setPdfPreviewLoading] = useState(false)
  const [pdfPreviewVisible, setPdfPreviewVisible] = useState(true)

  const closePdfPreview = () => {
    setPdfPreviewUrl((current) => {
      if (current) URL.revokeObjectURL(current)
      return null
    })
    setPdfPreviewVisible(true)
  }

  // Revoke on unmount too, not just on explicit close - otherwise
  // navigating away (or a hot reload in dev) leaks the blob URL.
  useEffect(() => () => closePdfPreview(), [])

  const fetchPdfPreview = async (item: CareerEntity) => {
    setPdfError(null)
    setPdfPreviewLoading(true)
    try {
      let blob: Blob
      if (config.pdfPreviewSource === 'template-render') {
        blob = await pdfTemplatesApi.render(String(item.id), {
          title: 'Vista previa',
          content: 'Contenido de ejemplo para la plantilla PDF.',
        })
      } else {
        const result = await careerApi.generateResourcePdf(config.key, item.id)
        blob = result.blob
      }
      await assertPdfBlob(blob)
      setPdfPreviewUrl(URL.createObjectURL(blob))
    } catch (err) {
      closePdfPreview()
      setPdfError(await getBlobErrorMessage(err))
    } finally {
      setPdfPreviewLoading(false)
    }
  }

  const backToList = () => {
    setViewState('list')
    setActiveItem(null)
    setFormError(null)
    setPdfError(null)
    closePdfPreview()
  }

  const openView = (item: CareerEntity) => {
    setActiveItem(item)
    setFormError(null)
    setPdfError(null)
    closePdfPreview()
    setViewState('view')
    if (isPdfExportable) fetchPdfPreview(item)
  }

  const openCreate = () => {
    setActiveItem(null)
    setFormError(null)
    setViewState('create')
  }

  const openEdit = (item: CareerEntity) => {
    setActiveItem(item)
    setFormError(null)
    closePdfPreview()
    setViewState('edit')
  }

  const cancelForm = () => {
    if (activeItem) {
      setViewState('view')
      setFormError(null)
    } else {
      backToList()
    }
  }

  const handleDelete = (item: CareerEntity) => {
    const demonstrative = config.genderFeminine ? 'esta' : 'este'
    if (
      !window.confirm(`¿Eliminar ${demonstrative} ${config.labelSingular.toLowerCase()}? Esta acción no se puede deshacer.`)
    ) {
      return
    }
    deleteMutation.mutate(item.id, {
      onSuccess: () => {
        if (activeItem?.id === item.id) backToList()
      },
    })
  }

  /** PDF-exportable resources only: POST /career/{key}/{id}/pdf, then force
   * a "Save As" download of the returned PDF blob - same
   * fetch-blob/createObjectURL/synthetic-`<a>` pattern as
   * `filesApi.downloadBlob` (see FilesPage's handleDownload). Filename
   * comes from the response's `Content-Disposition` header when the
   * backend sends one, otherwise falls back to `${title}.pdf`. */
  const handleGeneratePdf = async (item: CareerEntity) => {
    setPdfError(null)
    setPdfDownloading(true)
    try {
      let blob: Blob
      let filename: string | null = null
      if (config.pdfPreviewSource === 'template-render') {
        blob = await pdfTemplatesApi.render(String(item.id), {
          title: 'Vista previa',
          content: 'Contenido de ejemplo para la plantilla PDF.',
        })
        filename = `${String(item.title ?? config.labelSingular)}.pdf`
      } else {
        const result = await careerApi.generateResourcePdf(config.key, item.id)
        blob = result.blob
        filename = result.filename
      }
      const fallbackName = `${String(item.title ?? config.labelSingular)}.pdf`
      const objectUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = objectUrl
      link.download = filename || fallbackName
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(objectUrl)
    } catch (err) {
      setPdfError(await getBlobErrorMessage(err))
    } finally {
      setPdfDownloading(false)
    }
  }

  /** Just a show/hide toggle - the preview itself is already fetched
   * automatically by `openView` (see above), so toggling it back on after
   * hiding it doesn't call WeasyPrint again. */
  const handleTogglePdfPreview = () => {
    setPdfPreviewVisible((visible) => !visible)
  }

  const handleSubmit = (payload: Record<string, unknown>) => {
    setFormError(null)
    if (viewState === 'edit' && activeItem) {
      updateMutation.mutate(
        { id: activeItem.id, payload },
        {
          onSuccess: (updated) => {
            setActiveItem(updated)
            setViewState('view')
            // `openEdit` already cleared the previous preview - reload it
            // for the just-saved content, same as opening the record fresh
            // would (openView does this too; this handler is the other
            // place that lands on `viewState === 'view'`).
            if (isPdfExportable) fetchPdfPreview(updated)
          },
          onError: (err) => setFormError(getErrorMessage(err)),
        }
      )
    } else {
      createMutation.mutate(payload, {
        onSuccess: (created) => {
          setActiveItem(created)
          setViewState('view')
          if (isPdfExportable) fetchPdfPreview(created)
        },
        onError: (err) => setFormError(getErrorMessage(err)),
      })
    }
  }

  // ---------------------------------------------------------------------
  // Singleton mode (e.g. `identity`): at most one record, no table to come
  // back to. Defaults to a read-only view (same RecordView as everything
  // else) with its own Editar/Eliminar, exactly like a record you opened
  // from a list - only the form (create/edit) replaces it in place.
  // Straight to the form only when there's nothing to view yet (first-time
  // setup, nothing to look at read-only).
  // ---------------------------------------------------------------------
  if (isSingleton) {
    const existing = items[0]
    if (isLoading) return <LoadingSpinner fullScreen={false} message={`Cargando ${config.label.toLowerCase()}...`} />

    const showForm = !existing || isEditingSingleton

    const handleDeleteSingleton = () => {
      if (!existing) return
      const demonstrative = config.genderFeminine ? 'esta' : 'este'
      if (
        !window.confirm(`¿Eliminar ${demonstrative} ${config.labelSingular.toLowerCase()}? Esta acción no se puede deshacer.`)
      ) {
        return
      }
      deleteMutation.mutate(existing.id)
    }

    return (
      <div className="card">
        {!hideTitle && (
          <div className="card-header flex items-center justify-between gap-3">
            <h2 className="font-semibold text-text">{title || config.label}</h2>
            {!showForm && (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setFormError(null)
                    setIsEditingSingleton(true)
                  }}
                  className="btn-icon"
                  aria-label="Editar"
                  title="Editar"
                >
                  <Pencil size={16} />
                </button>
                <button
                  type="button"
                  onClick={handleDeleteSingleton}
                  className="btn-icon btn-icon-danger"
                  aria-label="Eliminar"
                  title="Eliminar"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            )}
          </div>
        )}
        <div className="card-body">
          {isError && (
            <p className="text-red-600 dark:text-red-400 text-sm mb-4">{getErrorMessage(error)}</p>
          )}
          {formError && (
            <p className="text-red-600 dark:text-red-400 text-sm mb-4">{formError}</p>
          )}

          {showForm ? (
            <ResourceForm
              config={config}
              initialValues={existing}
              onSubmit={(payload) => {
                setFormError(null)
                if (existing) {
                  updateMutation.mutate(
                    { id: existing.id, payload },
                    {
                      onSuccess: () => setIsEditingSingleton(false),
                      onError: (err) => setFormError(getErrorMessage(err)),
                    }
                  )
                } else {
                  createMutation.mutate(payload, { onError: (err) => setFormError(getErrorMessage(err)) })
                }
              }}
              onCancel={existing ? () => setIsEditingSingleton(false) : undefined}
              isSubmitting={createMutation.isPending || updateMutation.isPending}
              submitLabel={existing ? 'Actualizar' : 'Crear'}
            />
          ) : (
            <RecordView item={existing} fields={config.fields} resourceKey={config.key} />
          )}
        </div>
      </div>
    )
  }

  const isCards = config.variant === 'cards'

  // ---------------------------------------------------------------------
  // Header - changes with viewState instead of always showing the table's
  // title + "Nuevo" button.
  // ---------------------------------------------------------------------
  const headerTitle =
    viewState === 'list'
      ? title || config.label
      : viewState === 'create'
        ? `${config.genderFeminine ? 'Nueva' : 'Nuevo'} ${config.labelSingular}`
        : viewState === 'edit'
          ? `Editar ${config.labelSingular}`
          : String(activeItem?.[config.columns[0]?.key ?? ''] ?? config.labelSingular)

  const headerActions =
    viewState === 'list' ? (
      <button type="button" onClick={openCreate} className="btn-icon" aria-label="Nuevo" title="Nuevo">
        <Plus size={16} />
      </button>
    ) : (
      <div className="flex items-center gap-2">
        <button type="button" onClick={backToList} className="btn-icon" aria-label="Volver" title="Volver">
          <ArrowLeft size={16} />
        </button>
        {viewState === 'view' && activeItem && (
          <>
            {isPdfExportable && (
              <>
                <button
                  type="button"
                  onClick={handleTogglePdfPreview}
                  disabled={pdfPreviewLoading}
                  className="btn-icon"
                  aria-label={pdfPreviewVisible ? 'Ocultar vista previa de impresión' : 'Mostrar vista previa de impresión'}
                  title={pdfPreviewVisible ? 'Ocultar vista previa de impresión' : 'Mostrar vista previa de impresión'}
                >
                  {pdfPreviewVisible ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
                <button
                  type="button"
                  onClick={() => handleGeneratePdf(activeItem)}
                  disabled={pdfDownloading}
                  className="btn-icon"
                  aria-label="Generar PDF"
                  title="Generar PDF"
                >
                  <FileDown size={16} />
                </button>
              </>
            )}
            <button
              type="button"
              onClick={() => openEdit(activeItem)}
              className="btn-icon"
              aria-label="Editar"
              title="Editar"
            >
              <Pencil size={16} />
            </button>
            <button
              type="button"
              onClick={() => handleDelete(activeItem)}
              className="btn-icon btn-icon-danger"
              aria-label="Eliminar"
              title="Eliminar"
            >
              <Trash2 size={16} />
            </button>
          </>
        )}
      </div>
    )

  return (
    <div className={hideTitle ? '' : 'card'}>
      {!hideTitle && (
        <div className="card-header flex items-center justify-between gap-3">
          <h2 className="font-semibold text-text flex items-center gap-2">
            {headerTitle}
            {viewState === 'list' && totalCount !== undefined && (
              <span className="badge badge-slate mono">{totalCount}</span>
            )}
          </h2>
          {headerActions}
        </div>
      )}

      {hideTitle && (
        <div className="flex items-center justify-between gap-3 mb-3">
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide">{headerTitle}</h3>
          {headerActions}
        </div>
      )}

      <div className={hideTitle ? '' : 'card-body'}>
        {viewState === 'view' && pdfError && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-lg">
            <p className="text-red-800 dark:text-red-300 text-sm font-medium">{pdfError}</p>
          </div>
        )}
        {/* The `pdfExportField` (e.g. `content`) is excluded here - a
            PDF-exportable resource shows the rendered PDF preview in its
            place below (auto-loaded by openView) instead of that field's
            raw Markdown text. */}
        {viewState === 'view' && activeItem && (
          <RecordView
            item={activeItem}
            fields={recordViewFields}
            resourceKey={config.key}
            showMeta={!isPdfExportable}
          />
        )}

        {viewState === 'view' && isPdfExportable && pdfPreviewVisible && pdfPreviewLoading && (
          <div className="mt-4">
            <LoadingSpinner fullScreen={false} message="Generando vista previa..." />
          </div>
        )}

        {viewState === 'view' && isPdfExportable && pdfPreviewVisible && pdfPreviewUrl && (
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-2">
              Vista previa de impresión
            </h3>
            <iframe
              src={pdfPreviewUrl}
              title="Vista previa de impresión"
              className="w-full rounded-xl border border-border"
              style={{ height: '85vh' }}
            />
          </div>
        )}

        {/* Metadatos (ID/Creado/Última actualización) goes after the print
            preview for PDF-exportable resources, instead of RecordView's
            default position right after "Información" - see `showMeta`
            above. */}
        {viewState === 'view' && isPdfExportable && activeItem && (
          <div className="mt-4">
            <RecordMetadata item={activeItem} />
          </div>
        )}

        {(viewState === 'edit' || viewState === 'create') && (
          <>
            {formError && (
              <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-lg">
                <p className="text-red-800 dark:text-red-300 text-sm font-medium">{formError}</p>
              </div>
            )}
            <ResourceForm
              config={config}
              initialValues={viewState === 'edit' ? activeItem || undefined : undefined}
              presetValues={presetValues}
              onSubmit={handleSubmit}
              onCancel={cancelForm}
              isSubmitting={createMutation.isPending || updateMutation.isPending}
              submitLabel={viewState === 'create' ? 'Crear' : 'Actualizar'}
            />
          </>
        )}

        {viewState === 'list' && (
          <>
            {supportsListControls && (
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <div className="relative flex-1 min-w-[200px]">
                  <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-secondary" />
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder={`Buscar en ${config.label.toLowerCase()}...`}
                    className="input-field pl-8 pr-8 py-1.5 text-sm w-full"
                  />
                  {searchInput && (
                    <button
                      type="button"
                      onClick={() => setSearchInput('')}
                      aria-label="Limpiar búsqueda"
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>

                {isCards && config.columns.length > 0 && (
                  <div className="flex items-center gap-1">
                    <ThemedSelect
                      value={sortBy ?? ''}
                      onChange={(v) => toggleSort(v)}
                      className="w-auto min-w-[11rem]"
                      aria-label="Ordenar por"
                      placeholder="Orden por defecto"
                      options={config.columns.map((col) => ({ value: col.key, label: col.label }))}
                    />
                    {sortBy && (
                      <button
                        type="button"
                        onClick={() => setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'))}
                        className="btn-secondary btn-small"
                        aria-label={sortDir === 'asc' ? 'Ascendente' : 'Descendente'}
                        title={sortDir === 'asc' ? 'Ascendente' : 'Descendente'}
                      >
                        {sortDir === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />}
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

            {isLoading && <LoadingSpinner fullScreen={false} message="Cargando..." />}

            {isError && (
              <div className="text-center py-6">
                <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
                <button type="button" onClick={() => refetch()} className="btn-secondary btn-small mt-3">
                  Reintentar
                </button>
              </div>
            )}

            {!isLoading && !isError && items.length === 0 && (
              <p className="text-text-secondary text-sm text-center py-6">
                {search ? 'Sin resultados para esa búsqueda.' : `No hay ${config.label.toLowerCase()} todavía.`}
              </p>
            )}

            {!isLoading && !isError && items.length > 0 && isCards && (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {items.map((item) => (
                  <ProjectCard
                    key={item.id}
                    item={item}
                    config={config}
                    onView={() => openView(item)}
                    onEdit={() => openEdit(item)}
                    onDelete={() => handleDelete(item)}
                  />
                ))}
              </div>
            )}

            {!isLoading && !isError && items.length > 0 && !isCards && (
              <div className="overflow-x-auto -mx-6">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-text-secondary">
                      {config.columns.map((col) =>
                        supportsListControls ? (
                          <th key={col.key} className="px-6 py-2 font-medium whitespace-nowrap">
                            <button
                              type="button"
                              onClick={() => toggleSort(col.key)}
                              className="flex items-center gap-1 hover:text-text"
                            >
                              {col.label}
                              {sortBy === col.key ? (
                                sortDir === 'asc' ? (
                                  <ArrowUp size={12} />
                                ) : (
                                  <ArrowDown size={12} />
                                )
                              ) : (
                                <ArrowUpDown size={12} className="opacity-30" />
                              )}
                            </button>
                          </th>
                        ) : (
                          <th key={col.key} className="px-6 py-2 font-medium whitespace-nowrap">
                            {col.label}
                          </th>
                        )
                      )}
                      <th className="px-6 py-2 font-medium text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => (
                      <tr
                        key={item.id}
                        onClick={() => openView(item)}
                        className={`border-b border-border last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer ${rowClassName ? rowClassName(item) : ''}`}
                      >
                        {config.columns.map((col) => {
                          const value = item[col.key]
                          if (col.format === 'badge' && value !== null && value !== undefined && value !== '') {
                            return (
                              <td key={col.key} className="px-6 py-2 whitespace-nowrap">
                                <Badge color={col.badgeColor ? col.badgeColor(value) : 'slate'}>
                                  {String(value)}
                                </Badge>
                              </td>
                            )
                          }
                          return (
                            <td key={col.key} className="px-6 py-2 whitespace-nowrap text-text">
                              {formatCellValue(value, col.format)}
                            </td>
                          )
                        })}
                        <td className="px-6 py-2 text-right whitespace-nowrap">
                          <div className="flex justify-end items-center gap-1">
                            {renderExtraRowAction?.(item)}
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                openEdit(item)
                              }}
                              aria-label="Editar"
                              className="p-1.5 rounded text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-cyan-600"
                            >
                              <Pencil size={15} />
                            </button>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDelete(item)
                              }}
                              aria-label="Eliminar"
                              className="p-1.5 rounded text-text-secondary hover:bg-red-50 dark:hover:bg-red-950/40 hover:text-red-600"
                            >
                              <Trash2 size={15} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {!isNested && !isLoading && !isError && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setSkip((s) => Math.max(0, s - pageSize))}
                  disabled={skip === 0}
                  className="btn-secondary btn-small flex items-center gap-1 disabled:opacity-40"
                >
                  <ChevronLeft size={14} /> Anterior
                </button>
                <span className="text-xs text-text-secondary">
                  Mostrando {items.length === 0 ? 0 : skip + 1}–{skip + items.length}
                </span>
                <button
                  type="button"
                  onClick={() => setSkip((s) => s + pageSize)}
                  disabled={items.length < pageSize}
                  className="btn-secondary btn-small flex items-center gap-1 disabled:opacity-40"
                >
                  Siguiente <ChevronRight size={14} />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
