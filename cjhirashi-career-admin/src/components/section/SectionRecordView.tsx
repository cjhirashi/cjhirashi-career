import React from 'react'

/** One label/value pair in a record (detail) view. `wide` spans both columns. */
export const SectionField: React.FC<{
  label: string
  children: React.ReactNode
  wide?: boolean
}> = ({ label, children, wide }) => (
  <div className={wide ? 'md:col-span-2' : ''}>
    <dt className="text-xs text-text-secondary mb-1">{label}</dt>
    <dd className="text-sm text-text">{children}</dd>
  </div>
)

/** A titled group of fields laid out as a 2-column `<dl>` grid. */
export const SectionFieldGroup: React.FC<{
  title?: string
  children: React.ReactNode
}> = ({ title, children }) => (
  <div>
    {title && (
      <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
        {title}
      </h3>
    )}
    <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">{children}</dl>
  </div>
)

export interface RecordFieldSpec {
  label: string
  value: React.ReactNode
  wide?: boolean
}

export interface RecordGroupSpec {
  title?: string
  fields: RecordFieldSpec[]
}

/**
 * Declarative record view: a stack of titled 2-column field groups. Shared by
 * every section detail page so their "Información" blocks look identical.
 */
export const SectionRecordView: React.FC<{ groups: RecordGroupSpec[] }> = ({ groups }) => (
  <div className="space-y-6">
    {groups.map((group, i) => (
      <SectionFieldGroup key={group.title ?? i} title={group.title}>
        {group.fields.map((field) => (
          <SectionField key={field.label} label={field.label} wide={field.wide}>
            {field.value}
          </SectionField>
        ))}
      </SectionFieldGroup>
    ))}
  </div>
)
