import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownProps {
  children: string
  className?: string
}

/** Renders admin-authored Markdown text (bio, project narrative, work
 * history, blog posts, ...) the same way the admin panel's own record view
 * does - bold/italic, lists, links, tables. Uses the `.markdown-content`
 * styles in index.css. */
export const Markdown = ({ children, className }: MarkdownProps) => (
  <div className={`markdown-content ${className ?? ''}`}>
    <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
  </div>
)
