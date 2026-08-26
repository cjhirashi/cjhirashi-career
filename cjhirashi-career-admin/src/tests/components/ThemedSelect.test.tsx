import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, within } from '../utils'
import { ThemedSelect } from '@/components/ThemedSelect'

const options = [
  { value: 'cv', label: 'CV' },
  { value: 'letter', label: 'Carta' },
]

describe('ThemedSelect', () => {
  it('opens a themed listbox instead of a native option menu', () => {
    const onChange = vi.fn()
    render(
      <ThemedSelect
        aria-label="Tipo de documento"
        value=""
        onChange={onChange}
        options={options}
        placeholder="Selecciona tipo"
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'Tipo de documento' }))
    const listbox = screen.getByRole('listbox')
    expect(listbox).toBeInTheDocument()
    fireEvent.click(within(listbox).getByRole('option', { name: /CV/ }))
    expect(onChange).toHaveBeenCalledWith('cv')
  })

  it('renders option photos when imageUrl is set', () => {
    render(
      <ThemedSelect
        aria-label="Responsable"
        value="user"
        onChange={() => undefined}
        allowEmpty={false}
        options={[
          { value: 'user', label: 'Carlos', imageUrl: 'https://example.com/me.jpg' },
          { value: 'agent_x', label: 'Buscador', imageUrl: null },
        ]}
      />
    )
    const trigger = screen.getByRole('button', { name: 'Responsable' })
    expect(trigger.querySelector('img')?.getAttribute('src')).toBe('https://example.com/me.jpg')
    fireEvent.click(trigger)
    expect(screen.getByRole('option', { name: /Buscador/ })).toHaveTextContent('BU')
  })

  it('shows the selected option label', () => {
    render(
      <ThemedSelect
        aria-label="Tipo"
        value="letter"
        onChange={() => undefined}
        options={options}
      />
    )
    expect(screen.getByRole('button', { name: 'Tipo' })).toHaveTextContent('Carta')
  })

  it('adds a typed value that is not yet in the list', () => {
    const onChange = vi.fn()
    render(
      <ThemedSelect
        aria-label="Tipo de contrato"
        value=""
        onChange={onChange}
        options={[{ value: 'empleado', label: 'empleado' }]}
        creatable
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'Tipo de contrato' }))
    fireEvent.change(screen.getByLabelText('Filtrar o añadir opción'), {
      target: { value: 'freelance' },
    })
    fireEvent.click(screen.getByRole('option', { name: /Añadir «freelance»/ }))
    expect(onChange).toHaveBeenCalledWith('freelance')
  })
})
