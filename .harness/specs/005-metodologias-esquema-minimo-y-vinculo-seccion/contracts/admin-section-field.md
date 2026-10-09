# Contrato — campo y celda "Sección" del recurso `operational-methodologies` (Admin, spec 005)

Feature 005. Frontend `cjhirashi-career-admin`.

## Campo de formulario (`operationalMethodologiesConfig.fields`)

```ts
{
  name: 'section_ids',
  label: 'Secciones del Admin',
  type: 'fk-multi-select',
  fkApi: 'admin-sections',   // FkApiMode nuevo
  fullWidth: true,
  helpText: 'Secciones del Admin a las que aplica esta metodología. Un agente ligado a una de esas secciones la recibe. También editable desde /settings/sections/:id.',
}
```

- **Wire format en el formulario:** string con los `sec-N` separados por `\n`
  (mismo formato que `multi-select`/`fk-multi-select`; `splitValues`/`join('\n')`).
- **Wire format hacia la API:** `section_ids: string[]` en el body del `PUT`
  (`ResourceForm` serializa la lista antes de enviar, igual que `agent_profile_ids`).
- **Opciones:** `useFkOptions('admin-sections')` → `adminSectionsApi.list()` →
  `GET /admin/sections`. Se consumen `id` (`sec-N`) y `label`.

## Celda de tabla (`operationalMethodologiesConfig.columns`)

```ts
{ key: 'section_ids', label: 'Sección', format: 'sections' }
```

`formatCellValue(value, 'sections')`:
- `value` = `string[]` de `sec-N`.
- resuelve cada id a su label con `getSectionLabel` (`@/config/sectionCatalog`).
- `sec-N` desconocido → se **omite** (nunca "sección desconocida").
- lista vacía / todos desconocidos → `'—'`.
- varios labels → unidos por `', '`.

## `GET /admin/sections` (existente, admin-only) — campos consumidos

```json
[ { "id": "sec-32", "label": "Proyectos", "system_name": "career-projects", "...": "..." } ]
```
Sólo `id` y `label` son contrato para esta feature.

## RNF-001 — una sola carga del catálogo

`useFkOptions('admin-sections', ...)` (campo) y `useAdminSectionsCatalog()` (celda,
que además llama `primeSectionLabels`) comparten la **misma** React Query key
(`['fk-options', 'admin-sections', 'admin-sections']`). Máximo una petición a
`/admin/sections` por render de la vista; nunca una por fila.
