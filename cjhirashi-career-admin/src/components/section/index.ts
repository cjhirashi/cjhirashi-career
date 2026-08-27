// Shared building blocks for every Admin section. See ./README.md.
export { SectionShell } from './SectionShell'
export type { SectionBreadcrumb } from './SectionShell'
export { SectionToolbar } from './SectionToolbar'
export type { ColumnSettingsProps } from './SectionToolbar'
export { SectionTable } from './SectionTable'
export { SectionTableFooter } from './SectionTableFooter'
export {
  SectionRecordView,
  SectionFieldGroup,
  SectionField,
} from './SectionRecordView'
export type { RecordGroupSpec, RecordFieldSpec } from './SectionRecordView'
export { TableSectionTemplate } from './templates/TableSectionTemplate'
export { DetailSectionTemplate } from './templates/DetailSectionTemplate'
export { useSectionTable } from '@/hooks/useSectionTable'
