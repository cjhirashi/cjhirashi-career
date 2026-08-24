import { describe, expect, it } from 'vitest'
import { sanitizeAssistantReply } from '@/utils/chatReply'

describe('sanitizeAssistantReply', () => {
  it('strips thinking blocks and keeps the visible answer', () => {
    const raw =
      '<thinking>Voy a revisar las vacantes.</thinking>\n\nNo hay cambios recientes.'
    expect(sanitizeAssistantReply(raw)).toBe('No hay cambios recientes.')
  })

  it('keeps inner text when the entire reply is wrapped', () => {
    const raw =
      '<thinking>Parece que actualmente no hay cambios recientes en las vacantes.</thinking>'
    expect(sanitizeAssistantReply(raw)).toBe(
      'Parece que actualmente no hay cambios recientes en las vacantes.',
    )
  })

  it('strips think aliases', () => {
    expect(sanitizeAssistantReply('<think>razon</think>\nListo.')).toBe('Listo.')
  })
})
