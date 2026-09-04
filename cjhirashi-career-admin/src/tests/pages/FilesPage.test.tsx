import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen, fireEvent, waitFor } from '../utils'
import { FilesPage } from '@/pages/FilesPage'
import { filesApi } from '@/api/files'

vi.mock('@/api/files')

const mockedFilesApi = vi.mocked(filesApi)

const sampleFile = {
  id: 'flu-1',
  user_id: 'usr-1',
  original_filename: 'diagrama.png',
  stored_filename: 'public/certificaciones/abc123.png',
  file_type: 'image' as const,
  mime_type: 'image/png',
  file_size: 204800,
  description: null,
  category: 'certificaciones',
  is_public: true,
  download_url: 'https://files.cjhirashi.com/cjhirashi-career/public/certificaciones/abc123.png',
  created_at: '2026-08-19T00:00:00Z',
}

const renderPage = () =>
  render(
    <MemoryRouter>
      <FilesPage />
    </MemoryRouter>
  )

describe('FilesPage', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
    mockedFilesApi.list.mockResolvedValue([sampleFile])
    mockedFilesApi.categories.mockResolvedValue(['certificaciones', 'proyectos'])
  })

  it('lists uploaded files as a table row with size, folder and status', async () => {
    const { container } = renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())
    expect(screen.getByRole('table')).toBeInTheDocument()
    const badges = Array.from(container.querySelectorAll('.badge')).map((b) => b.textContent)
    expect(badges.some((t) => t?.includes('certificaciones'))).toBe(true)
    expect(badges.some((t) => t?.includes('Público'))).toBe(true)
    expect(screen.getByRole('button', { name: /copiar link/i })).toBeInTheDocument()
  })

  it('shows an empty state when there are no files', async () => {
    mockedFilesApi.list.mockResolvedValue([])
    renderPage()
    await waitFor(() => expect(screen.getByText(/no has subido/i)).toBeInTheDocument())
  })

  it('copies the public download URL to the clipboard', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })

    renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /copiar link/i }))
    expect(writeText).toHaveBeenCalledWith(sampleFile.download_url)
    await waitFor(() => expect(screen.getByRole('button', { name: /^copiado$/i })).toBeInTheDocument())
  })

  it('opens a preview for a public image without an extra request', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /^ver$/i }))

    expect(screen.getByRole('dialog', { name: 'diagrama.png' })).toBeInTheDocument()
    expect(mockedFilesApi.getDownloadUrl).not.toHaveBeenCalled()
  })

  it('fetches a signed URL to preview a private image', async () => {
    mockedFilesApi.list.mockResolvedValue([{ ...sampleFile, is_public: false, download_url: null }])
    mockedFilesApi.getDownloadUrl.mockResolvedValue('https://files.cjhirashi.com/...signed...')

    renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    expect(screen.queryByRole('button', { name: /copiar link/i })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /^ver$/i }))

    await waitFor(() => expect(mockedFilesApi.getDownloadUrl).toHaveBeenCalledWith(sampleFile.id))
    await waitFor(() => expect(screen.getByRole('dialog', { name: 'diagrama.png' })).toBeInTheDocument())
  })

  it('opens a new tab for a non-image file instead of a Modal preview', async () => {
    mockedFilesApi.list.mockResolvedValue([
      { ...sampleFile, file_type: 'document', original_filename: 'cv.pdf' },
    ])
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)

    renderPage()
    await waitFor(() => expect(screen.getByText('cv.pdf')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /^ver$/i }))

    expect(openSpy).toHaveBeenCalledWith(sampleFile.download_url, '_blank', 'noopener,noreferrer')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    openSpy.mockRestore()
  })

  it('downloads a file as a forced Blob save instead of navigating to it', async () => {
    const blob = new Blob(['contenido'], { type: 'image/png' })
    mockedFilesApi.downloadBlob.mockResolvedValue(blob)
    const createObjectURL = vi.fn().mockReturnValue('blob:mock-url')
    const revokeObjectURL = vi.fn()
    Object.assign(URL, { createObjectURL, revokeObjectURL })
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /descargar/i }))

    await waitFor(() => expect(mockedFilesApi.downloadBlob).toHaveBeenCalledWith(sampleFile.id))
    await waitFor(() => expect(clickSpy).toHaveBeenCalled())
    expect(createObjectURL).toHaveBeenCalledWith(blob)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    clickSpy.mockRestore()
  })

  it('uploads a selected file with no folder by default', async () => {
    mockedFilesApi.upload.mockResolvedValue({ ...sampleFile, id: 'flu-2', original_filename: 'nuevo.png' })
    renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    const file = new File(['contenido'], 'nuevo.png', { type: 'image/png' })
    const input = screen.getByLabelText(/seleccionar archivo/i) as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() =>
      expect(mockedFilesApi.upload).toHaveBeenCalledWith(file, { category: undefined, isPublic: true })
    )
  })

  it('uploads as private when the "Público" switch is turned off', async () => {
    mockedFilesApi.upload.mockResolvedValue({ ...sampleFile, id: 'flu-2', original_filename: 'nuevo.png' })
    renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('switch', { name: /público/i }))
    const file = new File(['contenido'], 'nuevo.png', { type: 'image/png' })
    fireEvent.change(screen.getByLabelText(/seleccionar archivo/i), { target: { files: [file] } })

    await waitFor(() =>
      expect(mockedFilesApi.upload).toHaveBeenCalledWith(file, { category: undefined, isPublic: false })
    )
  })

  it('uploads to the typed folder when one is set', async () => {
    mockedFilesApi.upload.mockResolvedValue({ ...sampleFile, id: 'flu-2', original_filename: 'nuevo.png' })
    renderPage()
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

  it('lets the user hide a table column from the settings menu', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())
    expect(screen.getByRole('columnheader', { name: 'Carpeta' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('combobox', { name: 'Columnas visibles' }))
    fireEvent.click(screen.getByRole('option', { name: /Carpeta/ }))

    await waitFor(() => expect(screen.queryByRole('columnheader', { name: 'Carpeta' })).not.toBeInTheDocument())
  })

  it('filters the list by folder', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())
    mockedFilesApi.list.mockClear()

    fireEvent.click(screen.getByRole('button', { name: /filtrar por carpeta/i }))
    fireEvent.click(screen.getByRole('option', { name: 'proyectos' }))

    await waitFor(() =>
      expect(mockedFilesApi.list).toHaveBeenCalledWith(expect.objectContaining({ category: 'proyectos' }))
    )
  })

  it('toggles a public file to private', async () => {
    mockedFilesApi.setVisibility.mockResolvedValue({ ...sampleFile, is_public: false, download_url: null })
    renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /hacer privado/i }))

    await waitFor(() => expect(mockedFilesApi.setVisibility).toHaveBeenCalledWith(sampleFile.id, false))
  })

  it('asks for confirmation and deletes a file', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockedFilesApi.remove.mockResolvedValue(undefined)
    renderPage()
    await waitFor(() => expect(screen.getByText('diagrama.png')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /eliminar/i }))

    expect(confirmSpy).toHaveBeenCalled()
    await waitFor(() => expect(mockedFilesApi.remove).toHaveBeenCalledWith(sampleFile.id))
    confirmSpy.mockRestore()
  })
})
