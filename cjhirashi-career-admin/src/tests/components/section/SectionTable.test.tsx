import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '../../utils'
import { SectionTable } from '@/components/section/SectionTable'
import { ColumnConfig } from '@/config/careerResources'

interface Row {
  id: string
  name: string
  count: number
}

const columns: ColumnConfig[] = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Nombre' },
  { key: 'count', label: 'Total', format: 'number' },
]

const rows: Row[] = [
  { id: 'a-1', name: 'Alfa', count: 2 },
  { id: 'a-2', name: 'Beta', count: 5 },
]

describe('SectionTable', () => {
  it('renders headers, the id cell and formatted values', () => {
    render(
      <SectionTable<Row>
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        emptyMessage="vacío"
      />,
    )
    expect(screen.getByText('Nombre')).toBeInTheDocument()
    expect(screen.getByText('a-1')).toBeInTheDocument()
    expect(screen.getByText('Beta')).toBeInTheDocument()
  })

  it('shows the loading, error and empty states', () => {
    const { rerender } = render(
      <SectionTable<Row>
        columns={columns}
        rows={[]}
        getRowKey={(r) => r.id}
        state={{ isLoading: true }}
        emptyMessage="vacío"
      />,
    )
    expect(screen.getByText(/Cargando/i)).toBeInTheDocument()

    rerender(
      <SectionTable<Row>
        columns={columns}
        rows={[]}
        getRowKey={(r) => r.id}
        state={{ isError: true, errorMessage: 'boom', onRetry: () => undefined }}
        emptyMessage="vacío"
      />,
    )
    expect(screen.getByText('boom')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument()

    rerender(
      <SectionTable<Row>
        columns={columns}
        rows={[]}
        getRowKey={(r) => r.id}
        emptyMessage="No hay filas."
      />,
    )
    expect(screen.getByText('No hay filas.')).toBeInTheDocument()
  })

  it('calls onToggleSort from the header and onRowClick from a row', () => {
    const onToggleSort = vi.fn()
    const onRowClick = vi.fn()
    render(
      <SectionTable<Row>
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        sort={{ key: 'name', dir: 'asc' }}
        onToggleSort={onToggleSort}
        onRowClick={onRowClick}
        emptyMessage="vacío"
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: /Nombre/i }))
    expect(onToggleSort).toHaveBeenCalledWith('name')

    fireEvent.click(screen.getByText('Alfa'))
    expect(onRowClick).toHaveBeenCalledWith(rows[0])
  })

  it('uses renderCell overrides and a trailing actions column', () => {
    render(
      <SectionTable<Row>
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        renderCell={(row, key) => (key === 'name' ? <em data-testid="ov">{row.name}!</em> : undefined)}
        rowActions={(row) => <button type="button">edit {row.id}</button>}
        emptyMessage="vacío"
      />,
    )
    expect(screen.getAllByTestId('ov')[0]).toHaveTextContent('Alfa!')
    expect(screen.getByText('Acciones')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'edit a-1' })).toBeInTheDocument()
  })
})
