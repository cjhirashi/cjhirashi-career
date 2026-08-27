# `components/section/` — chrome compartido de las secciones del Admin

**Toda vista de tabla del Admin se construye con estos componentes.** El markup del marco
(card, pestañas folder, toolbar, tabla, footer) vive aquí y en ningún otro sitio. Ver
[ADR-020](../../../../docs/09-DECISIONS/020-admin-section-templates.md).

Pantalla de referencia: **`pages/ErrorReportsPage.tsx`**.

## Lista estándar → `TableSectionTemplate`

```tsx
import { TableSectionTemplate, useSectionTable } from '@/components/section'

const COLUMNS: ColumnConfig[] = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Nombre' },
  { key: 'created_at', label: 'Creado', format: 'datetime' },
]

export const FooPage = () => {
  const navigate = useNavigate()
  const { data = [], isLoading, isError, error } = useFoos()

  const { visibleColumns, columnSettings, sort, toggleSort, searchInput, setSearchInput, rows } =
    useSectionTable<Foo>({
      storageKey: 'foos',
      columns: COLUMNS,
      rows: data,
      searchAccessor: (r) => `${r.id} ${r.name}`,
    })

  return (
    <TableSectionTemplate<Foo>
      title="Foos"
      count={isLoading ? undefined : data.length}
      query={{ isLoading, isError, error }}
      toolbar={{
        search: { value: searchInput, onChange: setSearchInput, placeholder: 'Buscar…' },
        columnSettings,
      }}
      table={{
        columns: visibleColumns,
        rows,
        getRowKey: (r) => r.id,
        sort,
        onToggleSort: toggleSort,
        onRowClick: (r) => navigate(`/foos/${r.id}`),
        // renderCell devuelve undefined -> formatCellValue(value, col.format)
        renderCell: (r, key) => (key === 'status' ? <StatusBadge value={r.status} /> : undefined),
        emptyMessage: 'No hay foos.',
      }}
      footer={{ variant: 'count', total: data.length }}
    />
  )
}
```

Filtros por columna → `table.headerExtra(colKey)`; acciones por fila → `table.rowActions(row)`;
paginación de servidor → `footer={{ variant: 'pager', page, hasMore, onPageChange, pageSize, total }}`.

## Detalle (`:id`) → `DetailSectionTemplate` + `SectionRecordView`

```tsx
import { DetailSectionTemplate, SectionRecordView } from '@/components/section'

export const FooDetailPage = () => {
  const { id = '' } = useParams()
  const { data } = useFoo(id)
  if (!data) return null
  return (
    <DetailSectionTemplate
      sectionTitle="Foos"
      listPath="/foos"
      record={{ id: data.id, name: data.name }}
      actions={<button className="btn-icon btn-icon-sm">…</button>}
    >
      <SectionRecordView
        groups={[
          { title: 'Información', fields: [
            { label: 'ID', value: <span className="mono text-primary">{data.id}</span> },
            { label: 'Nombre', wide: true, value: data.name },
          ]},
        ]}
      />
    </DetailSectionTemplate>
  )
}
```

Para una pestaña `edit` con formulario propio, pásalo como `children` y controla
`activeTab` / `tabs` (ver `AdminSectionsPage.tsx`).

## Cuerpo a medida → primitivos directos

Cuando la vista no es una tabla estándar (subida de archivos, tableros), compón
`SectionShell` + `SectionToolbar` + `SectionTable` + `SectionTableFooter` a mano — pero
**no** reescribas el markup del chrome (ver `FilesPage.tsx`, `TasksPage.tsx`).
