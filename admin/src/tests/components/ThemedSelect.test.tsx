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
    fireEvent.click(within(listbox).getByRole('option', { name: 'CV' }))
    expect(onChange).toHaveBeenCalledWith('cv')
  })

  it('shows the selected label on the trigger', () => {
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
})
