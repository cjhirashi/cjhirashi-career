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
  stored_filename: 'certificaciones/abc123.png',
  file_type: 'image' as const,
  mime_type: 'image/png',
  file_size: 204800,
  description: null,
  category: 'certificaciones',
  is_public: true,
  download_url: 'https://files.cjhirashi.com/portafolio-cjhirashi/certificaciones/abc123.png',
  created_at: '2026-08-19T00:00:00Z',
}

describe('FilesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedFilesApi.list.mockResolvedValue([sampleFile])
    mockedFilesApi.categories.mockResolvedValue(['certificaciones', 'proyectos'])
  })

  it('lists uploaded files with size, folder badge and a copy-link action', async () => {
    const { container } = render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /copiar link/i })).toBeInTheDocument()
    expect(container.querySelector('.badge')?.textContent).toContain('certificaciones')
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

  it('uploads a selected file with no folder by default', async () => {
    mockedFilesApi.upload.mockResolvedValue({ ...sampleFile, id: 2, original_filename: 'nuevo.png' })
    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    const file = new File(['contenido'], 'nuevo.png', { type: 'image/png' })
    const input = screen.getByLabelText(/seleccionar archivo/i) as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() =>
      expect(mockedFilesApi.upload).toHaveBeenCalledWith(file, { category: undefined, isPublic: true })
    )
  })

  it('uploads as private when the "Público" checkbox is unchecked', async () => {
    mockedFilesApi.upload.mockResolvedValue({ ...sampleFile, id: 2, original_filename: 'nuevo.png' })
    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('checkbox', { name: /público/i }))
    const file = new File(['contenido'], 'nuevo.png', { type: 'image/png' })
    fireEvent.change(screen.getByLabelText(/seleccionar archivo/i), { target: { files: [file] } })

    await waitFor(() =>
      expect(mockedFilesApi.upload).toHaveBeenCalledWith(file, { category: undefined, isPublic: false })
    )
  })

  it('uploads to the typed folder when one is set', async () => {
    mockedFilesApi.upload.mockResolvedValue({ ...sampleFile, id: 2, original_filename: 'nuevo.png' })
    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.change(screen.getByLabelText(/carpeta para el próximo archivo/i), {
      target: { value: 'blog' },
    })
    const file = new File(['contenido'], 'nuevo.png', { type: 'image/png' })
    fireEvent.change(screen.getByLabelText(/seleccionar archivo/i), { target: { files: [file] } })

    await waitFor(() =>
      expect(mockedFilesApi.upload).toHaveBeenCalledWith(file, { category: 'blog', isPublic: true })
    )
  })

  it('filters the list by folder', async () => {
    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())
    mockedFilesApi.list.mockClear()

    fireEvent.change(screen.getByLabelText(/filtrar por carpeta/i), { target: { value: 'proyectos' } })

    await waitFor(() =>
      expect(mockedFilesApi.list).toHaveBeenCalledWith(expect.objectContaining({ category: 'proyectos' }))
    )
  })

  it('opens a larger preview when the image thumbnail is clicked', async () => {
    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /ver diagrama.png en grande/i }))

    expect(screen.getByRole('dialog', { name: 'diagrama.png' })).toBeInTheDocument()
  })

  it('toggles a public file to private', async () => {
    mockedFilesApi.setVisibility.mockResolvedValue({ ...sampleFile, is_public: false, download_url: null })
    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /hacer privado/i }))

    await waitFor(() => expect(mockedFilesApi.setVisibility).toHaveBeenCalledWith(1, false))
  })

  it('opens a signed download URL for a private file instead of copying a link', async () => {
    const privateFile = { ...sampleFile, is_public: false, download_url: null }
    mockedFilesApi.list.mockResolvedValue([privateFile])
    mockedFilesApi.getDownloadUrl.mockResolvedValue('https://files.cjhirashi.com/...signed...')
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)

    render(<FilesPage />)
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    expect(screen.queryByRole('button', { name: /copiar link/i })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /^ver$/i }))

    await waitFor(() => expect(mockedFilesApi.getDownloadUrl).toHaveBeenCalledWith(1))
    await waitFor(() =>
      expect(openSpy).toHaveBeenCalledWith(
        'https://files.cjhirashi.com/...signed...',
        '_blank',
        'noopener,noreferrer'
      )
    )
    openSpy.mockRestore()
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
