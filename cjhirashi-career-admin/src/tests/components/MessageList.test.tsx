import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MessageList } from '@/components/bedrock/MessageList'
import { BedrockChatMessage } from '@/types/bedrock'

const tableReply = `Analisis de los historiales actuales:

| ID | Empresa | Rol |
| --- | --- | --- |
| wkh-24 | CYVSA Mantenimiento | Gerente de Automatizacion |
| wkh-23 | Atom Controles | Arquitecto Independiente |
`

describe('MessageList markdown tables', () => {
  it('wraps GFM tables in a horizontal scroll container', () => {
    const messages: BedrockChatMessage[] = [
      {
        id: 'm1',
        role: 'assistant',
        content: tableReply,
        created_at: '2026-08-26T00:00:00Z',
      },
    ]

    const { container } = render(
      <MessageList messages={messages} isSending={false} statusMessage={null} />
    )

    expect(container.querySelector('.markdown-table-scroll')).toBeInTheDocument()
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('CYVSA Mantenimiento')).toBeInTheDocument()
  })
})
