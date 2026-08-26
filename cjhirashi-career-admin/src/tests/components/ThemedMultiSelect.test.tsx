import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, within } from '../utils'
import { ThemedMultiSelect } from '@/components/ThemedMultiSelect'

const options = [
  { value: 'ach-13', label: 'Bioterio del INS' },
  { value: 'ach-16', label: 'DHL Almacenes' },
  { value: 'ach-18', label: 'Sistema de Gestión de Carrera' },
]

describe('ThemedMultiSelect', () => {
  it('opens a themed listbox and keeps it open after toggling an option', () => {
    const onChange = vi.fn()
    render(
      <ThemedMultiSelect
        aria-label="Logros"
        value={[]}
        onChange={onChange}
        options={options}
        placeholder="— Selecciona logros —"
      />
    )

    fireEvent.click(screen.getByRole('combobox', { name: 'Logros' }))
    const listbox = screen.getByRole('listbox')
    expect(listbox).toBeInTheDocument()
    fireEvent.click(within(listbox).getByRole('option', { name: /Bioterio del INS/ }))
    expect(onChange).toHaveBeenCalledWith(['ach-13'])
    expect(screen.getByRole('listbox')).toBeInTheDocument()
  })

  it('shows selected labels as chips on the trigger', () => {
    render(
      <ThemedMultiSelect
        aria-label="Logros"
        value={['ach-13', 'ach-16']}
        onChange={() => undefined}
        options={options}
      />
    )
    const trigger = screen.getByRole('combobox', { name: 'Logros' })
    expect(trigger).toHaveTextContent('Bioterio del INS')
    expect(trigger).toHaveTextContent('DHL Almacenes')
  })

  it('removes a value from a chip without opening the list', () => {
    const onChange = vi.fn()
    render(
      <ThemedMultiSelect
        aria-label="Logros"
        value={['ach-13', 'ach-16']}
        onChange={onChange}
        options={options}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: 'Quitar Bioterio del INS' }))
    expect(onChange).toHaveBeenCalledWith(['ach-16'])
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('opens the option list from an icon filter button', () => {
    const onChange = vi.fn()
    render(
      <ThemedMultiSelect
        variant="icon"
        aria-label="Tipo de evidencia"
        value={[]}
        onChange={onChange}
        options={options}
      />
    )

    fireEvent.click(screen.getByRole('combobox', { name: 'Filtrar Tipo de evidencia' }))
    const listbox = screen.getByRole('listbox')
    fireEvent.click(within(listbox).getByRole('option', { name: /Bioterio del INS/ }))
    expect(onChange).toHaveBeenCalledWith(['ach-13'])
    expect(screen.getByRole('listbox')).toBeInTheDocument()
  })

  it('uses a settings trigger label without the Filtrar prefix', () => {
    render(
      <ThemedMultiSelect
        variant="icon"
        triggerLabel="Columnas visibles"
        aria-label="Columnas visibles"
        showCount={false}
        value={['title']}
        onChange={() => undefined}
        options={[
          { value: 'title', label: 'Título' },
          { value: 'narrative', label: 'Narrativa' },
        ]}
      />
    )
    expect(screen.getByRole('combobox', { name: 'Columnas visibles' })).toBeInTheDocument()
  })
})
