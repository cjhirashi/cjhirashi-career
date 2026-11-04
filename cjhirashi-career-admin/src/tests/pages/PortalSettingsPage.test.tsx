import type React from 'react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render as baseRender, screen, waitFor, fireEvent, within } from '../utils'
import { PortalSettingsPage } from '@/pages/PortalSettingsPage'
import { careerApi } from '@/api/career'

vi.mock('@/api/career')
const api = vi.mocked(careerApi)
const render = (ui: React.ReactElement) => baseRender(<MemoryRouter>{ui}</MemoryRouter>)

const lists: Record<string, unknown[]> = {}
const section = (title: string) => screen.getByText(title).closest('.card') as HTMLElement

beforeEach(() => {
  vi.clearAllMocks()
  Object.assign(lists, {
    'portal-sites': [{ id: 'psi-1', name: 'cjhirashi.com' }],
    'portal-goals': [
      { id: 'pgl-1', name: 'cv_download', type: 'event', match: { event_type: 'download' }, is_key_event: true },
      { id: 'pgl-2', name: 'lee_mucho', type: 'min_active', match: { ms: 45000 }, is_key_event: false },
    ],
    'portal-funnels': [{ id: 'pfn-1', name: 'Del inicio al CV', steps: [
      { label: 'Inicio', type: 'page', match: { path_prefix: '/' } },
      { label: 'Descarga', type: 'event', match: { event_type: 'download' } },
    ] }],
    'portal-annotations': [{ id: 'pan-1', day: '2026-10-30', title: 'Postulación a Acme', kind: 'application', ref: null }],
  })
  api.list.mockImplementation((async (resource: string) => lists[resource] ?? []) as never)
  api.create.mockResolvedValue({} as never)
  api.update.mockResolvedValue({} as never)
  api.remove.mockResolvedValue(undefined)
  vi.spyOn(window, 'confirm').mockReturnValue(true)
})

describe('PortalSettingsPage', () => {
  it('lista metas, embudos y anotaciones con su descripción en español', async () => {
    render(<PortalSettingsPage />)
    expect(await screen.findByText('cv_download')).toBeInTheDocument()
    expect(screen.getByText('Evento: Descarga de archivo')).toBeInTheDocument()
    expect(screen.getByText('45 s activos o más')).toBeInTheDocument()
    expect(screen.getByText('Inicio · Ruta que empieza con /')).toBeInTheDocument()
    expect(screen.getByText(/2026-10-30 · Postulación/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Volver a Métricas/ })).toHaveAttribute('href', '/metrics')
  })

  it('sin sitio de analítica lo dice y no ofrece crear nada', async () => {
    lists['portal-sites'] = []
    render(<PortalSettingsPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('No hay un sitio de analítica configurado')
    expect(screen.queryByRole('button', { name: 'Nueva meta' })).not.toBeInTheDocument()
  })

  describe('metas', () => {
    it('crea una meta de tiempo activo: segundos a milisegundos y con el sitio', async () => {
      render(<PortalSettingsPage />)
      await screen.findByText('cv_download')
      fireEvent.click(screen.getByRole('button', { name: 'Nueva meta' }))
      const form = screen.getByRole('form', { name: 'Nueva meta' })
      fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Se queda' } })
      fireEvent.change(within(form).getByLabelText('Tipo'), { target: { value: 'min_active' } })
      fireEvent.change(within(form).getByLabelText('Segundos activos mínimos'), { target: { value: '30' } })
      fireEvent.click(within(form).getByLabelText(/Evento clave/))
      fireEvent.click(within(form).getByRole('button', { name: 'Crear meta' }))
      await waitFor(() => expect(api.create).toHaveBeenCalledWith('portal-goals', {
        name: 'Se queda', type: 'min_active', match: { ms: 30000 }, is_key_event: true, site_id: 'psi-1',
      }))
    })

    it('no llama a la API si falta algo y dice qué', async () => {
      render(<PortalSettingsPage />)
      await screen.findByText('cv_download')
      fireEvent.click(screen.getByRole('button', { name: 'Nueva meta' }))
      const form = screen.getByRole('form', { name: 'Nueva meta' })
      fireEvent.click(within(form).getByRole('button', { name: 'Crear meta' }))
      expect(await within(form).findByRole('alert')).toHaveTextContent('Falta el nombre de la meta.')
      fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'X' } })
      fireEvent.change(within(form).getByLabelText('Tipo'), { target: { value: 'page' } })
      fireEvent.change(within(form).getByLabelText('La ruta empieza con'), { target: { value: 'sin-barra' } })
      fireEvent.click(within(form).getByRole('button', { name: 'Crear meta' }))
      expect(await within(form).findByRole('alert')).toHaveTextContent('La ruta debe empezar con «/».')
      expect(api.create).not.toHaveBeenCalled()
    })

    it('edita sin reenviar el sitio y devuelve los milisegundos como segundos', async () => {
      render(<PortalSettingsPage />)
      fireEvent.click(await screen.findByRole('button', { name: 'Editar meta lee_mucho' }))
      const form = screen.getByRole('form', { name: 'Editar meta' })
      expect(within(form).getByLabelText('Segundos activos mínimos')).toHaveValue('45')
      fireEvent.change(within(form).getByLabelText('Segundos activos mínimos'), { target: { value: '60' } })
      fireEvent.click(within(form).getByRole('button', { name: 'Guardar cambios' }))
      await waitFor(() => expect(api.update).toHaveBeenCalledWith('portal-goals', 'pgl-2', {
        name: 'lee_mucho', type: 'min_active', match: { ms: 60000 }, is_key_event: false,
      }))
    })

    it('pide confirmación para eliminar y no borra si se cancela', async () => {
      render(<PortalSettingsPage />)
      const del = await screen.findByRole('button', { name: 'Eliminar meta cv_download' })
      vi.mocked(window.confirm).mockReturnValueOnce(false)
      fireEvent.click(del)
      expect(api.remove).not.toHaveBeenCalled()
      fireEvent.click(del)
      await waitFor(() => expect(api.remove).toHaveBeenCalledWith('portal-goals', 'pgl-1'))
    })

    it('muestra el error del servidor al guardar', async () => {
      api.create.mockRejectedValueOnce(new Error('El servidor se negó'))
      render(<PortalSettingsPage />)
      await screen.findByText('cv_download')
      fireEvent.click(screen.getByRole('button', { name: 'Nueva meta' }))
      const form = screen.getByRole('form', { name: 'Nueva meta' })
      fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Otra' } })
      fireEvent.click(within(form).getByRole('button', { name: 'Crear meta' }))
      expect(await within(form).findByRole('alert')).toHaveTextContent('El servidor se negó')
    })
  })

  describe('embudos', () => {
    const open = async () => {
      render(<PortalSettingsPage />)
      await screen.findByText('Del inicio al CV')
      fireEvent.click(screen.getByRole('button', { name: 'Nuevo embudo' }))
      return screen.getByRole('form', { name: 'Nuevo embudo' })
    }
    const fillStep = (form: HTMLElement, n: number, label: string, type: string, value: string) => {
      const step = within(form).getByRole('listitem', { name: `Paso ${n}` })
      fireEvent.change(within(step).getByLabelText('Nombre del paso'), { target: { value: label } })
      fireEvent.change(within(step).getByLabelText('Tipo'), { target: { value: type } })
      fireEvent.change(within(step).getByLabelText(type === 'event' ? 'Tipo de evento' : type === 'page' ? 'La ruta empieza con' : 'La dirección contiene'), { target: { value } })
    }

    it('crea un embudo de 3 pasos con la forma que pide el servidor', async () => {
      const form = await open()
      fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Contacto' } })
      fillStep(form, 1, 'Inicio', 'page', '/')
      fillStep(form, 2, 'Abre un proyecto', 'page', '/projects/')
      fireEvent.click(within(form).getByRole('button', { name: 'Añadir paso' }))
      fillStep(form, 3, 'Escribe', 'event', 'form_submit')
      fireEvent.click(within(form).getByRole('button', { name: 'Crear embudo' }))
      await waitFor(() => expect(api.create).toHaveBeenCalledWith('portal-funnels', {
        name: 'Contacto', site_id: 'psi-1', steps: [
          { label: 'Inicio', type: 'page', match: { path_prefix: '/' } },
          { label: 'Abre un proyecto', type: 'page', match: { path_prefix: '/projects/' } },
          { label: 'Escribe', type: 'event', match: { event_type: 'form_submit' } },
        ],
      }))
    })

    it('arranca con 2 pasos y no deja quitar por debajo de 2', async () => {
      const form = await open()
      expect(within(form).getAllByRole('listitem', { name: /^Paso/ })).toHaveLength(2)
      expect(within(form).getByRole('button', { name: 'Quitar paso 1' })).toBeDisabled()
      fireEvent.click(within(form).getByRole('button', { name: 'Añadir paso' }))
      expect(within(form).getByRole('button', { name: 'Quitar paso 1' })).toBeEnabled()
      fireEvent.click(within(form).getByRole('button', { name: 'Quitar paso 3' }))
      expect(within(form).getAllByRole('listitem', { name: /^Paso/ })).toHaveLength(2)
    })

    it('lista todos los problemas a la vez y no guarda', async () => {
      const form = await open()
      fireEvent.click(within(form).getByRole('button', { name: 'Crear embudo' }))
      const alert = await within(form).findByRole('alert')
      expect(alert).toHaveTextContent('Falta el nombre del embudo.')
      expect(alert).toHaveTextContent('El paso 1 no tiene nombre.')
      expect(alert).toHaveTextContent('Paso 2: Falta el valor.')
      expect(api.create).not.toHaveBeenCalled()
    })

    it('reordena los pasos y lo guarda en ese orden', async () => {
      render(<PortalSettingsPage />)
      fireEvent.click(await screen.findByRole('button', { name: 'Editar embudo Del inicio al CV' }))
      const form = screen.getByRole('form', { name: 'Editar embudo' })
      fireEvent.click(within(form).getByRole('button', { name: 'Subir paso 2' }))
      fireEvent.click(within(form).getByRole('button', { name: 'Guardar cambios' }))
      await waitFor(() => expect(api.update).toHaveBeenCalledWith('portal-funnels', 'pfn-1', {
        name: 'Del inicio al CV', steps: [
          { label: 'Descarga', type: 'event', match: { event_type: 'download' } },
          { label: 'Inicio', type: 'page', match: { path_prefix: '/' } },
        ],
      }))
    })
  })

  describe('anotaciones', () => {
    it('crea una con fecha, tipo y referencia opcional', async () => {
      render(<PortalSettingsPage />)
      await screen.findByText('Postulación a Acme')
      fireEvent.click(screen.getByRole('button', { name: 'Nueva anotación' }))
      const form = screen.getByRole('form', { name: 'Nueva anotación' })
      fireEvent.click(within(form).getByRole('button', { name: 'Crear anotación' }))
      expect(await within(form).findByRole('alert')).toHaveTextContent('Falta la fecha.')
      fireEvent.change(within(form).getByLabelText('Fecha'), { target: { value: '2026-11-02' } })
      fireEvent.click(within(form).getByRole('button', { name: 'Crear anotación' }))
      expect(await within(form).findByRole('alert')).toHaveTextContent('Falta el título.')
      fireEvent.change(within(form).getByLabelText('Título'), { target: { value: 'Post sobre Synapse' } })
      fireEvent.change(within(form).getByLabelText('Tipo'), { target: { value: 'blog_post' } })
      fireEvent.click(within(form).getByRole('button', { name: 'Crear anotación' }))
      await waitFor(() => expect(api.create).toHaveBeenCalledWith('portal-annotations', {
        day: '2026-11-02', title: 'Post sobre Synapse', kind: 'blog_post', ref: null, site_id: 'psi-1',
      }))
    })

    it('elimina con confirmación', async () => {
      render(<PortalSettingsPage />)
      fireEvent.click(await screen.findByRole('button', { name: 'Eliminar anotación Postulación a Acme' }))
      await waitFor(() => expect(api.remove).toHaveBeenCalledWith('portal-annotations', 'pan-1'))
      expect(section('Anotaciones')).toBeInTheDocument()
    })
  })
})
