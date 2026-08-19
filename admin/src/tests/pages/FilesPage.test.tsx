import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../utils'
import { FilesPage } from '@/pages/FilesPage'
import { filesApi } from '@/api/files'

vi.mock('@/api/files')

const mockedFilesApi = vi.mocked(filesApi)

const sampleFile = {
  id: 1,
  user_id: 1,
  original_filename: 'diagrama.png',
  stored_filename: 'abc123.png',
  file_type: 'image' as const,
  mime_type: 'image/png',
  file_size: 204800,
  description: null,
  is_public: true,
  download_url: 'https://files.cjhirashi.com/portafolio-cjhirashi/abc123.png',
  created_at: '2026-08-19T00:00:00Z',
}

describe('FilesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedFilesApi.list.mockResolvedValue([sampleFile])
  })

  it('lists uploaded files with size and a copy-link action', async () => {
    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /copiar link/i })).toBeInTheDocument()
  })

  it('shows an empty state when there are no files', async () => {
    mockedFilesApi.list.mockResolvedValue([])
    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText(/no has subido/i)).toBeInTheDocument())
  })

  it('copies the public download URL to the clipboard', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })

    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /copiar link/i }))
    expect(writeText).toHaveBeenCalledWith(sampleFile.download_url)
    await waitFor(() => expect(screen.getByRole('button', { name: /^copiado$/i })).toBeInTheDocument())
  })

  it('uploads a selected file', async () => {
    mockedFilesApi.upload.mockResolvedValue({ ...sampleFile, id: 2, original_filename: 'nuevo.png' })
    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    const file = new File(['contenido'], 'nuevo.png', { type: 'image/png' })
    const input = screen.getByLabelText(/seleccionar archivo/i) as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => expect(mockedFilesApi.upload).toHaveBeenCalledWith(file, undefined))
  })

  it('asks for confirmation and deletes a file', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockedFilesApi.remove.mockResolvedValue(undefined)
    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /eliminar/i }))

    expect(confirmSpy).toHaveBeenCalled()
    await waitFor(() => expect(mockedFilesApi.remove).toHaveBeenCalledWith(1))
    confirmSpy.mockRestore()
  })
})
