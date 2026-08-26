import type { ComponentPropsWithoutRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ExtraProps } from 'react-markdown'

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

/** Renders admin-authored Markdown text (bio, project narrative, work
 * history, blog posts, ...) the same way the admin panel's own record view
 * does - bold/italic, lists, links, tables. Uses the `.markdown-content`
 * styles in index.css. */
export const Markdown = ({ children, className }: MarkdownProps) => (
  <div className={`markdown-content ${className ?? ''}`}>
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ table: MarkdownTable }}>
      {children}
    </ReactMarkdown>
  </div>
)
