import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, Check, ChevronLeft, ChevronRight, Copy, Pencil, Plus, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize'
import rehypeHighlight from 'rehype-highlight'
import { useThemeStore } from '@/stores/themeStore'
import { FieldConfig, FieldType, ResourceConfig } from '@/config/careerResources'
import { useCareerList, useCareerMutations } from '@/hooks/useCareerResource'
import { CareerEntity } from '@/types/career'
import { getErrorMessage } from '@/utils/errors'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ResourceForm } from './ResourceForm'
import { formatCellValue } from './careerFieldUtils'
import { formatDate, formatDateTime } from '@/utils/formatters'

export interface ParentFilter {
  field: string
  value: number
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

  return <div className="mermaid-diagram mb-3" dangerouslySetInnerHTML={{ __html: svg }} />
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
    <div className="relative group/code">
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
        className="absolute top-2 right-2 p-1.5 rounded-lg text-text-secondary hover:text-text bg-glass opacity-0 group-hover/code:opacity-100 focus:opacity-100 transition-opacity"
      >
        {copied ? <Check size={14} /> : <Copy size={14} />}
      </button>
    </div>
  )
}

interface CareerResourceViewProps {
  config: ResourceConfig
  pageSize?: number
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

/** Read-only rendering of a single field's value, matching its `FieldType` -
 * no truncation (unlike the table's `formatCellValue`), since this is the
 * one place meant to show the complete content. */
const FieldValue: React.FC<{ value: unknown; type: FieldType }> = ({ value, type }) => {
  if (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) {
    return <span className="text-text-muted">—</span>
  }

  switch (type) {
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

/** Every field the record has, in full - not just the table's summary
 * columns - grouped into "Información" plus an automatic "Metadatos"
 * section for whichever of id/created_at/updated_at the record actually
 * carries (not every career table has all three, see types/career.ts). */
const RecordView: React.FC<{ item: CareerEntity; fields: FieldConfig[] }> = ({ item, fields }) => {
  const metaEntries = useMemo(() => {
    const entries: { label: string; value: string }[] = []
    if (typeof item.id === 'number') entries.push({ label: 'ID', value: String(item.id) })
    if (typeof item.created_at === 'string') entries.push({ label: 'Creado', value: formatDateTime(item.created_at) })
    if (typeof item.updated_at === 'string')
      entries.push({ label: 'Última actualización', value: formatDateTime(item.updated_at) })
    return entries
  }, [item])

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">Información</h3>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {fields.map((field) => (
            <div key={field.name} className={field.fullWidth ? 'md:col-span-2' : ''}>
              <dt className="text-xs text-text-secondary mb-1">{field.label}</dt>
              <dd className="text-sm text-text">
                <FieldValue value={item[field.name]} type={field.type} />
              </dd>
            </div>
          ))}
        </dl>
      </div>

      {metaEntries.length > 0 && (
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
      )}
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
  parentFilter,
  presetValues,
  title,
  hideTitle,
  renderExtraRowAction,
  rowClassName,
}) => {
  const isSingleton = config.mode === 'singleton'
  const isNested = !!parentFilter
  const [skip, setSkip] = useState(0)
  const limit = isNested ? 100 : isSingleton ? 1 : pageSize

  const { data, isLoading, isError, error, refetch } = useCareerList<CareerEntity>(config.key, {
    skip: isNested || isSingleton ? 0 : skip,
    limit,
  })
  const { createMutation, updateMutation, deleteMutation } = useCareerMutations<CareerEntity>(config.key)

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

  const backToList = () => {
    setViewState('list')
    setActiveItem(null)
    setFormError(null)
  }

  const openView = (item: CareerEntity) => {
    setActiveItem(item)
    setFormError(null)
    setViewState('view')
  }

  const openCreate = () => {
    setActiveItem(null)
    setFormError(null)
    setViewState('create')
  }

  const openEdit = (item: CareerEntity) => {
    setActiveItem(item)
    setFormError(null)
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

  const handleSubmit = (payload: Record<string, unknown>) => {
    setFormError(null)
    if (viewState === 'edit' && activeItem) {
      updateMutation.mutate(
        { id: activeItem.id, payload },
        {
          onSuccess: (updated) => {
            setActiveItem(updated)
            setViewState('view')
          },
          onError: (err) => setFormError(getErrorMessage(err)),
        }
      )
    } else {
      createMutation.mutate(payload, {
        onSuccess: (created) => {
          setActiveItem(created)
          setViewState('view')
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
            <RecordView item={existing} fields={config.fields} />
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
          <h2 className="font-semibold text-text">{headerTitle}</h2>
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
        {viewState === 'view' && activeItem && <RecordView item={activeItem} fields={config.fields} />}

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
                No hay {config.label.toLowerCase()} todavía.
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
                      {config.columns.map((col) => (
                        <th key={col.key} className="px-6 py-2 font-medium whitespace-nowrap">
                          {col.label}
                        </th>
                      ))}
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
