import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Markdown } from '@/components/Common/Markdown'

const tableMarkdown = `| ID | Empresa |
| --- | --- |
| wkh-24 | CYVSA Mantenimiento |
`

describe('Markdown tables', () => {
  it('wraps GFM tables in a horizontal scroll container', () => {
    const { container } = render(<Markdown>{tableMarkdown}</Markdown>)

    expect(container.querySelector('.markdown-table-scroll')).toBeInTheDocument()
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('CYVSA Mantenimiento')).toBeInTheDocument()
  })
})
