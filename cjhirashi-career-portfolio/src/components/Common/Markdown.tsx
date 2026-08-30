import React, { type ComponentPropsWithoutRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ExtraProps } from 'react-markdown'
import { MermaidDiagram } from './MermaidDiagram'

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

/** Recursively pulls the plain source text out of a fenced code block's
 * `children` (a <code> element whose own children are a string, or an array
 * of them) - the React-tree fallback when the hast node isn't available. */
const extractText = (node: React.ReactNode): string => {
  if (typeof node === 'string') return node
  if (typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(extractText).join('')
  if (React.isValidElement<{ children?: React.ReactNode }>(node)) {
    return extractText(node.props.children)
  }
  return ''
}

/** Minimal hast shapes - `ExtraProps.node` is typed as `Element | undefined`
 * but we only need to walk `children`/`value`/`properties.className`. */
type HastNode = {
  type?: string
  tagName?: string
  value?: string
  properties?: { className?: unknown }
  children?: HastNode[]
}

/** Flattens a hast subtree to its text content (the raw fenced-code source). */
const hastText = (node: HastNode | undefined): string => {
  if (!node) return ''
  if (typeof node.value === 'string') return node.value
  return (node.children ?? []).map(hastText).join('')
}

/** Reads the `language-xxx` token off a hast <code> element, tolerating
 * `className` being an array (`['language-mermaid']`) or a string. */
const languageOf = (codeNode: HastNode | undefined): string | null => {
  const raw = codeNode?.properties?.className
  const tokens = Array.isArray(raw)
    ? raw.map(String)
    : typeof raw === 'string'
      ? raw.split(/\s+/)
      : []
  const match = tokens.find((t) => t.startsWith('language-'))
  return match ? match.slice('language-'.length) : null
}

/** ReactMarkdown `pre` override: a ```mermaid fenced block renders as an
 * actual diagram (same as the admin panel's record view); every other
 * fenced block falls through to a plain <pre>. Detection works off the hast
 * `node` (reliable regardless of how `className` is serialized onto the
 * rendered React child), with a React-tree fallback. */
const MarkdownPre = ({
  children,
  node,
  ...props
}: ComponentPropsWithoutRef<'pre'> & ExtraProps) => {
  const preNode = node as HastNode | undefined
  const codeNode = preNode?.children?.find(
    (child) => child.type === 'element' && child.tagName === 'code',
  )

  let language = languageOf(codeNode)
  if (!language && React.isValidElement<{ className?: string }>(children)) {
    const cls = children.props.className
    if (typeof cls === 'string') language = cls.match(/language-(\w+)/)?.[1] ?? null
  }

  if (language === 'mermaid') {
    const source = codeNode ? hastText(codeNode) : extractText(children)
    return <MermaidDiagram code={source.replace(/\n$/, '')} />
  }

  return <pre {...props}>{children}</pre>
}

/** Renders admin-authored Markdown text (bio, project narrative, work
 * history, blog posts, ...) the same way the admin panel's own record view
 * does - bold/italic, lists, links, tables, and ```mermaid diagrams. Uses
 * the `.markdown-content` styles in index.css. */
export const Markdown = ({ children, className }: MarkdownProps) => (
  <div className={`markdown-content ${className ?? ''}`}>
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{ table: MarkdownTable, pre: MarkdownPre }}
    >
      {children}
    </ReactMarkdown>
  </div>
)
