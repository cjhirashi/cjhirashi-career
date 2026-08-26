import type { ComponentPropsWithoutRef } from 'react'
import type { ExtraProps } from 'react-markdown'

type MarkdownTableProps = ComponentPropsWithoutRef<'table'> & ExtraProps

/** Horizontal scroll wrapper for GFM tables so they cannot stretch the
 * surrounding layout (chat sidebar, record Markdown, task cards). */
export function MarkdownTable({ children, node: _node, ...props }: MarkdownTableProps) {
  return (
    <div className="markdown-table-scroll">
      <table {...props}>{children}</table>
    </div>
  )
}
