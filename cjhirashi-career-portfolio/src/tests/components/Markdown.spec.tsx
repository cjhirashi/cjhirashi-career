import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Markdown } from '@/components/Common/Markdown'

// Keep Mermaid's render pending so the component stays in its "loading"
// state - this asserts the ```mermaid branch is taken (diagram component
// mounted, no <pre>), not the finished SVG (jsdom has no SVG layout, so a
// real render never resolves here anyway).
vi.mock('mermaid', () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn(() => new Promise(() => {})),
  },
}))

const tableMarkdown = `| ID | Empresa |
| --- | --- |
| wkh-24 | CYVSA Mantenimiento |
`

const mermaidMarkdown = '```mermaid\ngraph TD\n  A --> B\n```\n'

describe('Markdown tables', () => {
  it('wraps GFM tables in a horizontal scroll container', () => {
    const { container } = render(<Markdown>{tableMarkdown}</Markdown>)

    expect(container.querySelector('.markdown-table-scroll')).toBeInTheDocument()
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('CYVSA Mantenimiento')).toBeInTheDocument()
  })
})

describe('Markdown mermaid blocks', () => {
  it('renders a ```mermaid fenced block as a diagram, not a code block', () => {
    const { container } = render(<Markdown>{mermaidMarkdown}</Markdown>)

    expect(container.querySelector('pre')).not.toBeInTheDocument()
    expect(screen.getByText(/renderizando diagrama/i)).toBeInTheDocument()
  })

  it('still renders non-mermaid fenced blocks as plain <pre>', () => {
    const { container } = render(<Markdown>{'```js\nconst x = 1\n```\n'}</Markdown>)

    expect(container.querySelector('pre')).toBeInTheDocument()
    expect(container.querySelector('pre code')?.textContent).toContain('const x = 1')
  })
})
