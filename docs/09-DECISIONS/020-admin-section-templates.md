# ADR-020: Plantilla compartida para las secciones de tabla del Admin

## Estado

Aceptado — 2026-08-27

## Contexto

Cada pantalla de lista del Admin Panel reescribía a mano el mismo *chrome* (el marco
visual): `card has-view-tabs` → `card-header` con título + pestañas folder → `table-toolbar`
con búsqueda y ajustes de columnas → `table-scroll` con un `<table>` de cabeceras ordenables
→ `table-footer`. Ese markup estaba **duplicado en 6 sitios**
(`components/career/CareerResourceView.tsx`, `pages/AdminSectionsPage.tsx`,
`pages/AgentCatalogPage.tsx`, `pages/ErrorReportsPage.tsx`, `pages/FilesPage.tsx`, y la
pestaña *Lista* de `pages/TasksPage.tsx`), y `compareCells` (orden de celdas) copiado 4
veces. Cada pantalla nueva nacía con pequeñas diferencias de estructura y estilo; mantener
congruencia exigía tocar N archivos por cada cambio.

## Decisión

Un **único punto de verdad para el chrome**: el módulo `src/components/section/`.

### Primitivos componibles

| Componente | Responsabilidad |
|---|---|
| `SectionShell` | El `card has-view-tabs` + cabecera (título / breadcrump `título · id · nombre` + badge de conteo + `SectionViewTabs` + `view-tabs-actions`) + cuerpo. `variant="list"` añade `table-list-body`; `embedded` lo usa sin `card`. |
| `SectionToolbar` | La fila `table-toolbar`: búsqueda + "Limpiar filtros" + controles extra + engranaje `TableColumnSettings`. |
| `SectionTable` | El `<table>`: cabecera pegajosa ordenable, columna id resaltada, slot de filtro por columna, columna de acciones opcional, y los estados loading / error / vacío. |
| `SectionTableFooter` | El `table-footer`: etiqueta "N–M de total", con o sin paginación prev/next. |
| `SectionRecordView` + `SectionField` | El `<dl>` de 2 columnas de las vistas de detalle. |

### Hook + util

- `useSectionTable` agrupa el estado que toda lista necesita: columnas visibles/ordenadas
  (persistidas en `localStorage` vía `useVisibleTableColumns`), alternado de orden, y
  búsqueda con debounce (con filtrado en cliente cuando se pasa `searchAccessor`).
- `compareCells` se movió a `utils/tableColumns.ts` (fuente única; se eliminaron las 4
  copias).

### Plantillas de alto nivel

- `TableSectionTemplate` — una llamada declarativa para una lista estándar (compone
  Shell + Toolbar + Table + Footer). Las pantallas simples la usan.
- `DetailSectionTemplate` — el marco de una vista de detalle (`:id`): mismo `SectionShell`
  con breadcrumb, pestañas (Lista vuelve al listado) y slot de acciones.

### Regla

**Toda vista de tabla nueva se construye con `components/section/`.** Las pantallas que no
encajan en `TableSectionTemplate` (cuerpo a medida: subida de archivos, tableros de tareas)
componen los primitivos directamente — nunca vuelven a escribir el markup del chrome.

### Roadmap por `section_type`

Sólo existe hoy la plantilla `table`. `functional` / `metrics` / `bucket` usan `SectionShell`
+ primitivos con cuerpo propio; tendrán su plantilla dedicada cuando haya suficientes
pantallas de ese tipo que lo justifiquen.

## Consecuencias

### Positivas

- Un cambio de estructura del chrome se hace en **un solo punto** y todas las vistas lo
  adoptan.
- Congruencia garantizada entre pantallas (incluida la corrección del folder-tab en tema
  claro, que ahora vale para todas).
- Pantallas nuevas más cortas y difíciles de "desalinear".

### Costos / estado de la migración

- Migradas a la plantilla/primitivos: **Reportes de Falla** (a `TableSectionTemplate`),
  **Secciones del Admin** (a `TableSectionTemplate`), **Catálogo de Agentes**, **Archivos**
  y **Tareas** (a los primitivos, conservando su lógica y sus cuerpos a medida).
- **Pendiente: `CareerResourceView`** (los ~30 recursos de carrera). Es el archivo más
  grande (1600+ líneas) y con más modos (singleton, anidado, export PDF, capsulas de
  select, json-list). Su migración se hace como cambio propio y **verificado a mano** sobre
  recursos representativos (`competencies`, `vacancies`, un singleton como `identity`, y un
  export de `cv-versions`) — delegada a `admin-panel-specialist`.
- `TableColumnSettings` conserva sus `storageKey` por recurso → no se pierden las
  preferencias de columnas de los usuarios.

### Alternativas rechazadas

- **Sólo una plantilla declarativa `<TableSectionTemplate config={...}>`**: cualquier caso
  especial (Tareas, subida de Archivos, preview PDF de carrera) obligaría a props de escape
  que ensucian la API. De ahí el split primitivos + plantilla.
- **Sólo primitivos, sin plantilla de alto nivel**: más verboso por pantalla y sin un
  "camino feliz" evidente para la lista estándar.
- **Extender el motor genérico `CareerResourceView`** para cubrir también las pantallas
  no-carrera: ese motor está acoplado al repositorio de carrera (`careerApi`, FK, formularios
  de campo); forzarlo habría sido peor que el markup duplicado.

## Referencias

- `cjhirashi-career-admin/src/components/section/` (+ `README.md`, `templates/`)
- `cjhirashi-career-admin/src/hooks/useSectionTable.ts`
- `cjhirashi-career-admin/src/utils/tableColumns.ts` (`compareCells`)
- Pantallas migradas: `src/pages/ErrorReportsPage.tsx`, `AdminSectionsPage.tsx`,
  `AgentCatalogPage.tsx`, `FilesPage.tsx`, `TasksPage.tsx`
- [ADR-018](./018-error-reports-registry.md) (Reportes de Falla, la pantalla de referencia)

---

**Creado por**: Arquitecto de Soluciones
**Fecha de creación**: 2026-08-27
**Estado de vigencia**: Vigente (migración de `CareerResourceView` pendiente)
