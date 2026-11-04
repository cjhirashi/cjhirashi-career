import { beforeEach, describe, expect, it, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { render, screen, waitFor } from '../testUtils'
import { trackingApi } from '@/api/tracking'
import { contactApi } from '@/api/contact'
import { PrivacyPage } from '@/pages/PrivacyPage'
import { Footer } from '@/components/Layout/Footer'
import { mockContact } from '../fixtures/mockData'

vi.mock('@/api/tracking')
vi.mock('@/api/contact')

beforeEach(() => {
  vi.clearAllMocks()
})

describe('RF-053 PrivacyPage', () => {
  it('explica qué se mide, qué no y cómo se trata el id', () => {
    render(<PrivacyPage />)
    expect(screen.getByRole('heading', { name: /Privacidad y medición/i })).toBeInTheDocument()
    expect(screen.getByText(/No se guarda tu dirección IP/i)).toBeInTheDocument()
    expect(screen.getByText(/Do Not Track/i)).toBeInTheDocument()
  })

  it('borrar mis datos llama a forgetMe y avisa del resultado', async () => {
    vi.mocked(trackingApi.forgetMe).mockResolvedValue(undefined)
    render(<PrivacyPage />)
    await userEvent.setup().click(screen.getByRole('button', { name: /Borrar mis datos/i }))
    await waitFor(() => expect(screen.getByText(/se borraron los registros asociados/i)).toBeInTheDocument())
    expect(trackingApi.forgetMe).toHaveBeenCalledTimes(1)
  })

  it('si el borrado falla, lo dice y deja reintentar', async () => {
    vi.mocked(trackingApi.forgetMe).mockRejectedValue(new Error('500'))
    render(<PrivacyPage />)
    await userEvent.setup().click(screen.getByRole('button', { name: /Borrar mis datos/i }))
    await waitFor(() => expect(screen.getByText(/No se pudo completar el borrado/i)).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /Borrar mis datos/i })).toBeEnabled()
  })

  it('el pie de página enlaza al aviso', async () => {
    vi.mocked(contactApi.getContact).mockResolvedValue(mockContact)
    render(<Footer />)
    expect(await screen.findByRole('link', { name: 'Privacidad' })).toHaveAttribute('href', '/privacy')
  })
})
