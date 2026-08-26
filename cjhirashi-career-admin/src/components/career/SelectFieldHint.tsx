import React from 'react'
import { FieldConfig, selectFieldMeta } from '@/config/careerResources'

/** Muted hint on select/multi-select titles: tabla vs lista, opción vs múltiple. */
export const SelectFieldHint: React.FC<{ field: FieldConfig }> = ({ field }) => {
  const meta = selectFieldMeta(field)
  if (!meta) return null
  return (
    <span className="ml-1.5 font-normal text-[11px] text-text-muted tracking-normal">
      · {meta.source} · {meta.cardinality}
    </span>
  )
}
